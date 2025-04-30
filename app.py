import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# Configuración de página
st.set_page_config(page_title="Gestión de Publicidad", layout="wide")

# --- Conexión con Google Sheets ---
SHEET_ID = "19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w"
SHEET_NAME = "Ingreso"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(SHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)

# --- Función para cargar datos ---
def cargar_datos():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()  # Limpia espacios accidentales
    st.write("Columnas detectadas:", df.columns.tolist())  # DEBUG temporal
    return df

# --- Función para guardar datos ---
def guardar_datos(nuevo):
    sheet.append_row(nuevo)

# --- Dashboard visual ---
def mostrar_dashboard():
    df = cargar_datos()

    st.markdown("""
        <style>
            .metric-box {
                background-color: #f0f4f8;
                padding: 1rem;
                border-radius: 1rem;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                font-size: 1.3rem;
                margin-bottom: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        activas = df[df["Estado"] == "Activo"].shape[0]
        st.markdown(f"<div class='metric-box'>🟢<br><strong>Activas</strong><br>{activas}</div>", unsafe_allow_html=True)

    with col2:
        vencidas = df[df["Estado"] == "Vencido"].shape[0]
        st.markdown(f"<div class='metric-box'>🔴<br><strong>Vencidas</strong><br>{vencidas}</div>", unsafe_allow_html=True)

    with col3:
        total = df.shape[0]
        st.markdown(f"<div class='metric-box'>📊<br><strong>Total</strong><br>{total}</div>", unsafe_allow_html=True)

# --- Formulario de carga ---
def formulario():
    with st.form("formulario_publicidad"):
        st.subheader("📤 Cargar nueva publicidad")

        usuario = st.text_input("Usuario")
        fecha = st.date_input("Fecha", value=datetime.date.today(), format="%d/%m/%Y")
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio ($)", min_value=0, step=100)
        estado = st.selectbox("Estado", ["Activo", "Vencido"])

        enviado = st.form_submit_button("Guardar")

        if enviado:
            nueva_fila = [usuario, fecha.strftime("%d/%m/%Y"), dias, precio, estado]
            guardar_datos(nueva_fila)
            st.success("✅ Publicidad cargada correctamente")

# --- Resumen mensual y anual ---
def resumenes():
    st.subheader("📅 Resumen mensual y anual")
    df = cargar_datos()
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors='coerce')

    df["Mes"] = df["Fecha"].dt.strftime("%Y-%m")
    resumen_mensual = df.groupby("Mes")["Precio"].sum().reset_index()
    resumen_mensual.columns = ["Mes", "Total"]

    df["Año"] = df["Fecha"].dt.year
    resumen_anual = df.groupby("Año")["Precio"].sum().reset_index()
    resumen_anual.columns = ["Año", "Total"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 Mensual")
        st.bar_chart(resumen_mensual.set_index("Mes"))

    with col2:
        st.markdown("### 📊 Anual")
        st.bar_chart(resumen_anual.set_index("Año"))

# --- Ejecución ---
st.title("📱 Gestión de Publicidad en Instagram")

mostrar_dashboard()
st.markdown("---")
formulario()
st.markdown("---")
resumenes()
