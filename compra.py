import os
import pandas as pd
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
import streamlit as st

EXCEL_PATH = "assets/alumnosprimaria.xlsx"
FOLIOS_DIR = "assets/folios"
LOGO_PATH = "assets/logo.png"
QR_PATH = "assets/qr_ticket.png"


@st.cache_data
def cargar_alumnos_por_pestanas():
  """Carga los alumnos desde las hojas del 1 al 15, leyendo desde la columna 10 (J) en adelante.

  Retorna un DataFrame consolidado con columnas: ['Alumno', 'Grupo']
  """
  if not os.path.exists(EXCEL_PATH):
    return (
        None,
        f"No se encontró el archivo de Excel en la ruta: {EXCEL_PATH}",
    )

  try:
    xls = pd.ExcelFile(EXCEL_PATH)
    todas_hojas = xls.sheet_names
    lista_registros = []

    # Iteramos sobre las hojas (grupos del 1 al 15)
    for hoja in todas_hojas:
      df_hoja = pd.read_excel(EXCEL_PATH, sheet_name=hoja, header=None)

      # La columna 10 corresponde al índice 9 (A=0, B=1, ..., J=9)
      if df_hoja.shape[1] > 9:
        df_columnas_interes = df_hoja.iloc[:, 9:]

        for col in df_columnas_interes.columns:
          for val in df_columnas_interes[col].dropna():
            nombre_limpio = str(val).strip()
            if nombre_limpio and nombre_limpio.lower() not in [
                "nan",
                "nombre",
                "alumnos",
                "none",
            ]:
              lista_registros.append(
                  {"Alumno": nombre_limpio, "Grupo": str(hoja)}
              )

    if not lista_registros:
      return (
          None,
          "No se encontraron alumnos a partir de la columna 10 en las hojas.",
      )

    df_consolidado = pd.DataFrame(lista_registros)
    df_consolidado = df_consolidado.drop_duplicates(
        subset=["Alumno"]
    ).reset_index(drop=True)

    return df_consolidado, None

  except Exception as e:
    return None, f"Error al procesar el archivo Excel: {str(e)}"


def generar_ticket_pdf(datos_compra, folio):
  """Genera el ticket en PDF con formato térmico estricto de 80mm."""
  os.makedirs(FOLIOS_DIR, exist_ok=True)
  pdf_path = os.path.join(FOLIOS_DIR, f"ticket_{folio}.pdf")

  ancho_ticket = 80 * mm
  alto_ticket = 180 * mm

  doc = SimpleDocTemplate(
      pdf_path,
      pagesize=(ancho_ticket, alto_ticket),
      rightMargin=6 * mm,
      leftMargin=6 * mm,
      topMargin=6 * mm,
      bottomMargin=6 * mm,
  )

  story = []
  styles = getSampleStyleSheet()

  style_mono_centro = ParagraphStyle(
      "TicketCentro",
      parent=styles["Normal"],
      fontName="Courier-Bold",
      fontSize=8.5,
      leading=11,
      alignment=1,
      textColor="#000000",
  )

  style_mono_izq = ParagraphStyle(
      "TicketIzquierda",
      parent=styles["Normal"],
      fontName="Courier-Bold",
      fontSize=8.5,
      leading=11,
      alignment=0,
      textColor="#000000",
  )

  if os.path.exists(LOGO_PATH):
    try:
      img_logo = Image(LOGO_PATH, width=35 * mm, height=12 * mm)
      img_logo.hAlign = "CENTER"
      story.append(img_logo)
      story.append(Spacer(1, 4))
    except Exception:
      pass

  story.append(Paragraph("================================", style_mono_centro))
  story.append(Paragraph("    FOTOGRAFÍA NAVIDAD 2026   ", style_mono_centro))
  story.append(Paragraph("   ¡Gracias por su compra!    ", style_mono_centro))
  story.append(Paragraph("================================", style_mono_centro))

  story.append(Paragraph(f"Ticket: #{folio}", style_mono_izq))
  story.append(Paragraph(f"Fecha: {datos_compra['Fecha']}", style_mono_izq))
  story.append(Paragraph(f"Cliente: {datos_compra['Alumno']}", style_mono_izq))
  story.append(Paragraph(f"Grupo: {datos_compra['Grupo']}", style_mono_izq))
  story.append(Paragraph("--------------------------------", style_mono_centro))

  story.append(Paragraph("CANT DESCRIPCIÓN          P.UNIT", style_mono_izq))
  story.append(Paragraph("            TOTAL               ", style_mono_izq))
  story.append(Paragraph("--------------------------------", style_mono_centro))

  cant_str = "1".ljust(3)
  desc_str = datos_compra["Concepto"][:14].ljust(14)
  precio_str = f"${datos_compra['Importe']:.2f}".rjust(8)
  total_str = f"${datos_compra['Importe']:.2f}".rjust(12)

  story.append(Paragraph(f"{cant_str} {desc_str} {precio_str}", style_mono_izq))
  story.append(Paragraph(f"            {total_str}", style_mono_izq))
  story.append(Paragraph("--------------------------------", style_mono_centro))

  subtotal = datos_compra["Importe"]
  story.append(
      Paragraph(
          f"SUBTOTAL:         " + f"${subtotal:.2f}".rjust(13), style_mono_izq
      )
  )
  story.append(
      Paragraph(
          f"TOTAL A PAGAR:    " + f"${subtotal:.2f}".rjust(13), style_mono_izq
      )
  )
  story.append(Paragraph("================================", style_mono_centro))

  story.append(Paragraph("   Atendió: " + datos_compra["Atendio"], style_mono_izq))
  story.append(Spacer(1, 2))
  story.append(Paragraph("  Conserve su ticket para       ", style_mono_centro))
  story.append(Paragraph("   cualquier aclaración.        ", style_mono_centro))
  story.append(Paragraph("       ¡Vuelva pronto!          ", style_mono_centro))
  story.append(Paragraph("================================", style_mono_centro))
  story.append(Spacer(1, 6))

  if os.path.exists(QR_PATH):
    try:
      img_qr = Image(QR_PATH, width=24 * mm, height=24 * mm)
      img_qr.hAlign = "CENTER"
      story.append(img_qr)
    except Exception:
      pass

  doc.build(story)
  return pdf_path


def app():
  st.subheader("📝 Registrar Nueva Compra")

  df_alumnos, error = cargar_alumnos_por_pestanas()
  if error:
    st.error(f"Error al cargar el archivo de Excel: {error}")
    return

  with st.form("form_compra"):
    lista_nombres = sorted(df_alumnos["Alumno"].unique().tolist())
    nombre_alumno = st.selectbox(
        "Nombre del alumno:",
        options=lista_nombres,
        index=0 if lista_nombres else None,
    )

    grupo_asignado = ""
    if nombre_alumno:
      fila = df_alumnos[df_alumnos["Alumno"] == nombre_alumno]
      if not fila.empty:
        grupo_asignado = str(fila.iloc[0]["Grupo"])

    st.text_input("Grupo (Automático):", value=grupo_asignado, disabled=True)

    st.markdown("---")
    concepto = st.text_input("Concepto:", value="Fotografía Navidad 2026")
    importe = st.number_input("Importe ($):", value=350.0, format="%.2f")

    atendio = st.selectbox(
        "Quién atendió:",
        options=[
            "Victoria Garcia Valencia",
            "Jose Francisco Resendiz",
            "Grecia Ramirez Arenas",
        ],
    )

    submitted = st.form_submit_button("Confirmar Compra")

  if submitted:
    st.session_state["pending_compra"] = {
        "Alumno": nombre_alumno,
        "Grupo": grupo_asignado,
        "Concepto": concepto,
        "Importe": importe,
        "Atendio": atendio,
        "Fecha": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
    }
    st.session_state["show_confirm"] = True

  if st.session_state.get("show_confirm", False):
    st.warning("⚠️ ¿Está seguro de confirmar y registrar esta compra?")
    col_si, col_no = st.columns(2)

    with col_si:
      if st.button("Sí, Confirmar"):
        datos = st.session_state["pending_compra"]
        folio = pd.Timestamp.now().strftime("%Y%m%d%H%M%S")
        datos["Folio"] = folio

        csv_path = "assets/registros_compras.csv"
        os.makedirs("assets", exist_ok=True)
        if os.path.exists(csv_path):
          df_reg = pd.read_csv(csv_path)
          df_reg = pd.concat([df_reg, pd.DataFrame([datos])], ignore_index=True)
        else:
          df_reg = pd.DataFrame([datos])
        df_reg.to_csv(csv_path, index=False)

        pdf_path = generar_ticket_pdf(datos, folio)

        st.success(f"¡Compra realizada con éxito! Folio generado: {folio}")
        st.session_state["show_confirm"] = False

        with open(pdf_path, "rb") as f:
          st.download_button(
              label="🖨️ Imprimir Ticket Térmico (Descargar PDF)",
              data=f,
              file_name=f"ticket_{folio}.pdf",
              mime="application/pdf",
          )

    with col_no:
      if st.button("No, Regresar"):
        st.info("Captura cancelada. Puede modificar los datos.")
        st.session_state["show_confirm"] = False
        st.rerun()
