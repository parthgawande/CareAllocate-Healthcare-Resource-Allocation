import logging
import pandas as pd
import pika
import time
from tqdm import tqdm
import requests
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_date
import psycopg2

def update_stored(batch):
    """Update the 'stored' status of datasets in the PostgreSQL database."""
    
    # Connection details for PostgreSQL
    conn_details = {
        "host": "postgres",
        "dbname": "mydatabase",
        "user": "myuser",
        "password": "mypassword"
    }

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**conn_details)
    cursor = conn.cursor()

    # Prepare the SQL query with parameterized inputs to prevent SQL injection
    sql = "UPDATE datasets SET stored = TRUE WHERE DataSetId = ANY(%s);"

    try:
        # Execute the SQL command
        cursor.execute(sql, (batch,))
        conn.commit()  # Commit the changes to the database
        print(f"Updated {cursor.rowcount} rows successfully.")
    except Exception as e:
        # Rollback changes if an error occurs and print the error
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        # Close the cursor and connection to free up resources
        cursor.close()
        conn.close()

def map_hospitals(spark_session):
    """Fetch hospital mapping data from an API and insert it into a PostgreSQL table."""
    print('Fetching Hospitals data...')
    
    # API endpoint and headers for authentication
    url = "https://myhospitalsapi.aihw.gov.au/api/v1/reporting-units-downloads/mappings"
    headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  # A personal token is not actually reuired, you can leave this as it is
        'User-Agent': 'MyApp/1.0',
        'accept': 'application/json'
    }

    # Send a GET request to the API
    response = requests.get(url, headers=headers)
    filename = 'hospital_mapping.xlsx'

    # Save the API response content to an Excel file
    with open(filename, 'wb') as file:
        file.write(response.content)

    # Load the Excel file into a Pandas DataFrame
    df = pd.read_excel(filename, engine='openpyxl', skiprows=3)

    # Convert the Pandas DataFrame to a Spark DataFrame
    sdf = spark_session.createDataFrame(df)

    # Rename columns to match database schema
    sdf = sdf.withColumnRenamed("Open/Closed", "Open_Closed") \
             .withColumnRenamed("Local Hospital Network (LHN)", "LHN") \
             .withColumnRenamed("Primary Health Network area (PHN)", "PHN")

    # Convert all column names to lowercase
    for column in sdf.columns:
        sdf = sdf.withColumnRenamed(column, column.lower())
    
    # Insert the DataFrame into the PostgreSQL 'hospitals' table
    insert_into_postgresql(spark_session, sdf, "hospitals")
    print("Hospital mapping inserted successfully into the PostgreSQL database")

def get_ids():
    """Fetch all DataSetIds from the 'datasets' table where 'stored' is False."""
    
    # Connection details for PostgreSQL
    conn_details = {
        "host": "postgres",
        "dbname": "mydatabase",
        "user": "myuser",
        "password": "mypassword"
    }

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**conn_details)
    cursor = conn.cursor()

    # SQL query to select DataSetIds where 'stored' is False
    sql = "SELECT DataSetId FROM datasets WHERE stored = FALSE;"

    try:
        # Execute the query
        cursor.execute(sql)
        # Fetch all rows from the query result
        rows = cursor.fetchall()
        # Extract DataSetIds from the rows
        dataset_ids = [row[0] for row in rows]
        return dataset_ids
    except Exception as e:
        # Print an error message if the query fails
        print(f"An error occurred: {e}")
        return []  # Return an empty list in case of error
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

def insert_into_postgresql(spark, data_frame, table_name):
    """Insert data from a Spark DataFrame into a PostgreSQL table, ensuring only new records are added."""
    
    # JDBC URL and connection properties for PostgreSQL
    url = "jdbc:postgresql://postgres:5432/mydatabase"
    properties = {
        "user": "myuser",
        "password": "mypassword",
        "driver": "org.postgresql.Driver"
    }

    # Mapping of table names to their primary key columns
    ids = {
        "hospitals" : 'code',
        "measurements" : 'measurecode',
        "reported_measurements" : 'reportedmeasurecode',
        "datasets" : 'datasetid',
        "info" : "id"
    }

    # Read existing data from the PostgreSQL table
    try:
        existing_df = spark.read.format("jdbc") \
            .option("url", url) \
            .option("dbtable", table_name) \
            .option("user", properties["user"]) \
            .option("password", properties["password"]) \
            .option("driver", properties["driver"]) \
            .load()

        # Check if the primary key exists in the DataFrame columns
        if ids[table_name] in data_frame.columns:
            # Perform a left anti join to find records not present in the existing data
            new_records_df = data_frame.join(existing_df, data_frame[ids[table_name]] == existing_df[ids[table_name]], "left_anti")
            
            # If there are new records, insert them into the PostgreSQL table
            if new_records_df.count() > 0:
                new_records_df.write.format("jdbc") \
                    .option("url", url) \
                    .option("dbtable", table_name) \
                    .option("user", properties["user"]) \
                    .option("password", properties["password"]) \
                    .option("driver", properties["driver"]) \
                    .mode("append") \
                    .save()
                logging.info(f"Data successfully inserted into {table_name}.")
            else:
                logging.info("No new unique records to insert.")
        else:
            logging.error("Primary key not in DataFrame columns.")
            logging.error(table_name)

    except Exception as e:
        # Log an error message if the interaction with PostgreSQL fails
        logging.error(f"Failed to interact with PostgreSQL: {e}")
        raise

def send_to_rabbitmq(concatenated_csv):
    """Send concatenated CSV data to a RabbitMQ queue."""
    
    connection_attempts = 0
    max_attempts = 5
    
    # Try to establish a connection to RabbitMQ, with retries
    while connection_attempts < max_attempts:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            channel = connection.channel()
            channel.queue_declare(queue='values_queue')
            channel.basic_publish(exchange='', routing_key='values_queue', body=concatenated_csv)
        
            logging.info("Data sent to RabbitMQ.")
            connection.close()
            return
        except Exception as e:
            # Log an error and increment the attempt counter if connection fails
            logging.error(f"Failed to send CSV files to RabbitMQ: {e}")
            connection_attempts += 1
            time.sleep(5)
    
    # Log an error message if maximum connection attempts are exceeded
    logging.error("Exceeded maximum attempts to connect to RabbitMQ.")

def consume_from_rabbitmq(spark_session, queue_name, callback_function):
    """Consume messages from a RabbitMQ queue and process them using a callback function."""
    
    try:
        # Setup the connection to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        
        # Ensure the queue exists
        channel.queue_declare(queue=queue_name, passive=True)

        # Define the callback function to handle incoming messages
        def on_message_callback(ch, method, properties, body):
            callback_function(spark_session, ch, method, properties, body)
        
        # Start consuming messages from the queue
        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback, auto_ack=True)
        
        logging.info(f'[*] Waiting for messages on queue "{queue_name}". To exit press CTRL+C')
        channel.start_consuming()

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully
        logging.info("KeyboardInterrupt detected. Stopping consumption.")
        channel.stop_consuming()
    except Exception as e:
        # Log any exceptions that occur during consumption
        logging.error(f"Failed to consume messages from RabbitMQ: {e}")
    finally:
        # Ensure the connection is closed when done or if an error occurs
        if 'connection' in locals():
            connection.close()

def download_datasetlist(spark_session):
    """Download a list of datasets from an API, process it, and insert relevant data into PostgreSQL."""
    
    # API endpoint and headers for authentication
    url = "https://myhospitalsapi.aihw.gov.au/api/v1/datasets/"
    headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  # A personal token is not actually reuired, you can leave this as it is
        'User-Agent': 'MyApp/1.0',
        'accept': 'text/csv'
    }
    
    try:
        # Send a GET request to download the dataset list as a CSV
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_path = 'datasets.csv'
            # Save the CSV content to a file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logging.info("List of available data retrieved")

            # Load the CSV file into a Pandas DataFrame
            df = pd.read_csv(file_path)
            
            # Convert the Pandas DataFrame to a Spark DataFrame
            sdf = spark_session.createDataFrame(df)

            # Convert all column names to lowercase
            for column in sdf.columns:
                sdf = sdf.withColumnRenamed(column, column.lower())
        
            # Select and process specific columns
            reportedmeasurements = sdf.select('reportedmeasurecode', 'reportedmeasurename').dropDuplicates()
            measurements = sdf.select('measurecode', 'measurename').dropDuplicates()
            values = sdf.select('reportingstartdate', 'reportedmeasurecode', 'datasetid', 'measurecode', 'datasetname')
            values = values.withColumn("reportingstartdate", to_date(col("reportingstartdate"), "yyyy-MM-dd"))
        
            # Insert processed data into PostgreSQL tables
            insert_into_postgresql(spark_session, reportedmeasurements, "reported_measurements")
            insert_into_postgresql(spark_session, measurements, "measurements")
            insert_into_postgresql(spark_session, values, "datasets")

        else:
            # Log an error if the API request fails
            logging.error(f"Failed to fetch data. Status code: {response.status_code}")
            return None
    except Exception as e:
        # Log an error if an exception occurs during the data download process
        logging.error(f"Exception occurred while fetching datasets list: {e}")
        return None
