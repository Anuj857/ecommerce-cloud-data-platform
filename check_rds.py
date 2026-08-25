import psycopg2

conn = psycopg2.connect(
    host="ecommerce-gold-db.crum4a0ouzw0.ap-south-1.rds.amazonaws.com",
    port=5432,
    database="postgres",
    user="postgres",
    password="Anuj85780"
)

cur = conn.cursor()

tables = [
    "fact_orders",
    "fact_order_items",
    "dim_customers",
    "dim_products",
    "dim_sellers",
    "fact_payments",
    "fact_reviews",
    "sales_by_product",
    "sales_by_seller",
    "sales_by_category"
]

print("\n========== GOLD TABLE COUNTS ==========\n")

for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"{table:<25}: {count:,}")

cur.close()
conn.close()