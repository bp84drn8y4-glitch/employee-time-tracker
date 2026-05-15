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
                    id INTEGER PRIMARY KEY, date TEXT, employee TEXT,
                    start_time TEXT, end_time TEXT, task TEXT, 
                    customer TEXT, hours REAL)''')
    conn.commit()
    conn.close()

init_db()

# ... [Keep all your existing functions: calculate_hours, add_user, check_login, update_password, add_entry, delete_entry] ...

def get_all_employees():
    """Get list of all registered employees"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT username FROM users WHERE role = 'employee' ORDER BY username", conn)
    conn.close()
    return df

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

# ===================== MAIN APP =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🕒 Employee Working Hours Tracker")

# Login & Register (same as before - only employee registration)
if not st.session_state.logged_in:
    # ... keep your existing login and register code ...
    pass  # I'll keep it short here, use your previous version

else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    current_month = date.today().strftime("%Y-%m")

    if st.session_state.role == "employee":
        # Employee interface (same)
        st.subheader("📝 Add New Entry")
        # ... your employee code ...
        pass

    else:  # ==================== EMPLOYER VIEW ====================
        st.subheader("👥 Employer Dashboard")

        tab1, tab2 = st.tabs(["📊 All Employees", "📋 Time Entries"])

        with tab1:
            st.subheader("All Registered Employees")
            employees_df = get_all_employees()
            
            if not employees_df.empty:
                st.dataframe(employees_df, use_container_width=True, hide_index=True)
                st.success(f"**Total Employees: {len(employees_df)}**")
            else:
                st.info("No employees registered yet.")

        with tab2:
            st.subheader("Time Entries")
            month = st.text_input("Filter by Month (YYYY-MM)", value=current_month)
            df = get_entries(month=month)
            
            if not df.empty:
                summary = df.groupby('employee')['hours'].sum().reset_index()
                summary = summary.rename(columns={'hours': 'Total Hours'}).sort_values('Total Hours', ascending=False)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.subheader("Summary")
                    st.dataframe(summary, use_container_width=True)
                    st.success(f"**Grand Total: {df['hours'].sum():.2f} hours**")
                
                with col2:
                    st.subheader("All Entries")
                    df_display = df.copy()
                    df_display['Delete'] = False
                    edited = st.data_editor(df_display, use_container_width=True, hide_index=True)
                    
                    if st.button("🗑️ Delete Selected Entries"):
                        to_delete = df_display[edited['Delete'] == True]['id'].tolist()
                        for eid in to_delete:
                            delete_entry(eid)
                        st.success("Entries deleted")
                        st.rerun()
            else:
                st.info("No time entries found for this month.")

    # Sidebar Stats
    total = pd.read_sql_query("SELECT SUM(hours) as t FROM entries", sqlite3.connect(DB_FILE)).iloc[0]['t'] or 0
    st.sidebar.metric("Total Hours Recorded", f"{total:.1f}")
