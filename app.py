import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3

# Database Setup
DB_FILE = "time_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    employee TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    task TEXT,
                    customer TEXT,
                    hours REAL)''')
    conn.commit()
    conn.close()

init_db()

def calculate_hours(start, end):
    fmt = "%H:%M"
    t1 = datetime.strptime(start, fmt)
    t2 = datetime.strptime(end, fmt)
    return round((t2 - t1).seconds / 3600, 2)

def add_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (username, password, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def add_entry(employee, start, end, task, customer):
    hours = calculate_hours(start, end)
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO entries 
                 (date, employee, start_time, end_time, task, customer, hours)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""", 
              (today, employee, start, end, task, customer, hours))
    conn.commit()
    conn.close()

def get_entries(employee=None, month=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM entries"
    params = []
    if employee or month:
        conditions = []
        if employee:
            conditions.append("employee = ?")
            params.append(employee)
        if month:
            conditions.append("date LIKE ?")
            params.append(f"{month}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ===================== MAIN APP =====================
st.set_page_config(page_title="Employee Time Tracker", layout="wide")
st.title("🕒 Employee Working Hours Tracker")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = check_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.success(f"Logged in as {role}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Register New User")
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        role_choice = st.selectbox("Role", ["employee", "employer"])
        if st.button("Create Account"):
            if add_user(new_user, new_pass, role_choice):
                st.success("Account created! Now go to Login tab.")
            else:
                st.error("Username already taken")
else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if st.session_state.role == "employee":
        st.subheader("Add Work Entry")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time", datetime.strptime("09:00", "%H:%M").time())
        with col2:
            end_time = st.time_input("End Time", datetime.strptime("17:00", "%H:%M").time())
        
        task = st.text_input("Task Description")
        customer = st.text_input("Customer / Project")
        
        if st.button("Submit Entry"):
            if task and customer:
                add_entry(st.session_state.username, start_time.strftime("%H:%M"), 
                         end_time.strftime("%H:%M"), task, customer)
                st.success("✅ Entry saved!")
            else:
                st.warning("Please fill Task and Customer")
        
        st.subheader("My This Month's Entries")
        df = get_entries(st.session_state.username, date.today().strftime("%Y-%m"))
        if not df.empty:
            st.dataframe(df)
            st.success(f"**Total Hours: {df['hours'].sum():.2f}**")
        else:
            st.info("No entries yet.")

    else:  # Employer
        st.subheader("All Records")
        month = st.text_input("Month (YYYY-MM)", date.today().strftime("%Y-%m"))
        df = get_entries(month=month)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.success(f"**Total Hours: {df['hours'].sum():.2f}**")
        else:
            st.info("No data found.")