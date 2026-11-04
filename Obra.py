
import streamlit as st

def app():
    st.title("🎭 Sistema de Gestión - Obra de Teatro en Inglés")
    st.markdown("---")

    # Menú interno para el módulo de Obra
    menu = st.sidebar.selectbox(
        "Selecciona una opción (Obra)", ["Nueva Compra", "Consultar Compra"]
    )

    if menu == "Nueva Compra":
        try:
            import compra_obra
            compra_obra.app()
        except ImportError:
            st.error("No se encontró el módulo `compra_obra.py`.")
            
    elif menu == "Consultar Compra":
        try:
            import consulta  # O puedes crear un consulta_obra.py si requieres consultas específicas independientes
            consulta.app()
        except ImportError:
            st.error("No se encontró el módulo `consulta.py`.")
