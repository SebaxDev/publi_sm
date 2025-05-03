import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Publicidades", layout="wide")

# --- AUTENTICACIÓN GOOGLE SHEETS ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(creds)
SHEET_ID = "19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w"
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet("Base")

# --- FUNCIÓN PARA CARGAR DATOS ---
def cargar_datos():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
    return df

# --- FUNCIÓN PARA AGREGAR NUEVO REGISTRO ---
def agregar_registro(usuario, fecha, dias, precio):
    worksheet.append_row([usuario, fecha.strftime("%d/%m/%Y"), dias, precio, "Activo"])

# --- FUNCIÓN PARA MARCAR COMO VENCIDO ---
def marcar_vencido(index):
    cell = worksheet.cell(index + 2, 5)  # Columna "Estado"
    worksheet.update_cell(cell.row, 5, "Vencido")

# --- DASHBOARD PRINCIPAL ---
def mostrar_dashboard():
    st.title("📢 Gestión de Publicidades")

    df = cargar_datos()

    st.subheader("🔎 Publicidades Activas")
    activas = df[df["Estado"] == "Activo"]
    if activas.empty:
        st.info("No hay publicidades activas.")
    else:
        for i, row in activas.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            col1.markdown(f"**{row['Usuario']}**")
            col2.markdown(f"📅 {row['Fecha'].strftime('%d/%m/%Y')}")
            col3.markdown(f"📆 {row['Días']} días")
            if col4.button("❌ Marcar vencido", key=f"vencer_{i}"):
                marcar_vencido(i)
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("➕ Nueva Publicidad")
    with st.form("formulario"):
        usuario = st.text_input("Usuario")
        fecha = st.date_input("Fecha", value=datetime.date.today())
        dias = st.number_input("Días contratados", min_value=1, step=1)
        precio = st.number_input("Precio ($)", min_value=0, step=100)

        col1, col2 = st.columns([2, 1])
        enviar = col1.form_submit_button("Guardar")
        limpiar = col2.form_submit_button("Limpiar")

        if enviar:
            if usuario and dias > 0:
                agregar_registro(usuario, fecha, dias, precio)
                st.success("Publicidad cargada correctamente.")
                st.experimental_rerun()
            else:
                st.error("Por favor, completá todos los campos.")

    st.markdown("---")
    st.subheader("💰 Resumen de Ingresos")
    if not df.empty:
        df['Mes'] = df['Fecha'].dt.to_period('M')
        resumen = df.groupby('Mes')['Precio'].sum().reset_index()
        resumen['Mes'] = resumen['Mes'].astype(str)
        resumen['Precio'] = resumen['Precio'].apply(lambda x: f"${int(x):,}".replace(",", "."))
        st.dataframe(resumen.rename(columns={"Mes": "Mes", "Precio": "Total ($)"}), use_container_width=True)

# --- EJECUTAR APP ---
if __name__ == "__main__":
    mostrar_dashboard()
