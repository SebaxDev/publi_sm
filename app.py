import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# -------------------- CONFIGURACIÓN --------------------

st.set_page_config(page_title="Panel Publicidad Instagram", layout="wide")

st.markdown("""
    <style>
        .metric-box {
            background-color: #f0f4f8;
            padding: 1.2rem;
            margin: 0.5rem;
            border-radius: 1rem;
            text-align: center;
            font-weight: bold;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            display: inline-block;
            width: 180px;
        }
        .main-title {
            text-align: center;
            font-size: 2rem;
            margin-top: 1rem;
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------- CONEXIÓN A GOOGLE SHEETS --------------------

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPE
)
client = gspread.authorize(creds)
sheet = client.open_by_key("19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w")

# -------------------- FUNCIONES --------------------

def cargar_datos():
    worksheet = sheet.worksheet("Base")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.map(str).str.strip()
    return df

def agregar_registro(usuario, fecha, dias, precio, estado):
    worksheet = sheet.worksheet("Base")
    worksheet.append_row([usuario, fecha, dias, precio, estado])

def mostrar_dashboard():
    df = cargar_datos()

    st.markdown("<div class='main-title'>📊 Panel de Control</div>", unsafe_allow_html=True)

    if 'Estado' not in df.columns:
        st.error("La columna 'Estado' no está en los datos cargados. Verificá el nombre en la hoja de cálculo.")
        return

    activas = df[df["Estado"] == "Activo"].shape[0]
    vencidas = df[df["Estado"] == "Vencido"].shape[0]
    total = df.shape[0]
    total_ganado = df["Precio"].sum()
    ganado_format = f"${total_ganado:,.0f}".replace(",", ".")

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='metric-box'>🟢<br><strong>Activas</strong><br>{activas}</div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-box'>🔴<br><strong>Vencidas</strong><br>{vencidas}</div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-box'>📌<br><strong>Total</strong><br>{total}</div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='metric-box'>💰<br><strong>Ganado</strong><br>{ganado_format}</div>", unsafe_allow_html=True)

def formulario():
    st.markdown("<div class='main-title'>📥 Cargar Nueva Publicidad</div>", unsafe_allow_html=True)

    with st.form(key="formulario"):
        usuario = st.text_input("Usuario de Instagram")
        fecha = st.date_input("Fecha", value=datetime.date.today())
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio ($)", min_value=0.0, step=0.01)
        estado = st.selectbox("Estado", ["Activo", "Vencido"])
        submit = st.form_submit_button("Cargar")

        if submit:
            fecha_str = fecha.strftime("%d/%m/%Y")
            agregar_registro(usuario, fecha_str, dias, precio, estado)
            st.success("✅ Publicidad cargada correctamente")

def resumenes():
    df = cargar_datos()
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Fecha"])

    df["Mes"] = df["Fecha"].dt.strftime("%B %Y")
    df["Año"] = df["Fecha"].dt.year

    resumen_mensual = df.groupby("Mes")["Precio"].sum().reset_index().sort_values(by="Mes", ascending=False)
    resumen_mensual["Precio"] = resumen_mensual["Precio"].apply(lambda x: f"${x:,.0f}".replace(",", "."))

    resumen_anual = df.groupby("Año")["Precio"].sum().reset_index().sort_values(by="Año", ascending=False)
    resumen_anual["Precio"] = resumen_anual["Precio"].apply(lambda x: f"${x:,.0f}".replace(",", "."))

    st.markdown("<div class='main-title'>📆 Resumen de Ingresos</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Por Mes")
        st.dataframe(resumen_mensual)

    with col2:
        st.subheader("Por Año")
        st.dataframe(resumen_anual)

# -------------------- UI --------------------

mostrar_dashboard()
formulario()
resumenes()
