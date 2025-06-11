from sqlalchemy import create_engine, text
from contextlib import contextmanager
import sqlalchemy.exc

# Global engine configuration to connect to a PostgreSQL database
# The connection string includes the username, password, host, port, and database name
# pool_size defines the number of connections to keep in the pool
# max_overflow allows additional connections above the pool size
engine = create_engine('postgresql+psycopg2://myuser:mypassword@postgres:5432/mydatabase', pool_size=10, max_overflow=20)

@contextmanager
def get_connection():
    """Provide a transactional scope around a series of operations."""
    # Establish a connection to the database
    connection = engine.connect()
    # Begin a transaction on this connection
    transaction = connection.begin()
    try:
        # Yield the connection to the caller, allowing them to execute queries within this context
        yield connection
        # If no exceptions occur, commit the transaction
        transaction.commit()
    except sqlalchemy.exc.SQLAlchemyError as e:
        # If an error occurs during the transaction, print the error message
        print("An error occurred:", e)
        # Rollback the transaction to undo any changes made during the transaction
        transaction.rollback()
    finally:
        # Ensure that the connection is closed after the transaction completes
        connection.close()

def create_table(sql_command):
    """Create a table in the PostgreSQL database."""
    try:
        # Use the get_connection context manager to establish a connection and begin a transaction
        with get_connection() as conn:
            # Execute the provided SQL command to create the table
            conn.execute(text(sql_command))
            print("Table created successfully.")
    except Exception as e:
        # If an error occurs, print a message indicating that table creation failed
        print("Failed to create table:", e)

def schema():
    """Create the schema for the database by initializing required tables."""
    # Define SQL commands to create necessary tables in the database
    tables_sql = [
        """CREATE TABLE IF NOT EXISTS datasets (
            reportingstartdate DATE,
            reportedmeasurecode VARCHAR,
            datasetid INT PRIMARY KEY,
            measurecode VARCHAR,
            datasetname TEXT,
            stored BOOLEAN DEFAULT FALSE
        );""",
        """CREATE TABLE IF NOT EXISTS hospitals (
            code VARCHAR(255) PRIMARY KEY,
            name TEXT,
            type TEXT,
            latitude FLOAT,
            longitude FLOAT,
            sector TEXT,
            open_closed TEXT,
            state TEXT,
            lhn TEXT,
            phn TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS measurements (
            measurecode VARCHAR PRIMARY KEY,
            measurename TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS reported_measurements (
            reportedmeasurecode VARCHAR PRIMARY KEY,
            reportedmeasurename TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS info (
            datasetid INT,
            reportingunitcode VARCHAR,
            value FLOAT,
            caveats TEXT,
            id VARCHAR PRIMARY KEY
        );"""
    ]

    # Loop through each SQL command and create the corresponding table in the database
    for sql in tables_sql:
        create_table(sql)
