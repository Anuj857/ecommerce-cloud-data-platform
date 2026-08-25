import os
import boto3

# Set your S3 bucket name
S3_BUCKET_NAME = "ecommerce-medallion-lake-2026"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def upload_file_to_s3(file_name, s3_prefix="bronze"):
    s3_client = boto3.client('s3')
    local_path = os.path.join(DATA_DIR, file_name)
    s3_key = f"{s3_prefix}/{file_name}"

    if os.path.exists(local_path):
        print(f"Uploading {file_name} to s3://{S3_BUCKET_NAME}/{s3_key}...")
        s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_key)
        print(f"Successfully uploaded {file_name}")
    else:
        print(f"File not found: {local_path}")

def main():
    csv_files = [
        'olist_orders_dataset.csv',
        'olist_order_items_dataset.csv',
        'olist_customers_dataset.csv'
    ]
    for file in csv_files:
        upload_file_to_s3(file)

if __name__ == "__main__":
    main()