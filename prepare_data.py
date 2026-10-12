"""Build the compact order-level file used by the Streamlit dashboard.

The Kaggle download has nine relational CSVs.  The app needs one row per
order, so this script joins only the fields required for delivery operations.
Raw files stay local and are not committed; the resulting CSV is small enough
for GitHub and Streamlit Community Cloud.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
RAW = ROOT / "raw"


def main() -> None:
    orders = pd.read_csv(
        RAW / "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv")
    translations = pd.read_csv(RAW / "product_category_name_translation.csv")

    products = products.merge(translations, on="product_category_name", how="left")
    items = items.merge(
        products[["product_id", "product_category_name_english"]],
        on="product_id",
        how="left",
    )
    items["product_category_name_english"] = items[
        "product_category_name_english"
    ].fillna("Unknown")

    # An order can contain several categories.  Use the category attached to
    # the most expensive item, so category filters keep one row per order.
    primary_category = (
        items.sort_values(["order_id", "price"], ascending=[True, False])
        .drop_duplicates("order_id")
        [["order_id", "product_category_name_english"]]
        .rename(columns={"product_category_name_english": "primary_category"})
    )
    order_value = (
        items.groupby("order_id", as_index=False)
        .agg(merchandise_value_brl=("price", "sum"), freight_value_brl=("freight_value", "sum"))
    )
    reviews = reviews.groupby("order_id", as_index=False).agg(review_score=("review_score", "mean"))

    data = (
        orders.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
        .merge(order_value, on="order_id", how="left")
        .merge(primary_category, on="order_id", how="left")
        .merge(reviews, on="order_id", how="left")
    )
    data["purchase_date"] = data["order_purchase_timestamp"].dt.date.astype(str)
    data["purchase_month"] = data["order_purchase_timestamp"].dt.to_period("M").astype(str)
    data["was_delivered"] = data["order_delivered_customer_date"].notna()
    data["late_delivery"] = (
        data["was_delivered"]
        & (data["order_delivered_customer_date"] > data["order_estimated_delivery_date"])
    )
    data["delivery_days"] = (
        data["order_delivered_customer_date"] - data["order_purchase_timestamp"]
    ).dt.total_seconds() / 86_400
    data["days_late"] = (
        data["order_delivered_customer_date"] - data["order_estimated_delivery_date"]
    ).dt.total_seconds().div(86_400).clip(lower=0)
    data["primary_category"] = data["primary_category"].fillna("Unknown")
    data["merchandise_value_brl"] = data["merchandise_value_brl"].fillna(0)
    data["freight_value_brl"] = data["freight_value_brl"].fillna(0)
    data["customer_state"] = data["customer_state"].fillna("Unknown")

    # The dashboard is for diagnosing completed deliveries.  Keeping orders
    # still in progress would make delivery speed and punctuality undefined,
    # so the app uses the 96k delivered orders only.
    data = data.loc[data["was_delivered"]].copy()

    keep = [
        "order_id",
        "purchase_date",
        "purchase_month",
        "order_status",
        "customer_state",
        "primary_category",
        "merchandise_value_brl",
        "freight_value_brl",
        "review_score",
        "was_delivered",
        "late_delivery",
        "delivery_days",
        "days_late",
    ]
    data[keep].to_csv(ROOT / "olist_order_health.csv", index=False)


if __name__ == "__main__":
    main()
