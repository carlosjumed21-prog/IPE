import streamlit as st

def app():
    st.title("🏙️ Sistema de Gestión - KidZania")
    st.markdown("---")

    # Menú interno para el módulo de KidZania
    menu = st.sidebar.selectbox(
        "Selecciona una opción (KidZania)", ["Nueva Compra", "Consultar Compra"]
    )

    if menu == "Nueva Compra":
        try:
            import kidzania_compra
            kidzania_compra.app()
        except ImportError:
            st.error("No se encontró el módulo `kidzania_compra.py`.")
            
    elif menu == "Consultar Compra":
        try:
            # Aquí puedes crear después tu archivo kidzania_consulta.py si lo necesitas
            st.info("Módulo de consulta en desarrollo...")
        except ImportError:
            st.error("No se encontró el módulo de consulta.")
