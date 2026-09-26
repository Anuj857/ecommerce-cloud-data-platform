
import os
from urllib.parse import quote_plus

import boto3
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="E-Commerce BI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

S3_BUCKET = os.getenv("S3_BUCKET", "ecommerce-medallion-lake-2026")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

RDS_HOST = (
    os.getenv("RDS_HOST")
    or os.getenv("RDS_ENDPOINT")
    or "ecommerce-gold-db.crum4a0ouzw0.ap-south-1.rds.amazonaws.com"
)
RDS_PORT = os.getenv("RDS_PORT", "5432")
RDS_DB = os.getenv("RDS_DB_NAME") or os.getenv("RDS_DATABASE") or "postgres"
RDS_USER = os.getenv("RDS_USER") or os.getenv("RDS_USERNAME") or "postgres"
RDS_PASSWORD = os.getenv("RDS_PASSWORD") or os.getenv("RDS_PASS")

# Optional aliases so the app also works with common .env names.
if not RDS_PASSWORD:
    RDS_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0b0f17;
    }

    [data-testid="stSidebar"] {
        background: #111827;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    .kpi-card {
        background: linear-gradient(135deg, #17233a, #101827);
        border: 1px solid #263754;
        border-radius: 14px;
        padding: 18px 20px;
        min-height: 120px;
    }

    .kpi-title {
        color: #9ca8bb;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .kpi-value {
        color: #f8fafc;
        font-size: 30px;
        font-weight: 700;
    }

    .kpi-note {
        color: #6f809b;
        font-size: 12px;
        margin-top: 5px;
    }

    .insight {
        background: #111827;
        border-left: 4px solid #6366f1;
        padding: 14px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }

    .small-muted {
        color: #8b98ad;
        font-size: 13px;
    }

    h1, h2, h3 {
        letter-spacing: -0.3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATABASE
# ============================================================

@st.cache_resource
def get_engine():
    if not RDS_PASSWORD:
        raise RuntimeError(
            "RDS_PASSWORD is missing. Add RDS_PASSWORD to your .env file."
        )

    password = quote_plus(RDS_PASSWORD)
    user = quote_plus(RDS_USER)
    database_url = (
        f"postgresql+psycopg2://{user}:{password}"
        f"@{RDS_HOST}:{RDS_PORT}/{RDS_DB}"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@st.cache_data(ttl=300)
def get_table_names():
    engine = get_engine()
    inspector = inspect(engine)
    return sorted(inspector.get_table_names())


@st.cache_data(ttl=300)
def load_table(table_name):
    allowed = {
        "fact_orders",
        "fact_order_items",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "fact_payments",
        "fact_reviews",
        "sales_by_product",
        "sales_by_seller",
        "sales_by_category",
    }

    if table_name not in allowed:
        raise ValueError("Table is not allowed.")

    engine = get_engine()
    return pd.read_sql(text(f'SELECT * FROM "{table_name}"'), engine)


def load_if_exists(table_name):
    try:
        if table_name not in get_table_names():
            return pd.DataFrame()
        return load_table(table_name)
    except Exception as exc:
        st.warning(f"Could not load {table_name}: {exc}")
        return pd.DataFrame()


# ============================================================
# HELPERS
# ============================================================

def find_col(df, candidates):
    """Return the first matching column from candidates."""
    if df.empty:
        return None

    lower_map = {str(c).lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    # Also allow a partial match.
    for candidate in candidates:
        for col_name in df.columns:
            if candidate.lower() in str(col_name).lower():
                return col_name

    return None


def numeric(df, column):
    if column and column in df.columns:
        return pd.to_numeric(df[column], errors="coerce")
    return pd.Series(dtype="float64")


def money(value):
    if pd.isna(value):
        return "—"
    value = float(value)

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.2f}"


def number(value):
    if pd.isna(value):
        return "—"
    return f"{int(value):,}"


def kpi(title, value, note=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_message(message):
    st.info(message)


def safe_datetime(df, column):
    if column and column in df.columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def get_product_label(products, product_id):
    if products.empty or product_id is None:
        return None

    product_id_col = find_col(products, ["product_id"])
    if not product_id_col:
        return None

    # Olist does NOT contain an actual product-name field.
    # Use translated category as the readable business label.
    name_col = find_col(
        products,
        [
            "product_name",
            "product_name_english",
            "product_title",
            "product_category_name_english",
        ],
    )

    if name_col:
        lookup = products[[product_id_col, name_col]].drop_duplicates(product_id_col)
        lookup = lookup.rename(
            columns={product_id_col: "product_id", name_col: "product_label"}
        )
        return lookup

    category_col = find_col(
        products,
        [
            "product_category_name_english",
            "category_name_english",
            "product_category_name",
            "category",
        ],
    )

    if category_col:
        lookup = products[[product_id_col, category_col]].drop_duplicates(product_id_col)
        lookup = lookup.rename(
            columns={product_id_col: "product_id", category_col: "product_label"}
        )
        return lookup

    return None


def get_seller_label(sellers):
    if sellers.empty:
        return None

    seller_id_col = find_col(sellers, ["seller_id"])
    city_col = find_col(sellers, ["seller_city", "city"])
    state_col = find_col(sellers, ["seller_state", "state"])
    name_col = find_col(sellers, ["seller_name", "name"])

    if not seller_id_col:
        return None

    out = sellers[[seller_id_col]].drop_duplicates().rename(
        columns={seller_id_col: "seller_id"}
    )

    if name_col:
        names = sellers[[seller_id_col, name_col]].drop_duplicates(seller_id_col)
        names = names.rename(columns={seller_id_col: "seller_id", name_col: "seller_label"})
        return out.merge(names, on="seller_id", how="left")

    parts = []
    if city_col:
        parts.append(sellers[city_col].fillna("").astype(str).str.title())
    if state_col:
        parts.append(sellers[state_col].fillna("").astype(str).str.upper())

    if parts:
        label = parts[0]
        if len(parts) == 2:
            label = label + ", " + parts[1]

        location = pd.DataFrame(
            {
                "seller_id": sellers[seller_id_col],
                "seller_label": label,
            }
        ).drop_duplicates("seller_id")

        return out.merge(location, on="seller_id", how="left")

    return out.assign(seller_label=out["seller_id"].astype(str).str[:12])


def add_product_labels(df, products):
    if df.empty:
        return df

    product_id_col = find_col(df, ["product_id"])
    if not product_id_col:
        return df

    labels = get_product_label(products, product_id_col)
    if labels is None:
        df = df.copy()
        df["product_label"] = df[product_id_col].astype(str).str[:12]
        return df

    result = df.copy()
    result[product_id_col] = result[product_id_col].astype(str)
    labels["product_id"] = labels["product_id"].astype(str)

    result = result.merge(labels, left_on=product_id_col, right_on="product_id", how="left")

    if product_id_col != "product_id" and "product_id" in result.columns:
        result = result.drop(columns=["product_id"])

    result["product_label"] = result["product_label"].fillna(
        result[product_id_col].astype(str).str[:12]
    )

    return result


def add_seller_labels(df, sellers):
    if df.empty:
        return df

    seller_id_col = find_col(df, ["seller_id"])
    if not seller_id_col:
        return df

    labels = get_seller_label(sellers)
    if labels is None:
        return df

    result = df.copy()
    result[seller_id_col] = result[seller_id_col].astype(str)
    labels["seller_id"] = labels["seller_id"].astype(str)

    result = result.merge(labels, left_on=seller_id_col, right_on="seller_id", how="left")

    if seller_id_col != "seller_id" and "seller_id" in result.columns:
        result = result.drop(columns=["seller_id"])

    result["seller_label"] = result["seller_label"].fillna(
        result[seller_id_col].astype(str).str[:12]
    )

    return result


# ============================================================
# LOAD COMMON DATA
# ============================================================

try:
    table_names = get_table_names()
except Exception as exc:
    st.error(f"Could not connect to RDS PostgreSQL: {exc}")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🛒 E-Commerce BI")
    st.caption("AWS Serverless Medallion Architecture")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Executive Overview",
            "📦 Product Analytics",
            "👥 Customer Analytics",
            "🏪 Seller Analytics",
            "💳 Payment Analytics",
            "⭐ Reviews",
            "🚚 Delivery & Logistics",
            "🔎 Data Explorer",
            "🏗️ Architecture",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("### ☁️ Pipeline")
    st.markdown(
        """
        🟤 **Bronze**  
        Raw CSV datasets

        ↓

        ⚪ **Silver**  
        Cleaned Parquet

        ↓

        🟡 **Gold**  
        Business-ready tables

        ↓

        🐘 **RDS PostgreSQL**  
        Analytics serving layer

        ↓

        📊 **Streamlit**  
        Business intelligence
        """
    )

    st.divider()

    st.markdown("### 📤 Upload New Dataset")
    uploaded_file = st.file_uploader(
        "CSV file",
        type=["csv"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        if st.button("Upload to Bronze", use_container_width=True):
            try:
                s3 = boto3.client("s3", region_name=AWS_REGION)
                key = f"bronze/{uploaded_file.name}"
                s3.upload_fileobj(uploaded_file, S3_BUCKET, key)
                st.success(f"Uploaded: {uploaded_file.name}")
            except Exception as exc:
                st.error(f"S3 upload failed: {exc}")

    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.caption(f"RDS: {RDS_HOST}")
    st.caption(f"Region: {AWS_REGION}")

# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

if page == "🏠 Executive Overview":
    st.title("🏠 Executive Overview")
    st.caption("Business performance across orders, customers, products, sellers and payments.")

    orders = load_if_exists("fact_orders")
    items = load_if_exists("fact_order_items")
    customers = load_if_exists("dim_customers")
    products = load_if_exists("dim_products")
    sellers = load_if_exists("dim_sellers")
    payments = load_if_exists("fact_payments")

    revenue_col = find_col(orders, ["total_order_value", "order_value", "revenue", "total_price"])
    order_id_col = find_col(orders, ["order_id"])
    customer_id_col = find_col(orders, ["customer_id"])

    revenue = numeric(orders, revenue_col).sum()
    order_count = orders[order_id_col].nunique() if order_id_col else len(orders)
    customer_count = (
        customers[find_col(customers, ["customer_id"])].nunique()
        if find_col(customers, ["customer_id"])
        else 0
    )
    # Count physical order-item records, not columns or aggregated metrics.
    # fact_order_items contains one row per order item.
    item_id_col = find_col(items, ["order_item_id", "item_id"])
    if item_id_col:
        item_count = items[item_id_col].dropna().astype(str).nunique()
    else:
        item_count = len(items)
    aov = revenue / order_count if order_count else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi("Revenue", money(revenue), "Order value")
    with c2:
        kpi("Orders", number(order_count), "Unique orders")
    with c3:
        kpi("Customers", number(customer_count), "Customer records")
    with c4:
        kpi("Order Items", number(item_count), "Items sold")
    with c5:
        kpi("Average Order", money(aov), "Revenue / order")

    # Data-quality note: this project uses the Gold fact table directly.
    if item_count and item_count < order_count:
        st.caption(
            f"ℹ️ {item_count:,} order-item records across {order_count:,} orders in the Gold layer."
        )
    else:
        st.caption(
            f"ℹ️ {item_count:,} order-item records loaded from fact_order_items."
        )

    st.divider()

    if not orders.empty:
        orders = safe_datetime(
            orders,
            find_col(
                orders,
                [
                    "order_purchase_timestamp",
                    "purchase_timestamp",
                    "order_date",
                ],
            ),
        )

        date_col = find_col(
            orders,
            [
                "order_purchase_timestamp",
                "purchase_timestamp",
                "order_date",
            ],
        )

        left, right = st.columns(2)

        with left:
            st.subheader("📈 Monthly Revenue")

            if date_col and revenue_col:
                trend = (
                    orders.dropna(subset=[date_col])
                    .set_index(date_col)[revenue_col]
                    .pipe(pd.to_numeric, errors="coerce")
                    .resample("ME")
                    .sum()
                    .reset_index()
                )

                fig = px.line(
                    trend,
                    x=date_col,
                    y=revenue_col,
                    markers=True,
                    labels={
                        date_col: "Month",
                        revenue_col: "Revenue",
                    },
                )
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("📦 Order Status")

            status_col = find_col(orders, ["order_status", "status"])
            if status_col:
                status = orders[status_col].fillna("unknown").value_counts().reset_index()
                status.columns = [status_col, "count"]

                fig = px.pie(
                    status,
                    names=status_col,
                    values="count",
                    hole=0.48,
                )
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 Business Insights")

    insights = []

    if not products.empty and not items.empty:
        product_items = add_product_labels(items, products)
        pid = find_col(product_items, ["product_id"])
        price = find_col(product_items, ["price", "product_price"])

        if pid and price:
            p = product_items.copy()
            p[price] = pd.to_numeric(p[price], errors="coerce")
            top = (
                p.groupby("product_label", as_index=False)
                .agg(units_sold=(pid, "count"), revenue=(price, "sum"))
                .sort_values("revenue", ascending=False)
                .head(1)
            )
            if not top.empty:
                insights.append(
                    f"Top revenue-driving product category: **{top.iloc[0]['product_label']}**."
                )

    if not customers.empty and not orders.empty:
        city_col = find_col(customers, ["customer_city", "city"])
        cid = find_col(customers, ["customer_id"])
        if city_col and cid and customer_id_col:
            city = (
                customers.groupby(city_col)[cid]
                .nunique()
                .sort_values(ascending=False)
                .head(1)
            )
            if not city.empty:
                insights.append(
                    f"Largest customer concentration is in **{city.index[0]}**."
                )

    if insights:
        for item in insights:
            st.markdown(f'<div class="insight">💡 {item}</div>', unsafe_allow_html=True)
    else:
        st.info("More business insights will appear when the corresponding Gold data is available.")

# ============================================================
# PRODUCT ANALYTICS
# ============================================================

elif page == "📦 Product Analytics":
    st.title("📦 Product Analytics")
    st.caption("Identify products and categories driving sales.")

    sales = load_if_exists("sales_by_product")
    items = load_if_exists("fact_order_items")
    products = load_if_exists("dim_products")

    # If the aggregate table exists, use it. Otherwise build from fact_order_items.
    if sales.empty and not items.empty:
        sales = items.copy()

        pid = find_col(sales, ["product_id"])
        price = find_col(sales, ["price", "product_price"])
        sales["units_sold"] = 1

        if price:
            sales["product_revenue"] = pd.to_numeric(sales[price], errors="coerce")

        if pid:
            sales = (
                sales.groupby(pid, as_index=False)
                .agg(
                    units_sold=("units_sold", "sum"),
                    product_revenue=("product_revenue", "sum"),
                )
            )

    sales = add_product_labels(sales, products)

    if sales.empty:
        empty_message("sales_by_product / fact_order_items is empty.")
        st.stop()

    units_col = find_col(sales, ["units_sold", "item_count", "items_sold"])
    revenue_col = find_col(
        sales,
        ["product_revenue", "revenue", "total_revenue", "sales"],
    )

    if units_col:
        sales[units_col] = pd.to_numeric(sales[units_col], errors="coerce")

    if revenue_col:
        sales[revenue_col] = pd.to_numeric(sales[revenue_col], errors="coerce")

    left, right = st.columns(2)

    with left:
        st.subheader("🔥 Top Products / Categories by Units")

        if units_col:
            top_units = (
                sales.groupby("product_label", as_index=False)[units_col]
                .sum()
                .nlargest(15, units_col)
                .sort_values(units_col)
            )

            fig = px.bar(
                top_units,
                x=units_col,
                y="product_label",
                orientation="h",
                labels={"product_label": "Product / Category"},
            )
            fig.update_layout(height=560)
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("💰 Top Products / Categories by Revenue")

        if revenue_col:
            top_revenue = (
                sales.groupby("product_label", as_index=False)[revenue_col]
                .sum()
                .nlargest(15, revenue_col)
                .sort_values(revenue_col)
            )

            fig = px.bar(
                top_revenue,
                x=revenue_col,
                y="product_label",
                orientation="h",
                labels={"product_label": "Product / Category"},
            )
            fig.update_layout(height=560)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("📁 Category Performance")

    category_col = find_col(
        products,
        [
            "product_category_name_english",
            "category_name_english",
            "product_category_name",
            "category",
        ],
    )

    if not products.empty and category_col:
        pid_products = find_col(products, ["product_id"])
        pid_sales = find_col(sales, ["product_id"])

        if pid_products and pid_sales:
            cat = products[[pid_products, category_col]].drop_duplicates(pid_products)
            cat = cat.rename(
                columns={
                    pid_products: "product_id_join",
                    category_col: "category",
                }
            )

            temp = sales.copy()
            temp["product_id_join"] = temp[pid_sales].astype(str)
            cat["product_id_join"] = cat["product_id_join"].astype(str)

            temp = temp.merge(cat, on="product_id_join", how="left")

            agg = {}
            if units_col:
                agg["Units Sold"] = (units_col, "sum")
            if revenue_col:
                agg["Revenue"] = (revenue_col, "sum")

            if agg:
                category = (
                    temp.groupby("category")
                    .agg(**agg)
                    .reset_index()
                    .sort_values(
                        "Revenue" if "Revenue" in agg else "Units Sold",
                        ascending=False,
                    )
                    .head(20)
                )

                st.dataframe(
                    category,
                    use_container_width=True,
                    hide_index=True,
                )

    st.caption(
        "Note: The Olist source dataset does not contain a true product-name field. "
        "The dashboard therefore uses translated product category as the readable label "
        "instead of inventing product names."
    )

# ============================================================
# CUSTOMER ANALYTICS
# ============================================================

elif page == "👥 Customer Analytics":
    st.title("👥 Customer Analytics")
    st.caption("Understand customer distribution and revenue concentration.")

    customers = load_if_exists("dim_customers")
    orders = load_if_exists("fact_orders")

    if customers.empty:
        empty_message("dim_customers is not available.")
        st.stop()

    city_col = find_col(customers, ["customer_city", "city"])
    state_col = find_col(customers, ["customer_state", "state"])
    customer_id_col = find_col(customers, ["customer_id"])

    if not orders.empty:
        order_customer_col = find_col(orders, ["customer_id"])
        revenue_col = find_col(
            orders,
            ["total_order_value", "order_value", "revenue"],
        )

        if order_customer_col and revenue_col and customer_id_col:
            temp = orders[[order_customer_col, revenue_col]].copy()
            temp[revenue_col] = pd.to_numeric(temp[revenue_col], errors="coerce")
            temp = temp.rename(columns={order_customer_col: "customer_id"})

            cust = customers[[customer_id_col] + ([state_col] if state_col else [])].copy()
            cust = cust.rename(columns={customer_id_col: "customer_id"})

            temp["customer_id"] = temp["customer_id"].astype(str)
            cust["customer_id"] = cust["customer_id"].astype(str)

            merged = temp.merge(cust, on="customer_id", how="left")

            revenue = merged[revenue_col].sum()
            active_customers = merged["customer_id"].nunique()
            avg_customer_value = revenue / active_customers if active_customers else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                kpi("Active Customers", number(active_customers))
            with c2:
                kpi("Customer Revenue", money(revenue))
            with c3:
                kpi("Avg Customer Value", money(avg_customer_value))

            if state_col:
                state_revenue = (
                    merged.groupby(state_col)[revenue_col]
                    .sum()
                    .nlargest(15)
                    .reset_index()
                )

                st.subheader("💰 Revenue by Customer State")
                fig = px.bar(
                    state_revenue,
                    x=state_col,
                    y=revenue_col,
                    labels={revenue_col: "Revenue"},
                )
                st.plotly_chart(fig, use_container_width=True)

    if city_col:
        city_count = (
            customers.groupby(city_col)[customer_id_col]
            .nunique()
            .nlargest(20)
            .reset_index(name="customers")
        )

        st.subheader("📍 Customer Concentration by City")
        fig = px.bar(
            city_count.sort_values("customers"),
            x="customers",
            y=city_col,
            orientation="h",
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# SELLER ANALYTICS
# ============================================================

elif page == "🏪 Seller Analytics":
    st.title("🏪 Seller Analytics")
    st.caption("Compare seller performance without exposing unreadable seller IDs.")

    sales = load_if_exists("sales_by_seller")
    items = load_if_exists("fact_order_items")
    sellers = load_if_exists("dim_sellers")

    if sales.empty and not items.empty:
        seller_col = find_col(items, ["seller_id"])
        price_col = find_col(items, ["price", "product_price"])

        if seller_col:
            temp = items.copy()
            temp["items_sold"] = 1
            if price_col:
                temp["seller_revenue"] = pd.to_numeric(
                    temp[price_col], errors="coerce"
                )
            else:
                temp["seller_revenue"] = 0

            sales = (
                temp.groupby(seller_col, as_index=False)
                .agg(
                    items_sold=("items_sold", "sum"),
                    seller_revenue=("seller_revenue", "sum"),
                )
            )

    sales = add_seller_labels(sales, sellers)

    if sales.empty:
        empty_message("sales_by_seller / fact_order_items is empty.")
        st.stop()

    revenue_col = find_col(
        sales,
        ["seller_revenue", "revenue", "total_revenue", "sales"],
    )
    units_col = find_col(
        sales,
        ["items_sold", "units_sold", "item_count"],
    )

    if revenue_col:
        sales[revenue_col] = pd.to_numeric(sales[revenue_col], errors="coerce")

    if units_col:
        sales[units_col] = pd.to_numeric(sales[units_col], errors="coerce")

    left, right = st.columns(2)

    with left:
        st.subheader("💰 Top Sellers by Revenue")
        if revenue_col:
            top = (
                sales.groupby("seller_label", as_index=False)[revenue_col]
                .sum()
                .nlargest(15, revenue_col)
                .sort_values(revenue_col)
            )
            fig = px.bar(
                top,
                x=revenue_col,
                y="seller_label",
                orientation="h",
                labels={"seller_label": "Seller Location"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("📦 Top Sellers by Items")
        if units_col:
            top = (
                sales.groupby("seller_label", as_index=False)[units_col]
                .sum()
                .nlargest(15, units_col)
                .sort_values(units_col)
            )
            fig = px.bar(
                top,
                x=units_col,
                y="seller_label",
                orientation="h",
                labels={"seller_label": "Seller Location"},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("🏪 Seller Performance")
    display_cols = ["seller_label"]
    if revenue_col:
        display_cols.append(revenue_col)
    if units_col:
        display_cols.append(units_col)

    table = (
        sales.groupby("seller_label", as_index=False)[display_cols[1:]]
        .sum()
        .sort_values(
            revenue_col if revenue_col else units_col,
            ascending=False,
        )
        .head(25)
    )

    st.dataframe(table, use_container_width=True, hide_index=True)

    st.caption(
        "The Olist source does not provide seller names. Seller city/state is used "
        "as the human-readable business label."
    )

# ============================================================
# PAYMENT ANALYTICS
# ============================================================

elif page == "💳 Payment Analytics":
    st.title("💳 Payment Analytics")
    st.caption("Understand payment methods, value and installment behavior.")

    payments = load_if_exists("fact_payments")

    if payments.empty:
        empty_message("fact_payments is not available.")
        st.stop()

    type_col = find_col(payments, ["payment_type", "method"])
    value_col = find_col(payments, ["payment_value", "value", "amount"])
    installment_col = find_col(
        payments,
        ["payment_installments", "installments"],
    )

    if value_col:
        payments[value_col] = pd.to_numeric(
            payments[value_col],
            errors="coerce",
        )

    total_payment = payments[value_col].sum() if value_col else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Payment Value", money(total_payment))
    with c2:
        kpi("Payment Records", number(len(payments)))
    with c3:
        if installment_col:
            avg_installment = pd.to_numeric(
                payments[installment_col],
                errors="coerce",
            ).mean()
            kpi("Avg Installments", f"{avg_installment:.1f}")
        else:
            kpi("Avg Installments", "—")

    if type_col and value_col:
        mix = (
            payments.groupby(type_col)[value_col]
            .sum()
            .reset_index()
            .sort_values(value_col, ascending=False)
        )

        st.subheader("💳 Payment Method Value")
        fig = px.bar(
            mix,
            x=type_col,
            y=value_col,
            labels={value_col: "Payment Value"},
        )
        st.plotly_chart(fig, use_container_width=True)

    if type_col:
        count = payments[type_col].value_counts().reset_index()
        count.columns = [type_col, "count"]

        st.subheader("Payment Method Usage")
        fig = px.pie(
            count,
            names=type_col,
            values="count",
            hole=0.45,
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# REVIEWS
# ============================================================

elif page == "⭐ Reviews":
    st.title("⭐ Customer Reviews")
    st.caption("Customer satisfaction and review distribution.")

    reviews = load_if_exists("fact_reviews")

    if reviews.empty:
        empty_message("fact_reviews is not available.")
        st.stop()

    score_col = find_col(
        reviews,
        ["review_score", "rating", "score"],
    )

    # IMPORTANT:
    # RDS may return review_score as text. Convert it before mean/count logic.
    if score_col:
        reviews[score_col] = pd.to_numeric(
            reviews[score_col],
            errors="coerce",
        )

        average_rating = reviews[score_col].mean()
        valid_reviews = reviews[score_col].notna().sum()

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi("Average Rating", f"{average_rating:.2f} / 5")
        with c2:
            kpi("Review Records", number(len(reviews)))
        with c3:
            kpi("Valid Ratings", number(valid_reviews))

        left, right = st.columns(2)

        with left:
            st.subheader("⭐ Rating Distribution")

            rating = (
                reviews[score_col]
                .dropna()
                .value_counts()
                .sort_index()
                .reset_index()
            )
            rating.columns = ["rating", "reviews"]

            fig = px.bar(
                rating,
                x="rating",
                y="reviews",
                labels={
                    "rating": "Rating",
                    "reviews": "Number of Reviews",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("😊 Rating Mix")

            rating_pie = (
                reviews[score_col]
                .dropna()
                .value_counts()
                .sort_index()
                .reset_index()
            )
            rating_pie.columns = ["rating", "reviews"]

            fig = px.pie(
                rating_pie,
                names="rating",
                values="reviews",
                hole=0.45,
            )
            st.plotly_chart(fig, use_container_width=True)

        low_rating = reviews[reviews[score_col] <= 2]

        st.subheader("⚠️ Low-Rating Reviews")

        if not low_rating.empty:
            comment_col = find_col(
                low_rating,
                [
                    "review_comment_message",
                    "comment_message",
                    "review_comment_title",
                ],
            )

            show_cols = [score_col]
            if comment_col:
                show_cols.append(comment_col)

            order_col = find_col(low_rating, ["order_id"])
            if order_col:
                show_cols.insert(0, order_col)

            st.dataframe(
                low_rating[show_cols].head(50),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No 1–2 star reviews found.")

# ============================================================
# DELIVERY & LOGISTICS
# ============================================================

elif page == "🚚 Delivery & Logistics":
    st.title("🚚 Delivery & Logistics")
    st.caption("Order status, freight cost and delivery-related performance.")

    orders = load_if_exists("fact_orders")
    items = load_if_exists("fact_order_items")

    if orders.empty:
        empty_message("fact_orders is not available.")
        st.stop()

    status_col = find_col(orders, ["order_status", "status"])
    freight_col = find_col(
        orders,
        ["total_freight", "freight_value", "freight"],
    )
    revenue_col = find_col(
        orders,
        ["total_order_value", "order_value", "revenue"],
    )

    if freight_col:
        orders[freight_col] = pd.to_numeric(
            orders[freight_col],
            errors="coerce",
        )

    if revenue_col:
        orders[revenue_col] = pd.to_numeric(
            orders[revenue_col],
            errors="coerce",
        )

    total_freight = orders[freight_col].sum() if freight_col else 0
    avg_freight = orders[freight_col].mean() if freight_col else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Total Freight", money(total_freight))
    with c2:
        kpi("Average Freight", money(avg_freight))
    with c3:
        if revenue_col and total_freight:
            freight_ratio = total_freight / orders[revenue_col].sum() * 100
            kpi("Freight / Revenue", f"{freight_ratio:.1f}%")
        else:
            kpi("Freight / Revenue", "—")

    if status_col:
        status = orders[status_col].fillna("unknown").value_counts().reset_index()
        status.columns = [status_col, "count"]

        st.subheader("📦 Order Status")
        fig = px.bar(
            status.sort_values("count"),
            x="count",
            y=status_col,
            orientation="h",
        )
        st.plotly_chart(fig, use_container_width=True)

    if freight_col and revenue_col:
        st.subheader("🚚 Freight vs Order Value")
        sample = orders[[freight_col, revenue_col]].dropna().head(5000)

        fig = px.scatter(
            sample,
            x=revenue_col,
            y=freight_col,
            opacity=0.5,
            labels={
                revenue_col: "Order Value",
                freight_col: "Freight",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# DATA EXPLORER
# ============================================================

elif page == "🔎 Data Explorer":
    st.title("🔎 Data Explorer")
    st.caption("Inspect the business-ready Gold tables stored in RDS PostgreSQL.")

    preferred = [
        "fact_orders",
        "fact_order_items",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "fact_payments",
        "fact_reviews",
        "sales_by_product",
        "sales_by_seller",
        "sales_by_category",
    ]

    available = [x for x in preferred if x in table_names]

    if not available:
        st.warning("No Gold tables found.")
        st.stop()

    selected = st.selectbox("Select Table", available)
    data = load_if_exists(selected)

    st.write(f"Showing **{len(data):,}** records from `{selected}`")

    if not data.empty:
        st.dataframe(
            data,
            use_container_width=True,
            height=650,
            hide_index=True,
        )

        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV",
            csv,
            file_name=f"{selected}.csv",
            mime="text/csv",
        )

# ============================================================
# ARCHITECTURE
# ============================================================

elif page == "🏗️ Architecture":
    st.title("🏗️ Data Architecture")
    st.caption("End-to-end E-Commerce data platform.")

    st.markdown(
        """
        ### Data Flow

        **CSV / User Upload**

        ↓

        **Amazon S3 — Bronze**
        - Raw Olist CSV files
        - Immutable landing layer

        ↓

        **AWS Glue — Silver**
        - Schema enforcement
        - Type conversion
        - Null handling
        - Deduplication
        - Standardization

        ↓

        **Amazon S3 — Silver**
        - Customers
        - Orders
        - Order Items
        - Products
        - Sellers
        - Payments
        - Reviews
        - Geolocation
        - Category Translation

        ↓

        **AWS Glue — Gold**

        ↓

        **Amazon S3 — Gold**
        - Fact tables
        - Dimension tables
        - Business aggregates

        ↓

        **Amazon RDS PostgreSQL**
        - BI serving layer

        ↓

        **Streamlit**
        - Executive Overview
        - Product Analytics
        - Customer Analytics
        - Seller Analytics
        - Payment Analytics
        - Reviews
        - Delivery & Logistics
        - Data Explorer
        """
    )

    st.divider()

    st.subheader("📊 Gold Data Model")

    cols = st.columns(3)

    with cols[0]:
        st.markdown(
            """
            **Facts**
            - fact_orders
            - fact_order_items
            - fact_payments
            - fact_reviews
            """
        )

    with cols[1]:
        st.markdown(
            """
            **Dimensions**
            - dim_customers
            - dim_products
            - dim_sellers
            """
        )

    with cols[2]:
        st.markdown(
            """
            **Aggregates**
            - sales_by_product
            - sales_by_seller
            - sales_by_category
            """
        )

    st.divider()

    st.subheader("✅ Data Health")

    health = pd.DataFrame(
        {
            "Table": [
                "fact_orders",
                "fact_order_items",
                "dim_customers",
                "dim_products",
                "dim_sellers",
                "fact_payments",
                "fact_reviews",
                "sales_by_product",
                "sales_by_seller",
                "sales_by_category",
            ],
            "Available": [
                "Yes" if t in table_names else "No"
                for t in [
                    "fact_orders",
                    "fact_order_items",
                    "dim_customers",
                    "dim_products",
                    "dim_sellers",
                    "fact_payments",
                    "fact_reviews",
                    "sales_by_product",
                    "sales_by_seller",
                    "sales_by_category",
                ]
            ],
        }
    )

    st.dataframe(health, use_container_width=True, hide_index=True)
