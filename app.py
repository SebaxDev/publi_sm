import streamlit as st
import pandas as pd
import datetime
import gspread
import uuid
from google.oauth2.service_account import Credentials

# Configuración de la página
st.set_page_config(layout="wide", page_title="Gestión de Publicidad")

# Conexión con Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPE)
gc = gspread.authorize(CREDS)
sheet = gc.open_by_key("19xOkLYWxB3_Y1zVGV8qKCH8BrcujNktV3-jr1Q9A1-w")
worksheet = sheet.worksheet("Ingreso")

# --- Funciones ---

def cargar_datos():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.astype(str).str.strip()
    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    return df

def guardar_datos(usuario, fecha, dias, precio):
    id_unico = str(uuid.uuid4())
    worksheet.append_row([
        usuario,
        fecha.strftime("%d/%m/%Y"),
        dias,
        precio,
        "Activo",
        id_unico
    ])

def marcar_vencido(index, df):
    try:
        id_unico = df.loc[index, "ID"]
        celda_id = worksheet.find(id_unico)
        if celda_id:
            fila = celda_id.row
            worksheet.update_cell(fila, 5, "Vencido")
        else:
            st.error("❌ No se encontró el ID único en la hoja.")
    except Exception as e:
        st.error(f"❌ Error al marcar como vencido: {e}")

def limpiar_precio(valor):
    try:
        numero = float(str(valor).replace("$", "").replace(".", "").replace(",", "").strip())
        return f"${int(numero):,}".replace(",", ".")
    except:
        return "N/D"

# --- Secciones ---

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
                st.session_state["form_guardado"] = True
                st.rerun()
            else:
                st.warning("⚠️ Completá todos los campos.")

        if clear:
            st.session_state["form_limpio"] = True
            st.rerun()

    if st.session_state.get("form_guardado"):
        st.success("✅ Publicidad cargada correctamente.")
        del st.session_state["form_guardado"]

    if st.session_state.get("form_limpio"):
        st.info("🧼 Formulario limpiado.")
        del st.session_state["form_limpio"]

def mostrar_dashboard():
    df = cargar_datos()
    if "Estado" not in df.columns or "Usuario" not in df.columns:
        st.error("Faltan las columnas necesarias ('Estado', 'Usuario') en la hoja de cálculo.")
        return

    st.subheader("📢 Publicidades Activas")
    activas = df[df["Estado"] == "Activo"].copy()

    for index, row in activas.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        col1.markdown(f"**👤** {row['Usuario']}")
        col2.markdown(f"📅 **Fecha:** {row['Fecha'].strftime('%d/%m/%Y') if pd.notnull(row['Fecha']) else 'Fecha inválida'}")
        col3.markdown(f"📆 **Días:** {row.get('Días', 'N/D')}")
        if col4.button("❌ Marcar vencido", key=f"vencido_{index}"):
            marcar_vencido(index, df)
            st.rerun()

def resumen_ingresos():
    df = cargar_datos()
    if "Estado" not in df.columns or "Usuario" not in df.columns or "Precio $" not in df.columns or "Fecha" not in df.columns:
        st.error("❌ Las columnas necesarias no se encuentran en el archivo.")
        return

    activos = df.copy()
    if activos.empty:
        st.warning("⚠️ No hay registros disponibles.")
        return

    activos["Precio $"] = activos["Precio $"].astype(str).str.replace("$", "").str.replace(".", "").str.replace(",", "")
    activos["Precio $"] = pd.to_numeric(activos["Precio $"], errors="coerce").fillna(0)

    resumen_usuario = activos.groupby("Usuario", as_index=False)["Precio $"].sum()
    resumen_usuario = resumen_usuario.sort_values(by="Precio $", ascending=False).head(10)
    resumen_usuario["Precio $"] = resumen_usuario["Precio $"].apply(limpiar_precio)

    st.subheader("🏆 Top 10 Usuarios por Ingresos")
    st.dataframe(resumen_usuario)

    activos["Mes/Año"] = activos["Fecha"].dt.strftime("%m/%Y")
    resumen_mes = activos.groupby("Mes/Año", as_index=False)["Precio $"].sum()
    resumen_mes["Precio $"] = resumen_mes["Precio $"].apply(limpiar_precio)

    st.subheader("📆 Total de ingresos por mes")
    st.dataframe(resumen_mes)

    activos["Año"] = activos["Fecha"].dt.year
    resumen_anio = activos.groupby("Año", as_index=False)["Precio $"].sum()
    resumen_anio["Precio $"] = resumen_anio["Precio $"].apply(limpiar_precio)

    st.subheader("🗓️ Total de ingresos por año")
    st.dataframe(resumen_anio)

# --- Menú horizontal centrado y sin etiqueta ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
    }
    div[data-testid="stRadio"] > label {
        display: none;
    }
    .centered-radio {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True)

menu = st.radio(
    label="",
    options=["Inicio", "Activos", "Ingresos"],
    horizontal=True,
    key="menu_principal")

if menu == "Inicio":
    formulario()
elif menu == "Activos":
    mostrar_dashboard()
elif menu == "Ingresos":
    resumen_ingresos()
