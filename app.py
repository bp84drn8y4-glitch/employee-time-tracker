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
                    id INTEGER PRIMARY KEY,
                    date TEXT, employee TEXT, business TEXT,
                    category TEXT, item TEXT, specification TEXT,
                    issued INTEGER DEFAULT 0, returned INTEGER DEFAULT 0,
                    remark TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ===================== MATERIAL LISTS =====================
MATERIAL_LISTS = {
    "Fürst Hauser Gebäudereinigung": [
        ("Müllbeutel", "Müllbeutel Groß (Large trash bags)", "120 L"),
        ("Müllbeutel", "Müllbeutel Medium (Medium trash bags)", "60 L"),
        ("Müllbeutel", "Müllbeutel Klein (Small trash bags)", "28 L"),
        ("Wischmopp", "Wischmopp Mikrofaser (Microfiber mop)", "50 cm"),
        ("Wischmopp", "Wischmopp Baumwolle (Cotton mop)", "50 cm"),
        ("Lappen", "Mikrofaser Lappen rot (Red microfiber cloth)", "40 × 40 cm"),
        ("Lappen", "Mikrofaser Lappen blau (Blue microfiber cloth)", "40 × 40 cm"),
        ("Lappen", "Mikrofaser Lappen grün (Green microfiber cloth)", "40 × 40 cm"),
        ("Lappen", "Mikrofaser Lappen gelb (Yellow microfiber cloth)", "40 × 40 cm"),
        ("Geschirrtücher", "Geschirrtücher (Kitchen / Dish towels)", "70 × 50 cm"),
        ("Sanitäreiniger", "Sanitäreiniger Milizid (Bathroom cleaner)", "Sprühflasche"),
        ("Bodenreiniger", "Bodenreiniger Torrun (Floor cleaner)", "Konzentrat"),
        ("Oberflächenreiniger", "Oberflächenreiniger (Surface cleaner)", "-"),
        ("Verbrauchsmaterial", "Toilettenpapier (Toilet paper)", "-"),
        ("Verbrauchsmaterial", "Falthandtücher (Folded hand towels)", "-"),
        ("Verbrauchsmaterial", "Handseife (Hand soap)", "10 Liter"),
        ("Sonstiges", "Sonstiges (Miscellaneous)", "-"),
    ],
    "Bullauge Waschsalon": [
        ("Verbrauchsmaterial", "Hände folien (Plastic gloves)", "-"),
        ("Verbrauchsmaterial", "Bügelstärke (Ironing starch)", "-"),
        ("Verbrauchsmaterial", "Chlor (Chlorine / Bleach)", "-"),
        ("Waschmittel", "Waschpulver (Washing powder)", "20 kg"),
        ("Waschmittel", "Weichspüler (Fabric softener)", "20 Liter"),
        ("Sonstiges", "Sonstiges (Miscellaneous)", "-"),
    ]
}

def calculate_hours(start, end):
    fmt = "%H:%M"
    t1 = datetime.strptime(start, fmt)
    t2 = datetime.strptime(end, fmt)
    return round((t2 - t1).seconds / 3600, 2)

def add_entry(employee, start, end, task, customer):
    hours = calculate_hours(start, end)
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO entries (date, employee, start_time, end_time, task, customer, hours)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""", 
              (today, employee, start, end, task, customer, hours))
    conn.commit()
    conn.close()

def get_entries(month=None):
    conn = sqlite3.connect(DB_FILE)
    if month:
        df = pd.read_sql_query("SELECT * FROM entries WHERE date LIKE ? ORDER BY date DESC", conn, params=[f"{month}%"])
    else:
        df = pd.read_sql_query("SELECT * FROM entries ORDER BY date DESC", conn)
    conn.close()
    return df

def add_supply(employee, business, category, item, spec, issued=0, returned=0, remark=""):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO supplies 
                 (date, employee, business, category, item, specification, issued, returned, remark)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
              (today, employee, business, category, item, spec, issued, returned, remark))
    conn.commit()
    conn.close()

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
                st.error("Invalid username or password")

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
                    st.success("✅ Employee account created! Please login.")
                except:
                    st.error("Username already exists")
                conn.close()

else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    tabs = st.tabs(["⏱️ Time Tracking", "🧴 Material Tracking", "📊 Dashboard"])

    # ==================== TIME TRACKING ====================
    with tabs[0]:
        st.subheader("📝 Add Work Entry")
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
                st.success("✅ Entry added successfully!")
                st.rerun()
            else:
                st.warning("Task and Customer are required")

        st.subheader("My Entries This Month")
        current_month = date.today().strftime("%Y-%m")
        df = get_entries(current_month)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.success(f"**Total Hours this month: {df['hours'].sum():.2f}**")
        else:
            st.info("No entries yet this month.")

    # ==================== MATERIAL TRACKING ====================
    with tabs[1]:
        st.subheader("🧴 Material Issuance & Return")
        business = st.selectbox("Business", list(MATERIAL_LISTS.keys()))
        action = st.radio("Aktion", ["Ausgabe (Issue)", "Rücknahme (Return)"], horizontal=True)
        
        items = MATERIAL_LISTS[business]
        selected = st.selectbox("Material", [f"{i[1]} — {i[2]}" for i in items])
        
        idx = [f"{i[1]} — {i[2]}" for i in items].index(selected)
        category, item_name, spec = items[idx]
        
        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("Menge / Quantity", min_value=1, value=1)
        with col2:
            remark = st.text_input("Bemerkung / Remark")
        
        if st.button("💾 Speichern", type="primary"):
            if action == "Ausgabe (Issue)":
                add_supply(st.session_state.username, business, category, item_name, spec, issued=qty, returned=0, remark=remark)
            else:
                add_supply(st.session_state.username, business, category, item_name, spec, issued=0, returned=qty, remark=remark)
            st.success("✅ Saved successfully!")

    # ==================== DASHBOARD ====================
    with tabs[2]:
        st.subheader("📊 Dashboard")
        st.write("### Time Entries")
        month = st.text_input("Month (YYYY-MM)", value=date.today().strftime("%Y-%m"))
        time_df = get_entries(month)
        if not time_df.empty:
            st.dataframe(time_df, use_container_width=True)
            st.success(f"Total Hours: {time_df['hours'].sum():.2f}")
        else:
            st.info("No time entries for this month.")

        st.write("### Material History")
        supplies_df = get_supplies()
        if not supplies_df.empty:
            st.dataframe(supplies_df, use_container_width=True)
        else:
            st.info("No material records yet.")
