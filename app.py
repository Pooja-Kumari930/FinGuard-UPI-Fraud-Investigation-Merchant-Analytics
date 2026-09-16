import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import math

st.set_page_config(
    page_title="FinGuard UPI Fraud Investigation & Merchant Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme / layout ----------
st.markdown("""
<style>
/* FinGuard — safe premium purple-charcoal theme */
:root{--bg:#151126;--panel:#211a32;--panel2:#261e3b;--border:#3a3154;--cyan:#27e6f5;--red:#ff4d78;--purple:#8b5cf6;--text:#f7f4ff;--muted:#b9b1cc;--dim:#8f87a4;}
html,body,.stApp{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:#151126!important;color:var(--text)!important;}
.stApp{background:radial-gradient(circle at 8% 5%,rgba(139,92,246,.22),transparent 27%),radial-gradient(circle at 94% 8%,rgba(39,230,245,.10),transparent 23%),linear-gradient(135deg,#151126 0%,#19132b 52%,#120e20 100%)!important;min-height:100vh;}
.block-container{max-width:1540px;padding-top:1.2rem;padding-bottom:2.5rem;}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stSidebar"]{background:#171228!important;border-right:1px solid #3a3154!important;min-width:292px;max-width:292px;}
[data-testid="stSidebar"]>div:first-child{background:transparent!important;padding-top:1rem;}
[data-testid="stSidebar"] *{color:var(--text)!important;}
[data-testid="stCaptionContainer"] *{color:var(--muted)!important;}
.stMarkdown,.stMarkdown p,.stMarkdown span,.stMarkdown li{color:var(--text)!important;}
[data-testid="stWidgetLabel"] *{color:var(--text)!important;}
.hero{position:relative;overflow:hidden;padding:28px 32px 26px;margin-bottom:22px;border-radius:22px;background:linear-gradient(135deg,#29203e,#211a33)!important;border:1px solid #4a3d67!important;box-shadow:0 18px 45px rgba(0,0,0,.28)!important;}
.hero:after{content:"";position:absolute;right:-70px;top:-100px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(39,230,245,.16),transparent 68%);pointer-events:none;}
.hero h1{position:relative;color:#fff!important;font-size:37px;margin:0 0 8px;font-weight:800;letter-spacing:-.7px;line-height:1.15;}
.hero p{position:relative;color:#c8c0d8!important;margin:0;font-size:14px;}
.kpi,.card,.signal{background:#211a32!important;border:1px solid #3a3154!important;box-shadow:0 12px 30px rgba(0,0,0,.22)!important;}
.kpi{border-radius:16px;padding:16px 18px;min-height:108px;overflow:hidden;position:relative;}
.kpi:hover,.card:hover{transform:translateY(-3px);border-color:#7562a4!important;}
.kpi .label{color:#bdb5cf!important;font-size:12px;font-weight:700;white-space:nowrap;text-transform:uppercase;letter-spacing:.6px;}
.kpi .value{color:#fff!important;font-size:26px;font-weight:800;margin-top:7px;line-height:1.15;}
.kpi .hint{color:#9188a7!important;font-size:10.5px;margin-top:8px;}
.card{border-radius:16px;padding:15px 18px;}
.signal{border-radius:13px;padding:12px 15px;margin-bottom:8px;color:#f1edf8!important;background:#291b32!important;}
.signal:hover{transform:translateY(-2px);border-color:#b13d64!important;}
.section{color:#fff!important;font-size:20px;font-weight:800;margin:22px 0 8px;}
.subtle{color:#aaa1bd!important;font-size:12.5px;line-height:1.6;}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#211a32!important;border:1px solid #3a3154!important;border-radius:16px!important;}
button[data-baseweb="tab"]{color:#aaa1bd!important;font-weight:700!important;background:transparent!important;}
button[data-baseweb="tab"][aria-selected="true"]{color:#fff!important;background:#2b2142!important;box-shadow:inset 0 -2px 0 #27e6f5!important;border-radius:9px 9px 0 0!important;}
div[data-baseweb="select"]>div{background:#241c37!important;color:#fff!important;border:1px solid #42365c!important;border-radius:10px!important;}
[role="option"]{background:#241c37!important;color:#fff!important;}
[role="option"]:hover{background:#33274b!important;}
.stButton>button{color:#fff!important;background:linear-gradient(90deg,#7048d9,#8b5cf6)!important;border:1px solid #9d7df0!important;border-radius:10px!important;font-weight:700!important;}
.stTextInput input,.stTextArea textarea{background:#241c37!important;color:#fff!important;border:1px solid #42365c!important;border-radius:10px!important;}
.stDataFrame{border:1px solid #3a3154!important;}
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
tx = pd.read_csv("transactions_dashboard.csv")
cb = pd.read_csv("fact_chargebacks.csv")
customers = pd.read_csv("dim_customers.csv")
merchants = pd.read_csv("dim_merchants.csv")

tx["timestamp"] = pd.to_datetime(tx["timestamp"], errors="coerce", format="mixed")
for c in ["transaction_timestamp", "reported_timestamp", "bank_response_timestamp"]:
    if c in cb.columns:
        cb[c] = pd.to_datetime(cb[c], errors="coerce", format="mixed")

# ---------- Helpers ----------
def money(v):
    try:
        v = float(v)
    except Exception:
        return "₹0"
    a = abs(v)
    if a >= 1_000_000_000:
        return f"₹{v/1_000_000_000:.1f}B"
    if a >= 1_000_000:
        return f"₹{v/1_000_000:.1f}M"
    if a >= 100_000:
        return f"₹{v/100_000:.1f}L"
    return f"₹{v:,.0f}"

def pct(v):
    return f"{float(v):.1f}%"

def base_layout(fig, height=390, margin=None):
    if margin is None:
        margin = dict(l=18, r=18, t=58, b=42)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,14,23,0.72)",
        font=dict(color="#B9B2C4", size=12),
        title_font=dict(color="#FFFFFF", size=18),
        margin=margin,
        height=height,
        hoverlabel=dict(bgcolor="#151d2c", bordercolor="#00f0ff", font_color="#FFFFFF"),
        legend=dict(bgcolor="rgba(10,14,23,.82)", font=dict(color="#E7ECF5")),
    )
    return fig

def network_graph(data, merchant_id):
    d = data[data["merchant_id"].astype(str) == str(merchant_id)].copy()
    d = d.sort_values(["has_chargeback", "amount_inr"], ascending=[False, False]).head(25)
    mid = str(merchant_id)
    merchant_name = d["merchant_name"].dropna().iloc[0] if len(d) else mid
    users = d["user_id"].astype(str).dropna().unique().tolist()[:18]
    if not users:
        return None, "No linked users are available for this merchant in the cleaned transaction table."
    nodes = [(mid, merchant_name, 0, 0, "merchant")]
    for i, u in enumerate(users):
        a = 2 * math.pi * i / max(len(users), 1)
        nodes.append((u, f"User {u[-8:]}", 2.7 * math.cos(a), 2.7 * math.sin(a), "user"))
    pos = {n[0]: (n[2], n[3]) for n in nodes}
    edge_x, edge_y = [], []
    for u in users:
        x1, y1 = pos[mid]; x2, y2 = pos[u]
        edge_x += [x1, x2, None]; edge_y += [y1, y2, None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1.5, color="rgba(0,240,255,.34)"), hoverinfo="none"))
    xs = [n[2] for n in nodes]; ys = [n[3] for n in nodes]
    labels = [n[1] for n in nodes]
    sizes = [34] + [15] * len(users)
    texts = [f"Merchant: {merchant_name}<br>ID: {mid}"] + [f"User: {u}" for u in users]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=labels, textposition="top center", marker=dict(size=sizes, line=dict(width=2, color="white")), customdata=texts, hovertemplate="%{customdata}<extra></extra>"))
    fig.update_layout(showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,14,23,0.72)", margin=dict(l=10,r=10,t=20,b=10), height=470)
    return fig, None

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>🛡️ FinGuard UPI Fraud Investigation &amp; Merchant Analytics</h1>
  <p>Merchant Analytics • Chargeback Intelligence • Risk Investigation • Transaction Network Explorer</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🔎 Dashboard Filters")
    st.caption("Leave any filter empty to include all values.")
    status_options = sorted(tx["status"].dropna().astype(str).unique().tolist())
    cat_options = sorted(tx["merchant_category"].fillna("UNKNOWN").astype(str).unique().tolist())
    risk_options = sorted(tx["risk_segment"].fillna("UNKNOWN").astype(str).unique().tolist())
    statuses = st.multiselect("Transaction status", status_options, default=status_options, key="status_filter")
    cats = st.multiselect("Merchant category", cat_options, default=cat_options, key="cat_filter")
    risks = st.multiselect("Customer risk segment", risk_options, default=risk_options, key="risk_filter")
    selected_statuses = statuses if statuses else status_options
    selected_cats = cats if cats else cat_options
    selected_risks = risks if risks else risk_options
    st.markdown("---")
    st.caption("Synthetic datathon data • Signals support investigation and are not confirmed fraud labels.")

f = tx[
    tx["status"].isin(selected_statuses)
    & tx["merchant_category"].fillna("UNKNOWN").astype(str).isin(selected_cats)
    & tx["risk_segment"].fillna("UNKNOWN").astype(str).isin(selected_risks)
].copy()

# ---------- KPI strip ----------
total_transactions = len(f)
total_value = f["amount_inr"].sum()
total_cb = int(f["chargeback_count"].sum())
failed_rate = 100 * f["status"].eq("FAILED").mean() if len(f) else 0
avg_value = f["amount_inr"].mean() if len(f) else 0

kcols = st.columns(5, gap="medium")
kpis = [
    (kcols[0], "Transactions", f"{total_transactions:,}", "Filtered transaction count"),
    (kcols[1], "Transaction Value", money(total_value), "Total transaction amount"),
    (kcols[2], "Avg. Transaction", money(avg_value), "Average ticket size"),
    (kcols[3], "Chargebacks", f"{total_cb:,}", "Linked dispute events"),
    (kcols[4], "Failed Rate", pct(failed_rate), "Failed / filtered transactions"),
]
for col, label, value, hint in kpis:
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="hint">{hint}</div></div>', unsafe_allow_html=True)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🚨 Risk Investigation", "🕸️ Fraud Ring Explorer", "🤖 Ask FinGuard"])
chart_template = "plotly_dark"

def add_category_chargeback_chart(data):
    g = data.groupby("merchant_category", dropna=False).agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum"), value=("amount_inr", "sum")).reset_index()
    g["chargeback_rate"] = 100 * g["chargebacks"] / g["transactions"].replace(0, pd.NA)
    g = g.dropna(subset=["chargeback_rate"]).sort_values("chargeback_rate", ascending=False).head(12)
    fig = px.bar(g, x="chargeback_rate", y="merchant_category", orientation="h", text=g["chargeback_rate"].map(lambda x: f"{x:.1f}%"), title="Chargeback Rate by Merchant Category", template=chart_template)
    fig.update_traces(marker_color="#ff3366", textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Chargeback rate (%)", rangemode="tozero")
    return base_layout(fig, 410, dict(l=18,r=40,t=58,b=38))

with tab1:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        daily = f.dropna(subset=["timestamp"]).assign(date=f.dropna(subset=["timestamp"])["timestamp"].dt.floor("D")).groupby("date", as_index=False).agg(value=("amount_inr", "sum"))
        fig = px.line(daily, x="date", y="value", title="Daily Transaction Value", template=chart_template, markers=False, hover_data={"value":":,.0f"})
        fig.update_traces(line=dict(width=3, color="#00f0ff"))
        fig.update_xaxes(type="date", tickformat="%b %d", dtick="M1", title="Date", showgrid=False)
        fig.update_yaxes(title="Transaction value (₹)", tickprefix="₹", separatethousands=True, rangemode="tozero")
        st.plotly_chart(base_layout(fig, 390, dict(l=20,r=20,t=58,b=50)), width="stretch", key="daily_transaction_value")
    with c2:
        cat = f.groupby("merchant_category", dropna=False)["amount_inr"].sum().reset_index().sort_values("amount_inr", ascending=False).head(12)
        cat["merchant_category"] = cat["merchant_category"].fillna("UNKNOWN")
        fig = px.bar(cat.sort_values("amount_inr"), x="amount_inr", y="merchant_category", orientation="h", title="Transaction Value by Merchant Category", template=chart_template, text=cat.sort_values("amount_inr")["amount_inr"].map(money))
        fig.update_traces(marker_color="#7000ff", textposition="outside", cliponaxis=False)
        fig.update_xaxes(title="Transaction value (₹)", tickprefix="₹", separatethousands=True)
        fig.update_yaxes(title="")
        st.plotly_chart(base_layout(fig, 390, dict(l=18,r=70,t=58,b=42)), width="stretch", key="category_value")

    c3, c4 = st.columns(2, gap="medium")
    with c3:
        st.plotly_chart(add_category_chargeback_chart(f), width="stretch", key="category_chargeback_rate")
    with c4:
        reasons = cb["reason_code"].fillna("UNKNOWN").value_counts().head(10).reset_index()
        reasons.columns = ["reason", "count"]
        fig = px.bar(reasons.sort_values("count"), x="count", y="reason", orientation="h", title="Top Chargeback Reasons", template=chart_template, text="count")
        fig.update_traces(marker_color="#ff3366", textposition="outside", cliponaxis=False)
        fig.update_xaxes(title="Chargeback events")
        fig.update_yaxes(title="")
        st.plotly_chart(base_layout(fig, 410, dict(l=18,r=50,t=58,b=42)), width="stretch", key="chargeback_reasons")

    # Additional composition and trend visuals for deeper analysis
    st.markdown('<div class="section">📈 Payment Health & Risk Mix</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3, gap="medium")
    with p1:
        status = f["status"].fillna("UNKNOWN").value_counts().reset_index()
        status.columns = ["status", "count"]
        fig = px.pie(status, names="status", values="count", hole=0.55, title="Transaction Status Mix", template=chart_template)
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#0a0e17", width=2)))
        st.plotly_chart(base_layout(fig, 360, dict(l=10,r=10,t=58,b=20)), width="stretch", key="transaction_status_donut")
    with p2:
        risk_mix = f["risk_segment"].fillna("UNKNOWN").value_counts().reset_index()
        risk_mix.columns = ["risk_segment", "count"]
        fig = px.pie(risk_mix, names="risk_segment", values="count", hole=0.55, title="Customer Risk Distribution", template=chart_template)
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#0a0e17", width=2)))
        st.plotly_chart(base_layout(fig, 360, dict(l=10,r=10,t=58,b=20)), width="stretch", key="risk_distribution_donut")
    with p3:
        sev = cb["severity"].fillna("UNKNOWN").value_counts().reset_index()
        sev.columns = ["severity", "count"]
        fig = px.pie(sev, names="severity", values="count", hole=0.55, title="Chargeback Severity Mix", template=chart_template)
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="#0a0e17", width=2)))
        st.plotly_chart(base_layout(fig, 360, dict(l=10,r=10,t=58,b=20)), width="stretch", key="chargeback_severity_donut")

    trend_cols = st.columns(2, gap="medium")
    with trend_cols[0]:
        daily_count = f.dropna(subset=["timestamp"]).assign(date=lambda d: d["timestamp"].dt.floor("D")).groupby("date", as_index=False).size().rename(columns={"size":"transactions"})
        fig = px.line(daily_count, x="date", y="transactions", title="Daily Transaction Volume", template=chart_template, markers=True)
        fig.update_traces(line=dict(width=3, color="#00f0ff"), marker=dict(size=5, color="#7000ff"))
        fig.update_xaxes(title="Date", tickformat="%b %d", dtick="M1", showgrid=False)
        fig.update_yaxes(title="Transactions", rangemode="tozero")
        st.plotly_chart(base_layout(fig, 380, dict(l=20,r=20,t=58,b=50)), width="stretch", key="daily_transaction_count")
    with trend_cols[1]:
        cb_month = cb.dropna(subset=["transaction_timestamp"]).assign(month=lambda d: d["transaction_timestamp"].dt.to_period("M").astype(str)).groupby("month", as_index=False).agg(chargebacks=("txn_id","count"))
        fig = px.line(cb_month, x="month", y="chargebacks", title="Monthly Chargeback Trend", template=chart_template, markers=True)
        fig.update_traces(line=dict(width=3, color="#ff3366"), marker=dict(size=6, color="#7000ff"))
        fig.update_xaxes(title="Month", showgrid=False)
        fig.update_yaxes(title="Chargeback events", rangemode="tozero")
        st.plotly_chart(base_layout(fig, 380, dict(l=20,r=20,t=58,b=50)), width="stretch", key="monthly_chargeback_trend")

with tab2:
    st.markdown('<div class="section">🚨 Investigation Signals</div>', unsafe_allow_html=True)
    high_users = int((f["risk_segment"] == "HIGH").sum())
    high_cb = int(f.loc[f["risk_segment"] == "HIGH", "chargeback_count"].sum())
    invalid_utr = int((~f["utr_valid"].fillna(False)).sum())
    signal_cols = st.columns(3, gap="medium")
    for col, title, val, desc in [
        (signal_cols[0], "High-risk transactions", f"{high_users:,}", "Transactions linked to HIGH risk users"),
        (signal_cols[1], "High-risk chargebacks", f"{high_cb:,}", "Chargebacks from HIGH risk users"),
        (signal_cols[2], "Missing / invalid UTR", f"{invalid_utr:,}", "Data-quality investigation signal"),
    ]:
        col.markdown(f'<div class="signal"><b>{title}</b><br><span style="font-size:24px;font-weight:800">{val}</span><br><small>{desc}</small></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        m = f.groupby("merchant_name", dropna=False).agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum"), value=("amount_inr", "sum")).reset_index()
        m["rate"] = 100 * m["chargebacks"] / m["transactions"].replace(0, pd.NA)
        m = m.dropna(subset=["rate"]).sort_values("rate", ascending=False).head(12).sort_values("rate")
        fig = px.bar(m, x="rate", y="merchant_name", orientation="h", title="Merchants with Highest Chargeback Rate", template=chart_template, text=m["rate"].map(lambda x: f"{x:.1f}%"))
        fig.update_traces(marker_color="#ff3366", textposition="outside", cliponaxis=False)
        fig.update_xaxes(title="Chargeback rate (%)")
        fig.update_yaxes(title="")
        st.plotly_chart(base_layout(fig, 430, dict(l=18,r=45,t=58,b=42)), width="stretch", key="merchant_chargeback_rate")
    with c2:
        risk = f.groupby("risk_segment").agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum")).reset_index()
        fig = px.bar(risk, x="risk_segment", y="chargebacks", title="Chargebacks by Customer Risk Segment", template=chart_template, text="chargebacks")
        fig.update_traces(marker_color="#00f0ff", textposition="outside", cliponaxis=False)
        fig.update_yaxes(title="Chargeback events")
        st.plotly_chart(base_layout(fig, 430), width="stretch", key="risk_chargebacks")

    st.markdown('<div class="section">Why these are signals</div>', unsafe_allow_html=True)
    st.info("These indicators prioritize records for investigation. They are not confirmed fraud labels.")
    sig = f.groupby("risk_flag").agg(transactions=("txn_id", "count"), amount=("amount_inr", "sum"), chargebacks=("chargeback_count", "sum")).reset_index().sort_values("chargebacks", ascending=False)
    st.dataframe(sig, width="stretch", hide_index=True, column_config={"amount": st.column_config.NumberColumn("Amount (₹)", format="₹%0.0f")})

with tab3:
    st.markdown('<div class="section">🕸️ Fraud Ring Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtle">Explore user ↔ merchant relationship links from cleaned transactions. A connection is an analytical relationship, not proof of a criminal ring.</div>', unsafe_allow_html=True)
    merchant_pool = f.groupby(["merchant_id", "merchant_name"], dropna=False).agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum"), value=("amount_inr", "sum")).reset_index().sort_values(["chargebacks", "transactions"], ascending=False)
    merchant_pool = merchant_pool[merchant_pool["merchant_id"].notna()].head(100)
    if len(merchant_pool):
        labels = {str(r.merchant_id): f"{r.merchant_name} | {str(r.merchant_id)[-8:]}" for _, r in merchant_pool.iterrows()}
        chosen = st.selectbox("Select a merchant to investigate", list(labels.keys()), format_func=lambda x: labels[x])
        row = merchant_pool[merchant_pool["merchant_id"].astype(str) == str(chosen)].iloc[0]
        a,b,c,d = st.columns(4)
        a.metric("Transactions", f"{int(row.transactions):,}")
        b.metric("Transaction Value", money(row.value))
        c.metric("Chargebacks", f"{int(row.chargebacks):,}")
        d.metric("Chargeback Rate", pct(100 * row.chargebacks / row.transactions if row.transactions else 0))
        gcol, tcol = st.columns([1.7,1], gap="medium")
        with gcol:
            fig, msg = network_graph(f, chosen)
            if fig: st.plotly_chart(fig, width="stretch", key="network_graph")
            else: st.warning(msg)
        with tcol:
            st.markdown('<div class="card"><b>Investigation checklist</b></div>', unsafe_allow_html=True)
            md = f[f["merchant_id"].astype(str) == str(chosen)].copy()
            high = int((md["risk_segment"] == "HIGH").sum())
            cbn = int(md["chargeback_count"].sum())
            bad = int((~md["utr_valid"].fillna(False)).sum())
            items = []
            if cbn: items.append(f"⚠️ {cbn} linked chargeback events")
            if high: items.append(f"⚠️ {high} transactions linked to HIGH risk users")
            if bad: items.append(f"⚠️ {bad} transactions with missing/invalid UTR signal")
            if not items: items.append("✓ No major investigation signal in the selected filters")
            for item in items: st.markdown(f'<div class="signal">{item}</div>', unsafe_allow_html=True)
            st.caption("Use this view to prioritize investigation, not to declare fraud.")
    else:
        st.warning("No merchant relationships are available under the current filters.")

with tab4:
    st.markdown('<div class="section">🤖 Ask FinGuard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtle">Ask a business question in plain language. This prototype routes supported questions to the relevant metric and visualization.</div>', unsafe_allow_html=True)
    examples = [
        "Which merchant category has the highest chargeback-to-transaction ratio?",
        "Show me the top merchants by chargebacks",
        "What is the failed transaction rate by merchant category?",
        "Show high-risk transaction activity",
        "What are the most common chargeback reasons?",
    ]
    query = st.text_input("Ask a question", placeholder="e.g. Which merchant category has the highest chargeback-to-transaction ratio?")
    if not query:
        st.markdown("**Try one of these:**")
        st.write(" • ".join(examples))
    else:
        q = query.lower()
        if any(x in q for x in ["chargeback-to-transaction", "chargeback rate", "dispute rate", "ratio"]):
            g = f.groupby("merchant_category", dropna=False).agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum")).reset_index()
            g["chargeback_rate"] = 100 * g["chargebacks"] / g["transactions"].replace(0, pd.NA)
            g = g.dropna(subset=["chargeback_rate"]).sort_values("chargeback_rate", ascending=False)
            if len(g):
                top = g.iloc[0]
                st.success(f"Highest chargeback-to-transaction ratio: **{top.merchant_category}** at **{top.chargeback_rate:.1f}%** ({int(top.chargebacks):,} chargebacks across {int(top.transactions):,} transactions).")
                fig = px.bar(g.head(10).sort_values("chargeback_rate"), x="chargeback_rate", y="merchant_category", orientation="h", title="Chargeback-to-Transaction Ratio by Category", template=chart_template, text=g.head(10).sort_values("chargeback_rate")["chargeback_rate"].map(lambda x:f"{x:.1f}%"))
                fig.update_traces(marker_color="#ff3366", textposition="outside", cliponaxis=False)
                st.plotly_chart(base_layout(fig, 410, dict(l=18,r=45,t=58,b=42)), width="stretch", key="ask_ratio")
        elif "top merchant" in q or ("merchants" in q and "chargeback" in q):
            g = f.groupby("merchant_name", dropna=False).agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum"), value=("amount_inr", "sum")).reset_index().sort_values("chargebacks", ascending=False).head(10).sort_values("chargebacks")
            fig = px.bar(g, x="chargebacks", y="merchant_name", orientation="h", title="Top Merchants by Chargebacks", template=chart_template, text="chargebacks")
            fig.update_traces(marker_color="#00f0ff", textposition="outside", cliponaxis=False)
            st.plotly_chart(base_layout(fig, 420, dict(l=18,r=55,t=58,b=42)), width="stretch", key="ask_merchants")
            if len(g): st.success(f"Highest chargeback merchant in the current filter: **{g.iloc[-1].merchant_name}** with **{int(g.iloc[-1].chargebacks):,}** chargebacks.")
        elif "failed" in q:
            g = f.groupby("merchant_category", dropna=False).agg(transactions=("txn_id", "count"), failed=("status", lambda s: (s == "FAILED").sum())).reset_index()
            g["failed_rate"] = 100 * g["failed"] / g["transactions"].replace(0, pd.NA)
            g = g.dropna(subset=["failed_rate"]).sort_values("failed_rate", ascending=False).head(12).sort_values("failed_rate")
            fig = px.bar(g, x="failed_rate", y="merchant_category", orientation="h", title="Failed Transaction Rate by Merchant Category", template=chart_template, text=g["failed_rate"].map(lambda x:f"{x:.1f}%"))
            fig.update_traces(marker_color="#7000ff", textposition="outside", cliponaxis=False)
            st.plotly_chart(base_layout(fig, 410, dict(l=18,r=45,t=58,b=42)), width="stretch", key="ask_failed")
        elif "high-risk" in q or "high risk" in q or "risk" in q:
            g = f[f["risk_segment"] == "HIGH"].groupby("merchant_category").agg(transactions=("txn_id", "count"), chargebacks=("chargeback_count", "sum"), value=("amount_inr", "sum")).reset_index().sort_values("transactions", ascending=False).head(12)
            st.dataframe(g, width="stretch", hide_index=True)
            st.info("This result shows HIGH-risk customer activity in the current filtered dataset; it is an investigation signal, not a fraud verdict.")
        elif "reason" in q or "chargeback" in q:
            r = cb["reason_code"].fillna("UNKNOWN").value_counts().head(10).reset_index(); r.columns = ["reason", "count"]; r = r.sort_values("count")
            fig = px.bar(r, x="count", y="reason", orientation="h", title="Most Common Chargeback Reasons", template=chart_template, text="count")
            fig.update_traces(marker_color="#ff3366", textposition="outside", cliponaxis=False)
            st.plotly_chart(base_layout(fig, 420, dict(l=18,r=55,t=58,b=42)), width="stretch", key="ask_reasons")
        else:
            st.warning("I can currently answer questions about chargeback rates, top merchants, failed rates, high-risk activity, and chargeback reasons. Try one of the examples above.")

st.markdown("<div style='text-align:center;color:#8FA9C2;font-size:11px;margin-top:18px'>FinGuard UPI Fraud Investigation &amp; Merchant Analytics • AgentIQ Datathon 2026 • Synthetic dataset • Analytical risk signals only</div>", unsafe_allow_html=True)
