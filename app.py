import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Employee Time Tracker", layout="wide")

# ===================== DATABASE =====================
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

def add_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'employee')", 
                  (username, password))
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

def update_password(username, new_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_all_employees():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT username FROM users WHERE role = 'employee' ORDER BY username", conn)
    conn.close()
    return df

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
    query = "SELECT id, date, employee, start_time, end_time, task, customer, hours FROM entries"
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
    query += " ORDER BY date DESC, start_time DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def delete_entry(entry_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# ===================== SESSION STATE =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🕒 Employee Working Hours Tracker")

# ===================== LOGIN & REGISTER =====================
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register Employee"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            role = check_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Register New Employee")
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        if st.button("Create Employee Account"):
            if add_user(new_user, new_pass):
                st.success("✅ Employee account created successfully! You can now login.")
            else:
                st.error("Username already exists")

else:
    # ===================== LOGGED IN =====================
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    
    with st.sidebar.expander("🔑 Change Password"):
        new_pass = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if new_pass == confirm and new_pass:
                if update_password(st.session_state.username, new_pass):
                    st.success("Password updated successfully!")
                else:
                    st.error("Failed to update password")
            else:
                st.error("Passwords do not match")

    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    current_month = date.today().strftime("%Y-%m")

    if st.session_state.role == "employee":
        st.subheader("📝 Add Today's Work")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time", datetime.strptime("09:00", "%H:%M").time())
        with col2:
            end_time = st.time_input("End Time", datetime.strptime("17:00", "%H:%M").time())
        
        task = st.text_input("Task Description")
        customer = st.text_input("Customer / Project")
        
        if st.button("Submit Entry", type="primary"):
            if task and customer:
                add_entry(st.session_state.username, start_time.strftime("%H:%M"), 
                         end_time.strftime("%H:%M"), task, customer)
                st.success("✅ Entry added!")
                st.rerun()
            else:
                st.warning("Task and Customer are required")

        st.subheader("My Entries This Month")
        df = get_entries(st.session_state.username, current_month)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.success(f"**Total Hours: {df['hours'].sum():.2f}**")
        else:
            st.info("No entries yet this month.")

    else:  # Employer
        st.subheader("👥 Employer Dashboard")
        
        tab1, tab2 = st.tabs(["All Registered Employees", "Time Entries"])

        with tab1:
            st.subheader("All Employees")
            emp_df = get_all_employees()
            if not emp_df.empty:
                st.dataframe(emp_df, use_container_width=True, hide_index=True)
                st.success(f"**Total Registered Employees: {len(emp_df)}**")
            else:
                st.info("No employees registered yet.")

        with tab2:
            st.subheader("Time Entries")
            month = st.text_input("Month (YYYY-MM)", value=current_month)
            df = get_entries(month=month)
            
            if not df.empty:
                summary = df.groupby('employee')['hours'].sum().reset_index()
                summary = summary.rename(columns={'hours': 'Total Hours'}).sort_values('Total Hours', ascending=False)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.dataframe(summary, use_container_width=True)
                    st.success(f"**Grand Total: {df['hours'].sum():.2f} hours**")
                
                with col2:
                    df_display = df.copy()
                    df_display['Delete'] = False
                    edited = st.data_editor(df_display, use_container_width=True, hide_index=True)
                    
                    if st.button("🗑️ Delete Selected Entries"):
                        to_delete = df_display[edited['Delete'] == True]['id'].tolist()
                        for eid in to_delete:
                            delete_entry(eid)
                        st.success("Selected entries deleted")
                        st.rerun()
            else:
                st.info("No entries found for this month.")

    # Sidebar total
    total = pd.read_sql_query("SELECT SUM(hours) as t FROM entries", sqlite3.connect(DB_FILE)).iloc[0]['t'] or 0
    st.sidebar.metric("Total Hours (All Time)", f"{total:.1f}")
