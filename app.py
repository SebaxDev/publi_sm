# -------------------- LIBRERIAS --------------------

import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# -------------------- CONFIGURACION DE PANTALLA --------------------

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

# -------------------- FUNCION DE LOGIN --------------------

def login():
    st.title("🔐 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        usuarios = st.secrets.get("auth", {})
        if username in usuarios and password == usuarios[username]:
            st.session_state["logueado"] = True
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")

if "logueado" not in st.session_state or not st.session_state["logueado"]:
    login()
    st.stop()

# -------------------- CONEXION A GOOGLE SHEETS --------------------

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPE
)
client = gspread.authorize(creds)

try:
    sheet = client.open_by_key("19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w")
except Exception as e:
    st.error(f"No se pudo abrir la hoja de cálculo: {e}")
    st.stop()

# -------------------- TRADUCCION DE MESES --------------------

MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo",
    "April": "Abril", "May": "Mayo", "June": "Junio",
    "July": "Julio", "August": "Agosto", "September": "Septiembre",
    "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

# -------------------- FUNCIONES DE DATOS --------------------

def cargar_datos():
    try:
        worksheet = sheet.worksheet("Ingreso")
    except gspread.exceptions.WorksheetNotFound:
        st.error("❌ La hoja 'Ingreso' no fue encontrada en el documento.")
        hojas = [ws.title for ws in sheet.worksheets()]
        st.info(f"Hojas disponibles: {hojas}")
        st.stop()

    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = pd.Index([str(col).strip() for col in df.columns])
    return df

def guardar_datos(df):
    worksheet = sheet.worksheet("Ingreso")
    worksheet.clear()
    worksheet.append_row(df.columns.tolist())
    for row in df.itertuples(index=False):
        worksheet.append_row(list(row))

# -------------------- UI: DASHBOARD --------------------

def mostrar_dashboard():
    df = cargar_datos()

    # Conversión de fecha y campos derivados
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Fecha"])
    df["Mes"] = df["Fecha"].dt.strftime("%B %Y").map(
        lambda x: MESES_ES.get(x.split(" ")[0], x.split(" ")[0]) + " " + x.split(" ")[1]
    )
    df["Año"] = df["Fecha"].dt.year

    # FILTROS
    estados = st.sidebar.multiselect("Filtrar por Estado", df["Estado"].unique(), default=list(df["Estado"].unique()))
    meses = st.sidebar.multiselect("Filtrar por Mes", df["Mes"].unique(), default=list(df["Mes"].unique()))
    anios = st.sidebar.multiselect("Filtrar por Año", df["Año"].unique(), default=list(df["Año"].unique()))

    df_filtrado = df[(df["Estado"].isin(estados)) & (df["Mes"].isin(meses)) & (df["Año"].isin(anios))]

    # METRICAS
    activas = df_filtrado[df_filtrado["Estado"] == "Activo"].shape[0]
    vencidas = df_filtrado[df_filtrado["Estado"] == "Vencido"].shape[0]
    total = df_filtrado.shape[0]
    total_ganado = df_filtrado["Precio"].sum()

    st.markdown("<div class='main-title'>📊 Panel de Control</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='metric-box'>🟢<br><strong>Activas</strong><br>{activas}</div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-box'>🔴<br><strong>Vencidas</strong><br>{vencidas}</div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-box'>📌<br><strong>Total</strong><br>{total}</div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='metric-box'>💰<br><strong>Ganado</strong><br>${total_ganado}</div>", unsafe_allow_html=True)

    # MOSTRAR PUBLICIDADES ACTIVAS CON BOTON PARA SUMAR DIA
    st.subheader("📺 Publicidades Activas")
    df_activas = df[df["Estado"] == "Activo"].copy()

    for i, row in df_activas.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.write(f"👤 {row['Usuario']}")
        col2.write(f"📅 {row['Fecha'].strftime('%d/%m/%Y')}")
        col3.write(f"⏳ {row['Dias Usados']} / {row['Dias']}")
        col4.write(f"💰 ${row['Precio']}")
        col5.write(f"📝 {row.get('Notas', '')}")
        if col6.button("➕ Sumar día", key=f"sumar_{i}"):
            df.at[i, "Dias Usados"] += 1
            if df.at[i, "Dias Usados"] >= df.at[i, "Dias"]:
                df.at[i, "Estado"] = "Vencido"
            guardar_datos(df)
            st.experimental_rerun()

# -------------------- UI: FORMULARIO DE CARGA --------------------

def formulario():
    st.markdown("<div class='main-title'>📥 Cargar Nueva Publicidad</div>", unsafe_allow_html=True)

    with st.form(key="formulario"):
        usuario = st.text_input("Usuario de Instagram")
        fecha = st.date_input("Fecha", value=datetime.date.today())
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio ($)", min_value=0.0, step=0.01)
        estado = st.selectbox("Estado", ["Activo", "Vencido"])
        notas = st.text_input("Notas (opcional)")
        submit = st.form_submit_button("Cargar")

        if submit:
            fecha_str = fecha.strftime("%d/%m/%Y")
            nuevo = {
                "Usuario": usuario,
                "Fecha": fecha_str,
                "Dias": dias,
                "Precio": precio,
                "Estado": estado,
                "Dias Usados": 0,
                "Notas": notas
            }
            df = cargar_datos()
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            guardar_datos(df)
            st.success("✅ Publicidad cargada correctamente")
            st.experimental_rerun()

# -------------------- UI: RESUMENES Y CLIENTES --------------------

def resumenes():
    df = cargar_datos()
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Fecha"])

    df["Mes"] = df["Fecha"].dt.strftime("%B %Y").map(
        lambda x: MESES_ES.get(x.split(" ")[0], x.split(" ")[0]) + " " + x.split(" ")[1]
    )
    df["Año"] = df["Fecha"].dt.year

    st.markdown("<div class='main-title'>📆 Resumen de Ingresos</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    resumen_mensual = df.groupby("Mes")["Precio"].sum().reset_index().sort_values(by="Mes", ascending=False)
    resumen_anual = df.groupby("Año")["Precio"].sum().reset_index().sort_values(by="Año", ascending=False)

    with col1:
        st.subheader("Por Mes")
        st.dataframe(resumen_mensual)

    with col2:
        st.subheader("Por Año")
        st.dataframe(resumen_anual)

    st.subheader("💼 Gasto Total por Cliente")
    resumen_cliente = df.groupby("Usuario")["Precio"].sum().reset_index().sort_values(by="Precio", ascending=False)
    st.dataframe(resumen_cliente)

# -------------------- EJECUCION DE LA APP --------------------

mostrar_dashboard()
formulario()
resumenes()
