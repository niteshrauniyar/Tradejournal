# =========================
# 📦 IMPORTS
# =========================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
import random

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(
    page_title="MNQ Prop Firm Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "trading.db"

# =========================
# 🎨 ULTRA MODERN UI
# =========================
st.markdown("""
<style>

/* GLOBAL */
.stApp {
    background: radial-gradient(circle at top, #0b1220, #05070d);
    color: #ffffff;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #0a0f1c;
    border-right: 1px solid #1f2a44;
}

/* GLASS CARDS */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 16px;
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}

/* BUTTONS */
.stButton button {
    background: linear-gradient(90deg, #3b82f6, #06b6d4);
    color: white;
    border-radius: 12px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    border: none;
    transition: 0.2s;
}

.stButton button:hover {
    transform: scale(1.03);
}

/* TITLES */
h1, h2, h3 {
    color: #e6edf3;
}

/* DATAFRAME */
.dataframe {
    background: rgba(255,255,255,0.03);
}

</style>
""", unsafe_allow_html=True)

# =========================
# 🧠 DATABASE
# =========================
def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init():
    c = conn().cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        d TEXT,
        dir TEXT,
        entry REAL,
        exit REAL,
        qty INTEGER,
        pnl REAL,
        score REAL
    )
    """)
    conn().commit()
    conn().close()

init()

def add_trade(row):
    c = conn().cursor()
    c.execute("""
    INSERT INTO trades (d, dir, entry, exit, qty, pnl, score)
    VALUES (?,?,?,?,?,?,?)
    """, row)
    conn().commit()
    conn().close()

def load():
    return pd.read_sql("SELECT * FROM trades", conn())

# =========================
# 🧮 CALC
# =========================
def pnl(entry, exit, qty, dir):
    return (exit-entry)*qty if dir=="Buy" else (entry-exit)*qty

def quote():
    return random.choice([
        "Discipline beats intelligence.",
        "Protect capital first.",
        "Execution is the edge.",
        "Consistency compounds."
    ])

# =========================
# 🧭 SIDEBAR
# =========================
st.sidebar.title("📊 PROP FIRM TERMINAL")
menu = st.sidebar.radio("NAVIGATION", ["Dashboard", "Add Trade", "Analytics"])

st.sidebar.markdown("### 🧠 Daily Quote")
st.sidebar.info(quote())

# =========================
# 📊 DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📈 MNQ Trading Command Center")

    df = load()

    if len(df) > 0:

        total = df["pnl"].sum()
        win = len(df[df.pnl > 0]) / len(df) * 100
        score = df["score"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Net PnL", f"${total:.2f}")
        col2.metric("🎯 Win Rate", f"{win:.1f}%")
        col3.metric("🧠 Discipline", f"{score:.1f}%")

        st.divider()

        # EQUITY CURVE
        df["cum"] = df["pnl"].cumsum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["d"],
            y=df["cum"],
            mode="lines",
            line=dict(color="#00e5ff", width=3)
        ))

        fig.update_layout(
            template="plotly_dark",
            title="Equity Curve",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # DAILY PNL
        daily = df.groupby("d")["pnl"].sum().reset_index()

        fig2 = px.bar(
            daily,
            x="d",
            y="pnl",
            color="pnl",
            color_continuous_scale=["red", "black", "lime"]
        )

        fig2.update_layout(template="plotly_dark", height=350)

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("No trades yet.")

# =========================
# ➕ ADD TRADE
# =========================
elif menu == "Add Trade":
    st.title("➕ Add Trade")

    with st.form("t"):

        dir = st.selectbox("Direction", ["Buy", "Sell"])
        entry = st.number_input("Entry")
        exit = st.number_input("Exit")
        qty = st.number_input("Qty", value=1)

        st.subheader("📌 RULE CHECK")

        liq = st.checkbox("Liquidity Hunt")
        eng = st.checkbox("Engulfing Confirmed")
        kill = st.checkbox("Killzone")
        trend = st.checkbox("Trend Aligned")
        risk = st.checkbox("Risk Defined")

        submit = st.form_submit_button("Save Trade")

        if submit:

            p = pnl(entry, exit, qty, dir)

            score = (liq + eng + kill + trend + risk) / 5 * 100

            add_trade((
                str(date.today()),
                dir,
                entry,
                exit,
                qty,
                p,
                score
            ))

            st.success(f"Saved ✔ PnL: {p:.2f} | Score: {score:.1f}%")

# =========================
# 📊 ANALYTICS
# =========================
elif menu == "Analytics":
    st.title("📊 Analytics Engine")

    df = load()

    if len(df) > 0:

        st.subheader("PnL Distribution")

        fig = px.histogram(df, x="pnl", nbins=20, color_discrete_sequence=["#00e5ff"])
        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Performance Trend")

        fig2 = px.line(df, x="d", y="score", color_discrete_sequence=["#3b82f6"])
        fig2.update_layout(template="plotly_dark")

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No data yet.")
