import os
import pandas as pd
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
import streamlit as st

EXCEL_PATH = "assets/datos_alumnos.xlsx"
FOLIOS_DIR = "assets/folios"
LOGO_PATH = "assets/logo.png"
QR_PATH = "assets/qr_ticket.png"


@st.cache_data
def cargar_datos_alumnos():
  """Carga los alumnos y su grupo desde la pestaña de alojamiento del Excel."""
  if not os.path.exists(EXCEL_PATH):
    return None, f"No se encontró el archivo en {EXCEL_PATH}"
  try:
    xls = pd.ExcelFile(EXCEL_PATH)
    hojas = xls.sheet_names
    hoja_alojamiento = (
        'alojamiento'
        if 'alojamiento' in [h.lower() for h in hojas]
        else hojas[0]
    )
    df = pd.read_excel(EXCEL_PATH, sheet_name=hoja_alojamiento)
    return df, None
  except Exception as e:
    return None, str(e)


def generar_ticket_pdf(datos_compra, folio):
  """Genera el ticket en PDF con formato térmico estricto de 80mm adaptado del script de Apps Script."""
  os.makedirs(FOLIOS_DIR, exist_ok=True)
  pdf_path = os.path.join(FOLIOS_DIR, f"ticket_{folio}.pdf")

  # Ancho estándar de ticket térmico: 80 mm (~226.77 puntos)
  ancho_ticket = 80 * mm
  alto_ticket = 180 * mm  # Altura dinámica suficiente para el contenido

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

  # Estilos tipográficos inspirados en la configuración CSS térmica (Courier / Monospace)
  style_mono_centro = ParagraphStyle(
      'TicketCentro',
      parent=styles['Normal'],
      fontName='Courier-Bold',
      fontSize=8.5,
      leading=11,
      alignment=1,  # Centrado
      textColor='#000000',
  )

  style_mono_izq = ParagraphStyle(
      'TicketIzquierda',
      parent=styles['Normal'],
      fontName='Courier-Bold',
      fontSize=8.5,
      leading=11,
      alignment=0,  # Izquierda
      textColor='#000000',
  )

  # 1. Imagen inicial (Logotipo institucional en assets/logo.png)
  if os.path.exists(LOGO_PATH):
    try:
      img_logo = Image(LOGO_PATH, width=35 * mm, height=12 * mm)
      img_logo.hAlign = 'CENTER'
      story.append(img_logo)
      story.append(Spacer(1, 4))
    except Exception:
      pass

  # Encabezado térmico
  story.append(
      Paragraph("================================", style_mono_centro)
  )
  story.append(Paragraph("    FOTOGRAFÍA NAVIDAD 2026   ", style_mono_centro))
  story.append(Paragraph("   ¡Gracias por su compra!    ", style_mono_centro))
  story.append(
      Paragraph("================================", style_mono_centro)
  )

  # Datos del ticket
  story.append(Paragraph(f"Ticket: #{folio}", style_mono_izq))
  story.append(Paragraph(f"Fecha: {datos_compra['Fecha']}", style_mono_izq))
  story.append(Paragraph(f"Cliente: {datos_compra['Alumno']}", style_mono_izq))
  story.append(Paragraph(f"Grupo: {datos_compra['Grupo']}", style_mono_izq))
  story.append(
      Paragraph("--------------------------------", style_mono_centro)
  )

  # Detalle de productos / conceptos
  story.append(
      Paragraph("CANT DESCRIPCIÓN          P.UNIT", style_mono_izq)
  )
  story.append(
      Paragraph("            TOTAL               ", style_mono_izq)
  )
  story.append(
      Paragraph("--------------------------------", style_mono_centro)
  )

  # Ítem de compra formateado como el script térmico
  cant_str = "1".ljust(3)
  desc_str = datos_compra["Concepto"][:14].ljust(14)
  precio_str = f"${datos_compra['Importe']:.2f}".rjust(8)
  total_str = f"${datos_compra['Importe']:.2f}".rjust(12)

  story.append(
      Paragraph(f"{cant_str} {desc_str} {precio_str}", style_mono_izq)
  )
  story.append(Paragraph(f"            {total_str}", style_mono_izq))
  story.append(
      Paragraph("--------------------------------", style_mono_centro)
  )

  # Totales
  subtotal = datos_compra["Importe"]
  story.append(
      Paragraph(
          f"SUBTOTAL:         "
          + f"${subtotal:.2f}".rjust(13),
          style_mono_izq,
      )
  )
  story.append(
      Paragraph(
          f"TOTAL A PAGAR:    "
          + f"${subtotal:.2f}".rjust(13),
          style_mono_izq,
      )
  )
  story.append(
      Paragraph("================================", style_mono_centro)
  )

  # Pie de ticket
  story.append(
      Paragraph("   Atendió: " + datos_compra["Atendio"], style_mono_izq)
  )
  story.append(Spacer(1, 2))
  story.append(
      Paragraph("  Conserve su ticket para       ", style_mono_centro)
  )
  story.append(
      Paragraph("   cualquier aclaración.        ", style_mono_centro)
  )
  story.append(
      Paragraph("       ¡Vuelva pronto!          ", style_mono_centro)
  )
  story.append(
      Paragraph("================================", style_mono_centro)
  )
  story.append(Spacer(1, 6))

  # 2. Código QR al final (leído desde assets/qr_ticket.png)
  if os.path.exists(QR_PATH):
    try:
      img_qr = Image(QR_PATH, width=24 * mm, height=24 * mm)
      img_qr.hAlign = 'CENTER'
      story.append(img_qr)
    except Exception:
      pass

  doc.build(story)
  return pdf_path


def app():
  st.subheader("📝 Registrar Nueva Compra")

  df_excel, error = cargar_datos_alumnos()
  if error:
    st.error(f"Error al cargar el archivo de Excel: {error}")
    return

  columnas = [c.strip() for c in df_excel.columns]
  col_nombre = next(
      (c for c in columnas if 'nombre' in c.lower() or 'alumno' in c.lower()),
      columnas[0],
  )
  col_grupo = next(
      (c for c in columnas if 'grupo' in c.lower() or 'alojamiento' in c.lower()),
      columnas[1] if len(columnas) > 1 else columnas[0],
  )

  with st.form('form_compra'):
    lista_alumnos = sorted(df_excel[col_nombre].dropna().astype(str).unique())
    nombre_alumno = st.selectbox('Nombre del alumno:', options=lista_alumnos)

    grupo_asignado = ''
    if nombre_alumno:
      fila = df_excel[df_excel[col_nombre].astype(str) == nombre_alumno]
      if not fila.empty:
        grupo_asignado = str(fila.iloc[0][col_grupo])

    st.text_input('Grupo (Automático):', value=grupo_asignado, disabled=True)

    st.markdown('---')
    concepto = st.text_input('Concepto:', value='Fotografía Navidad 2026')
    importe = st.number_input('Importe ($):', value=350.0, format='%.2f')

    atendio = st.selectbox(
        'Quién atendió:',
        options=[
            'Victoria Garcia Valencia',
            'Jose Francisco Resendiz',
            'Grecia Ramirez Arenas',
        ],
    )

    submitted = st.form_submit_button('Confirmar Compra')

  if submitted:
    st.session_state['pending_compra'] = {
        'Alumno': nombre_alumno,
        'Grupo': grupo_asignado,
        'Concepto': concepto,
        'Importe': importe,
        'Atendio': atendio,
        'Fecha': pd.Timestamp.now().strftime('%d/%MM/yyyy %H:%M'),
    }
    st.session_state['show_confirm'] = True

  if st.session_state.get('show_confirm', False):
    st.warning('⚠️ ¿Está seguro de confirmar y registrar esta compra?')
    col_si, col_no = st.columns(2)

    with col_si:
      if st.button('Sí, Confirmar'):
        datos = st.session_state['pending_compra']
        folio = pd.Timestamp.now().strftime('%Y%m%d%H%M%S')
        datos['Folio'] = folio

        csv_path = 'assets/registros_compras.csv'
        os.makedirs('assets', exist_ok=True)
        if os.path.exists(csv_path):
          df_reg = pd.read_csv(csv_path)
          df_reg = pd.concat([df_reg, pd.DataFrame([datos])], ignore_index=True)
        else:
          df_reg = pd.DataFrame([datos])
        df_reg.to_csv(csv_path, index=False)

        pdf_path = generar_ticket_pdf(datos, folio)

        st.success(f'¡Compra realizada con éxito! Folio generado: {folio}')
        st.session_state['show_confirm'] = False

        with open(pdf_path, 'rb') as f:
          st.download_button(
              label='🖨️ Imprimir Ticket Térmico (Descargar PDF)',
              data=f,
              file_name=f'ticket_{folio}.pdf',
              mime='application/pdf',
          )

    with col_no:
      if st.button('No, Regresar'):
        st.info('Captura cancelada. Puede modificar los datos.')
        st.session_state['show_confirm'] = False
        st.rerun()
