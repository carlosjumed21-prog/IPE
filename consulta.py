from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

SHEET_URL = "https://docs.google.com/spreadsheets/d/1O8kzQuR1Um2BbVO5rcEDbgZWauSPto_2uI8rM_JVdUg/edit?usp=sharing"


@st.cache_data(ttl=60)
def cargar_todos_los_registros_gsheets():
    """Carga y consolida todas las pestañas (grupos) del Google Sheet oficial usando credenciales nativas."""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        sh = client.open_by_url(SHEET_URL)
        worksheets = sh.worksheets()
        datos_consolidados = []

        for ws in worksheets:
            nombre_grupo = ws.title
            registros = ws.get_all_values()

            if len(registros) > 1:
                # Omitimos el encabezado (fila 1) y recorremos las filas de datos
                filas = registros[1:]
                for fila in filas:
                    # Validamos que al menos tenga datos en las columnas principales
                    if len(fila) >= 6 and str(fila[1]).strip() != "":
                        datos_consolidados.append({
                            "Grupo": nombre_grupo,
                            "#": fila[0],
                            "Folio": fila[1],
                            "Nombre de alumno": fila[2],
                            "Fecha y Hora": fila[3],
                            "Importe": fila[4],
                            "Atendió": fila[5],
                        })

        if not datos_consolidados:
            return pd.DataFrame(
                columns=[
                    "Grupo",
                    "#",
                    "Folio",
                    "Nombre de alumno",
                    "Fecha y Hora",
                    "Importe",
                    "Atendió",
                ]
            )

        return pd.DataFrame(datos_consolidados)
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None


def app():
    st.subheader("🔍 Consulta de Ventas y Tickets")
    st.markdown(
        "Busca y filtra los registros sincronizados en el Google Sheet oficial."
    )

    with st.spinner("Sincronizando datos desde Google Sheets..."):
        df_ventas = cargar_todos_los_registros_gsheets()

    if df_ventas is None or df_ventas.empty:
        st.info(
            "Aún no hay registros en las hojas de Google Sheets o no se pudo"
            " establecer conexión."
        )
        return

    # Filtros de búsqueda en la interfaz
    col1, col2 = st.columns(2)

    with col1:
        grupos_disponibles = ["TODOS"] + sorted(
            list(df_ventas["Grupo"].unique())
        )
        filtro_grupo = st.selectbox(
            "Filtrar por Grupo:", options=grupos_disponibles
        )

    with col2:
        busqueda_texto = st.text_input(
            "Buscar por Alumno o Folio:",
            placeholder="Ej. Juan o 20260928-IPE-001",
        )

    # Aplicar filtros
    df_filtrado = df_ventas.copy()

    if filtro_grupo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Grupo"] == filtro_grupo]

    if busqueda_texto.strip():
        texto = busqueda_texto.strip().lower()
        df_filtrado = df_filtrado[
            df_filtrado["Nombre de alumno"].str.lower().str.contains(texto)
            | df_filtrado["Folio"].str.lower().str.contains(texto)
        ]

    st.markdown("---")
    st.markdown(f"**Total de registros encontrados:** {len(df_filtrado)}")

    # Mostrar tabla interactiva
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # Opción para refrescar caché y recargar datos de la nube
    if st.button("🔄 Actualizar Datos desde Google Sheets"):
        st.cache_data.clear()
        st.success("¡Datos actualizados correctamente!")
        st.rerun()
