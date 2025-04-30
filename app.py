import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# ------------------------------
# Autenticación con Google Sheets
# ------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(credentials)

# Conectamos con la hoja por ID (más confiable)
sheet_id = "19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w"  # <- Reemplazá con el ID real
database = client.open_by_key(sheet_id).sheet1

# ------------------------------
# Autenticación simple con login básico
# ------------------------------
def login():
    st.markdown("## Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if username == "PubliSM" and password == "PubliSM":
            st.session_state.logged_in = True
            st.success("Sesión iniciada con éxito")
        else:
            st.error("Usuario o contraseña incorrectos")

# ------------------------------
# Carga de datos al formulario
# ------------------------------
def cargar_datos():
    st.markdown("## Cargar nueva publicidad")
    usuario = st.text_input("Usuario de Instagram")
    dias = st.number_input("Días contratados", min_value=1, step=1)
    precio = st.number_input("Precio total $", min_value=0.0, step=100.0)
    fecha = datetime.now().strftime("%d/%m/%Y")  # Formato día/mes/año
    estado = "Activo"

    if st.button("Cargar datos"):
        if usuario:
            database.append_row([usuario, fecha, dias, precio, estado])
            st.success("✅ Publicidad cargada correctamente")
        else:
            st.warning("⚠️ Completá todos los campos")

# ------------------------------
# Vista general y tabla de resumen
# ------------------------------
def ver_dashboard():
    st.markdown("## 📊 Panel de control")

    # Obtener los datos
    data = database.get_all_records()
    df = pd.DataFrame(data)

    # Formato de fecha correcto y resumen
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
    df['Dias Contratados'] = pd.to_numeric(df['Dias Contratados'], errors='coerce')
    df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce')

    total_ventas = df['Precio'].sum()
    activos = df[df['Estado'] == 'Activo']

    col1, col2 = st.columns(2)
    col1.metric("Total recaudado", f"$ {total_ventas:,.0f}")
    col2.metric("Campañas activas", len(activos))

    st.markdown("### Tabla de registros")
    st.dataframe(df.sort_values(by="Fecha", ascending=False))

    with st.expander("🔍 Filtros avanzados"):
        cliente = st.text_input("Filtrar por cliente")
        if cliente:
            filtrado = df[df['Usuario'].str.contains(cliente, case=False)]
            st.dataframe(filtrado)

# ------------------------------
# App principal
# ------------------------------
st.set_page_config(page_title="Gestión de Publicidad SM", layout="centered")
st.title("📱 Publicidad Instagram - Gestión")

if 'logged_in' not in st.session_state:
    login()
elif st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menú", ["Formulario de carga", "Dashboard"])
    if menu == "Formulario de carga":
        cargar_datos()
    elif menu == "Dashboard":
        ver_dashboard()
