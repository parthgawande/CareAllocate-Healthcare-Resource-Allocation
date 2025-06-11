###################################### DA sistemare !! ##############################################################

#LINEAR MODEL

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import col
import psycopg2
import matplotlib.pyplot as plt


spark = SparkSession.builder \
    .appName("Python Spark MLlib Example") \
    .getOrCreate()

file_path = "/Users/soniaborsi/Desktop/aihw-93-Health-expenditure-Australia-2021-2022.xlsx"
budget_state_per_capital = pd.read_excel(file_path, sheet_name="Table 5", usecols="A:X", skiprows=[0, 1], nrows=12)

budget_state_per_capital = budget_state_per_capital.drop(budget_state_per_capital.index[[0, 1]])
budget_state_per_capital = budget_state_per_capital.drop(columns=[budget_state_per_capital.columns[i] for i in [2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23]])
print("Length of DataFrame after dropping rows and columns:", len(budget_state_per_capital))

budget_state_per_capital.columns = ["Year","NSW", "Vic", "Qld", "WA", "SA", "Tas", "NT", "NAT"]
budget_state_per_capital["Year"] = list(range(2011, 2011 + len(budget_state_per_capital)))
budget_state_per_capital = budget_state_per_capital[["Year"] + sorted(budget_state_per_capital.columns[1:])]
budget_state_per_capital_spark = spark.createDataFrame(budget_state_per_capital)
print(budget_state_per_capital)


conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="myuser",
    password="mypassword",
    dbname="mydatabase"
)

query = "SELECT * FROM values" #qui dobbiamo selezionare le values dei dataset su cui vogliamo fare predicitons (measure)
values = pd.read_sql(query, conn)
conn.close()


values_national = values[values["ReportingUnitCode"].isin(["NSW", "Vic", "Qld", "SA", "WA", "Tas", "NAT"])]
values_wide = values_national.pivot(index='DataSetId', columns='ReportingUnitCode', values='Value').reset_index(drop=True)
values_wide = values_wide[sorted(values_wide.columns)]
values_wide["Year"] = list(range(2011, 2011 + len(values_wide)))
values_wide = values_wide[["Year"] + sorted(values_wide.columns[:-1])]
values_wide = values_wide.iloc[:-1]  # Removing the last row to have 11 years

values_wide.columns = ["Year"] + [f"{col}_values" for col in values_wide.columns if col != "Year"]

values_wide_spark = spark.createDataFrame(values_wide)


models = {}
coefficients_list = []

for col_name in values_wide_spark.columns[1:]:
    dataset = budget_state_per_capital_spark.join(values_wide_spark, on='Year') \
                                            .select(col("Year"), 
                                                    col(col_name).alias("y").cast("double"),
                                                    *[col(c).alias("x_" + c).cast("double") for c in budget_state_per_capital_spark.columns if c != "Year"])
    
    dataset = dataset.na.drop()
    

    feature_cols = [c for c in dataset.columns if c.startswith("x_")]
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    dataset = assembler.transform(dataset).select("features", col("y").alias("label"))
    

    train_data, test_data = dataset.randomSplit([0.8, 0.2])
    
    lr = LinearRegression(featuresCol="features", labelCol="label")
    lr_model = lr.fit(train_data)
    
    models[col_name] = lr_model
    coefficients_list.append((col_name, lr_model.coefficients))


for col_name, coeff in coefficients_list:
    print(f"Coefficients for {col_name}: {coeff}")

spark.stop()


# LM WITH L1 REGULARIZATION 
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.regression import LinearRegression
import psycopg2

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Python Spark MLlib Example") \
    .getOrCreate()

# File path
file_path = "/Users/soniaborsi/Desktop/aihw-93-Health-expenditure-Australia-2021-2022.xlsx"

# Load budget data from Excel
budget_state_per_capital = pd.read_excel(file_path, sheet_name="Table 5", usecols="A:X", skiprows=[0, 1], nrows=12)

# Drop unnecessary rows and columns
budget_state_per_capital = budget_state_per_capital.drop(budget_state_per_capital.index[[0, 1]])
columns_to_keep = [0, 2, 4, 7, 10, 13, 16, 19, 22]
budget_state_per_capital = budget_state_per_capital.iloc[:, columns_to_keep]

# Rename columns
budget_state_per_capital.columns = ["Year", "NAT", "NSW", "NT", "Qld", "SA", "Tas", "Vic", "WA"]
budget_state_per_capital["Year"] = list(range(2011, 2011 + len(budget_state_per_capital)))

# Ensure correct column order
budget_state_per_capital = budget_state_per_capital[["Year"] + sorted(budget_state_per_capital.columns[1:])]

# Convert to Spark DataFrame
budget_state_per_capital_spark = spark.createDataFrame(budget_state_per_capital)

# Connect to PostgreSQL database and load values
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="myuser",
    password="mypassword",
    dbname="mydatabase"
)

query = "SELECT * FROM values"  # Adjust this query as needed
values = pd.read_sql(query, conn)
conn.close()

# Filter and pivot the values DataFrame
values_national = values[values["ReportingUnitCode"].isin(["NSW", "Vic", "Qld", "SA", "WA", "Tas", "NAT"])]
values_wide = values_national.pivot(index='DataSetId', columns='ReportingUnitCode', values='Value').reset_index(drop=True)
values_wide["Year"] = list(range(2011, 2011 + len(values_wide)))
values_wide = values_wide[["Year"] + sorted(values_wide.columns[:-1])]
values_wide = values_wide.iloc[:-1]  # Removing the last row to have 11 years
values_wide.columns = ["Year"] + [f"{col}_values" for col in values_wide.columns if col != "Year"]

# Convert to Spark DataFrame
values_wide_spark = spark.createDataFrame(values_wide)

# Model training
models = {}
coefficients_list = []

for col_name in values_wide_spark.columns[1:]:
    dataset = budget_state_per_capital_spark.join(values_wide_spark, on='Year') \
                                            .select(col("Year"),
                                                    col(col_name).alias("y").cast("double"),
                                                    *[col(c).alias("x_" + c).cast("double") for c in budget_state_per_capital_spark.columns if c != "Year"])

    dataset = dataset.na.drop()

    feature_cols = [c for c in dataset.columns if c.startswith("x_")]
    
    # Feature scaling
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_unscaled")
    dataset = assembler.transform(dataset)

    scaler = StandardScaler(inputCol="features_unscaled", outputCol="features", withStd=True, withMean=True)
    scaler_model = scaler.fit(dataset)
    dataset = scaler_model.transform(dataset).select("features", col("y").alias("label"))

    train_data, test_data = dataset.randomSplit([0.8, 0.2])

    lr = LinearRegression(featuresCol="features", labelCol="label", elasticNetParam=0.8)  # Using L1 regularization
    lr_model = lr.fit(train_data)

    models[col_name] = lr_model
    coefficients_list.append((col_name, lr_model.coefficients))

for col_name, coeff in coefficients_list:
    print(f"Coefficients for {col_name}: {coeff}")

# Stop Spark session
spark.stop()

