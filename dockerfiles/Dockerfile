# Use the Bitnami Spark 3.5 base image
FROM bitnami/spark:3.5

# Switch to the root user to execute the following commands with superuser privileges
USER root

# Create a cache directory and set permissions to allow read/write access for all users
RUN mkdir -p /.cache && chmod -R 777 /.cache

# Create a directory for processing scripts within the Spark installation
RUN mkdir -p /opt/bitnami/spark/processing

# Copy the processing scripts from the local 'src/processing/' directory to the created directory inside the container
COPY src/processing/ /opt/bitnami/spark/processing

# Install required Python packages specified in the requirements file located in the processing directory
RUN pip install --no-cache-dir -r /opt/bitnami/spark/processing/requirements_spark.txt

# Set the default command to start the Spark master process when the container runs
CMD ["bin/spark-class", "org.apache.spark.deploy.master.Master"]

# Execute the setup script in the processing directory using Python
RUN python3 /opt/bitnami/spark/processing/setup.py

