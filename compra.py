import base64
from datetime import datetime
from zoneinfo import ZoneInfo
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
CSV_PATH = "assets/registros_compras.csv"


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
                "No se encontraron alumnos en la columna B (a partir de la fila 10) en las hojas.",
            )

        return datos_grupos, None

    except Exception as e:
        return None, f"Error al procesar el archivo Excel: {str(e)}"


def obtener_fecha_hora_actual():
    """Obtiene la fecha y hora exacta ajustada a la zona horaria de México."""
    try:
        zona_mexico = ZoneInfo("America/Mexico_City")
        return datetime.now(zona_mexico).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d/%m/%Y %H:%M")


def obtener_siguiente_folio():
    """Calcula el folio con formato AAAAMMDD-IPE-001 con continuidad diaria."""
    try:
        zona_mexico = ZoneInfo("America/Mexico_City")
        hoy_str = datetime.now(zona_mexico).strftime("%Y%m%d")
    except Exception:
        hoy_str = datetime.now().strftime("%Y%m%d")

    prefijo_base = f"{hoy_str}-IPE-"
    siguiente_secuencia = 1

    if os.path.exists(CSV_PATH):
        try:
            df_reg = pd.read_csv(CSV_PATH)
            if "Folio" in df_reg.columns and not df_reg.empty:
                folios_hoy = df_reg[
                    df_reg["Folio"].astype(str).str.startswith(prefijo_base)
                ]
                if not folios_hoy.empty:
                    secuencias = []
                    for f in folios_hoy["Folio"]:
                        try:
                            num = int(str(f).split("-")[-1])
                            secuencias.append(num)
                        except Exception:
                            pass
                    if secuencias:
                        siguiente_secuencia = max(secuencias) + 1
        except Exception:
            pass

    return f"{prefijo_base}{siguiente_secuencia:03d}"


def generar_ticket_pdf(datos_compra, folio):
    """Genera el ticket en PDF con tamaño físico de 48mm x 250mm y QR abajo."""
    os.makedirs(FOLIOS_DIR, exist_ok=True)
    pdf_path = os.path.join(FOLIOS_DIR, f"ticket_{folio.replace('/', '-')}.pdf")

    ancho_ticket = 48 * mm
    alto_ticket = 250 * mm

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=(ancho_ticket, alto_ticket),
        rightMargin=2 * mm,
        leftMargin=2 * mm,
        topMargin=4 * mm,
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

    # Logo arriba centrado
    if os.path.exists(LOGO_PATH):
        try:
            img_logo = Image(LOGO_PATH, width=18 * mm, height=7 * mm)
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
    desc_str = datos_compra["Concepto"][:10].ljust(10)
    precio_str = f"${datos_compra['Importe']:.2f}".rjust(6)
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

    # Código QR abajo centrado en el PDF
    if os.path.exists(QR_PATH):
        try:
            img_qr = Image(QR_PATH, width=18 * mm, height=18 * mm)
            img_qr.hAlign = "CENTER"
            story.append(img_qr)
        except Exception:
            pass

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
        concepto = st.text_input(
            "Concepto:", value="Fotografía Navidad 2026", disabled=True
        )
        importe = st.number_input(
            "Importe ($):", value=350.0, format="%.2f", disabled=True
        )

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
            fecha_hora_actual = obtener_fecha_hora_actual()
            st.session_state["pending_compra"] = {
                "Alumno": nombre_alumno,
                "Grupo": grupo_seleccionado,
                "Concepto": "Fotografía Navidad 2026",
                "Importe": 350.0,
                "Atendio": atendio,
                "Fecha": fecha_hora_actual,
            }
            st.session_state["show_confirm"] = True

    if st.session_state.get("show_confirm", False):
        st.warning("⚠️ ¿Está seguro de confirmar y registrar esta compra?")
        col_si, col_no = st.columns(2)

        with col_si:
            if st.button("Sí, Confirmar"):
                datos = st.session_state["pending_compra"]

                folio = obtener_siguiente_folio()
                datos["Folio"] = folio

                os.makedirs("assets", exist_ok=True)
                if os.path.exists(CSV_PATH):
                    df_reg = pd.read_csv(CSV_PATH)
                    df_reg = pd.concat(
                        [df_reg, pd.DataFrame([datos])], ignore_index=True
                    )
                else:
                    df_reg = pd.DataFrame([datos])
                df_reg.to_csv(CSV_PATH, index=False)

                pdf_path = generar_ticket_pdf(datos, folio)
                st.success(f"¡Compra realizada con éxito! Folio asignado: #{folio}")
                st.session_state["show_confirm"] = False

                lineas = []
                lineas.append("==================")
                lineas.append("   FOTOGRAFÍA   ")
                lineas.append("  NAVIDAD 2026  ")
                lineas.append("==================")
                lineas.append("Ticket: #" + folio)
                lineas.append("F/H: " + datos["Fecha"])
                lineas.append("Cliente:")
                lineas.append(datos["Alumno"])
                lineas.append("Grupo: " + datos["Grupo"])
                lineas.append("------------------")
                lineas.append("CANT DESCRIPCIÓN  P.UNIT")
                lineas.append("------------------")

                cant_str = "1".ljust(3)
                desc_str = datos["Concepto"][:10].ljust(10)
                precio_str = f"${datos['Importe']:.2f}".rjust(6)

                lineas.append(f"{cant_str} {desc_str} {precio_str}")
                lineas.append("------------------")

                subtotal = datos["Importe"]
                lineas.append(
                    f"TOTAL: " + f"${subtotal:.2f}".rjust(11)
                )
                lineas.append("==================")
                lineas.append("Atendió:")
                lineas.append(datos["Atendio"])
                lineas.append("Conserve su ticket")
                lineas.append("para cualquier")
                lineas.append("aclaración.")
                lineas.append("¡Vuelva pronto!")
                lineas.append("==================")

                texto_ticket_html = "\n".join(lineas)

                logo_base64 = obtener_imagen_base64(LOGO_PATH)
                qr_base64 = obtener_imagen_base64(QR_PATH)

                html_ticket_preview = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                  @media print {{
                    html, body {{
                      width: 48mm !important;
                      max-width: 48mm !important;
                      margin: 0 !important;
                      padding: 0 !important;
                      background: #fff !important;
                    }}
                    @page {{
                      size: 48mm 250mm;
                      margin: 0mm;
                    }}
                    .btn-print {{ display: none !important; }}
                    .ticket-card {{ box-shadow: none !important; padding: 0 !important; width: 48mm !important; }}
                  }}
                  body {{
                    font-family: "Courier New", Courier, monospace;
                    background: #f8f9fa;
                    margin: 0;
                    padding: 5px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                  }}
                  .ticket-card {{
                    background: #ffffff;
                    width: 48mm;
                    padding: 6px;
                    box-sizing: border-box;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                    border-radius: 4px;
                    text-align: center;
                  }}
                  .logo-container {{
                    margin-bottom: 6px;
                    display: flex;
                    justify-content: center;
                  }}
                  .logo-container img {{
                    max-width: 18mm;
                    height: auto;
                    display: block;
                  }}
                  .qr-container {{
                    margin-top: 8px;
                    margin-bottom: 4px;
                    display: flex;
                    justify-content: center;
                  }}
                  .qr-container img {{
                    width: 18mm;
                    height: 18mm;
                    display: block;
                  }}
                  pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    margin: 0 auto;
                    padding: 0;
                    font-family: inherit;
                    font-size: 10.5px;
                    font-weight: bold;
                    line-height: 1.2;
                    display: inline-block;
                    text-align: left;
                    color: #000;
                  }}
                  .btn-print {{
                    display: block;
                    width: 100%;
                    margin-top: 10px;
                    background: #000;
                    color: #fff;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                    font-size: 12px;
                    cursor: pointer;
                    border-radius: 4px;
                    text-align: center;
                  }}
                  .btn-print:hover {{
                    background: #333;
                  }}
                </style>
                </head>
                <body>
                  <div class="ticket-card">
                    <div class="logo-container">
                      {f'<img src="{logo_base64}" alt="Logo">' if logo_base64 else ''}
                    </div>
                    <pre>{texto_ticket_html}</pre>
                    <div class="qr-container">
                      {f'<img src="{qr_base64}" alt="QR">' if qr_base64 else ''}
                    </div>
                    <button class="btn-print" onclick="window.print();">🖨️ Imprimir Ticket</button>
                  </div>
                </body>
                </html>
                """

                st.markdown("### 🖨️ Vista Previa del Ticket (48x250 mm)")
                st.components.v1.html(html_ticket_preview, height=620, scrolling=True)

        with col_no:
            if st.button("No, Regresar"):
                st.info("Captura cancelada. Puede modificar los datos.")
                st.session_state["show_confirm"] = False
                st.rerun()
