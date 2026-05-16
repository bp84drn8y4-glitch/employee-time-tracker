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

# ===================== HELPER FUNCTIONS =====================
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

def get_supplies(employee=None, business=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM supplies ORDER BY date DESC"
    params = []
    # Can be extended with filters
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ===================== MAIN APP =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🧹 Employee Time + Material Tracker")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register Employee"])
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            # Simple check (add your check_login function)
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

    with tab2:
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Create Employee Account"):
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

    tabs = st.tabs(["⏱️ Time Tracking", "🧴 Material Tracking", "📊 Dashboard"])

    with tabs[0]:
        st.subheader("Time Tracking")
        st.info("Your previous time tracking code can be added here.")

    with tabs[1]:  # Material Tracking
        st.subheader("🧴 Material Issuance & Return")
        
        business = st.selectbox("Business / Kunde", 
                               ["Fürst Hauser Gebäudereinigung", "Bullauge Waschsalon"])
        
        action = st.radio("Aktion", ["Ausgabe (Issue)", "Rücknahme (Return)"])
        
        items = MATERIAL_LISTS[business]
        item_options = [f"{item[1]} - {item[2]}" for item in items]
        selected = st.selectbox("Material / Item", item_options)
        
        idx = item_options.index(selected)
        category, item_name, spec = items[idx]
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Menge / Quantity", min_value=0, value=1, step=1)
        with col2:
            remark = st.text_input("Bemerkung / Remark", value="" if category != "Sonstiges" else "Description")
        
        if st.button("✅ Save", type="primary"):
            if action == "Ausgabe (Issue)":
                add_supply(st.session_state.username, business, category, item_name, spec, 
                          issued=quantity, returned=0, remark=remark)
            else:
                add_supply(st.session_state.username, business, category, item_name, spec, 
                          issued=0, returned=quantity, remark=remark)
            st.success("✅ Saved successfully!")
            st.rerun()

    with tabs[2]:
        st.subheader("📊 Dashboard - Employer View")
        supplies_df = get_supplies()
        if not supplies_df.empty:
            st.dataframe(supplies_df, use_container_width=True)
        else:
            st.info("No material data yet.")
