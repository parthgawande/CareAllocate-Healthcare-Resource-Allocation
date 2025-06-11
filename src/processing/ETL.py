import utilities.values as values 
import logging
import utilities.tools as tools 
from tqdm import tqdm  
from setup import spark  

# Configuring the logging settings: 
# INFO level will display informational messages, 
# and the log format includes the timestamp, log level, and message.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Step 1: Map hospitals by fetching data from an API and inserting it into the PostgreSQL 'hospitals' table
tools.map_hospitals(spark)

# Step 2: Download the list of datasets, process it, and insert relevant data into PostgreSQL tables
datasets_csv = tools.download_datasetlist(spark)

# Step 3: Retrieve all dataset IDs from the 'datasets' table where 'stored' is False
datasets_ids = tools.get_ids()

# Step 4: Split the dataset IDs into batches of 20 for processing in chunks
batches = [datasets_ids[i:i+20] for i in range(0, len(datasets_ids), 20)]

# Step 5: Process each batch of dataset IDs
for batch in tqdm(batches, desc='Fetching data ...'):
    # Fetch the data values for the current batch of dataset IDs
    values_csv = values.get_values(batch)
    
    if values_csv:
        # Log that the batch is being processed
        logging.info("Processing batch...")
        
        # Send the concatenated CSV data to RabbitMQ
        tools.send_to_rabbitmq(values_csv)
        
        # Consume the message from RabbitMQ and process the data by inserting it into the PostgreSQL 'info' table
        tools.consume_from_rabbitmq(spark, "values_queue", values.callback_values)
        
        # Update the 'stored' status to True for the dataset IDs in this batch
        tools.update_stored(batch)
