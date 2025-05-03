import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la página
st.set_page_config(layout="wide", page_title="Gestión de Publicidad")

# Conexión con Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPE)
gc = gspread.authorize(CREDS)
sheet = gc.open_by_key("19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w")
worksheet = sheet.worksheet("Ingreso")

# Cargar datos
def cargar_datos():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')  # Manejo seguro de fechas
    return df

# Guardar nuevos datos
def guardar_datos(usuario, fecha, dias, precio):
    worksheet.append_row([usuario, fecha.strftime("%d/%m/%Y"), dias, precio, "Activo"])

# Actualizar estado a "Vencido"
def marcar_vencido(index, df):
    cell = worksheet.find(df.loc[index, "Usuario"])
    worksheet.update_cell(cell.row, 5, "Vencido")

# Mostrar publicidades activas
def mostrar_dashboard():
    df = cargar_datos()
    st.subheader("📢 Publicidades Activas")
    activas = df[df["Estado"] == "Activo"].copy()

    for index, row in activas.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        col1.markdown(f"**👤 Usuario:** {row['Usuario']}")
        col2.markdown(f"📅 **Fecha:** {row['Fecha'].strftime('%d/%m/%Y')}")
        col3.markdown(f"📆 **Días:** {row['Días']}")
        if col4.button("❌ Marcar vencido", key=f"vencido_{index}"):
            marcar_vencido(index, df)
            st.experimental_rerun()

# Formulario de carga
def formulario():
    st.subheader("➕ Cargar nueva publicidad")
    with st.form("carga_formulario", clear_on_submit=False):
        usuario = st.text_input("Usuario")
        fecha = st.date_input("Fecha", value=datetime.date.today(), format="DD/MM/YYYY")
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio $", min_value=0, step=100)
        col1, col2 = st.columns(2)
        submit = col1.form_submit_button("Guardar")
        clear = col2.form_submit_button("Limpiar")

        if submit:
            if usuario and dias > 0 and precio > 0:
                guardar_datos(usuario, fecha, dias, precio)
                st.success("✅ Publicidad cargada correctamente.")
                st.experimental_rerun()
            else:
                st.warning("⚠️ Completá todos los campos.")
        if clear:
            st.experimental_rerun()

# Mostrar resumen de ingresos
def resumen_ingresos():
    df = cargar_datos()
    st.subheader("💰 Resumen de Ingresos")
    df['Mes'] = df['Fecha'].dt.strftime('%B %Y')
    resumen = df.groupby('Mes')['Precio $'].sum().reset_index()

    resumen["Precio $"] = resumen["Precio $"].apply(lambda x: f"${int(x):,}".replace(",", "."))

    st.dataframe(resumen, use_container_width=True)

# Ejecutar componentes
st.markdown("<h1 style='text-align: center;'>Gestión de Publicidades</h1>", unsafe_allow_html=True)
mostrar_dashboard()
st.markdown("---")
formulario()
st.markdown("---")
resumen_ingresos()
