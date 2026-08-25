from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, lower, to_timestamp

spark = SparkSession.builder.appName("Ecommerce-Silver-Transform").getOrCreate()

BUCKET = "ecommerce-medallion-lake-2026"

BRONZE = f"s3://{BUCKET}/bronze"
SILVER = f"s3://{BUCKET}/silver"

print("Starting Silver transformation...")

def clean_columns(df):
    for column in df.columns:
        df = df.withColumnRenamed(column, column.strip().lower())
    return df

def save_parquet(df, name):
    path = f"{SILVER}/{name}"
    df.write.mode("overwrite").parquet(path)
    print(f"Saved: {path}")

# Customers
customers = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_customers_dataset.csv"
)
customers = clean_columns(customers).dropDuplicates()
save_parquet(customers, "customers")

# Orders
orders = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_orders_dataset.csv"
)
orders = clean_columns(orders).dropDuplicates()

timestamp_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for column in timestamp_columns:
    if column in orders.columns:
        orders = orders.withColumn(column, to_timestamp(col(column)))

save_parquet(orders, "orders")

# Order Items
order_items = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_order_items_dataset.csv"
)
order_items = clean_columns(order_items).dropDuplicates()
save_parquet(order_items, "order_items")

# Products
products = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_products_dataset.csv"
)
products = clean_columns(products).dropDuplicates()

if "product_category_name" in products.columns:
    products = products.withColumn(
        "product_category_name",
        lower(trim(col("product_category_name")))
    )

save_parquet(products, "products")

# Sellers
sellers = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_sellers_dataset.csv"
)
sellers = clean_columns(sellers).dropDuplicates()
save_parquet(sellers, "sellers")

# Payments
payments = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_order_payments_dataset.csv"
)
payments = clean_columns(payments).dropDuplicates()
save_parquet(payments, "payments")

# Reviews
reviews = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_order_reviews_dataset.csv"
)
reviews = clean_columns(reviews).dropDuplicates()
save_parquet(reviews, "reviews")

# Geolocation
geolocation = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/olist_geolocation_dataset.csv"
)
geolocation = clean_columns(geolocation).dropDuplicates()
save_parquet(geolocation, "geolocation")

# Category Translation
category_translation = spark.read.option("header", True).option("inferSchema", True).csv(
    f"{BRONZE}/product_category_name_translation.csv"
)
category_translation = clean_columns(category_translation).dropDuplicates()

if "product_category_name" in category_translation.columns:
    category_translation = category_translation.withColumn(
        "product_category_name",
        lower(trim(col("product_category_name")))
    )

save_parquet(category_translation, "category_translation")

print("Silver transformation completed successfully.")

spark.stop()