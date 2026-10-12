"""Create the small, reproducible EDA notebook required by the exercise."""

from pathlib import Path

import nbformat as nbf


root = Path(__file__).parent
nb = nbf.v4.new_notebook()
nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb["metadata"]["language_info"] = {"name": "python", "version": "3"}
nb.cells = [
    nbf.v4.new_markdown_cell(
        "# Olist Fulfillment Pulse — quick EDA\n\n"
        "This notebook examines the compact order-level file used by the Streamlit app. "
        "Each row is one **delivered** Olist order; orders still in progress are excluded because "
        "their delivery time and on-time status are not defined."
    ),
    nbf.v4.new_code_cell(
        "import pandas as pd\nimport matplotlib.pyplot as plt\n\n"
        "orders = pd.read_csv('olist_order_health.csv', parse_dates=['purchase_date'])\n"
        "orders.shape"
    ),
    nbf.v4.new_markdown_cell("## Structure and data quality"),
    nbf.v4.new_code_cell(
        "display(orders.dtypes.to_frame('dtype'))\n"
        "display(orders.isna().sum().sort_values(ascending=False).to_frame('missing values'))\n"
        "print('Purchase period:', orders.purchase_date.min().date(), 'to', orders.purchase_date.max().date())\n"
        "print('On-time rate:', f\"{1 - orders.late_delivery.mean():.1%}\")\n"
        "print('Average delivery time:', f\"{orders.delivery_days.mean():.1f} days\")"
    ),
    nbf.v4.new_markdown_cell(
        "`review_score` is missing for a small number of orders because no score was recorded. "
        "The app labels missing product categories `Unknown` rather than silently dropping them."
    ),
    nbf.v4.new_markdown_cell("## Delivery reliability over time"),
    nbf.v4.new_code_cell(
        "monthly = orders.groupby('purchase_month', as_index=False).agg(\n"
        "    orders=('order_id', 'size'), late_rate=('late_delivery', 'mean')\n"
        ")\n"
        "fig, ax = plt.subplots(figsize=(10, 4))\n"
        "ax.plot(monthly.purchase_month, (1-monthly.late_rate)*100, marker='o')\n"
        "ax.set(title='On-time delivery rate by purchase month', ylabel='On-time rate (%)', xlabel='Purchase month')\n"
        "ax.tick_params(axis='x', rotation=45)\n"
        "ax.grid(axis='y', alpha=.25)\n"
        "plt.show()\n"
        "monthly.sort_values('late_rate', ascending=False).head(8)"
    ),
    nbf.v4.new_markdown_cell("## State differences"),
    nbf.v4.new_code_cell(
        "state_risk = orders.groupby('customer_state', as_index=False).agg(\n"
        "    delivered_orders=('order_id', 'size'),\n"
        "    late_rate=('late_delivery', 'mean'),\n"
        "    average_review=('review_score', 'mean')\n"
        ").query('delivered_orders >= 50').sort_values('late_rate', ascending=False)\n"
        "state_risk.head(12)"
    ),
    nbf.v4.new_markdown_cell(
        "**Dashboard implication.** The EDA supports a weekly operations dashboard centered on on-time delivery, "
        "delivery time, the monthly trend, and a state–category priority list. We do not include revenue or payment "
        "breakdowns because they do not change the operations director's fulfillment decision. State differences are "
        "priorities to investigate, not proof of causality: this snapshot has no carrier or root-cause field."
    ),
]
nbf.write(nb, root / "eda.ipynb")
