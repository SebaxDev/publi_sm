import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la página
st.set_page_config(page_title="Panel Publicidad SM", layout="wide")

# Autenticación con Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key("19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w")
worksheet = sheet.sheet1

def cargar_datos():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def guardar_dato(usuario, fecha, dias, precio, estado):
    nueva_fila = [usuario, fecha, dias, precio, estado]
    worksheet.append_row(nueva_fila)

def formulario():
    with st.form("formulario_publi"):
        st.subheader("📋 Carga de Publicidad")
        usuario = st.text_input("Usuario")
        fecha = st.date_input("Fecha", value=datetime.date.today())
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio", min_value=0, step=100)
        estado = st.selectbox("Estado", ["Activo", "Vencido"])
        submitted = st.form_submit_button("Cargar")

        if submitted:
            fecha_str = fecha.strftime("%d/%m/%Y")
            guardar_dato(usuario, fecha_str, dias, precio, estado)
            st.success("✅ Publicidad cargada con éxito")

def mostrar_dashboard():
    df = cargar_datos()

    st.markdown("""
        <style>
        .metric-box {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            font-size: 1.2rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("📊 Panel de Control")

    total = df.shape[0]
    activas = df[df["Estado"] == "Activo"].shape[0]
    vencidas = df[df["Estado"] == "Vencido"].shape[0]
    total_ganado = df["Precio"].sum()

    st.markdown("""
    <div class="grid">
        <div class="metric-box">🔢 <br><strong>Total</strong><br> {} </div>
        <div class="metric-box">🟢 <br><strong>Activas</strong><br> {} </div>
        <div class="metric-box">🔴 <br><strong>Vencidas</strong><br> {} </div>
        <div class="metric-box">💰 <br><strong>Total Ganado</strong><br> ${} </div>
    </div>
    """.format(total, activas, vencidas, total_ganado), unsafe_allow_html=True)

def resumen():
    df = cargar_datos()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format="%d/%m/%Y", errors='coerce')

    df_mes = df[df['Fecha'].dt.month == datetime.datetime.now().month]
    df_ano = df[df['Fecha'].dt.year == datetime.datetime.now().year]

    total_mes = df_mes['Precio'].sum()
    total_ano = df_ano['Precio'].sum()

    st.subheader("📅 Resúmenes")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Ganado Este Mes", f"${total_mes}")
    with col2:
        st.metric("Total Ganado Este Año", f"${total_ano}")

# --- Estructura Principal ---
with st.sidebar:
    st.title("🔐 Acceso")
    password = st.text_input("Contraseña", type="password")
    login = st.button("Ingresar")

if password == "PubliSM" and login:
    mostrar_dashboard()
    formulario()
    resumen()
else:
    st.warning("🔒 Ingresá la contraseña correcta para acceder al panel.")
