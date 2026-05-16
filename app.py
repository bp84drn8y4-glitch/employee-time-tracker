import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Employee Time + Material Tracker", layout="wide")

DB_FILE = "time_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, username TEXT UNIQUE, 
                    password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY, date TEXT, employee TEXT,
                    start_time TEXT, end_time TEXT, task TEXT, 
                    customer TEXT, hours REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS supplies (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    employee TEXT,
                    business TEXT,
                    category TEXT,
                    item TEXT,
                    specification TEXT,
                    issued INTEGER DEFAULT 0,
                    returned INTEGER DEFAULT 0,
                    remark TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Material Lists (same as before)
MATERIAL_LISTS = { ... }   # Keep the same material lists from previous code

# ===================== HELPER FUNCTIONS =====================
def get_time_entries(month=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM entries ORDER BY date DESC"
    if month:
        query = "SELECT * FROM entries WHERE date LIKE ? ORDER BY date DESC"
        df = pd.read_sql_query(query, conn, params=[f"{month}%"])
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_supplies():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM supplies ORDER BY date DESC", conn)
    conn.close()
    return df

# ===================== MAIN APP =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🧹 Employee Time + Material Tracker")

if not st.session_state.logged_in:
    # Login + Register (same as last working version)
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register Employee"])
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
            result = c.fetchone()
            conn.close()
            if result:
                st.session_state.logged_in = True
                st.session_state.role = result[0]
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    # Register tab (same)
else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    tabs = st.tabs(["⏱️ Time Tracking", "🧴 Material Tracking", "📊 Dashboard"])

    with tabs[0]:
        st.subheader("Time Tracking")
        st.info("Add your time tracking code here if needed")

    with tabs[1]:
        # Material Tracking (same as before)
        st.subheader("🧴 Material Issuance & Return")
        business = st.selectbox("Business", list(MATERIAL_LISTS.keys()))
        action = st.radio("Aktion", ["Ausgabe (Issue)", "Rücknahme (Return)"], horizontal=True)
        # ... rest of material code (same as previous message)
        st.info("Material form here...")

    with tabs[2]:   # ← Improved Dashboard
        st.subheader("📊 Full Dashboard")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Time Entries")
            month = st.text_input("Month (YYYY-MM)", value=date.today().strftime("%Y-%m"))
            time_df = get_time_entries(month)
            if not time_df.empty:
                st.dataframe(time_df, use_container_width=True)
                st.success(f"Total Hours: {time_df['hours'].sum():.2f}")
            else:
                st.info("No time entries found")

        with col2:
            st.subheader("Material Transactions")
            supplies_df = get_supplies()
            if not supplies_df.empty:
                st.dataframe(supplies_df, use_container_width=True)
            else:
                st.info("No material transactions yet")

        # Summary
        st.subheader("Summary")
        total_employees = len(pd.read_sql_query("SELECT username FROM users WHERE role='employee'", sqlite3.connect(DB_FILE)))
        st.write(f"**Registered Employees:** {total_employees}")
