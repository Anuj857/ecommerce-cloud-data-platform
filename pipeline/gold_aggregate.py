import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as spark_sum, count, round


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")
GOLD_DIR = os.path.join(BASE_DIR, "data", "gold")


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv(os.path.join(BASE_DIR, ".env"))


RDS_ENDPOINT = os.getenv("RDS_ENDPOINT")
RDS_PORT = os.getenv("RDS_PORT", "5432")
RDS_DB_NAME = os.getenv("RDS_DB_NAME", "postgres")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")


required_variables = {
    "RDS_ENDPOINT": RDS_ENDPOINT,
    "RDS_USER": RDS_USER,
    "RDS_PASSWORD": RDS_PASSWORD,
}

missing_variables = [
    key
    for key, value in required_variables.items()
    if not value
]

if missing_variables:
    raise ValueError(
        "Missing environment variables: "
        + ", ".join(missing_variables)
    )


DATABASE_URL = (
    f"postgresql://{RDS_USER}:{RDS_PASSWORD}"
    f"@{RDS_ENDPOINT}:{RDS_PORT}/{RDS_DB_NAME}"
)


# ---------------------------------------------------------
# Main processing
# ---------------------------------------------------------

def main():

    print("Starting Gold Layer processing...")

    spark = (
        SparkSession.builder
        .appName("Ecommerce-Gold-Layer")
        .master("local[*]")
        .getOrCreate()
    )

    os.makedirs(GOLD_DIR, exist_ok=True)

    print("Spark session created.")


    # -----------------------------------------------------
    # Silver paths
    # -----------------------------------------------------

    orders_path = os.path.join(
        SILVER_DIR,
        "orders"
    )

    items_path = os.path.join(
        SILVER_DIR,
        "order_items"
    )

    customers_path = os.path.join(
        SILVER_DIR,
        "customers"
    )


    # -----------------------------------------------------
    # Check input data
    # -----------------------------------------------------

    if not os.path.exists(orders_path):
        raise FileNotFoundError(
            f"Orders dataset not found: {orders_path}"
        )

    if not os.path.exists(items_path):
        raise FileNotFoundError(
            f"Order items dataset not found: {items_path}"
        )

    if not os.path.exists(customers_path):
        raise FileNotFoundError(
            f"Customers dataset not found: {customers_path}"
        )


    # -----------------------------------------------------
    # Read Silver data
    # -----------------------------------------------------

    print("Reading Silver datasets...")

    df_orders = spark.read.parquet(orders_path)
    df_items = spark.read.parquet(items_path)
    df_customers = spark.read.parquet(customers_path)


    # -----------------------------------------------------
    # 1. Fact Orders
    # -----------------------------------------------------

    print("Creating fact_orders...")

    order_metrics = (
        df_items
        .groupBy("order_id")
        .agg(
            round(
                spark_sum("price"),
                2
            ).alias("total_order_value"),

            round(
                spark_sum("freight_value"),
                2
            ).alias("total_freight"),

            count(
                "order_item_id"
            ).alias("item_count")
        )
    )


    fact_orders = (
        df_orders
        .join(
            order_metrics,
            on="order_id",
            how="inner"
        )
        .select(
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "total_order_value",
            "total_freight",
            "item_count"
        )
    )


    fact_orders.write.mode(
        "overwrite"
    ).parquet(
        os.path.join(
            GOLD_DIR,
            "fact_orders"
        )
    )

    print("Gold Parquet created: fact_orders")


    # -----------------------------------------------------
    # 2. Customer Dimension
    # -----------------------------------------------------

    print("Creating dim_customers...")

    dim_customers = (
        df_customers
        .select(
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state"
        )
        .dropDuplicates()
    )


    dim_customers.write.mode(
        "overwrite"
    ).parquet(
        os.path.join(
            GOLD_DIR,
            "dim_customers"
        )
    )

    print("Gold Parquet created: dim_customers")


    # -----------------------------------------------------
    # 3. Connect to RDS
    # -----------------------------------------------------

    print("Connecting to AWS RDS PostgreSQL...")

    engine = create_engine(
        DATABASE_URL
    )


    # -----------------------------------------------------
    # Convert Spark DataFrames to Pandas
    # -----------------------------------------------------

    print("Preparing data for RDS...")

    pd_fact_orders = fact_orders.toPandas()
    pd_dim_customers = dim_customers.toPandas()


    # -----------------------------------------------------
    # Clear existing data
    # -----------------------------------------------------

    with engine.connect() as conn:

        conn.execute(
            text(
                """
                TRUNCATE TABLE
                    fact_orders,
                    dim_customers;
                """
            )
        )

        conn.commit()


    # -----------------------------------------------------
    # Load fact_orders
    # -----------------------------------------------------

    pd_fact_orders.to_sql(
        "fact_orders",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000
    )

    print(
        f"Loaded fact_orders: "
        f"{len(pd_fact_orders):,} records"
    )


    # -----------------------------------------------------
    # Load dim_customers
    # -----------------------------------------------------

    pd_dim_customers.to_sql(
        "dim_customers",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000
    )

    print(
        f"Loaded dim_customers: "
        f"{len(pd_dim_customers):,} records"
    )


    # -----------------------------------------------------
    # Finish
    # -----------------------------------------------------

    engine.dispose()

    spark.stop()

    print("Gold layer processing completed successfully.")


if __name__ == "__main__":
    main()