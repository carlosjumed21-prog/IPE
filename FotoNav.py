import streamlit as st

def app():
    st.title("🎢 Sistema de Gestión - Excursiones Escolares")
    st.markdown("---")

    # Menú interno para el módulo de KidZania / Excursiones
    menu = st.sidebar.selectbox(
        "Selecciona una opción (Excursiones)", ["Nueva Compra", "Consultar Compra"]
    )

    if menu == "Nueva Compra":
        try:
            import kidzania_compra
            kidzania_compra.app()
        except ImportError:
            st.error("No se encontró el módulo `kidzania_compra.py`.")
            
    elif menu == "Consultar Compra":
        try:
            import kidzania_consulta  # O el nombre que uses para consultar
            kidzania_consulta.app()
        except ImportError:
            st.error("No se encontró el módulo de consulta de KidZania.")
