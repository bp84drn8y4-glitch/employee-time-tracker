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

# Material Lists
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

# ===================== MAIN APP =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🧹 Employee Time + Material Tracker")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register Employee"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", 
                      (username, password))
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
        new_user = st.text_input("Choose Username", key="register_username")
        new_pass = st.text_input("Choose Password", type="password", key="register_password")
        
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
                st.warning("Please fill username and password")

else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    tabs = st.tabs(["⏱️ Time Tracking", "🧴 Material Tracking", "📊 Dashboard"])

    with tabs[0]:
        st.subheader("Time Tracking (Coming soon)")

    with tabs[1]:
        st.subheader("🧴 Material Issuance & Return")
        
        business = st.selectbox("Business", list(MATERIAL_LISTS.keys()))
        
        action = st.radio("Aktion", ["Ausgabe (Issue)", "Rücknahme (Return)"], horizontal=True)
        
        items = MATERIAL_LISTS[business]
        selected_item = st.selectbox("Material auswählen", 
                                    [f"{item[1]} — {item[2]}" for item in items])
        
        idx = [f"{item[1]} — {item[2]}" for item in items].index(selected_item)
        category, item_name, spec = items[idx]
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Menge / Quantity", min_value=1, value=1, step=1)
        with col2:
            remark = st.text_input("Bemerkung / Remark", 
                                 value="" if category != "Sonstiges" else "Bitte Beschreibung eingeben")
        
        if st.button("💾 Speichern", type="primary"):
            if action == "Ausgabe (Issue)":
                add_supply(st.session_state.username, business, category, item_name, spec, 
                          issued=quantity, returned=0, remark=remark)
            else:
                add_supply(st.session_state.username, business, category, item_name, spec, 
                          issued=0, returned=quantity, remark=remark)
            st.success("✅ Erfolgreich gespeichert!")

    with tabs[2]:
        st.subheader("📊 Dashboard")
        st.info("Material history and summary will be shown here (will improve soon).")
