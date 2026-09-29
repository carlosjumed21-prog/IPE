import os
import pandas as pd
import streamlit as st

FOLIOS_DIR = "assets/folios"
REGISTROS_PATH = "assets/registros_compras.csv"


def app():
  st.subheader("🔍 Consultar Compras y Tickets")

  if not os.path.exists(REGISTROS_PATH):
    st.info("Aún no existen registros de compras guardados.")
    return

  df_registros = pd.read_csv(REGISTROS_PATH)

  # Cuadro de búsqueda general (fecha, folio, nombre, etc.)
  busqueda = st.text_input(
      "Ingrese Folio, Fecha, Nombre del alumno o cualquier dato para buscar:"
  )

  if busqueda:
    # Filtrar filas que contengan el texto en cualquier columna
    mask = df_registros.apply(
        lambda row: row.astype(str).str.contains(busqueda, case=False).any(),
        axis=1,
    )
    df_filtrado = df_registros[mask]
  else:
    df_filtrado = df_registros

  if df_filtrado.empty:
    st.warning("No se encontraron registros con los datos proporcionados.")
    return

  st.dataframe(df_filtrado, use_container_width=True)

  st.markdown("### 🖨️ Tickets Disponibles para Impresión")

  # Seleccionar un folio específico de los resultados filtrados para ver/imprimir su ticket
  folios_encontrados = df_filtrado["Folio"].astype(str).tolist()
  folio_seleccionado = st.selectbox(
      "Seleccione el Folio del ticket a visualizar:", options=folios_encontrados
  )

  if folio_seleccionado:
    pdf_path = os.path.join(FOLIOS_DIR, f"ticket_{folio_seleccionado}.pdf")

    if os.path.exists(pdf_path):
      st.success(f"Ticket encontrado para el Folio: {folio_seleccionado}")
      with open(pdf_path, "rb") as f:
        st.download_button(
            label=f"📄 Descargar / Imprimir Ticket (Folio {folio_seleccionado})",
            data=f,
            file_name=f"ticket_{folio_seleccionado}.pdf",
            mime="application/pdf",
        )
    else:
      st.error(
          f"No se encontró el archivo PDF del ticket para el folio"
          f" {folio_seleccionado} en `{FOLIOS_DIR}`."
      )
