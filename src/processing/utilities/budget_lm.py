import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import col

def predict_budget():
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("Python Spark MLlib Example") \
        .getOrCreate()

    # Define file paths
    population_historic_file = "/app/files/data/Population.xlsx"
    population_prediction_file = "/app/files/data/Population Projections.xlsx"
    budget_data_file = "/app/files/data/Expediture.xlsx"

    # Load historical population data
    population_historic = pd.read_excel(population_historic_file, sheet_name=0, skiprows=1)
    population_historic = population_historic.iloc[:, [0, -1]] 
    population_historic.columns = ["Year", "TotalPopulation"]
    population_historic = population_historic.dropna()
    population_historic["Year"] = population_historic["Year"].astype(int)
    population_historic["TotalPopulation"] = population_historic["TotalPopulation"].astype(float)

    # Load population prediction data
    population_prediction = pd.read_excel(population_prediction_file, skiprows=1)
    population_prediction.columns = ["Year", "High series", "Medium series", "Low series", "Zero net overseas migration"]

    # Load budget data
    budget_data = pd.read_excel(budget_data_file, sheet_name="Table 5", usecols="A:X", skiprows=[0, 1], nrows=12)
    budget_data = budget_data.drop(budget_data.index[[0, 1]])
    budget_data = budget_data.drop(columns=[budget_data.columns[i] for i in [2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23]])
    budget_data.columns = ["Year", "NSW", "Vic", "Qld", "WA", "SA", "Tas", "NT", "NAT"]
    budget_data["Year"] = list(range(2011, 2011 + len(budget_data)))

    # Distribute population across states
    np.random.seed(42)
    proportions = {
        "NSW": 0.31, "Vic": 0.25, "Qld": 0.20, "WA": 0.10, 
        "SA": 0.07, "Tas": 0.02, "NT": 0.01, "ACT": 0.04
    }

    for state, prop in proportions.items():
        population_historic[state] = population_historic["TotalPopulation"] * prop

    # Merge budget and population data
    merged_data = pd.merge(budget_data, population_historic, on="Year")
    merged_data = merged_data.dropna(subset=["NAT"])

    # Convert to Spark DataFrames
    historical_data_spark = spark.createDataFrame(merged_data)
    population_prediction_spark = spark.createDataFrame(population_prediction)

    # Assemble features for training
    assembler = VectorAssembler(inputCols=["TotalPopulation"], outputCol="features")
    training_data = assembler.transform(historical_data_spark.select("TotalPopulation", col("NAT").alias("label")))

    # Train Linear Regression model
    lr = LinearRegression(featuresCol="features", labelCol="label")
    lr_model = lr.fit(training_data)

    # Prepare predictions for high, medium, and low series
    predictions_high = population_prediction_spark.withColumn("TotalPopulation", col("High series"))
    predictions_medium = population_prediction_spark.withColumn("TotalPopulation", col("Medium series"))
    predictions_low = population_prediction_spark.withColumn("TotalPopulation", col("Low series"))

    assembler_prediction = VectorAssembler(inputCols=["TotalPopulation"], outputCol="features")
    predictions_high = assembler_prediction.transform(predictions_high)
    predictions_medium = assembler_prediction.transform(predictions_medium)
    predictions_low = assembler_prediction.transform(predictions_low)

    # Generate predictions
    predicted_high = lr_model.transform(predictions_high).select("Year", "prediction").withColumnRenamed("prediction", "Predicted Budget (High)")
    predicted_medium = lr_model.transform(predictions_medium).select("Year", "prediction").withColumnRenamed("prediction", "Predicted Budget (Medium)")
    predicted_low = lr_model.transform(predictions_low).select("Year", "prediction").withColumnRenamed("prediction", "Predicted Budget (Low)")

    # Display predictions
    predicted_high.show()
    predicted_medium.show()
    predicted_low.show()

    return predicted_high, predicted_medium, predicted_low
