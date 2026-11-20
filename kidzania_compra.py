import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
import streamlit as st

EXCEL_PATH = "assets/alumnosprimaria.xlsx"
FOLIOS_DIR = "assets/folios_kidzania"
LOGO_PATH = "assets/logo.png"
QR_PATH = "assets/qr_ticket.png"
CSV_PATH = "assets/registros_compras_kidzania.csv"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZnTwACPO9rxudYkd-J4aV9PLRMSKqbW4SDry4iKNLvM/edit?usp=sharing"


@st.cache_data
def cargar_alumnos_por_grupos():
    """Carga los alumnos estrictamente de 1ro a 3ro (primeras 6 hojas, índices 0 a 5),
    leyendo desde la columna B (índice 1) a partir de la fila 10.
    """
    if not os.path.exists(EXCEL_PATH):
        return None, f"No se encontró el archivo de Excel en la ruta: {EXCEL_PATH}"

    try:
        xls = pd.ExcelFile(EXCEL_PATH)
        todas_hojas = xls.sheet_names
        datos_grupos = {}

        for idx, hoja in enumerate(todas_hojas):
            # Solo tomamos las primeras 6 hojas (1.º a 3.º de primaria, índices 0 al 5)
            if idx < 6:
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
                "No se encontraron alumnos de 1ro a 3ro en las hojas correspondientes.",
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
    """Calcula el folio con formato AAAAMMDD-KID-001 con continuidad diaria."""
    try:
        zona_mexico = ZoneInfo("America/Mexico_City")
        hoy_str = datetime.now(zona_mexico).strftime("%Y%m%d")
    except Exception:
        hoy_str = datetime.now().strftime("%Y%m%d")

    prefijo_base = f"{hoy_str}-KID-"
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


def obtener_historial_alumno_sheets(grupo, alumno_nombre):
    """Consulta Google Sheets para traer el paquete previo, pagos, costo total y restante."""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        sh = client.open_by_url(SHEET_URL)
        try:
            worksheet = sh.worksheet(str(grupo))
        except Exception:
            worksheet = sh.sheet1

        filas = worksheet.get_all_values()
        for idx, fila in enumerate(filas):
            if len(fila) > 2 and str(fila[2]).strip().lower() == alumno_nombre.strip().lower():
                tipo_paquete_previo = str(fila[3]).strip() if len(fila) > 3 else ""
                total_cubrir = float(fila[4]) if len(fila) > 4 and str(fila[4]).replace('.', '', 1).isdigit() else 0.0
                
                pagos_previos = []
                for col_idx in range(5, 10):  # Columnas F a J (índices 5 al 9)
                    val_pago = float(fila[col_idx]) if len(fila) > col_idx and str(fila[col_idx]).replace('.', '', 1).isdigit() else 0.0
                    if val_pago > 0:
                        pagos_previos.append(val_pago)
                
                restante = float(fila[10]) if len(fila) > 10 and str(fila[10]).replace('.', '', 1).isdigit() else max(0.0, total_cubrir - sum(pagos_previos))
                return {
                    "fila": idx + 1,
                    "tipo_paquete": tipo_paquete_previo,
                    "total_cubrir": total_cubrir,
                    "pagos_previos": pagos_previos,
                    "restante": restante
                }
    except Exception as e:
        print(f"Error al leer historial de Sheets: {e}")
    
    return None


def guardar_en_google_sheets(datos):
    """Registra el abono en la celda correspondiente y actualiza la tabla."""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        sh = client.open_by_url(SHEET_URL)
        grupo_hoja = str(datos["Grupo"])

        try:
            worksheet = sh.worksheet(grupo_hoja)
        except Exception:
            worksheet = sh.sheet1

        historial = obtener_historial_alumno_sheets(grupo_hoja, datos["Alumno"])
        
        if historial and historial["fila"] > 1:
            fila_idx = historial["fila"]
            total_cubrir = historial["total_cubrir"] if historial["total_cubrir"] > 0 else datos["Total_Cubrir"]
            pagos = historial["pagos_previos"]
            pagos.append(datos["ImporteAbono"])
            
            while len(pagos) < 5:
                pagos.append("")
                
            pagos_a_escribir = pagos[:5]
            nuevo_restante = max(0.0, total_cubrir - sum([p for p in pagos_a_escribir if isinstance(p, (int, float))]))

            worksheet.update_cell(fila_idx, 4, datos["TipoPaquete"])
            worksheet.update_cell(fila_idx, 5, total_cubrir)
            for i, p_val in enumerate(pagos_a_escribir):
                worksheet.update_cell(fila_idx, 6 + i, p_val if p_val != "" else "")
            worksheet.update_cell(fila_idx, 11, nuevo_restante)
            return True
        else:
            todas_las_filas = worksheet.get_all_values()
            
            ultima_fila_con_datos = 1
            for idx, fila in enumerate(todas_las_filas):
                if len(fila) > 0 and str(fila[0]).strip() != "":
                    if idx > 0:
                        ultima_fila_con_datos = idx + 1
                    elif idx == 0 and str(fila[0]).lower() not in ["#", "id", "número", "numero"]:
                        ultima_fila_con_datos = 1

            siguiente_fila = max(2, ultima_fila_con_datos + 1)
            siguiente_id = siguiente_fila - 1

            nueva_fila = [
                siguiente_id,
                datos["Folio"],
                datos["Alumno"],
                datos["TipoPaquete"],
                datos["Total_Cubrir"],
                datos["ImporteAbono"],
                "", "", "", "",
                max(0.0, datos["Total_Cubrir"] - datos["ImporteAbono"])
            ]
            rango_celda = f"A{siguiente_fila}:K{siguiente_fila}"
            worksheet.update(rango_celda, [nueva_fila])
            return True
    except Exception as e:
        print(f"Error al sincronizar abono con Google Sheets: {e}")
        return False


def generar_ticket_pdf(datos_compra, folio):
    """Genera el ticket en PDF tamaño 48mm x 250mm mostrando el abono y restante."""
    os.makedirs(FOLIOS_DIR, exist_ok=True)
    pdf_path = os.path.join(FOLIOS_DIR, f"ticket_kidzania_{folio.replace('/', '-')}.pdf")

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

    if os.path.exists(LOGO_PATH):
        try:
            img_logo = Image(LOGO_PATH, width=18 * mm, height=7 * mm)
            img_logo.hAlign = "CENTER"
            story.append(img_logo)
            story.append(Spacer(1, 4))
        except Exception:
            pass

    story.append(Paragraph("================================", style_mono_centro))
    story.append(Paragraph("      EXCURSION KIDZANIA        ", style_mono_centro))
    story.append(Paragraph("      COMPROBANTE DE ABONO      ", style_mono_centro))
    story.append(Paragraph("================================", style_mono_centro))

    story.append(Paragraph(f"Ticket: #{folio}", style_mono_izq))
    story.append(Paragraph(f"Fecha: {datos_compra['Fecha']}", style_mono_izq))
    story.append(Paragraph(f"Alumno: {datos_compra['Alumno']}", style_mono_izq))
    story.append(Paragraph(f"Grupo: {datos_compra['Grupo']}", style_mono_izq))
    story.append(Paragraph(f"Paquete: {datos_compra['TipoPaquete']}", style_mono_izq))
    story.append(Paragraph("--------------------------------", style_mono_centro))

    story.append(Paragraph(f"Costo Total: ${datos_compra['Total_Cubrir']:.2f}", style_mono_izq))
    story.append(Paragraph(f"Abono Actual: ${datos_compra['ImporteAbono']:.2f}", style_mono_izq))
    story.append(Paragraph(f"Restante:    ${datos_compra['RestanteNuevo']:.2f}", style_mono_izq))
    story.append(Paragraph("--------------------------------", style_mono_centro))

    if datos_compra['RestanteNuevo'] <= 0:
        story.append(Paragraph("   ¡CUENTA PAGADA AL 100%!      ", style_mono_centro))
        story.append(Paragraph("   ¡PAGO COMPLETO LIBERADO!     ", style_mono_centro))
    else:
        story.append(Paragraph("   ¡Sigue abonando a tu ritmo!  ", style_mono_centro))

    story.append(Paragraph("================================", style_mono_centro))
    story.append(Paragraph("   Atendió: " + datos_compra["Atendio"], style_mono_izq))
    story.append(Spacer(1, 2))
    story.append(Paragraph("  Conserve su ticket para       ", style_mono_centro))
    story.append(Paragraph("   cualquier aclaración.        ", style_mono_centro))
    story.append(Paragraph("================================", style_mono_centro))
    story.append(Spacer(1, 6))

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
    st.subheader("🏙️ Registrar Abono - Excursión KidZania")

    if "is_processing_kidzania" not in st.session_state:
        st.session_state["is_processing_kidzania"] = False
    if "ultima_venta_kidzania" not in st.session_state:
        st.session_state["ultima_venta_kidzania"] = None

    dic_grupos, error = cargar_alumnos_por_grupos()
    if error:
        st.error(f"Error al cargar el archivo de Excel: {error}")
        return

    lista_grupos = sorted(list(dic_grupos.keys()))

    if st.session_state["ultima_venta_kidzania"] is not None:
        st.success("🎉 ¡Abono registrado y sincronizado con éxito!")
        
        if st.button("🔄 Registrar Nuevo Abono", type="primary", use_container_width=True, key="btn_nuevo_reg_kidzania"):
            st.session_state["ultima_venta_kidzania"] = None
            st.rerun()

        st.markdown("---")
        st.markdown("### 🖨️ Comprobante de Abono")

        datos_venta = st.session_state["ultima_venta_kidzania"]
        folio = datos_venta["Folio"]
        pdf_path = generar_ticket_pdf(datos_venta, folio)

        lineas = []
        lineas.append("==================")
        lineas.append("   KIDZANIA       ")
        lineas.append("COMPROBANTE ABONO ")
        lineas.append("==================")
        lineas.append("Ticket: #" + folio)
        lineas.append("F/H: " + datos_venta["Fecha"])
        lineas.append("Alumno:")
        lineas.append(datos_venta["Alumno"])
        lineas.append("Grupo: " + datos_venta["Grupo"])
        lineas.append("------------------")
        lineas.append(f"Total: ${datos_venta['Total_Cubrir']:.2f}")
        lineas.append(f"Abono: ${datos_venta['ImporteAbono']:.2f}")
        lineas.append(f"Restante: ${datos_venta['RestanteNuevo']:.2f}")
        lineas.append("------------------")
        if datos_venta['RestanteNuevo'] <= 0:
            lineas.append(" ¡PAGADO AL 100%! ")
            lineas.append(" PAGO LIBERADO    ")
        else:
            lineas.append("¡Sigue abonando!")
        lineas.append("==================")
        lineas.append("Atendió:")
        lineas.append(datos_venta["Atendio"])
        lineas.append("Conserve su ticket")
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
            font-size: 10px;
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

        st.components.v1.html(html_ticket_preview, height=620, scrolling=True)
        return

    def actualizar_grupo():
        st.session_state["alumno_seleccionado_kidzania"] = None

    grupo_seleccionado = st.selectbox(
        "Seleccione el Grupo (1ro a 3ro):",
        options=lista_grupos,
        index=None,
        placeholder="Seleccione un grupo...",
        key="grupo_seleccionado_kidzania",
        on_change=actualizar_grupo,
    )

    lista_alumnos = dic_grupos.get(grupo_seleccionado, []) if grupo_seleccionado else []

    nombre_alumno = st.selectbox(
        "Nombre del alumno:",
        options=lista_alumnos,
        index=None,
        placeholder=(
            "Seleccione primero un grupo..."
            if not grupo_seleccionado
            else "Seleccione un alumno..."
        ),
        key="alumno_seleccionado_kidzania",
    )

    # Consultar historial en Google Sheets
    historial_actual = None
    paquete_fijo_index = 0
    tiene_registro_previo = False

    if grupo_seleccionado and nombre_alumno:
        historial_actual = obtener_historial_alumno_sheets(grupo_seleccionado, nombre_alumno)
        if historial_actual and historial_actual["total_cubrir"] > 0:
            tiene_registro_previo = True
            # Identificar qué paquete tenía asignado previamente
            if "Sin" in historial_actual["tipo_paquete"]:
                paquete_fijo_index = 1
            else:
                paquete_fijo_index = 0

            if historial_actual["restante"] <= 0:
                st.success(f"✅ **Estado Actual:** ¡Cuenta liquidada al 100%! Paquete: *{historial_actual['tipo_paquete']}* (Total: ${historial_actual['total_cubrir']:.2f})")
            else:
                st.warning(f"📊 **Cuenta Activa:** Paquete asignado: **{historial_actual['tipo_paquete']}** | Costo: ${historial_actual['total_cubrir']:.2f} | Pagado: ${sum(historial_actual['pagos_previos']):.2f} | **Restante: ${historial_actual['restante']:.2f}**")
        else:
            st.info("ℹ️ Este alumno no tiene registros previos. Seleccione el paquete inicial para su primer abono.")

    with st.form("form_abono_kidzania"):
        st.markdown("---")
        
        paquete_opciones = {
            "Con Alimentos": 1050.0,
            "Sin Alimentos": 900.0
        }
        
        # Si ya tiene registro previo, bloqueamos la selección del paquete con disabled=True
        tipo_paquete = st.selectbox(
            "Paquete Seleccionado:",
            options=list(paquete_opciones.keys()),
            index=paquete_fijo_index,
            disabled=tiene_registro_previo,
            help="El paquete no se puede modificar porque ya cuenta con un registro previo." if tiene_registro_previo else ""
        )
        
        # En caso de que el select esté deshabilitado, Streamlit a veces no pasa el valor en el form_submit directamente,
        # por lo que aseguramos el valor correcto si ya tenía registro previo.
        if tiene_registro_previo and historial_actual:
            tipo_paquete = historial_actual["tipo_paquete"] if historial_actual["tipo_paquete"] in paquete_opciones else list(paquete_opciones.keys())[paquete_fijo_index]

        costo_total_fijo = paquete_opciones[tipo_paquete]
        st.write(f"💵 **Costo Total del Paquete:** ${costo_total_fijo:.2f}")

        # Sugerir por defecto el restante exacto o un valor prudente
        sugerencia_abono = float(historial_actual["restante"]) if (historial_actual and historial_actual["restante"] > 0) else 100.0

        importe_abono = st.number_input(
            "Importe a abonar en esta ocasión ($):", 
            min_value=1.0, 
            value=sugerencia_abono, 
            format="%.2f"
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

        submitted = st.form_submit_button("Registrar Abono")

    if submitted:
        if not grupo_seleccionado:
            st.warning("⚠️ Por favor seleccione un grupo.")
        elif not nombre_alumno:
            st.warning("⚠️ Por favor seleccione un alumno.")
        elif not atendio:
            st.warning("⚠️ Por favor seleccione quién atiende.")
        elif importe_abono <= 0:
            st.warning("⚠️ El importe del abono debe ser mayor a 0.")
        else:
            total_base = historial_actual["total_cubrir"] if (historial_actual and historial_actual["total_cubrir"] > 0) else costo_total_fijo
            suma_pagos_anteriores = sum(historial_actual["pagos_previos"]) if historial_actual else 0.0
            
            # Validar que no abone más de lo que resta
            restante_actual_calculado = max(0.0, total_base - suma_pagos_anteriores)
            if importe_abono > restante_actual_calculado and restante_actual_calculado > 0:
                st.warning(f"⚠️ El abono (${importe_abono:.2f}) es mayor al saldo pendiente actual (${restante_actual_calculado:.2f}).")
            else:
                restante_nuevo = max(0.0, restante_actual_calculado - importe_abono)

                fecha_hora_actual = obtener_fecha_hora_actual()
                st.session_state["pending_compra_kidzania"] = {
                    "Alumno": nombre_alumno,
                    "Grupo": grupo_seleccionado,
                    "TipoPaquete": tipo_paquete,
                    "Total_Cubrir": total_base,
                    "ImporteAbono": importe_abono,
                    "RestanteNuevo": restante_nuevo,
                    "Atendio": atendio,
                    "Fecha": fecha_hora_actual,
                }
                st.session_state["show_confirm_kidzania"] = True

    if st.session_state.get("show_confirm_kidzania", False):
        st.warning("⚠️ ¿Está seguro de registrar este abono para KidZania?")
        col_si, col_no = st.columns(2)

        with col_si:
            if st.button(
                "Sí, Confirmar Abono",
                disabled=st.session_state["is_processing_kidzania"],
                key="btn_confirmar_abono_kidzania",
            ):
                st.session_state["is_processing_kidzania"] = True
                datos = st.session_state["pending_compra_kidzania"]

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

                sheet_ok = guardar_en_google_sheets(datos)

                st.session_state["ultima_venta_kidzania"] = datos
                st.session_state["show_confirm_kidzania"] = False
                st.session_state["is_processing_kidzania"] = False
                st.rerun()

        with col_no:
            if st.button("No, Regresar", disabled=st.session_state["is_processing_kidzania"], key="btn_cancelar_kidzania"):
                st.info("Registro de abono cancelado.")
                st.session_state["show_confirm_kidzania"] = False
                st.rerun()
