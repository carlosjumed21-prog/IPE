
import streamlit as st
from datetime import datetime
from gsheets import get_sheet_connection  # O tu método habitual de conexión a Google Sheets

def app():
    st.subheader("🎟️ Registro de Compra - KidZania / Papalote")
    st.markdown("Ingresa los datos del alumno, selecciona el grupo y registra los abonos correspondientes.")
    st.markdown("---")

    # Lista de tus grupos escolares
    grupos = [
        "1°APrim", "1°BPrim", "2°APrim", "2°BPrim", 
        "3°APrim", "3°BPrim", "4°APrim", "4°BPrim", "4°CPrim", 
        "5°APrim", "5°BPrim", "5°CPrim", "6°APrim", "6°BPrim", "6°CPrim"
    ]

    with st.form("form_kidzania_completo", clear_on_submit=False):
        col_1, col_2 = st.columns(2)
        
        with col_1:
            folio = st.text_input("Folio / ID de Registro:")
            nombre = st.text_input("Nombre Completo del Alumno:")
            grupo_seleccionado = st.selectbox("Selecciona el Grupo:", grupos)
            
        with col_2:
            fecha = st.date_input("Fecha de Registro:", value=datetime.today())
            total_cubrir = st.number_input("Total a cubrir ($):", min_value=0.0, format="%.2f", value=0.0)
            atendio = st.text_input("Atendió (Responsable):")

        st.markdown("### 💳 Métodos de Pago / Abonos")
        st.markdown("Registra los montos correspondientes a cada pago:")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            pago_1 = st.number_input("Pago 1", min_value=0.0, format="%.2f", value=0.0)
        with c2:
            pago_2 = st.number_input("Pago 2", min_value=0.0, format="%.2f", value=0.0)
        with c3:
            pago_3 = st.number_input("Pago 3", min_value=0.0, format="%.2f", value=0.0)
        with c4:
            pago_4 = st.number_input("Pago 4", min_value=0.0, format="%.2f", value=0.0)
        with c5:
            pago_5 = st.number_input("Pago 5", min_value=0.0, format="%.2f", value=0.0)

        # Cálculo automático en pantalla del Por Restar antes de enviar
        suma_abonos = pago_1 + pago_2 + pago_3 + pago_4 + pago_5
        por_restar_calculado = total_cubrir - suma_abonos

        st.markdown("---")
        st.info(f"💰 **Resumen automático:** Total a cubrir: ${total_cubrir:,.2f} | Abonos: ${suma_abonos:,.2f} | **Por restar: ${por_restar_calculado:,.2f}**")

        submitted = st.form_submit_button("💾 Guardar Registro en la Hoja", use_container_width=True)

        if submitted:
            if not folio or not nombre:
                st.warning("⚠️ Por favor, completa al menos el **Folio** y el **Nombre del alumno**.")
            else:
                try:
                    # Conexión a tu Google Sheet (ajusta según la hoja del grupo seleccionado)
                    # El script buscará la pestaña correspondiente al grupo (ej. "1°APrim")
                    ss = get_sheet_connection() 
                    hoja_grupo = ss.getSheetByName(grupo_seleccionado) or ss.worksheet(grupo_seleccionado)
                    
                    # Estructura de las 12 columnas:
                    # [Folio, Nombre, Fecha, Total a cubrir, Pago 1, Pago 2, Pago 3, Pago 4, Pago 5, Por restar (Fórmula), Atendió]
                    # Nota: La columna 'Por restar' (Columna J / índice 10) se envía como fórmula para que Google Sheets la calcule dinámicamente.
                    fila_datos = [
                        folio, 
                        nombre, 
                        str(fecha), 
                        total_cubrir, 
                        pago_1, 
                        pago_2, 
                        pago_3, 
                        pago_4, 
                        pago_5, 
                        f"=D{hoja_grupo.getLastRow() + 1}-SUMA(E{hoja_grupo.getLastRow() + 1}:I{hoja_grupo.getLastRow() + 1})", 
                        atendio
                    ]
                    
                    hoja_grupo.appendRow(fila_datos)
                    st.success(f"¡Registro guardado correctamente en la hoja **{grupo_seleccionado}** para {nombre}!")
                    
                except Exception as e:
                    # Si manejas la inserción por st.secrets o gspread nativo, puedes adaptarlo a tu función de conexión existente
                    st.error(f"Error al intentar guardar en Google Sheets: {e}")
