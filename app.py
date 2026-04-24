import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import base64

# =========================
# ⚙️ CONFIG & PREMIUM STYLING
# =========================
st.set_page_config(page_title="Trading Journal Pro Max", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Premium Dark Mode & Glassmorphism */
    .stApp { background-color: #0b0f19; color: #ffffff; }
    div[data-testid="stMetricValue"] { color: #00e676; }
    .css-1r6slb0 { background-color: #151a28; border-radius: 12px; border: 1px solid #2a3143; padding: 20px; }
    div[data-testid="stForm"] { background-color: #151a28; border: 1px solid #2a3143; border-radius: 12px; }
    hr { border-color: #2a3143; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
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
    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT, symbol TEXT, direction TEXT,
        entry REAL, exit REAL, stop_loss REAL, qty INTEGER,
        timeframe TEXT, setup TEXT, notes TEXT, screenshot TEXT,
        liq_hunt INTEGER, killzone INTEGER, followed_sl INTEGER, 
        followed_plan INTEGER, emotional_entry INTEGER, no_revenge INTEGER,
        pnl REAL, r_multiple REAL, rule_score REAL
    )""")
    conn.commit()
    conn.close()

init_db()

# =========================
# 📊 DATA HELPERS & CALCULATIONS
# =========================
def load_trades():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        # Advanced Metrics Math
        df['cum_pnl'] = df['pnl'].cumsum()
        df['peak'] = df['cum_pnl'].cummax()
        df['drawdown'] = df['cum_pnl'] - df['peak']
    return df

def encode_image(upload):
    if upload is not None:
        return base64.b64encode(upload.read()).decode()
    return ""

# =========================
# 🧭 SIDEBAR NAVIGATION
# =========================
with st.sidebar:
    st.title("⚡ Pro Terminal")
    menu = st.radio("Navigation", ["📊 Dashboard", "➕ Log Trade", "📅 Trade Vault", "⚙️ System"])
    st.markdown("---")
    st.markdown("### 💡 Daily Edge")
    st.info("Amateurs focus on how much they can make. Professionals focus on how much they can lose.")

# =========================
# 📊 DASHBOARD (POWER UI)
# =========================
if menu == "📊 Dashboard":
    st.title("Terminal Dashboard")
    df = load_trades()
    
    if not df.empty:
        # --- GLOBAL FILTERS ---
        st.markdown("### 🔍 Filters")
        c1, c2, c3 = st.columns(3)
        with c1:
            date_range = st.date_input("Date Range", [df['trade_date'].min().date(), date.today()])
        with c2:
            setup_filter = st.multiselect("Setup Filter", df['setup'].unique(), default=df['setup'].unique())
        with c3:
            symbol_filter = st.multiselect("Symbol Filter", df['symbol'].unique(), default=df['symbol'].unique())
            
        # Apply Filters
        if len(date_range) == 2:
            mask = (df['trade_date'].dt.date >= date_range[0]) & (df['trade_date'].dt.date <= date_range[1]) & \
                   (df['setup'].isin(setup_filter)) & (df['symbol'].isin(symbol_filter))
            filtered_df = df.loc[mask]
        else:
            filtered_df = df

        if not filtered_df.empty:
            # --- ADVANCED METRICS ---
            st.markdown("---")
            m1, m2, m3, m4, m5 = st.columns(5)
            
            total_pnl = filtered_df['pnl'].sum()
            win_rate = (len(filtered_df[filtered_df['pnl'] > 0]) / len(filtered_df)) * 100
            
            gross_profit = filtered_df[filtered_df['pnl'] > 0]['pnl'].sum()
            gross_loss = abs(filtered_df[filtered_df['pnl'] < 0]['pnl'].sum())
            profit_factor = (gross_profit / gross_loss) if gross_loss != 0 else float('inf')
            
            max_dd = filtered_df['drawdown'].min()
            
            m1.metric("Net PnL", f"${total_pnl:,.2f}")
            m2.metric("Win Rate", f"{win_rate:.1f}%")
            m3.metric("Profit Factor", f"{profit_factor:.2f}")
            m4.metric("Max Drawdown", f"${max_dd:,.2f}")
            m5.metric("Avg Score", f"{filtered_df['rule_score'].mean():.0f}%")

            # --- CHARTS ---
            st.markdown("---")
            tab1, tab2, tab3 = st.tabs(["📈 Equity & Drawdown", "🎯 Setup Edge", "📅 Daily Heat"])
            
            with tab1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=filtered_df['trade_date'], y=filtered_df['cum_pnl'], 
                                         mode='lines', name='Equity', line=dict(color='#00e676', width=3), shape='hv'))
                fig.add_trace(go.Scatter(x=filtered_df['trade_date'], y=filtered_df['drawdown'], 
                                         mode='lines', fill='tozeroy', name='Drawdown', line=dict(color='#ff1744', width=1), shape='hv'))
                fig.update_layout(title="Equity Curve vs Drawdown", template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                setup_stats = filtered_df.groupby('setup').agg(
                    Trades=('id', 'count'), PnL=('pnl', 'sum'), Win_Rate=('pnl', lambda x: (x>0).mean()*100)
                ).reset_index()
                
                c_a, c_b = st.columns(2)
                with c_a:
                    fig_bar = px.bar(setup_stats, x='setup', y='PnL', color='PnL', title="Net PnL by Setup", color_continuous_scale="RdYlGn")
                    st.plotly_chart(fig_bar, use_container_width=True)
                with c_b:
                    fig_pie = px.pie(setup_stats, names='setup', values='Trades', hole=0.4, title="Trade Distribution")
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
            with tab3:
                filtered_df['Day'] = filtered_df['trade_date'].dt.day_name()
                day_stats = filtered_df.groupby('Day')['pnl'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).reset_index()
                fig_day = px.bar(day_stats, x='Day', y='pnl', title="PnL by Day of Week", color='pnl', color_continuous_scale="RdYlGn")
                st.plotly_chart(fig_day, use_container_width=True)

        else:
            st.warning("No trades match your filters.")
    else:
        st.info("Your dashboard is empty. Go log your first trade!")

# =========================
# ➕ LOG TRADE (WITH IMAGES)
# =========================
elif menu == "➕ Log Trade":
    st.title("Log Execution")
    
    with st.form("trade_entry", clear_on_submit=True):
        st.subheader("Trade Details")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            t_date = st.date_input("Date", date.today())
            symbol = st.text_input("Ticker", "NQ")
        with c2:
            direction = st.selectbox("Type", ["Buy", "Sell"])
            qty = st.number_input("Size", value=1.0, step=0.1)
        with c3:
            entry = st.number_input("Entry", format="%.4f")
            exit_p = st.number_input("Exit", format="%.4f")
        with c4:
            stop_loss = st.number_input("Stop Loss", format="%.4f")
            setup = st.selectbox("Setup", ["MSS + FVG", "Silver Bullet", "Liquidity Sweep", "Trend Continuation", "Other"])

        st.markdown("---")
        st.subheader("Execution Quality & Proof")
        col_img, col_rules = st.columns([1, 2])
        
        with col_img:
            screenshot = st.file_uploader("Upload Chart Screenshot", type=["png", "jpg", "jpeg"])
            
        with col_rules:
            r1, r2 = st.columns(2)
            with r1:
                liq = st.checkbox("✅ Liquidity Hunted?")
                kill = st.checkbox("✅ Within Killzone?")
                plan = st.checkbox("✅ Followed Plan?")
            with r2:
                sl_rule = st.checkbox("✅ Respected Stop Loss?")
                emotional = st.checkbox("❌ Emotional Entry?")
                revenge = st.checkbox("❌ Revenge Trade?")

        notes = st.text_area("Trade Review / Narrative", placeholder="Why did you take this trade? What did you feel?")
        
        submit = st.form_submit_button("💾 Save Trade to Vault", use_container_width=True)

        if submit:
            img_b64 = encode_image(screenshot)
            
            pnl = (exit_p - entry) * qty if direction == "Buy" else (entry - exit_p) * qty
            risk_per_unit = abs(entry - stop_loss)
            r_multiple = pnl / (risk_per_unit * qty) if risk_per_unit != 0 else 0
            
            pos_rules = [liq, kill, plan, sl_rule]
            neg_rules = [emotional, revenge]
            score = (sum(pos_rules) + (2 - sum(neg_rules))) / 6 * 100

            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO trades 
                         (trade_date, symbol, direction, entry, exit, stop_loss, qty, timeframe, setup, notes, screenshot, 
                         liq_hunt, killzone, followed_sl, followed_plan, emotional_entry, no_revenge, pnl, r_multiple, rule_score) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                      (str(t_date), symbol, direction, entry, exit_p, stop_loss, qty, "N/A", setup, notes, img_b64, 
                       int(liq), int(kill), int(sl_rule), int(plan), int(emotional), int(not revenge), pnl, r_multiple, score))
            conn.commit()
            st.success(f"Trade Logged Successfully! Recorded PnL: ${pnl:.2f} | Edge Score: {score:.0f}%")

# =========================
# 📅 TRADE VAULT (HISTORY & IMAGES)
# =========================
elif menu == "📅 Trade Vault":
    st.title("Trade Vault")
    df = load_trades()
    
    if not df.empty:
        
    
