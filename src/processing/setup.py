from pyspark.sql import SparkSession 
import utilities.tables 

# Step 1: Initialize the database schema
# This function call creates the necessary tables in the PostgreSQL database
# based on the schema defined in the 'utilities.tables' module.
utilities.tables.schema()

# Step 2: Create a Spark session
# A Spark session is necessary for performing distributed data processing tasks with PySpark.
# The 'appName' parameter sets the name of the application, which is useful for identifying the job in Spark's UI.
# The 'config' method is used to set the class path for the PostgreSQL JDBC driver, which allows Spark to connect to PostgreSQL.
spark = SparkSession.builder \
    .appName("Healthcare-Resource-Allocation") \
    .config("spark.driver.extraClassPath", "/opt/bitnami/spark/processing/jars/postgresql-42.7.3.jar") \
    .getOrCreate()
