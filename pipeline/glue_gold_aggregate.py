import json
import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, count, round, avg, datediff, when

spark = SparkSession.builder.appName("Ecommerce-Gold-Layer").getOrCreate()

print("Starting Gold transformation...")

BUCKET = "ecommerce-medallion-lake-2026"
SILVER = f"s3://{BUCKET}/silver"
GOLD = f"s3://{BUCKET}/gold"

SECRET_NAME = "ecommerce/rds/credentials"
AWS_REGION = "ap-south-1"

# Read RDS credentials from Secrets Manager
secrets = boto3.client("secretsmanager", region_name=AWS_REGION)

secret_response = secrets.get_secret_value(SecretId=SECRET_NAME)
credentials = json.loads(secret_response["SecretString"])

RDS_HOST = credentials["host"]
RDS_PORT = credentials["port"]
RDS_DB = credentials["dbname"]
RDS_USER = credentials["username"]
RDS_PASSWORD = credentials["password"]

DATABASE_URL = (
    f"postgresql://{RDS_USER}:{RDS_PASSWORD}"
    f"@{RDS_HOST}:{RDS_PORT}/{RDS_DB}"
)

# Read Silver tables
orders = spark.read.parquet(f"{SILVER}/orders")
order_items = spark.read.parquet(f"{SILVER}/order_items")
customers = spark.read.parquet(f"{SILVER}/customers")
products = spark.read.parquet(f"{SILVER}/products")
sellers = spark.read.parquet(f"{SILVER}/sellers")
payments = spark.read.parquet(f"{SILVER}/payments")
reviews = spark.read.parquet(f"{SILVER}/reviews")
category_translation = spark.read.parquet(
    f"{SILVER}/category_translation"
)

print("Silver data loaded successfully.")

# ---------------------------------------------------------
# DIM CUSTOMERS
# ---------------------------------------------------------

dim_customers = customers.select(
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state"
).dropDuplicates()

dim_customers.write.mode("overwrite").parquet(
    f"{GOLD}/dim_customers"
)

# ---------------------------------------------------------
# DIM PRODUCTS
# ---------------------------------------------------------

dim_products = products

if "product_category_name" in dim_products.columns:
    dim_products = dim_products.join(
        category_translation,
        on="product_category_name",
        how="left"
    )

dim_products = dim_products.dropDuplicates(["product_id"])

dim_products.write.mode("overwrite").parquet(
    f"{GOLD}/dim_products"
)

# ---------------------------------------------------------
# DIM SELLERS
# ---------------------------------------------------------

dim_sellers = sellers.select(
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state"
).dropDuplicates()

dim_sellers.write.mode("overwrite").parquet(
    f"{GOLD}/dim_sellers"
)

# ---------------------------------------------------------
# FACT ORDER ITEMS
# ---------------------------------------------------------

fact_order_items = order_items.select(
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value"
)

fact_order_items = fact_order_items.withColumn(
    "item_revenue",
    round(col("price") + col("freight_value"), 2)
)

fact_order_items.write.mode("overwrite").parquet(
    f"{GOLD}/fact_order_items"
)

# ---------------------------------------------------------
# FACT ORDERS
# ---------------------------------------------------------

order_metrics = order_items.groupBy("order_id").agg(
    round(_sum("price"), 2).alias("total_order_value"),
    round(_sum("freight_value"), 2).alias("total_freight"),
    count("order_item_id").alias("item_count")
)

fact_orders = orders.join(
    order_metrics,
    on="order_id",
    how="left"
).select(
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "total_order_value",
    "total_freight",
    "item_count"
)

fact_orders.write.mode("overwrite").parquet(
    f"{GOLD}/fact_orders"
)

# ---------------------------------------------------------
# FACT PAYMENTS
# ---------------------------------------------------------

fact_payments = payments.select(
    "order_id",
    "payment_sequential",
    "payment_type",
    "payment_installments",
    "payment_value"
)

fact_payments.write.mode("overwrite").parquet(
    f"{GOLD}/fact_payments"
)

# ---------------------------------------------------------
# FACT REVIEWS
# ---------------------------------------------------------

fact_reviews = reviews.select(
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp"
)

fact_reviews.write.mode("overwrite").parquet(
    f"{GOLD}/fact_reviews"
)

# ---------------------------------------------------------
# SALES BY PRODUCT
# ---------------------------------------------------------

sales_by_product = order_items.groupBy(
    "product_id"
).agg(
    count("order_item_id").alias("units_sold"),
    round(_sum("price"), 2).alias("product_revenue"),
    round(avg("price"), 2).alias("average_price"),
    round(_sum("freight_value"), 2).alias("total_freight")
).orderBy(
    col("units_sold").desc()
)

sales_by_product.write.mode("overwrite").parquet(
    f"{GOLD}/sales_by_product"
)

# ---------------------------------------------------------
# SALES BY SELLER
# ---------------------------------------------------------

sales_by_seller = order_items.groupBy(
    "seller_id"
).agg(
    count("order_item_id").alias("items_sold"),
    count("order_id").alias("orders_handled"),
    round(_sum("price"), 2).alias("seller_revenue"),
    round(_sum("freight_value"), 2).alias("seller_freight")
).orderBy(
    col("seller_revenue").desc()
)

sales_by_seller.write.mode("overwrite").parquet(
    f"{GOLD}/sales_by_seller"
)

# ---------------------------------------------------------
# SALES BY CATEGORY
# ---------------------------------------------------------

category_products = products.select(
    "product_id",
    "product_category_name"
)

if "product_category_name_english" in category_translation.columns:
    category_products = category_products.join(
        category_translation.select(
            "product_category_name",
            "product_category_name_english"
        ),
        on="product_category_name",
        how="left"
    )

sales_by_category = order_items.join(
    category_products,
    on="product_id",
    how="left"
).groupBy(
    "product_category_name",
    *(
        ["product_category_name_english"]
        if "product_category_name_english" in category_products.columns
        else []
    )
).agg(
    count("order_item_id").alias("units_sold"),
    round(_sum("price"), 2).alias("category_revenue"),
    round(avg("price"), 2).alias("average_price")
).orderBy(
    col("category_revenue").desc()
)

sales_by_category.write.mode("overwrite").parquet(
    f"{GOLD}/sales_by_category"
)

print("Gold Parquet tables created successfully.")

# ---------------------------------------------------------
# LOAD GOLD TABLES INTO RDS
# ---------------------------------------------------------

print("Loading Gold tables into RDS...")

engine = create_engine(DATABASE_URL)

tables = {
    "dim_customers": dim_customers,
    "dim_products": dim_products,
    "dim_sellers": dim_sellers,
    "fact_order_items": fact_order_items,
    "fact_orders": fact_orders,
    "fact_payments": fact_payments,
    "fact_reviews": fact_reviews,
    "sales_by_product": sales_by_product,
    "sales_by_seller": sales_by_seller,
    "sales_by_category": sales_by_category
}

with engine.begin() as conn:
    for table_name in tables:
        conn.execute(
            text(f"DROP TABLE IF EXISTS {table_name}")
        )

for table_name, dataframe in tables.items():
    print(f"Loading {table_name}...")

    pandas_df = dataframe.toPandas()

    pandas_df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
        chunksize=5000
    )

    print(f"{table_name} loaded successfully.")

print("Gold layer and RDS sync completed successfully.")

spark.stop()