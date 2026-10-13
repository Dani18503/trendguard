import streamlit as st
import sqlite3
import json
import base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# --- SISTEMA DE LOGIN (SEGURIDAD) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 TrendGuard | Acceso CEO")
    st.markdown("Ingresa tus credenciales para gestionar las licencias.")
    with st.form("login_form"):
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            # AQUÍ ESTÁN LAS CREDENCIALES (CÁMBIALAS SI QUIERES)
            if user == "jhonny_admin" and password == "TrendGuard2026!":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

if not st.session_state.logged_in:
    login()
    st.stop() # Detiene el resto del código si no está logueado

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="TrendGuard Admin", page_icon="🔐", layout="wide")

# --- FUNCIONES DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('licenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS licenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_id TEXT,
                  expiration_date TEXT,
                  assets_allowed TEXT,
                  issued_at TEXT,
                  filename TEXT)''')
    conn.commit()
    conn.close()

def save_license_to_db(customer_id, exp_date, assets, issued_at, filename):
    conn = sqlite3.connect('licenses.db')
    c = conn.cursor()
    c.execute("INSERT INTO licenses (customer_id, expiration_date, assets_allowed, issued_at, filename) VALUES (?, ?, ?, ?, ?)",
              (customer_id, exp_date, assets, issued_at, filename))
    conn.commit()
    conn.close()

def get_all_licenses():
    conn = sqlite3.connect('licenses.db')
    c = conn.cursor()
    c.execute("SELECT customer_id, expiration_date, assets_allowed, issued_at, filename FROM licenses ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# --- FUNCIONES DE LICENCIAMIENTO ---
def load_private_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def generate_license_file(customer_id, expiration_days, assets):
    exp_date = (datetime.now() + timedelta(days=expiration_days)).isoformat()
    payload = {
        "customer_id": customer_id,
        "expiration_date": exp_date,
        "assets_allowed": assets,
        "issued_at": datetime.now().isoformat()
    }
    payload_json = json.dumps(payload, sort_keys=True).encode('utf-8')
    private_key = load_private_key("private_key.pem")
    signature = private_key.sign(payload_json)
    license_data = {
        "payload": payload,
        "signature": base64.b64encode(signature).decode('utf-8')
    }
    filename = f"license_{customer_id}.lic"
    with open(filename, "w") as f:
        json.dump(license_data, f, indent=4)
    
    save_license_to_db(customer_id, exp_date, ", ".join(assets), payload["issued_at"], filename)
    return filename

init_db()

# --- INTERFAZ GRÁFICA ---
st.title("🔐 TrendGuard | Panel de Administración")
st.markdown(f"Bienvenido, CEO. Genera y gestiona las licencias de tus clientes desde aquí.")
st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update(logged_in=False))

tab1, tab2 = st.tabs(["📝 Generar Nueva Licencia", "📋 Historial de Licencias"])

with tab1:
    st.header("Nueva Licencia")
    with st.form("license_form"):
        customer_id = st.text_input("Nombre o ID del Cliente", placeholder="Ej: Cliente_001")
        expiration_days = st.number_input("Días de vigencia", min_value=1, max_value=3650, value=30)
        
        st.write("Activos permitidos:")
        col1, col2, col3 = st.columns(3)
        with col1: btc = st.checkbox("BTC/USDT", value=True)
        with col2: eth = st.checkbox("ETH/USDT", value=True)
        with col3: sol = st.checkbox("SOL/USDT", value=True)
        
        submitted = st.form_submit_button("Generar Licencia")
        
        if submitted:
            if not customer_id:
                st.error("Por favor, ingresa el nombre del cliente.")
            else:
                assets = []
                if btc: assets.append("BTC/USDT")
                if eth: assets.append("ETH/USDT")
                if sol: assets.append("SOL/USDT")
                
                if not assets:
                    st.error("Debes seleccionar al menos un activo.")
                else:
                    filename = generate_license_file(customer_id, expiration_days, assets)
                    st.success(f"✅ Licencia generada con éxito: {filename}")
                    st.info("El archivo .lic ya está listo para ser enviado al cliente.")

with tab2:
    st.header("Licencias Generadas")
    licenses = get_all_licenses()
    if licenses:
        import pandas as pd
        df = pd.DataFrame(licenses, columns=["Cliente", "Expira", "Activos", "Emitida", "Archivo"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay licencias generadas aún.")
