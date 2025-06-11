import logging
import requests
from tqdm import tqdm
from utilities.tools import insert_into_postgresql  # Custom utility for inserting data into PostgreSQL
import io
from pyspark.sql.functions import concat, col

def get_values(dataset_ids):
    """
    Fetch data items for a list of dataset IDs from a remote API and concatenate them into a single CSV string.
    
    Parameters:
    dataset_ids (list): List of dataset IDs to fetch data for.

    Returns:
    str: A concatenated CSV string containing data from all requested datasets.
    """

    # Base URL for the API endpoint
    base_url = "https://myhospitalsapi.aihw.gov.au/api/v1/datasets/"
    
    # Headers for the API request
    headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  # A personal token is not actually reuired, you can leave this as it is
        'User-Agent': 'MyApp/1.0',
        'accept': 'text/csv'  # Expecting CSV response
    }

    # Initialize an empty string to concatenate CSV data
    concatenated_csv = ""
    
    # Loop through each dataset ID and fetch its corresponding data
    for dataset_id in dataset_ids:
        # Construct the URL for the specific dataset
        url = f"{base_url}{dataset_id}/data-items"
        try:
            # Send GET request to the API
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # If request is successful, append the CSV data to the string
                concatenated_csv += response.text
            else:
                # Log an error if the request fails with a non-200 status code
                logging.error(f"Failed to fetch dataset {dataset_id}. Status code: {response.status_code}")
        except Exception as e:
            # Log any exceptions that occur during the request
            logging.error(f"Exception occurred while fetching dataset {dataset_id}: {e}")

    # Return the concatenated CSV data
    return concatenated_csv

def callback_values(spark_session, ch, method, properties, body):
    """
    Process a CSV message from RabbitMQ, transform it into a Spark DataFrame, and insert it into a PostgreSQL table.

    Parameters:
    spark_session (SparkSession): The Spark session to use for DataFrame operations.
    ch (BlockingChannel): The channel object from RabbitMQ.
    method (Method): The method frame with delivery information.
    properties (BasicProperties): The properties for the message.
    body (bytes): The message body containing the CSV data.
    """
    try:
        # Decode the message body from bytes to a UTF-8 string
        csv_data = body.decode('utf-8')
        
        # Create an in-memory stream from the CSV string data
        csv_stream = io.StringIO(csv_data)
        # Split the CSV data into lines
        csv_lines = csv_stream.getvalue().split("\n")
        
        # Parallelize the CSV lines into an RDD
        csv_rdd = spark_session.sparkContext.parallelize(csv_lines)

        # Read the RDD as a CSV into a Spark DataFrame
        sdf = spark_session.read.csv(csv_rdd, header=True, inferSchema=True)

        # Convert all column names to lowercase to maintain consistency
        for column in sdf.columns:
            sdf = sdf.withColumnRenamed(column, column.lower())

        # Select relevant columns for the 'info' table
        values = sdf.select('datasetid', 'reportingunitcode', 'value', 'caveats')

        # Generate a unique ID by concatenating 'datasetid' and 'reportingunitcode'
        values = values.withColumn('id', concat(col('datasetid'), col('reportingunitcode')))
        
        # Insert the DataFrame into the PostgreSQL 'info' table
        insert_into_postgresql(spark_session, values, 'info')

        # Acknowledge that the message has been processed successfully
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        # Log any errors that occur during the message processing
        logging.error(f"Failed to process message: {e}")
