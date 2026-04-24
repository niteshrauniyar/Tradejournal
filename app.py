import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import random
import base64

# =========================
# ⚙️ CONFIG & PREMIUM UI
# =========================
st.set_page_config(page_title="Trading Journal Pro Max", layout="wide", page_icon="📈")

# Premium Glassmorphism CSS
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .stMetric { background-color: #161b28; padding: 15px; border-radius: 12px; border: 1px solid #2a3143; }
    div[data-testid="stForm"] { background-color: #161b28; border: 1px solid #2a3143; border-radius: 12px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    .stTab { background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "trading_journal.db"

# =========================
# 🧠 DATABASE SETUP
# =========================
def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Expanded Trade Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT, symbol TEXT, direction TEXT,
        entry REAL, exit REAL, stop_loss REAL, qty INTEGER,
        timeframe TEXT, setup TEXT, notes TEXT, screenshot TEXT,
        liq_hunt INTEGER, engulfing INTEGER, killzone INTEGER,
        trend INTEGER, risk_defined INTEGER, no_revenge INTEGER,
        followed_sl INTEGER, followed_plan INTEGER, emotional_entry INTEGER,
        pnl REAL, r_multiple REAL, rule_score REAL, status TEXT
    )""")
    # Original Daily Checks Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS daily_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT, rules_followed INTEGER, revenge INTEGER,
        risk INTEGER, overtrade INTEGER, score REAL
    )""")
    # Original Account Table
    c.execute("CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY, balance REAL)")
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
# 📊 DATA HELPERS
# =========================
def load_trades():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        df['cum_pnl'] = df['pnl'].cumsum()
    return df

def encode_image(upload):
    if upload is not None:
        return base64.b64encode(upload.read()).decode()
    return ""

def quote():
    return random.choice([
        "Discipline is the edge that no one can copy.",
        "Consistency beats intensity.",
        "Protect capital first, profits follow.",
        "Execution is everything."
    ])

# =========================
# 🧭 SIDEBAR NAVIGATION
# =========================
st.sidebar.title("📊 Journal Pro Max")
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Trade", "Trade Vault", "Calendar", "Discipline Check", "Account", "Analytics"]
)
st.sidebar.markdown("---")
st.sidebar.info(f"**Focus:** {quote()}")

# =========================
# 📊 DASHBOARD (Advanced)
# =========================
if menu == "Dashboard":
    st.title("Performance Terminal")
    df = load_trades()
    
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        win_rate = (len(df[df.pnl > 0]) / len(df) * 100)
        
        c1.metric("Total PnL", f"${df['pnl'].sum():,.2f}")
        c2.metric("Win Rate", f"{win_rate:.1f}%")
        c3.metric("Avg R-Multiple", f"{df['r_multiple'].mean():.2f}R")
        c4.metric("Rule Score", f"{df['rule_score'].mean():.1f}%")

        fig = px.area(df, x="trade_date", y="cum_pnl", title="Equity Curve ($)", 
                      line_shape="hv", color_discrete_sequence=['#00e676'])
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trades logged yet.")

# =========================
# ➕ ADD TRADE (With R:R & Image)
# =========================
elif menu == "Add Trade":
    st.title("➕ Log Execution")
    with st.form("trade_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            trade_date = str(date.today())
            symbol = st.text_input("Symbol", "MNQ")
            direction = st.selectbox("Direction", ["Buy", "Sell"])
        with col2:
            entry = st.number_input("Entry Price", format="%.2f")
            stop_loss = st.number_input("Stop Loss", format="%.2f")
            exit_price = st.number_input("Exit Price", format="%.2f")
        with col3:
            qty = st.number_input("Qty", value=1)
            setup = st.selectbox("Setup", ["MSS+FVG", "Silver Bullet", "Liq Sweep", "Other"])
            screenshot = st.file_uploader("Upload Chart", type=['png','jpg','jpeg'])

        st.subheader("📌 ICT & Discipline Rules")
        r1, r2, r3 = st.columns(3)
        with r1:
            liq = st.checkbox("Liquidity Hunt")
            eng = st.checkbox("Engulfing/MSS")
            kill = st.checkbox("Killzone Active")
        with r2:
            trend = st.checkbox("Trend Aligned")
            risk_d = st.checkbox("Risk Defined")
            plan = st.checkbox("Followed Plan")
        with r3:
            sl_f = st.checkbox("Followed SL")
            rev = st.checkbox("No Revenge")
            emot = st.checkbox("Emotional Entry")

        notes = st.text_area("Notes")
        submit = st.form_submit_button("Save Trade")

        if submit:
            pnl = (exit_price - entry) * qty if direction == "Buy" else (entry - exit_price) * qty
            risk_amt = abs(entry - stop_loss)
            r_multiple = pnl / (risk_amt * qty) if risk_amt != 0 else 0
            
            # Rule scoring
            rules = [liq, eng, kill, trend, risk_d, plan, sl_f, rev, (not emot)]
            rule_score = (sum(rules) / len(rules)) * 100
            
            img_str = encode_image(screenshot)
            
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO trades (trade_date, symbol, direction, entry, exit, stop_loss, qty, setup, notes, screenshot, liq_hunt, engulfing, killzone, trend, risk_defined, followed_plan, followed_sl, no_revenge, emotional_entry, pnl, r_multiple, rule_score, status) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (trade_date, symbol, direction, entry, exit_price, stop_loss, qty, setup, notes, img_str, int(liq), int(eng), int(kill), int(trend), int(risk_d), int(plan), int(sl_f), int(rev), int(emot), pnl, r_multiple, rule_score, "PASS" if rule_score >= 80 else "FAIL"))
            conn.commit()
            st.success(f"Trade Saved! Result: ${pnl:.2f} ({r_multiple:.2f}R)")

# =========================
# 📅 TRADE VAULT (Visual History)
# =========================
elif menu == "Trade Vault":
    st.title("📅 Trade Vault")
    df = load_trades()
    if not df.empty:
        for _, row in df.sort_values('trade_date', ascending=False).iterrows():
            with st.expander(f"{row['trade_date'].date()} | {row['symbol']} {row['direction']} | PnL: ${row['pnl']:.2f}"):
                c_left, c_right = st.columns([1, 1])
                with c_left:
                    st.write(f"**Setup:** {row['setup']} | **Score:** {row['rule_score']}%")
                    st.write(f"**Notes:** {row['notes']}")
                with c_right:
                    if row['screenshot']:
                        st.image(base64.b64decode(row['screenshot']))
    else: st.info("Vault is empty.")

# =========================
# 📅 CALENDAR (Original)
# =========================
elif menu == "Calendar":
    st.title("📅 PnL Calendar")
    df = load_trades()
    if not df.empty:
        daily = df.groupby("trade_date").agg({"pnl": "sum", "id": "count"}).reset_index()
        fig = px.bar(daily, x="trade_date", y="pnl", color="pnl", color_continuous_scale="RdYlGn")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(daily)

# =========================
# 🧠 DISCIPLINE (Original)
# =========================
elif menu == "Discipline Check":
    st.title("🧠 Daily Discipline")
    with st.form("daily"):
        day = str(date.today())
        a = st.radio("Followed rules?", ["Yes", "No"])
        b = st.radio("Revenge trades?", ["No", "Yes"])
        c = st.radio("Risk respected?", ["Yes", "No"])
        d = st.radio("Overtraded?", ["No", "Yes"])
        if st.form_submit_button("Save"):
            score = 100
            if a == "No": score -= 30
            if b == "Yes": score -= 30
            if c == "No": score -= 20
            if d == "Yes": score -= 20
            conn = get_conn(); c = conn.cursor()
            c.execute("INSERT INTO daily_checks (day, rules_followed, revenge, risk, overtrade, score) VALUES (?,?,?,?,?,?)", (day, a=="Yes", b=="Yes", c=="Yes", d=="Yes", score))
            conn.commit(); st.success(f"Score: {score}")

# =========================
# 💰 ACCOUNT (Original)
# =========================
elif menu == "Account":
    st.title("💰 Account")
    bal = get_balance()
    st.metric("Current Balance", f"${bal:,.2f}")
    add = st.number_input("Deposit / Withdrawal")
    if st.button("Update"):
        set_balance(bal + add)
        st.rerun()

# =========================
# 📊 ANALYTICS (Advanced)
# =========================
elif menu == "Analytics":
    st.title("📊 Advanced Analytics")
    df = load_trades()
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(px.histogram(df, x="pnl", title="PnL Distribution"), use_container_width=True)
        with col_b:
            st.plotly_chart(px.box(df, x="setup", y="pnl", title="PnL by Setup Type"), use_container_width=True)
        
        st.subheader("Strategy Efficiency")
        efficiency = df.groupby('setup').agg({'pnl': 'sum', 'id': 'count', 'r_multiple': 'mean'})
        st.table(efficiency)
    
