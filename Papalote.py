import streamlit as st

def app():
    st.title("🪁 Sistema de Gestión - Papalote Museo del Niño")
    st.markdown("---")

    # Menú interno para el módulo de Papalote
    menu = st.sidebar.selectbox(
        "Selecciona una opción (Papalote)", ["Registrar Abono", "Consultar Compra"]
    )

    if menu == "Registrar Abono":
        try:
            import papalote_compra
            papalote_compra.app()
        except ImportError:
            st.error("No se encontró el módulo `papalote_compra.py`. Asegúrate de guardarlo en la misma carpeta.")
            
    elif menu == "Consultar Compra":
        try:
            st.info("Módulo de consulta en desarrollo...")
        except ImportError:
            st.error("No se encontró el módulo de consulta.")
