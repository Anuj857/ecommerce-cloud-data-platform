# 🛒 E-Commerce Cloud Data Intelligence Platform

An end-to-end **Cloud Data Engineering and Business Intelligence** project built using AWS, Python, PostgreSQL and Streamlit.

This project processes raw e-commerce data through a **Medallion Architecture (Bronze → Silver → Gold)** and converts it into business-ready datasets for analytics and decision-making.

---

## 🚀 Live Demo

🔗 **Live Dashboard:**  
`Coming Soon`

🔗 **GitHub Repository:**  
`YOUR_GITHUB_REPOSITORY_URL`

> The dashboard will be deployed using Streamlit Community Cloud.

---

# 📌 Project Overview

E-commerce companies generate large amounts of data from customers, orders, products, sellers, payments, reviews and deliveries.

The objective of this project is to build a complete cloud-based data pipeline that:

- Ingests raw e-commerce datasets
- Stores raw data in Amazon S3
- Cleans and transforms data using AWS Glue
- Creates Silver-level datasets
- Creates business-ready Gold datasets
- Loads analytical data into PostgreSQL on Amazon RDS
- Provides an interactive Streamlit dashboard
- Helps users make business decisions using data

The project follows a modern **Medallion Data Architecture**.

---

# 🏗️ System Architecture

```text
                    RAW E-COMMERCE DATA
                           │
                           ▼
                 ┌─────────────────────┐
                 │      Amazon S3      │
                 │                     │
                 │    BRONZE LAYER     │
                 │   Raw CSV Datasets  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      AWS Glue       │
                 │                     │
                 │ Silver Transformation
                 │ Cleaning & Validation
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Amazon S3      │
                 │                     │
                 │    SILVER LAYER     │
                 │  Cleaned Datasets   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      AWS Glue       │
                 │                     │
                 │  Gold Aggregation   │
                 │ Business Logic      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Amazon S3      │
                 │                     │
                 │     GOLD LAYER      │
                 │ Business Datasets   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Amazon RDS        │
                 │   PostgreSQL        │
                 │                     │
                 │ Fact & Dimension    │
                 │ Tables              │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Streamlit       │
                 │     Dashboard       │
                 │                     │
                 │ Business Analytics  │
                 └─────────────────────┘
```

---

# 🔄 Complete Data Flow

```text
Raw CSV Files
      │
      ▼
Local Data
      │
      ▼
Amazon S3 - Bronze
      │
      ▼
AWS Glue Silver Transformation
      │
      ▼
Amazon S3 - Silver
      │
      ▼
AWS Glue Gold Aggregation
      │
      ▼
Amazon S3 - Gold
      │
      ▼
PostgreSQL on Amazon RDS
      │
      ▼
Streamlit Dashboard
      │
      ▼
Business Insights
```

---

# 🥉 Bronze Layer

The Bronze layer contains the original raw datasets.

Raw data is stored in Amazon S3 without changing the original business structure.

The project uses the Brazilian E-Commerce Public Dataset by Olist.

### Raw datasets

```text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

### S3 Bronze structure

```text
s3://ecommerce-medallion-lake-2026/bronze/

├── olist_customers_dataset.csv
├── olist_geolocation_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── product_category_name_translation.csv
```

The raw datasets are also kept inside the project's `data/` directory for local development and reproducibility.

---

# 🥈 Silver Layer

The Silver layer contains cleaned and transformed datasets.

AWS Glue is used to perform data transformation and validation.

### Major transformations

- Column standardization
- Data type conversion
- Date and timestamp parsing
- Missing value handling
- Duplicate handling
- Data validation
- Joining related datasets
- Cleaning categorical values
- Preparing datasets for analytical processing

### Silver datasets

```text
customers
orders
order_items
payments
reviews
products
sellers
geolocation
category_translation
```

### S3 structure

```text
s3://ecommerce-medallion-lake-2026/silver/

├── customers/
├── orders/
├── order_items/
├── payments/
├── reviews/
├── products/
├── sellers/
├── geolocation/
└── category_translation/
```

---

# 🥇 Gold Layer

The Gold layer contains business-ready datasets created using AWS Glue.

The data is transformed into fact tables, dimension tables and business aggregation tables.

## Fact Tables

```text
fact_orders
fact_order_items
fact_payments
fact_reviews
```

## Dimension Tables

```text
dim_customers
dim_products
dim_sellers
```

## Business Aggregation Tables

```text
sales_by_product
sales_by_seller
sales_by_category
```

These datasets are optimized for analytical queries and dashboard reporting.

---

# 🗄️ PostgreSQL / Amazon RDS

The Gold datasets are loaded into PostgreSQL running on Amazon RDS.

The RDS database acts as the analytical serving layer for the Streamlit dashboard.

### Current Gold tables

```text
fact_orders
fact_order_items
dim_customers
dim_products
dim_sellers
fact_payments
fact_reviews
sales_by_product
sales_by_seller
sales_by_category
```

### Current data volume

```text
fact_orders          : 99,441
fact_order_items     : 112,650
dim_customers        : 99,441
dim_products         : 32,951
dim_sellers          : 3,095
fact_payments        : 103,886
fact_reviews         : 104,077
sales_by_product     : 32,951
sales_by_seller      : 3,095
sales_by_category    : 74
```

---

# 📊 Streamlit Dashboard

The project includes an interactive Streamlit dashboard for business analysis.

The dashboard is designed to answer practical business questions rather than only display raw data.

---

## 📈 Executive Overview

The executive dashboard provides important KPIs such as:

- Total Revenue
- Total Orders
- Total Customers
- Total Order Items
- Average Order Value
- Freight Value
- Average Review Score
- Delivery Performance

---

# 🛍️ Product Analytics

The product analytics section helps answer:

- Which products sell the most?
- Which products generate the highest revenue?
- Which product categories perform best?
- What is the average product price?
- Which categories have the highest order volume?

Example business question:

> Which product category should receive more inventory?

---

# 👥 Customer Analytics

Customer analytics includes:

- Customer distribution
- Customer locations
- Orders by customer
- Revenue by customer location
- Customer purchasing patterns

Business questions:

> Which locations generate the most orders?

> Which cities have high customer demand?

---

# 🏪 Seller Analytics

Seller analytics provides:

- Top sellers
- Seller revenue
- Seller order volume
- Seller location
- Seller performance

Business questions:

> Which sellers generate the highest revenue?

> Which sellers have the highest order volume?

---

# 💳 Payment Analytics

Payment analytics provides insights into:

- Payment methods
- Payment value
- Payment frequency
- Installment behavior

Business questions:

> Which payment method is most commonly used?

> What is the average payment value?

---

# ⭐ Review Analytics

The review section analyzes:

- Review score distribution
- Average review score
- Review volume
- Customer satisfaction trends

Business questions:

> How satisfied are customers?

> Which areas have lower review scores?

---

# 🚚 Delivery & Logistics Analytics

The dashboard also analyzes:

- Delivery time
- Estimated delivery date
- Actual delivery date
- Delayed orders
- Freight cost
- Delivery performance

Business questions:

> How many orders were delivered late?

> How does freight cost affect orders?

---

# 🧠 Business Decisions Supported

The platform can help answer questions such as:

### Product

- Which products sell the most?
- Which categories generate the highest revenue?
- Which products have low sales?
- Which categories should receive more inventory?

### Customers

- Which cities generate the most orders?
- Where are the highest-value customers?
- Which locations should be targeted for marketing?

### Sellers

- Which sellers perform best?
- Which sellers generate the most revenue?
- Which sellers have high order volume?

### Payments

- Which payment method is most popular?
- What is the average payment value?
- What payment behavior do customers show?

### Reviews

- What is the average customer satisfaction?
- Which products/categories receive poor reviews?

### Logistics

- How many orders are delayed?
- What is the average delivery time?
- Which areas have delivery problems?
- How much is being spent on freight?

---

# 🧩 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and application development |
| Pandas | Data cleaning and analysis |
| PySpark | Distributed data processing |
| Amazon S3 | Cloud data lake |
| AWS Glue | ETL and data transformation |
| PostgreSQL | Analytical database |
| Amazon RDS | Managed PostgreSQL database |
| Streamlit | Interactive dashboard |
| Plotly | Data visualization |
| Docker | Application containerization |
| Git | Version control |
| GitHub | Source code management |

---

# 📁 Project Structure

```text
ecommerce-medallion-pipeline/
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── data/
│   ├── olist_customers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   └── product_category_name_translation.csv
│
├── frontend/
│   └── app.py
│
├── pipeline/
│   ├── bronze_ingest.py
│   ├── glue_silver_transform.py
│   ├── glue_gold_aggregate.py
│   ├── gold_aggregate.py
│   ├── silver_clean.py
│   └── init_db.py
│
├── tests/
│
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
└── check_rds.py
```

---

# 🔐 Security

Sensitive credentials are never stored in the GitHub repository.

The following files are excluded using `.gitignore`:

```text
.env
secret.json
venv/
.venv/
.streamlit/secrets.toml
```

AWS credentials and database passwords should always be stored using secure credential management mechanisms such as:

- AWS Secrets Manager
- Environment Variables
- Streamlit Secrets
- IAM Roles

---

# 🐳 Docker

Docker is included to make the Streamlit application easier to package and deploy consistently.

Application flow:

```text
Dockerfile
     │
     ▼
Docker Image
     │
     ▼
Docker Container
     │
     ▼
Streamlit Dashboard
```

Docker is primarily used for packaging the application layer.

The AWS data pipeline itself is handled by S3 and AWS Glue.

---

# ☁️ AWS Resources

The project uses:

```text
Amazon S3
AWS Glue
Amazon RDS
AWS Secrets Manager
AWS IAM
```

### S3

Used as the cloud data lake for:

```text
Bronze
Silver
Gold
```

### AWS Glue

Used for:

```text
Silver Transformation
Gold Aggregation
```

### Amazon RDS

Used as the analytical PostgreSQL database.

### AWS Secrets Manager

Used to securely store database credentials.

### IAM

Used to control access between AWS services.

---

# 🔄 ETL Pipeline

## Step 1 — Data Ingestion

Raw CSV datasets are uploaded to S3 Bronze.

```text
Local CSV
   ↓
AWS CLI
   ↓
S3 Bronze
```

---

## Step 2 — Silver Transformation

AWS Glue reads Bronze data and performs:

```text
Cleaning
   ↓
Validation
   ↓
Transformation
   ↓
S3 Silver
```

---

## Step 3 — Gold Aggregation

AWS Glue reads Silver datasets and creates:

```text
Fact Tables
Dimension Tables
Business Aggregations
```

---

## Step 4 — Load to RDS

Gold datasets are loaded into PostgreSQL:

```text
S3 Gold
   ↓
Python / PostgreSQL
   ↓
Amazon RDS
```

---

## Step 5 — Dashboard

Streamlit reads analytical data from RDS and provides interactive visualizations.

```text
RDS PostgreSQL
      ↓
Streamlit
      ↓
Business Dashboard
```

---

# 🧪 Data Validation

The project includes database validation scripts to verify that the Gold tables are populated correctly.

Example:

```bash
python check_rds.py
```

The validation checks:

- Table existence
- Record counts
- Gold dataset availability
- Database connectivity

---

# 📚 Dataset

This project uses the:

**Brazilian E-Commerce Public Dataset by Olist**

The dataset contains approximately 100K orders and information related to:

- Customers
- Orders
- Products
- Sellers
- Payments
- Reviews
- Geolocation

The raw datasets are included in the `data/` directory for local development and reproducibility.

---

# 🎯 Key Data Engineering Concepts

This project demonstrates practical implementation of:

- Medallion Architecture
- Data Lake
- ETL Pipeline
- Cloud Data Engineering
- AWS S3
- AWS Glue
- PostgreSQL
- Amazon RDS
- Fact Tables
- Dimension Tables
- Data Aggregation
- Data Cleaning
- Data Validation
- Business Intelligence
- Data Visualization
- Docker
- GitHub
- Cloud Deployment

---

# 👨‍💻 Author

**Anuj Kumar Yadav**

E-Commerce Cloud Data Engineering & Business Intelligence Project

---