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
st.set_page_config(page_title="MNQ Trading Journal", layout="wide")

DB_NAME = "trading_journal.db"

# =========================
# 🎨 PREMIUM UI STYLE
# =========================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top, #0b1220, #05070d);
    color: #ffffff;
}

section[data-testid="stSidebar"] {
    background-color: #0a0f1c;
    border-right: 1px solid #1f2a44;
}

div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
}

h1, h2, h3 {
    color: #e6edf3;
}

.stButton button {
    background: linear-gradient(90deg, #3b82f6, #06b6d4);
    color: white;
    border-radius: 10px;
    font-weight: 600;
    border: none;
}

.stButton button:hover {
    transform: scale(1.02);
}

</style>
""", unsafe_allow_html=True)

# =========================
# 🧠 DB
# =========================
def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT,
        direction TEXT,
        entry REAL,
        exit REAL,
        qty INTEGER,
        pnl REAL,
        rule_score REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# 📊 HELPERS
# =========================
def calc_pnl(entry, exit_price, qty, direction):
    return (exit_price - entry) * qty if direction == "Buy" else (entry - exit_price) * qty

def add_trade(row):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO trades (trade_date, direction, entry, exit, qty, pnl, rule_score)
    VALUES (?,?,?,?,?,?,?)
    """, row)
    conn.commit()
    conn.close()

def load():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()
    return df

def quote():
    return random.choice([
        "Discipline is the real edge.",
        "Consistency beats intensity.",
        "Protect capital first.",
        "Execution > Prediction"
    ])

# =========================
# 🧭 SIDEBAR
# =========================
st.sidebar.title("📊 MNQ Journal")
menu = st.sidebar.radio("Menu", ["Dashboard", "Add Trade", "Analytics"])

st.sidebar.markdown("### 🧠 Quote")
st.sidebar.info(quote())

# =========================
# 📊 DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📈 Trading Command Center")

    df = load()

    if len(df) > 0:
        pnl = df["pnl"].sum()
        winrate = len(df[df.pnl > 0]) / len(df) * 100
        avg_score = df["rule_score"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Net PnL", f"${pnl:.2f}")
        col2.metric("🎯 Win Rate", f"{winrate:.1f}%")
        col3.metric("🧠 Discipline", f"{avg_score:.1f}%")

        st.divider()

        # EQUITY CURVE
        df["cum"] = df["pnl"].cumsum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["trade_date"],
            y=df["cum"],
            mode="lines",
            line=dict(color="#00e5ff", width=3)
        ))

        fig.update_layout(
            template="plotly_dark",
            title="📈 Equity Curve",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # DAILY PNL
        daily = df.groupby("trade_date")["pnl"].sum().reset_index()

        fig2 = px.bar(
            daily,
            x="trade_date",
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

    with st.form("form"):
        direction = st.selectbox("Direction", ["Buy", "Sell"])
        entry = st.number_input("Entry")
        exit_price = st.number_input("Exit")
        qty = st.number_input("Qty", value=1)

        liq = st.checkbox("Liquidity
