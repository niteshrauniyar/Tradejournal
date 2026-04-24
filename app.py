# =========================
# 📦 IMPORTS
# =========================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import random
import os

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(page_title="Trading Journal Pro", layout="wide")

DB_NAME = "trading_journal.db"

# =========================
# 🧠 DATABASE SETUP
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
        symbol TEXT,
        direction TEXT,
        entry REAL,
        exit REAL,
        qty INTEGER,
        timeframe TEXT,
        setup TEXT,
        notes TEXT,
        screenshot TEXT,

        liq_hunt INTEGER,
        engulfing INTEGER,
        killzone INTEGER,
        trend INTEGER,
        risk_defined INTEGER,

        no_revenge INTEGER,
        followed_sl INTEGER,
        followed_plan INTEGER,
        emotional_entry INTEGER,

        pnl REAL,
        rule_score REAL,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS daily_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        rules_followed INTEGER,
        revenge INTEGER,
        risk INTEGER,
        overtrade INTEGER,
        score REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS account (
        id INTEGER PRIMARY KEY,
        balance REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# 💰 ACCOUNT FUNCTIONS
# =========================
def get_balance():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT balance FROM account WHERE id=1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def set_balance(val):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO account (id, balance) VALUES (1, ?)", (val,))
    conn.commit()
    conn.close()

# =========================
# 📊 DATA FUNCTIONS
# =========================
def add_trade(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO trades (
        trade_date, symbol, direction, entry, exit, qty, timeframe,
        setup, notes, screenshot,
        liq_hunt, engulfing, killzone, trend, risk_defined,
        no_revenge, followed_sl, followed_plan, emotional_entry,
        pnl, rule_score, status
    )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()

def load_trades():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()
    return df

def load_checks():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM daily_checks", conn)
    conn.close()
    return df

# =========================
# 🧮 CALCULATIONS
# =========================
def calc_pnl(entry, exit_price, qty, direction):
    if direction == "Buy":
        return (exit_price - entry) * qty
    else:
        return (entry - exit_price) * qty

def calc_rule_score(row):
    rules = [
        row["liq_hunt"], row["engulfing"], row["killzone"],
        row["trend"], row["risk_defined"],
        row["no_revenge"], row["followed_sl"],
        row["followed_plan"], (1 - row["emotional_entry"])
    ]
    return (sum(rules) / len(rules)) * 100

# =========================
# 🎨 UI HELPERS
# =========================
def quote():
    quotes = [
        "Discipline is the edge that no one can copy.",
        "Consistency beats intensity.",
        "Protect capital first, profits follow.",
        "You don’t trade the market — you trade your system.",
        "Execution is everything."
    ]
    return random.choice(quotes)

# =========================
# 🧭 SIDEBAR NAVIGATION
# =========================
st.sidebar.title("📊 Trading Journal Pro")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Trade", "Calendar", "Discipline Check", "Account", "Analytics"]
)

st.sidebar.markdown("### 🔥 Motivation")
st.sidebar.info(quote())

# =========================
# 📊 DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Performance Dashboard")

    df = load_trades()

    col1, col2, col3, col4 = st.columns(4)

    if len(df) > 0:
        col1.metric("Total Trades", len(df))
        col2.metric("Net PnL", round(df["pnl"].sum(), 2))
        col3.metric("Win Rate", f"{(len(df[df.pnl > 0]) / len(df) * 100):.2f}%")
        col4.metric("Avg Rule Score", f"{df['rule_score'].mean():.2f}%")

        fig = px.line(df, x="trade_date", y="pnl", title="Equity Curve")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trades yet.")

# =========================
# ➕ ADD TRADE
# =========================
elif menu == "Add Trade":
    st.title("➕ Add Trade")

    with st.form("trade_form"):
        trade_date = str(date.today())
        symbol = "MNQ"
        direction = st.selectbox("Direction", ["Buy", "Sell"])
        entry = st.number_input("Entry Price")
        exit_price = st.number_input("Exit Price")
        qty = st.number_input("Qty", value=1)
        timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m"])
        setup = st.text_input("Setup Type")
        notes = st.text_area("Notes")

        st.subheader("📌 ICT RULES")
        liq = st.checkbox("15m Liquidity Hunt")
        eng = st.checkbox("1m Engulfing")
        kill = st.checkbox("Killzone respected")
        trend = st.checkbox("Trend aligned")
        risk = st.checkbox("Risk defined")

        st.subheader("⚙️ DISCIPLINE RULES")
        revenge = st.checkbox("No revenge trade")
        sl = st.checkbox("Followed SL")
        plan = st.checkbox("Followed plan")
        emotional = st.checkbox("No emotional entry")

        submit = st.form_submit_button("Save Trade")

        if submit:
            pnl = calc_pnl(entry, exit_price, qty, direction)

            row = {
                "liq_hunt": int(liq),
                "engulfing": int(eng),
                "killzone": int(kill),
                "trend": int(trend),
                "risk_defined": int(risk),
                "no_revenge": int(revenge),
                "followed_sl": int(sl),
                "followed_plan": int(plan),
                "emotional_entry": int(emotional),
            }

            rule_score = calc_rule_score(row)
            status = "PASS" if rule_score >= 80 else "FAIL"

            data = (
                trade_date, symbol, direction, entry, exit_price, qty, timeframe,
                setup, notes, "",
                liq, eng, kill, trend, risk,
                revenge, sl, plan, emotional,
                pnl, rule_score, status
            )

            add_trade(data)
            st.success(f"Trade saved! PnL: {pnl:.2f} | Score: {rule_score:.1f}%")

# =========================
# 📅 CALENDAR
# =========================
elif menu == "Calendar":
    st.title("📅 PnL Calendar View")

    df = load_trades()

    if len(df) > 0:
        daily = df.groupby("trade_date").agg({
            "pnl": "sum",
            "rule_score": "mean",
            "id": "count"
        }).reset_index()

        fig = px.bar(
            daily,
            x="trade_date",
            y="pnl",
            color="pnl",
            title="Daily PnL Heat"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(daily)
    else:
        st.info("No data yet.")

# =========================
# 🧠 DISCIPLINE CHECK
# =========================
elif menu == "Discipline Check":
    st.title("🧠 Daily Discipline Check")

    with st.form("daily"):
        day = str(date.today())

        a = st.radio("Followed rules?", ["Yes", "No"])
        b = st.radio("Revenge trades?", ["No", "Yes"])
        c = st.radio("Risk respected?", ["Yes", "No"])
        d = st.radio("Overtraded?", ["No", "Yes"])

        submit = st.form_submit_button("Save")

        if submit:
            score = 100
            if a == "No": score -= 30
            if b == "Yes": score -= 30
            if c == "No": score -= 20
            if d == "Yes": score -= 20

            conn = get_conn()
            c = conn.cursor()
            c.execute("""
            INSERT INTO daily_checks (day, rules_followed, revenge, risk, overtrade, score)
            VALUES (?,?,?,?,?,?)
            """, (day, a=="Yes", b=="Yes", c=="Yes", d=="Yes", score))
            conn.commit()
            conn.close()

            st.success(f"Daily Score: {score}")

# =========================
# 💰 ACCOUNT
# =========================
elif menu == "Account":
    st.title("💰 Account Management")

    bal = get_balance()
    st.metric("Current Balance", bal)

    add = st.number_input("Deposit / Withdrawal")
    if st.button("Update Balance"):
        set_balance(bal + add)
        st.success("Updated")

# =========================
# 📊 ANALYTICS
# =========================
elif menu == "Analytics":
    st.title("📊 Advanced Analytics")

    df = load_trades()

    if len(df) > 0:
        st.subheader("Performance Overview")

        st.write("Total Trades:", len(df))
        st.write("Net PnL:", df["pnl"].sum())
        st.write("Rule Compliance:", df["rule_score"].mean())

        fig1 = px.histogram(df, x="pnl", title="PnL Distribution")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(df, x="trade_date", y="rule_score", title="Rule Compliance Trend")
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No data available.")
