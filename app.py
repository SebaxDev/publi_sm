import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ---------------- LOGIN ---------------- #
st.set_page_config(page_title="Panel Publicidad", layout="wide")
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Acceso al panel")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user == "PubliSM" and password == "PubliSM":
            st.session_state.logged_in = True
        else:
            st.error("Usuario o contraseña incorrectos")

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- CONEXIÓN A SHEET ---------------- #
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES,
)
client = gspread.authorize(creds)
sheet_id = "19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w"  # ⚠️ Reemplazá por tu ID real
spreadsheet = client.open_by_key(sheet_id)
worksheet = spreadsheet.sheet1

# ---------------- FUNCIONES ---------------- #
def cargar_datos(usuario, dias, precio):
    fecha = datetime.now().strftime("%d/%m/%Y")
    estado = "Activo"
    nueva_fila = [usuario, fecha, dias, precio, estado]
    worksheet.append_row(nueva_fila)

def obtener_datos():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    # 🔍 Debug: Ver columnas reales
    st.write("Columnas del DataFrame:", df.columns.tolist())

    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", dayfirst=True, errors="coerce")
        df = df.sort_values(by="Fecha", ascending=False)
    return df

# ---------------- INTERFAZ ---------------- #
menu = st.sidebar.selectbox("Menú", ["📥 Cargar Publicidad", "📊 Ver Dashboard"])

if menu == "📥 Cargar Publicidad":
    st.header("Cargar nueva publicidad")

    usuario = st.text_input("Usuario de Instagram")
    dias = st.number_input("Días contratados", min_value=1, step=1)
    precio = st.number_input("Precio ($)", min_value=0, step=10)

    if st.button("Cargar"):
        if usuario:
            cargar_datos(usuario, dias, precio)
            st.success("Publicidad cargada correctamente.")
        else:
            st.warning("Debe ingresar un nombre de usuario.")

elif menu == "📊 Ver Dashboard":
    st.title("Dashboard de Publicidad")

    df = obtener_datos()

    if df.empty:
        st.warning("No hay datos cargados aún.")
        st.stop()

    # FILTROS
    clientes = df["Usuario"].unique().tolist()
    cliente_sel = st.sidebar.selectbox("Filtrar por cliente", ["Todos"] + clientes)
    if cliente_sel != "Todos":
        df = df[df["Usuario"] == cliente_sel]

    # MÉTRICAS
    total = df["Precio"].sum()
    activos = df[df["Estado"] == "Activo"]
    vencidos = df[df["Estado"] != "Activo"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total generado", f"${total}")
    col2.metric("Publicidades activas", len(activos))
    col3.metric("Clientes únicos", df["Usuario"].nunique())

    st.markdown("---")

    # GRILLA DE DATOS
    with st.expander("📋 Ver datos"):
        st.dataframe(df, use_container_width=True)

    # PRÓXIMAS FUNCIONES
    st.markdown("### Funciones próximas:")
    st.markdown("- Sumar días a campañas activas")
    st.markdown("- Gráficos mensuales")
    st.markdown("- Exportar CSV")
    st.markdown("- Notificaciones de vencimiento")
