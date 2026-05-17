import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Employee Time Tracker", layout="wide")

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
                    id INTEGER PRIMARY KEY, date TEXT, employee TEXT, business TEXT,
                    item TEXT, issued INTEGER DEFAULT 0, returned INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# Auto create admin account
def create_admin():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ("admin", "Sam18@admin", "employer"))
        conn.commit()
        st.success("Admin account created/verified")
    except:
        pass  # already exists
    conn.close()

create_admin()

# ===================== MAIN APP =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🧹 Employee Time Tracker")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register Employee"])

    with tab1:
        st.subheader("Login")
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
                st.error("Invalid credentials - Try admin / Sam18@admin")

    with tab2:
        st.subheader("Register New Employee")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Create Employee Account"):
            if new_user and new_pass:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'employee')", 
                              (new_user, new_pass))
                    conn.commit()
                    st.success("✅ Employee account created!")
                except:
                    st.error("Username already exists")
                conn.close()

else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.success("✅ You are logged in!")

    # Rest of your app (Time Tracking, etc.)
    st.info("Time Tracking and Material sections will be here...")
