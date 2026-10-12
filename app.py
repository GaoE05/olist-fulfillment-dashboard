from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Olist Fulfillment Pulse", page_icon="📦", layout="wide")
DATA_FILE = Path(__file__).with_name("olist_order_health.csv")


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_FILE, parse_dates=["purchase_date"])
    data["late_delivery"] = data["late_delivery"].astype(bool)
    return data


def percent(value: float) -> str:
    return f"{value:.1%}"


data = load_data()
min_date = data["purchase_date"].min().date()
max_date = data["purchase_date"].max().date()

st.title("Olist Fulfillment Pulse — Team Gao")
st.caption(
    "For the Olist marketplace operations director: spot delivery reliability problems "
    "and decide which states or product categories need an investigation this week."
)

with st.sidebar:
    st.header("Operational filters")
    selected_dates = st.date_input(
        "Purchase-date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    states = sorted(data["customer_state"].unique())
    selected_states = st.multiselect("Customer states", states, default=states)
    categories = sorted(data["primary_category"].unique())
    selected_categories = st.multiselect(
        "Primary product categories", categories, default=categories
    )

if len(selected_dates) == 2:
    start_date, end_date = pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1])
else:
    start_date = end_date = pd.Timestamp(selected_dates[0])

filtered = data.loc[
    data["purchase_date"].between(start_date, end_date)
    & data["customer_state"].isin(selected_states)
    & data["primary_category"].isin(selected_categories)
].copy()

st.caption(
    "Data: Sep 2016 – Aug 2018 delivered Olist orders, Kaggle snapshot. "
    "In production: refresh nightly; review every Monday morning."
)

if filtered.empty:
    st.warning("No delivered orders match these filters. Expand at least one filter to continue.")
    st.stop()

on_time_rate = 1 - filtered["late_delivery"].mean()
average_delivery_days = filtered["delivery_days"].mean()
average_review = filtered["review_score"].mean()

metric_orders, metric_on_time, metric_delivery = st.columns(3)
metric_orders.metric("Delivered orders", f"{len(filtered):,}")
metric_on_time.metric("On-time delivery rate", percent(on_time_rate))
metric_delivery.metric("Average delivery time", f"{average_delivery_days:.1f} days")

st.caption(
    f"Average customer review score in this selection: {average_review:.2f}/5. "
    "On-time means delivery on or before Olist's promised date."
)

left, right = st.columns(2)
with left:
    st.subheader("Did delivery reliability change?")
    monthly = (
        filtered.groupby("purchase_month", as_index=False)
        .agg(orders=("order_id", "size"), on_time_rate=("late_delivery", lambda x: 1 - x.mean()))
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(monthly["purchase_month"], monthly["on_time_rate"] * 100, color="#2563eb", marker="o")
    ax.set_ylabel("On-time delivery rate (%)")
    ax.set_xlabel("Purchase month")
    ax.set_ylim(0, 105)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
    st.caption("A fall points to a recent fulfillment problem that needs investigation.")

with right:
    st.subheader("Where should operations investigate first?")
    state_risk = (
        filtered.groupby("customer_state", as_index=False)
        .agg(
            orders=("order_id", "size"),
            late_rate=("late_delivery", "mean"),
            avg_review=("review_score", "mean"),
        )
        .query("orders >= 50")
        .sort_values("late_rate", ascending=False)
        .head(10)
        .sort_values("late_rate")
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(state_risk["customer_state"], state_risk["late_rate"] * 100, color="#dc2626")
    ax.set_xlabel("Late deliveries (%)")
    ax.set_ylabel("Customer state")
    ax.grid(axis="x", alpha=0.25)
    for y, (_, row) in enumerate(state_risk.iterrows()):
        ax.text(row["late_rate"] * 100 + 0.3, y, f"{int(row['orders']):,} orders", va="center", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
    st.caption("States with fewer than 50 orders are excluded to avoid reacting to unstable rates.")

st.subheader("Priority list for the weekly operations meeting")
priority = (
    filtered.groupby(["customer_state", "primary_category"], as_index=False)
    .agg(
        delivered_orders=("order_id", "size"),
        late_delivery_rate=("late_delivery", "mean"),
        average_delivery_days=("delivery_days", "mean"),
        average_review_score=("review_score", "mean"),
    )
    .query("delivered_orders >= 30")
    .sort_values(["late_delivery_rate", "delivered_orders"], ascending=[False, False])
    .head(15)
)
priority["late_delivery_rate"] = priority["late_delivery_rate"].map(percent)
priority["average_delivery_days"] = priority["average_delivery_days"].round(1)
priority["average_review_score"] = priority["average_review_score"].round(2)
st.dataframe(priority, use_container_width=True, hide_index=True)

st.info(
    "Interpret carefully: this historical snapshot has no carrier identifier and no direct reason for a delay. "
    "A high late-delivery rate identifies where to investigate; it does not prove that a state or category caused the problem."
)
