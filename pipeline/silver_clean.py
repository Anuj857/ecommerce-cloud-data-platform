import glob
import os
import sys
import urllib.request


# ---------------------------------------------------------
# Java configuration
# ---------------------------------------------------------

java_home = os.environ.get(
    "JAVA_HOME"
)


if not java_home:

    possible_java_paths = glob.glob(
        r"C:\Program Files\Eclipse Adoptium\jdk-17*"
    )

    if possible_java_paths:
        java_home = possible_java_paths[0]


if not java_home:
    raise EnvironmentError(
        "JAVA_HOME is not configured. "
        "Please install Java 17 and set JAVA_HOME."
    )


os.environ["JAVA_HOME"] = java_home


os.environ["PATH"] = (
    os.path.join(
        java_home,
        "bin"
    )
    + os.pathsep
    + os.environ.get(
        "PATH",
        ""
    )
)


# ---------------------------------------------------------
# Hadoop configuration for Windows
# ---------------------------------------------------------

hadoop_dir = os.environ.get(
    "HADOOP_HOME",
    r"C:\hadoop"
)

hadoop_bin = os.path.join(
    hadoop_dir,
    "bin"
)


os.makedirs(
    hadoop_bin,
    exist_ok=True
)


winutils_path = os.path.join(
    hadoop_bin,
    "winutils.exe"
)

hadoop_dll_path = os.path.join(
    hadoop_bin,
    "hadoop.dll"
)


# ---------------------------------------------------------
# Download Windows Hadoop binaries if required
# ---------------------------------------------------------

if not os.path.exists(
    winutils_path
):

    print(
        "Downloading winutils.exe..."
    )

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/winutils.exe",
        winutils_path
    )


if not os.path.exists(
    hadoop_dll_path
):

    print(
        "Downloading hadoop.dll..."
    )

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/hadoop.dll",
        hadoop_dll_path
    )


os.environ["HADOOP_HOME"] = hadoop_dir


os.environ["PATH"] = (
    hadoop_bin
    + os.pathsep
    + os.environ.get(
        "PATH",
        ""
    )
)


# ---------------------------------------------------------
# PySpark Python configuration
# ---------------------------------------------------------

os.environ[
    "PYSPARK_PYTHON"
] = sys.executable

os.environ[
    "PYSPARK_DRIVER_PYTHON"
] = sys.executable


# ---------------------------------------------------------
# Spark imports
# ---------------------------------------------------------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp


# ---------------------------------------------------------
# Project directories
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


BRONZE_DIR = os.path.join(
    BASE_DIR,
    "data"
)


SILVER_DIR = os.path.join(
    BASE_DIR,
    "data",
    "silver"
)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print(
        "Starting Silver Layer processing..."
    )


    spark = (
        SparkSession.builder
        .appName(
            "Ecommerce-Silver-Layer"
        )
        .master("local[*]")
        .getOrCreate()
    )


    os.makedirs(
        SILVER_DIR,
        exist_ok=True
    )


    print(
        "Spark session created."
    )


    # -----------------------------------------------------
    # Orders
    # -----------------------------------------------------

    orders_path = os.path.join(
        BRONZE_DIR,
        "olist_orders_dataset.csv"
    )


    if os.path.exists(
        orders_path
    ):

        print(
            "Processing Orders..."
        )


        df_orders = (
            spark.read
            .option(
                "header",
                True
            )
            .option(
                "inferSchema",
                True
            )
            .csv(
                orders_path
            )
        )


        time_columns = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]


        for column_name in time_columns:

            df_orders = df_orders.withColumn(
                column_name,
                to_timestamp(
                    col(column_name)
                )
            )


        df_orders = (
            df_orders
            .dropDuplicates()
        )


        df_orders.write.mode(
            "overwrite"
        ).parquet(
            os.path.join(
                SILVER_DIR,
                "orders"
            )
        )


        print(
            "Successfully processed: Orders"
        )


    else:

        print(
            "Orders dataset not found."
        )


    # -----------------------------------------------------
    # Customers
    # -----------------------------------------------------

    customers_path = os.path.join(
        BRONZE_DIR,
        "olist_customers_dataset.csv"
    )


    if os.path.exists(
        customers_path
    ):

        print(
            "Processing Customers..."
        )


        df_customers = (
            spark.read
            .option(
                "header",
                True
            )
            .option(
                "inferSchema",
                True
            )
            .csv(
                customers_path
            )
        )


        df_customers = (
            df_customers
            .dropDuplicates()
        )


        df_customers.write.mode(
            "overwrite"
        ).parquet(
            os.path.join(
                SILVER_DIR,
                "customers"
            )
        )


        print(
            "Successfully processed: Customers"
        )


    else:

        print(
            "Customers dataset not found."
        )


    # -----------------------------------------------------
    # Order Items
    # -----------------------------------------------------

    items_path = os.path.join(
        BRONZE_DIR,
        "olist_order_items_dataset.csv"
    )


    if os.path.exists(
        items_path
    ):

        print(
            "Processing Order Items..."
        )


        df_items = (
            spark.read
            .option(
                "header",
                True
            )
            .option(
                "inferSchema",
                True
            )
            .csv(
                items_path
            )
        )


        df_items = (
            df_items
            .dropDuplicates()
        )


        df_items.write.mode(
            "overwrite"
        ).parquet(
            os.path.join(
                SILVER_DIR,
                "order_items"
            )
        )


        print(
            "Successfully processed: Order Items"
        )


    else:

        print(
            "Order Items dataset not found."
        )


    # -----------------------------------------------------
    # Finish
    # -----------------------------------------------------

    print(
        "Silver layer processing complete."
    )


    spark.stop()


if __name__ == "__main__":
    main()