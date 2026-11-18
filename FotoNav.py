
import streamlit as st

def app():
    st.title("🎄 Sistema de Gestión - Fotografía Navidad 2026")
    st.markdown("---")

    # Menú interno para el módulo FotoNav
    menu = st.sidebar.selectbox(
        "Selecciona una opción (FotoNav)", ["Nueva Compra", "Consultar Compra"]
    )

    if menu == "Nueva Compra":
        try:
            import compra
            compra.app()
        except ImportError:
            st.error("No se encontró el módulo `compra.py`.")
            
    elif menu == "Consultar Compra":
        try:
            import consulta
            consulta.app()
        except ImportError:
            st.error("No se encontró el módulo `consulta.py`.")
