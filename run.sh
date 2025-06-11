#!/bin/bash

SPARK_MASTER_URL=spark://spark-master:7077
PROGRAM_PATH=processing/ETL.py

# Build and start the Docker containers
docker compose up --build -d

# Infinite loop to run the spark-submit command every day
while true; do
  # Execute the spark-submit command
  docker compose exec spark-master spark-submit --jars processing/jars/postgresql-42.7.3.jar --master $SPARK_MASTER_URL $PROGRAM_PATH
  
  # Sleep for 24 hours (86400 seconds)
  sleep 86400
done
