import base64
import os
import pandas as pd
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

EXCEL_PATH = "assets/alumnosprimaria.xlsx"
FOLIOS_DIR = "assets/folios"
LOGO_PATH = "assets/logo.png"
QR_PATH = "assets/qr_ticket.png"


@st.cache_data
def cargar_alumnos_por_grupos():
  """Carga los alumnos por cada hoja (grupo), leyendo estrictamente

  desde la columna B (índice 1) a partir de la fila 10 (índice 9 en base 0)
  hasta la última fila existente.
  """
  if not os.path.exists(EXCEL_PATH):
    return None, f"No se encontró el archivo de Excel en la ruta: {EXCEL_PATH}"

  try:
    xls = pd.ExcelFile(EXCEL_PATH)
    todas_hojas = xls.sheet_names
    datos_grupos = {}

    for hoja in todas_hojas:
      df_hoja = pd.read_excel(EXCEL_PATH, sheet_name=hoja, header=None)

      if df_hoja.shape[0] >= 10 and df_hoja.shape[1] > 1:
        columna_b = df_hoja.iloc[9:, 1]

        lista_alumnos = []
        for val in columna_b:
          if pd.notna(val):
            nombre_limpio = str(val).strip()
            if nombre_limpio and nombre_limpio.lower() not in [
                "nan",
                "nombre",
                "alumnos",
                "none",
                "alumno",
                "nombres",
            ]:
              lista_alumnos.append(nombre_limpio)

        if lista_alumnos:
          datos_grupos[str(hoja)] = sorted(list(set(lista_alumnos)))

    if not datos_grupos:
      return (
          None,
          "No se encontraron alumnos en la columna B (a partir de la fila 10)"
          " en las hojas.",
      )

    return datos_grupos, None

  except Exception as e:
    return None, f"Error al procesar el archivo Excel: {str(e)}"


def generar_ticket_pdf(datos_compra, folio):
  """Genera el ticket en PDF con tamaño físico exacto de ticket térmico (80mm x 150mm)."""
  os.makedirs(FOLIOS_DIR, exist_ok=True)
  pdf_path = os.path.join(FOLIOS_DIR, f"ticket_{folio}.pdf")

  # Tamaño de papel térmico estándar de 80mm de ancho por 150mm de alto
  ancho_ticket = 80 * mm
  alto_ticket = 150 * mm

  doc = SimpleDocTemplate(
      pdf_path,
      pagesize=(ancho_ticket, alto_ticket),
      rightMargin=3 * mm,
      leftMargin=3 * mm,
      topMargin=4 * mm,
      bottomMargin=4 * mm,
  )

  story = []
  styles = getSampleStyleSheet()

  style_mono_centro = ParagraphStyle(
      "TicketCentro",
      parent=styles["Normal"],
      fontName="Courier-Bold",
      fontSize=9.5,
      leading=12,
      alignment=1,
      textColor="#000000",
  )

  style_mono_izq = ParagraphStyle(
      "TicketIzquierda",
      parent=styles["Normal"],
      fontName="Courier-Bold",
      fontSize=9.5,
      leading=12,
      alignment=0,
      textColor="#000000",
  )

  # Cabecera superior: Logo (reducido 25%) y QR (aumentado 25%)
  elementos_cabecera = []
  if os.path.exists(LOGO_PATH):
    try:
      img_logo = Image(LOGO_PATH, width=18 * mm, height=6.5 * mm)
      img_logo.hAlign = "CENTER"
      elementos_cabecera.append(img_logo)
    except Exception:
      elementos_cabecera.append("")
  else:
    elementos_cabecera.append("")

  if os.path.exists(QR_PATH):
    try:
      img_qr = Image(QR_PATH, width=20 * mm, height=20 * mm)
      img_qr.hAlign = "CENTER"
      elementos_cabecera.append(img_qr)
    except Exception:
      elementos_cabecera.append("")
  else:
    elementos_cabecera.append("")

  tabla_cabecera = Table([elementos_cabecera], colWidths=[42 * mm, 26 * mm])
  tabla_cabecera.setStyle(
      TableStyle([
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
      ])
  )
  story.append(tabla_cabecera)
  story.append(Spacer(1, 4))

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

  doc.build(story)
  return pdf_path


def obtener_imagen_base64(ruta_imagen):
  if os.path.exists(ruta_imagen):
    with open(ruta_imagen, "rb") as f:
      encoded = base64.b64encode(f.read()).decode("utf-8")
      if ruta_imagen.endswith(".png"):
        return f"data:image/png;base64,{encoded}"
      elif ruta_imagen.endswith(".jpg") or ruta_imagen.endswith(".jpeg"):
        return f"data:image/jpeg;base64,{encoded}"
  return ""


def app():
  st.subheader("📝 Registrar Nueva Compra")

  dic_grupos, error = cargar_alumnos_por_grupos()
  if error:
    st.error(f"Error al cargar el archivo de Excel: {error}")
    return

  lista_grupos = sorted(list(dic_grupos.keys()))

  def actualizar_grupo():
    st.session_state["alumno_seleccionado"] = None

  grupo_seleccionado = st.selectbox(
      "Seleccione el Grupo:",
      options=lista_grupos,
      index=None,
      placeholder="Seleccione un grupo...",
      key="grupo_seleccionado",
      on_change=actualizar_grupo,
  )

  lista_alumnos = (
      dic_grupos.get(grupo_seleccionado, []) if grupo_seleccionado else []
  )
  nombre_alumno = st.selectbox(
      "Nombre del alumno:",
      options=lista_alumnos,
      index=None,
      placeholder=(
          "Seleccione primero un grupo..."
          if not grupo_seleccionado
          else "Seleccione un alumno..."
      ),
      key="alumno_seleccionado",
  )

  with st.form("form_compra_detalles"):
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
        index=None,
        placeholder="Seleccione quién atiende...",
    )

    submitted = st.form_submit_button("Confirmar Compra")

  if submitted:
    if not grupo_seleccionado:
      st.warning("⚠️ Por favor seleccione un grupo.")
    elif not nombre_alumno:
      st.warning("⚠️ Por favor seleccione un alumno.")
    elif not atendio:
      st.warning("⚠️ Por favor seleccione quién atendió.")
    else:
      st.session_state["pending_compra"] = {
          "Alumno": nombre_alumno,
          "Grupo": grupo_seleccionado,
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

        lineas = []
        lineas.append("================================")
        lineas.append("    FOTOGRAFÍA NAVIDAD 2026   ")
        lineas.append("   ¡Gracias por su compra!    ")
        lineas.append("================================")
        lineas.append("Ticket: #" + folio)
        lineas.append("Fecha: " + datos["Fecha"])
        lineas.append("Cliente: " + datos["Alumno"])
        lineas.append("Grupo: " + datos["Grupo"])
        lineas.append("--------------------------------")
        lineas.append("CANT DESCRIPCIÓN          P.UNIT")
        lineas.append("            TOTAL               ")
        lineas.append("--------------------------------")

        cant_str = "1".ljust(3)
        desc_str = datos["Concepto"][:14].ljust(14)
        precio_str = f"${datos['Importe']:.2f}".rjust(8)
        total_str = f"${datos['Importe']:.2f}".rjust(12)

        lineas.append(f"{cant_str} {desc_str} {precio_str}")
        lineas.append(f"            {total_str}")
        lineas.append("--------------------------------")

        subtotal = datos["Importe"]
        lineas.append(
            f"SUBTOTAL:         " + f"${subtotal:.2f}".rjust(13)
        )
        lineas.append(
            f"TOTAL A PAGAR:    " + f"${subtotal:.2f}".rjust(13)
        )
        lineas.append("================================")
        lineas.append("   Atendió: " + datos["Atendio"])
        lineas.append("  Conserve su ticket para       ")
        lineas.append("   cualquier aclaración.        ")
        lineas.append("       ¡Vuelva pronto!          ")
        lineas.append("================================")

        texto_ticket_html = "\n".join(lineas)

        logo_base64 = obtener_imagen_base64(LOGO_PATH)
        qr_base64 = obtener_imagen_base64(QR_PATH)

        # CSS con @page forzado a 80mm por defecto para cualquier navegador/ordenador
        html_ticket_preview = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                  @media print {{
                    html, body {{
                      width: 80mm !important;
                      max-width: 80mm !important;
                      margin: 0 !important;
                      padding: 0 !important;
                    }}
                    @page {{
                      size: 80mm 150mm;
                      margin: 0mm;
                    }}
                    .btn-print {{ display: none !important; }}
                  }}
                  body {{
                    font-family: "Courier New", Courier, monospace;
                    font-size: 14px;
                    font-weight: bold;
                    color: #000;
                    width: 80mm;
                    margin: 0 auto;
                    padding: 5px;
                    background: #fff;
                    text-align: center;
                  }}
                  .header-container {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    width: 100%;
                    margin-bottom: 5px;
                    padding: 0 5px;
                    box-sizing: border-box;
                  }}
                  .logo-container img {{
                    max-width: 24mm;
                    height: auto;
                    display: block;
                  }}
                  .qr-container img {{
                    width: 22.5mm;
                    height: 22.5mm;
                    display: block;
                  }}
                  pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    margin: 0 auto;
                    padding: 0;
                    font-family: inherit;
                    font-size: inherit;
                    font-weight: bold;
                    line-height: 1.2;
                    display: inline-block;
                    text-align: left;
                  }}
                  .btn-print {{
                    display: block;
                    width: 90%;
                    margin: 15px auto;
                    background: #000;
                    color: #fff;
                    padding: 10px;
                    border: none;
                    font-weight: bold;
                    font-size: 14px;
                    cursor: pointer;
                    border-radius: 4px;
                  }}
                </style>
                </head>
                <body>
                  <div class="header-container">
                    <div class="logo-container">
                      {f'<img src="{logo_base64}" alt="Logo">' if logo_base64 else ''}
                    </div>
                    <div class="qr-container">
                      {f'<img src="{qr_base64}" alt="QR">' if qr_base64 else ''}
                    </div>
                  </div>
                  <pre>{texto_ticket_html}</pre>
                  <button class="btn-print" onclick="window.print();">🖨️ Imprimir Ticket</button>
                </body>
                </html>
                """

        st.markdown("### 🖨️ Vista Previa del Ticket Térmico")
        st.components.v1.html(html_ticket_preview, height=600, scrolling=True)

    with col_no:
      if st.button("No, Regresar"):
        st.info("Captura cancelada. Puede modificar los datos.")
        st.session_state["show_confirm"] = False
        st.rerun()
