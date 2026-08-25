import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ---------------------------------------------------------
# Load .env
# ---------------------------------------------------------

load_dotenv(
    os.path.join(
        BASE_DIR,
        ".env"
    )
)


# ---------------------------------------------------------
# RDS configuration
# ---------------------------------------------------------

RDS_ENDPOINT = os.getenv(
    "RDS_ENDPOINT"
)

RDS_PORT = os.getenv(
    "RDS_PORT",
    "5432"
)

RDS_DB_NAME = os.getenv(
    "RDS_DB_NAME",
    "postgres"
)

RDS_USER = os.getenv(
    "RDS_USER"
)

RDS_PASSWORD = os.getenv(
    "RDS_PASSWORD"
)


# ---------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Database connection
# ---------------------------------------------------------

DATABASE_URL = (
    f"postgresql://{RDS_USER}:{RDS_PASSWORD}"
    f"@{RDS_ENDPOINT}:{RDS_PORT}/{RDS_DB_NAME}"
)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("Connecting to RDS PostgreSQL...")

    engine = create_engine(
        DATABASE_URL
    )


    # -----------------------------------------------------
    # Fact Orders
    # -----------------------------------------------------

    create_fact_orders = """
    CREATE TABLE IF NOT EXISTS fact_orders (
        order_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50),
        order_status VARCHAR(20),
        order_purchase_timestamp TIMESTAMP,
        total_order_value NUMERIC(10, 2),
        total_freight NUMERIC(10, 2),
        item_count INT
    );
    """


    # -----------------------------------------------------
    # Customer Dimension
    # -----------------------------------------------------

    create_dim_customers = """
    CREATE TABLE IF NOT EXISTS dim_customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        customer_unique_id VARCHAR(50),
        customer_zip_code_prefix INT,
        customer_city VARCHAR(100),
        customer_state VARCHAR(10)
    );
    """


    # -----------------------------------------------------
    # Create tables
    # -----------------------------------------------------

    with engine.connect() as conn:

        conn.execute(
            text(create_fact_orders)
        )

        conn.execute(
            text(create_dim_customers)
        )

        conn.commit()


    engine.dispose()

    print(
        "Successfully created Gold tables "
        "in RDS PostgreSQL!"
    )


if __name__ == "__main__":
    main()