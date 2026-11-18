
import streamlit as st

def app():
    st.title("🪁 Sistema de Gestión - Papalote Museo del Niño")
    st.markdown("---")
    
    # Menú interno o contenido de Papalote
    st.write("Bienvenido al módulo de Papalote.")
    
    # Si quieres usar un sub-módulo de compra igual que KidZania:
    menu = st.sidebar.selectbox("Selecciona opción", ["Nueva Compra", "Consultar Compra"])
    
    if menu == "Nueva Compra":
        try:
            import papalote_compra
            papalote_compra.app()
        except ImportError:
            st.error("Falta crear el archivo `papalote_compra.py`.")
