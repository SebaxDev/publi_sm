import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# --- Login simple ---
def login():
    st.title("Ingreso al Dashboard")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user == "PubliSM" and password == "PubliSM":
            st.session_state.logged_in = True
        else:
            st.error("Usuario o contraseña incorrectos")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Conexión a Google Sheets con google-auth + secrets ---
if st.session_state.logged_in:
    st.title("Carga de Publicidad")

    # Configurar credenciales desde secrets
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)

    # Abrir hoja
    spreadsheet = client.open("NombreExactoDeTuHoja")  # Cambiar por el nombre real
    sheet = spreadsheet.worksheet("Ingreso")

    # --- Formulario ---
    with st.form("formulario_publi"):
        usuario = st.text_input("Usuario (@ejemplo)")
        fecha = st.date_input("Fecha", value=date.today())
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio", min_value=0.0, step=0.01)
        estado = st.selectbox("Estado", ["activo", "vencido"])

        submitted = st.form_submit_button("Cargar")

        if submitted:
            nueva_fila = [usuario, str(fecha), dias, precio, estado]
            sheet.append_row(nueva_fila)
            st.success("✅ Publicidad registrada correctamente.")

else:
    login()
