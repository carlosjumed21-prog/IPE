import streamlit as st

def app():
    st.title("🏙️ Sistema de Gestión - KidZania")
    st.markdown("---")

    # Menú interno para el módulo de KidZania
    menu = st.sidebar.selectbox(
        "Selecciona una opción (KidZania)", ["Registrar Abono", "Consultar Compra"]
    )

    if menu == "Registrar Abono":
        try:
            import kidzania_compra
            kidzania_compra.app()
        except ImportError:
            st.error("No se encontró el módulo `kidzania_compra.py`. Asegúrate de guardarlo en la misma carpeta.")
            
    elif menu == "Consultar Compra":
        try:
            st.info("Módulo de consulta en desarrollo...")
        except ImportError:
            st.error("No se encontró el módulo de consulta.")
