import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ------------------------- CONFIGURACION -------------------------
# Conexión a Google Sheets
SHEET_ID = "19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w"
SHEET_NAME = "Ingreso"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SHEET_ID)
worksheet = spreadsheet.worksheet(SHEET_NAME)

# ------------------------- FUNCIONES -------------------------
def cargar_datos():
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["Usuario", "Fecha", "Dias Contratados", "Precio", "Estado"])
    return pd.DataFrame(data)

def agregar_registro(usuario, fecha, dias, precio, estado):
    worksheet.append_row([usuario, fecha.strftime("%d/%m/%Y"), dias, precio, estado])

def formatear_moneda(valor):
    return "$ {:,.0f}".format(valor)

# ------------------------- LOGIN -------------------------
def login():
    st.title("🔐 Login")
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user == "PubliSM" and pwd == "PubliSM":
            st.session_state["logueado"] = True
        else:
            st.error("Credenciales incorrectas")

# ------------------------- DASHBOARD -------------------------
def dashboard(df):
    st.markdown("""
        <div class="grid grid-cols-3 gap-4 text-center mb-6">
            <div class="rounded-xl bg-green-100 p-4 shadow"><div class="text-2xl font-bold">🟢 {}<br/><span class='text-sm font-normal'>Activas</span></div></div>
            <div class="rounded-xl bg-red-100 p-4 shadow"><div class="text-2xl font-bold">🔴 {}<br/><span class='text-sm font-normal'>Vencidas</span></div></div>
            <div class="rounded-xl bg-blue-100 p-4 shadow"><div class="text-2xl font-bold">💰 {}<br/><span class='text-sm font-normal'>Total Ganado</span></div></div>
        </div>
    """.format(
        df[df["Estado"] == "Activo"].shape[0],
        df[df["Estado"] == "Vencido"].shape[0],
        formatear_moneda(df["Precio"].sum())
    ), unsafe_allow_html=True)

# ------------------------- FORMULARIO -------------------------
def formulario():
    st.subheader("📤 Cargar nueva publicidad")
    with st.form("formulario"):
        usuario = st.text_input("Usuario")
        fecha = st.date_input("Fecha", value=datetime.date.today(), format="%d/%m/%Y")
        dias = st.number_input("Días contratados", min_value=1, max_value=31, step=1)
        precio = st.number_input("Precio ($)", min_value=0)
        estado = st.selectbox("Estado", ["Activo", "Vencido"])
        enviar = st.form_submit_button("Guardar")
        if enviar:
            agregar_registro(usuario, fecha, dias, precio, estado)
            st.success("✅ Publicidad guardada con éxito")

# ------------------------- RESUMEN -------------------------
def resumen(df):
    st.subheader("📅 Resumen")
    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)
    df_mes = df[df["Fecha"].dt.month == datetime.datetime.now().month]
    df_anio = df[df["Fecha"].dt.year == datetime.datetime.now().year]

    col1, col2 = st.columns(2)
    col1.metric("Este mes", formatear_moneda(df_mes["Precio"].sum()))
    col2.metric("Este año", formatear_moneda(df_anio["Precio"].sum()))

    st.markdown("### 🧾 Historial")
    st.dataframe(df.sort_values("Fecha", ascending=False), use_container_width=True)

# ------------------------- MAIN -------------------------
st.set_page_config("Publicidad Instagram SM", layout="wide")

if "logueado" not in st.session_state:
    login()
else:
    df = cargar_datos()
    st.title("📊 Panel de Gestión de Publicidad")
    dashboard(df)
    st.divider()
    formulario()
    st.divider()
    resumen(df)

# ------------------------- CSS TAILWIND (simulado) -------------------------
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .metric-box {
            padding: 1rem;
            border-radius: 1rem;
            font-size: 1.25rem;
            background: #f0f9ff;
            text-align: center;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)
