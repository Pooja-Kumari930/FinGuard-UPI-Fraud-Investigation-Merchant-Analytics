# FinGuard UPI Fraud Investigation & Merchant Analytics

AgentIQ Datathon 2026 — FinTech & BFSI Track

## What this project does
FinGuard converts messy synthetic UPI, KYC, merchant and chargeback data into a cleaned analytical model and an interactive Streamlit investigation dashboard.

## Dashboard views
- Overview — executive KPIs, transaction value, merchant-category analysis, chargeback rate, chargeback reasons
- Payment Health & Risk Mix — transaction status donut, customer risk donut, chargeback severity donut, daily transaction volume line, monthly chargeback trend line
- Risk Investigation — merchant chargeback rate, risk-segment chargebacks and investigation signals
- Fraud Ring Explorer — user ↔ merchant relationship network
- Ask FinGuard — rule-based natural-language query routing for supported analytics questions

## Theme
Deep navy fintech theme with blue, purple and pink accents. The dashboard uses Plotly interactive charts with hover tooltips and filtering.

## Important interpretation note
Investigation signals are analytical prioritization aids. They are not confirmed fraud labels or criminal-ring findings. The dataset is synthetic.

## Run locally
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
https://github.com/Pooja-Kumari930/FinGuard-UPI-Fraud-Investigation-Merchant-Analytics.git
