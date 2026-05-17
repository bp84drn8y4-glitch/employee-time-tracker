import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3

st.set_page_config(page_title="Zeiterfassung (Time Tracker)", layout="wide")

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

MATERIAL_LISTS = {
    "Fürst Hauser Gebäudereinigung": [
        "Müllbeutel Groß (Large trash bags) 120 L", "Müllbeutel Medium (Medium) 60 L", 
        "Müllbeutel Klein (Small) 28 L", "Wischmopp Mikrofaser (Microfiber mop) 50 cm",
        "Wischmopp Baumwolle (Cotton mop) 50 cm", "Mikrofaser Lappen rot (Red)", 
        "Mikrofaser Lappen blau (Blue)", "Mikrofaser Lappen grün (Green)", 
        "Mikrofaser Lappen gelb (Yellow)", "Geschirrtücher (Kitchen towels)",
        "Sanitäreiniger (Bathroom cleaner)", "Bodenreiniger (Floor cleaner)",
        "Toilettenpapier (Toilet paper)", "Handseife (Hand soap)"
    ],
    "Bullauge Waschsalon": [
        "Hände folien (Plastic gloves)", "Bügelstärke (Ironing starch)", 
        "Chlor (Chlorine)", "Waschpulver (Washing powder) 20 kg", 
        "Weichspüler (Fabric softener) 20 Liter"
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
                 VALUES (?, ?, ?, ?, ?, ?, ?)""", (today, employee, start, end, task, customer, hours))
    conn.commit()
    conn.close()

def get_entries(employee=None, month=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM entries"
    params = []
    if employee:
        query += " WHERE employee = ?"
        params.append(employee)
    if month:
        query += " AND date LIKE ?" if employee else " WHERE date LIKE ?"
        params.append(f"{month}%")
    query += " ORDER BY date DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def add_supply(employee, business, item, issued=0, returned=0):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO supplies (date, employee, business, item, issued, returned)
                 VALUES (?, ?, ?, ?, ?, ?)""", (today, employee, business, item, issued, returned))
    conn.commit()
    conn.close()

def get_supplies(employee=None):
    conn = sqlite3.connect(DB_FILE)
    if employee:
        df = pd.read_sql_query("SELECT * FROM supplies WHERE employee = ? ORDER BY date DESC", conn, params=[employee])
    else:
        df = pd.read_sql_query("SELECT * FROM supplies ORDER BY date DESC", conn)
    conn.close()
    return df

def add_new_employee(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'employee')", (username, password))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# ===================== MAIN APP =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

st.title("🧹 Zeiterfassung (Employee Time Tracker)")

if not st.session_state.logged_in:
    tab1, _ = st.tabs(["🔑 Login", "👤 Mitarbeiter verwalten"])

    with tab1:
        st.subheader("Anmelden (Login)")
        username = st.text_input("Benutzername (Username)", key="login_user")
        password = st.text_input("Passwort (Password)", type="password", key="login_pass")
        if st.button("Anmelden (Login)", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
            result = c.fetchone()
            conn.close()
            if result:
                st.session_state.logged_in = True
                st.session_state.role = result[0]
                st.session_state.username = username
                st.success(f"Willkommen / Welcome, {username}!")
                st.rerun()
            else:
                st.error("Ungültige Zugangsdaten (Invalid credentials)")

else:
    st.sidebar.success(f"✅ {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Abmelden (Logout)"):
        st.session_state.clear()
        st.rerun()

    # ==================== ADMIN ONLY: Add Employee ====================
    if st.session_state.role == "employer":
        with st.expander("👤 Neuen Mitarbeiter hinzufügen (Add New Employee)"):
            new_user = st.text_input("Benutzername (Username)", key="admin_new_user")
            new_pass = st.text_input("Passwort (Password)", type="password", key="admin_new_pass")
            if st.button("Mitarbeiter erstellen (Create Employee)"):
                if new_user and new_pass:
                    if add_new_employee(new_user, new_pass):
                        st.success(f"Mitarbeiter '{new_user}' wurde erstellt!")
                    else:
                        st.error("Benutzername existiert bereits")
                else:
                    st.warning("Bitte alle Felder ausfüllen")

    # ==================== MAIN FUNCTIONS ====================
    st.subheader("📝 Arbeitszeit eintragen (Record Working Time)")
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("Startzeit (Start Time)", datetime.strptime("09:00", "%H:%M").time())
    with col2:
        end_time = st.time_input("Endzeit (End Time)", datetime.strptime("17:00", "%H:%M").time())
    
    task = st.text_input("Tätigkeit (Task Description)")
    customer = st.text_input("Kunde / Projekt (Customer / Project)")
    
    if st.button("Eintrag speichern (Submit Entry)", type="primary"):
        if task and customer:
            add_entry(st.session_state.username, start_time.strftime("%H:%M"), 
                     end_time.strftime("%H:%M"), task, customer)
            st.success("✅ Eintrag gespeichert! (Entry saved!)")
            st.rerun()
        else:
            st.warning("Tätigkeit und Kunde sind erforderlich")

    st.subheader("🧴 Material (Ausgabe / Rücknahme)")
    business = st.selectbox("Betrieb (Business)", list(MATERIAL_LISTS.keys()))
    item = st.selectbox("Material auswählen", MATERIAL_LISTS[business])
    
    col3, col4 = st.columns(2)
    with col3:
        issued = st.number_input("Ausgabe (Issued)", min_value=0, value=0)
    with col4:
        returned = st.number_input("Rücknahme (Returned)", min_value=0, value=0)
    
    if st.button("Material speichern (Save Material)"):
        if issued > 0 or returned > 0:
            add_supply(st.session_state.username, business, item, issued, returned)
            st.success("✅ Material gespeichert!")

    # History
    st.subheader("📋 Meine Einträge (My Entries)" if st.session_state.role == "employee" else "📋 Alle Einträge (All Entries)")
    current_month = date.today().strftime("%Y-%m")
    df = get_entries(st.session_state.username if st.session_state.role == "employee" else None, current_month)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.success(f"Gesamtstunden / Total Hours: {df['hours'].sum():.2f}")
    else:
        st.info("Noch keine Einträge (No entries yet)")

    supplies_df = get_supplies(st.session_state.username if st.session_state.role == "employee" else None)
    if not supplies_df.empty:
        st.subheader("🧴 Materialhistorie (Material History)")
        st.dataframe(supplies_df, use_container_width=True)
