import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2 import service_account

# ----------------- CONFIGURACIÓN -----------------
st.set_page_config(page_title="Panel de Publicidad", layout="wide")

# ----------------- AUTENTICACIÓN -----------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPE
)
client = gspread.authorize(creds)
sheet = client.open_by_key("19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w")
worksheet = sheet.worksheet("Base")

# ----------------- FUNCIONES -----------------
def cargar_datos():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors='coerce')
    if "Precio" in df.columns:
        df["Precio"] = pd.to_numeric(df["Precio"], errors='coerce').fillna(0)
    return df

def guardar_dato(usuario, fecha, dias, precio, estado):
    worksheet.append_row([usuario, fecha.strftime("%d/%m/%Y"), dias, precio, estado])

# ----------------- DASHBOARD -----------------
def mostrar_dashboard():
    st.markdown("## 📊 Dashboard")

    df = cargar_datos()

    activas = df[df["Estado"] == "Activo"].shape[0]
    vencidas = df[df["Estado"] == "Vencido"].shape[0]
    total_ganado = df["Precio"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Activas", f"{activas}")
    col2.metric("🔴 Vencidas", f"{vencidas}")
    col3.metric("💰 Total Ganado", f"${total_ganado:,.0f}")

# ----------------- FORMULARIO -----------------
def mostrar_formulario():
    st.markdown("## ➕ Cargar Publicidad")

    with st.form("formulario_publicidad"):
        usuario = st.text_input("Usuario")
        fecha = st.date_input("Fecha", value=datetime.date.today())
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio ($)", min_value=0, step=100)
        estado = st.selectbox("Estado", ["Activo", "Vencido"])
        enviar = st.form_submit_button("Cargar")

        if enviar:
            guardar_dato(usuario, fecha, dias, precio, estado)
            st.success("✅ Publicidad cargada con éxito.")

# ----------------- RESUMEN -----------------
def mostrar_resumen():
    st.markdown("## 📅 Resumen Mensual y Anual")
    df = cargar_datos()
    df["Mes"] = df["Fecha"].dt.strftime("%B")
    df["Año"] = df["Fecha"].dt.year

    resumen_mensual = df.groupby("Mes")["Precio"].sum().reset_index()
    resumen_anual = df.groupby("Año")["Precio"].sum().reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📆 Por Mes")
        st.dataframe(resumen_mensual)

    with col2:
        st.markdown("### 🗓️ Por Año")
        st.dataframe(resumen_anual)

# ----------------- EJECUCIÓN -----------------
mostrar_dashboard()
st.markdown("---")
mostrar_formulario()
st.markdown("---")
mostrar_resumen()
