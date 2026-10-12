# Olist Fulfillment Pulse

**Deployed app:** add the Streamlit URL here after deployment  
**Team:** Team Olist Ops

## 1. Dataset and decision-maker

This dashboard uses Kaggle's [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), a real dataset of roughly 100,000 marketplace orders in Brazil from 2016 to 2018. The original download contains nine related CSV files: orders, order items, products, customers, payments, reviews, sellers, and geolocation. One raw row can be an item, review, or customer rather than an order, so `prepare_data.py` joins the relevant tables into `olist_order_health.csv`, with **one row per delivered order**.

The source download is about 45 MB and its individual raw tables are not appropriate for deployment. They are deliberately excluded from Git. The committed dashboard file is 12.1 MB and has 96,476 delivered orders, so it is under the exercise's 25 MB limit. `primary_category` means the category of the highest-priced item in that order; this convention preserves one row per order when an order contains multiple items.

The dashboard is for the **Olist marketplace operations director**. The director reviews it every Monday before the weekly fulfillment meeting. It supports this decision: **if the director sees a state–category combination with a high late-delivery rate and enough orders to make that rate credible, they will assign an investigation to the relevant fulfillment or seller-operations team and review promised delivery dates.**

Without this dashboard, the director would need to export and join order, item, customer, and review tables manually. That delays the weekly meeting and makes it easy to react to a small, noisy group rather than a recurring fulfillment problem. A dashboard is justified because the same person makes the same prioritization decision every week; a one-off report or weekly email cannot let them narrow from all orders to the state and category under discussion.

## 2. What the EDA showed and what the dashboard shows

The quick EDA is in `eda.ipynb`. The delivered-order file has 96,476 rows and 13 columns; its purchase dates run from September 2016 through August 2018. Overall, 91.9% of delivered orders arrived on or before the promised date and the average delivery time was 12.6 days. The state breakdown shows meaningful differences: Maranhão (MA) had a 19.7% late-delivery rate across 717 delivered orders, Ceará (CE) 15.3% across 1,279, and Rio de Janeiro (RJ) 13.5% across 12,353. These are operations signals that merit follow-up, not proof that the customer state caused the delay.

The page follows the decision-maker's sequence:

1. **Top — three headline metrics.** Delivered orders shows the scale of the selected group; on-time delivery rate states whether there is a reliability problem; average delivery time gives its operational size. The director can read these within five seconds.
2. **Middle — two explanations.** The monthly on-time trend says whether the problem is recent or persistent. The state-risk bar chart ranks where to investigate, while excluding groups with fewer than 50 orders so a handful of late orders does not dominate the meeting.
3. **Bottom — a state–category priority table.** This is the drill-down list used to assign the next investigation. It includes order count, late rate, delivery days, and review score.

The only filters are purchase date, customer state, and primary product category. Each can change the weekly action; no generic slider or technical filter was added.

### What we cut

* **Revenue, payment type, and payment installments:** they are available in the original data and interesting for commercial analysis, but they do not help this director decide where delivery reliability needs intervention. They would compete with the central fulfillment decision.
* **Seller map and geolocation distances:** the raw dataset has seller and ZIP-code information, but the geolocation table is large, duplicate-prone, and would create a visually attractive map without identifying a controllable cause. The dashboard instead uses state and category, which the operations team can act on immediately.

### Data limitations and safeguards

The Kaggle data is a historical, frozen snapshot, not a live feed. The app uses delivered orders only: for an order still being processed, delivery time and lateness are not yet defined. About 646 delivered orders (0.7%) have no review score, so review averages ignore missing scores; a review score is customer feedback, not an objective delivery measurement. About 1,378 orders have no translated product category and are labeled `Unknown`. The source has no carrier identifier or a recorded root cause for a late delivery. Therefore the app labels high-risk state–category groups as *investigation priorities*, never as proven causes.

## 3. Refresh and review design

In production, order and promised-date data should **refresh nightly** from the marketplace and logistics systems. The operations director should **review it every Monday morning** before allocating the week's work; refresh and review frequency differ because weekly interventions need a current completed week, not minute-by-minute data.

The tracked action metric is the late-delivery rate for each state–category group. A practical alert would trigger when a group with at least 50 delivered orders exceeds **12% late deliveries** in the trailing four weeks, or rises by at least five percentage points versus the prior four weeks. That should prompt the director to contact the responsible seller-operations or fulfillment team the same day. A day of stale data is tolerable for the weekly review; a week of stale data could hide a newly failing route long enough for more customers to receive late orders and leave poor reviews.

The app repeats the historical data period and the intended nightly-refresh/Monday-review cadence below its filters so viewers do not mistake the Kaggle snapshot for live operations data.

## Run locally

```bash
uv run streamlit run app.py
```

To recreate the compact dashboard file after downloading the original Kaggle CSVs into `raw/`, run:

```bash
uv run python prepare_data.py
```

