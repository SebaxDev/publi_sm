import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- Autenticación con Streamlit secrets ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)

# --- Conexión a la hoja de cálculo ---
sheet_id = "19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w"
spreadsheet = client.open_by_key(sheet_id)
worksheet = spreadsheet.worksheet("Ingreso")

# --- Cargar datos existentes ---
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- Procesamiento de datos ---
if not df.empty:
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    df['Dias Contratados'] = pd.to_numeric(df['Dias Contratados'], errors='coerce')
    df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce')
    df['Vence'] = df['Fecha'] + pd.to_timedelta(df['Dias Contratados'], unit='D')
    df['Estado'] = df['Vence'].apply(lambda x: "Activo" if x >= datetime.now() else "Vencido")

# --- Estilos con HTML y CSS ---
st.markdown("""
    <style>
        .big-title {font-size: 40px; font-weight: bold; text-align: center; color: #4CAF50; margin-bottom: 10px;}
        .section-title {font-size: 28px; margin-top: 40px; color: #3F51B5; border-bottom: 2px solid #3F51B5; padding-bottom: 5px;}
        .metric-box {background: #f1f3f6; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);}
        .stButton>button {background-color: #4CAF50; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 16px;}
        .stButton>button:hover {background-color: #45a049;}
    </style>
""", unsafe_allow_html=True)

# --- Título principal ---
st.markdown("<div class='big-title'>📊 Panel de Gestión de Publicidad - PubliSM</div>", unsafe_allow_html=True)

# --- DASHBOARD ---
st.markdown("<div class='section-title'>📈 Dashboard General</div>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='metric-box'>🟢 <br> <strong>Activas</strong><br> {} </div>".format(df[df["Estado"] == "Activo"].shape[0]), unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-box'>🔴 <br> <strong>Vencidas</strong><br> {} </div>".format(df[df["Estado"] == "Vencido"].shape[0]), unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-box'>💰 <br> <strong>Total Ganado</strong><br> ${:,.0f} </div>".format(df['Precio'].sum()), unsafe_allow_html=True)

# --- FORMULARIO DE CARGA ---
st.markdown("<div class='section-title'>✍️ Nueva Publicidad</div>", unsafe_allow_html=True)
with st.form("formulario_carga"):
    usuario = st.text_input("Usuario")
    fecha = st.date_input("Fecha de inicio", format="DD/MM/YYYY")
    dias = st.number_input("Días contratados", min_value=1, step=1)
    precio = st.number_input("Precio total", min_value=0.0, step=100.0)
    estado = "Activo"
    enviar = st.form_submit_button("Cargar")
    if enviar:
        nueva_fila = [usuario, fecha.strftime("%d/%m/%Y"), dias, precio, estado]
        worksheet.append_row(nueva_fila)
        st.success(f"✅ Publicidad cargada para {usuario}")

# --- RESUMEN MENSUAL ---
st.markdown("<div class='section-title'>📆 Resumen Mensual</div>", unsafe_allow_html=True)
mes_actual = datetime.now().month
anio_actual = datetime.now().year
df_mes = df[(df["Fecha"].dt.month == mes_actual) & (df["Fecha"].dt.year == anio_actual)]
st.write(f"Total en {datetime.now().strftime('%B')} {anio_actual}: ${df_mes['Precio'].sum():,.0f}")
st.dataframe(df_mes[['Usuario', 'Fecha', 'Dias Contratados', 'Precio', 'Estado']], use_container_width=True)

# --- RESUMEN ANUAL ---
st.markdown("<div class='section-title'>📅 Resumen Anual</div>", unsafe_allow_html=True)
df_anual = df[df["Fecha"].dt.year == anio_actual]
total_anual = df_anual.groupby(df_anual["Fecha"].dt.month)["Precio"].sum()
st.bar_chart(total_anual)

st.markdown("---")
st.caption("Creado con ❤️ por vos. Mejorado con ayuda de ChatGPT.")
