import streamlit as st
import FotoNav
import Obra
import Papalote  # Nuevo módulo
import KidZania  # Nuevo módulo

# Configuración inicial del tablero principal
st.set_page_config(
    page_title="Panel de Control General",
    page_icon="🚀",
    layout="centered",
)

def main():
    # Inicializar el estado de la aplicación si no existe
    if "active_app" not in st.session_state:
        st.session_state["active_app"] = "home"

    # Si estamos en el menú principal (tablero)
    if st.session_state["active_app"] == "home":
        st.title("🚀 Panel de Control General")
        st.markdown("Bienvenido al tablero principal. Selecciona el sistema que deseas ejecutar:")
        st.markdown("---")

        # Fila 1: Fotografía y Teatro
        col1, col2 = st.columns(2)

        with col1:
            st.info("📸 **Fotografía Navidad 2026**")
            st.markdown("Sistema de control, registro de compra y consulta.")
            if st.button("Registrar Compra - FotoNav", use_container_width=True):
                st.session_state["active_app"] = "fotonav"
                st.rerun()

        with col2:
            st.success("🎭 **Obra de Teatro en Inglés**")
            st.markdown("Sistema de control, registro de compra y consulta.")
            if st.button("Registrar Compra - Obra", use_container_width=True):
                st.session_state["active_app"] = "obra"
                st.rerun()

        st.markdown("") # Espaciador visual

        # Fila 2: Excursiones
        col3, col4 = st.columns(2)

        with col3:
            st.warning("museum **Papalote Museo del Niño**") # O usa un emoji representativo como 🧸 o 🪁
            st.markdown("Sistema de control y registro de excursión.")
            if st.button("Registrar - Papalote", use_container_width=True):
                st.session_state["active_app"] = "papalote"
                st.rerun()

        with col4:
            st.error("🏙️ **KidZania**")
            st.markdown("Sistema de control y registro de excursión.")
            if st.button("Registrar - KidZania", use_container_width=True):
                st.session_state["active_app"] = "kidzania"
                st.rerun()

    # Si el usuario seleccionó FotoNav
    elif st.session_state["active_app"] == "fotonav":
        if st.button("⬅️ Volver al Tablero Principal"):
            st.session_state["active_app"] = "home"
            st.rerun()
        st.markdown("---")
        FotoNav.app()

    # Si el usuario seleccionó Obra
    elif st.session_state["active_app"] == "obra":
        if st.button("⬅️ Volver al Tablero Principal"):
            st.session_state["active_app"] = "home"
            st.rerun()
        st.markdown("---")
        Obra.app()

    # Si el usuario seleccionó Papalote
    elif st.session_state["active_app"] == "papalote":
        if st.button("⬅️ Volver al Tablero Principal"):
            st.session_state["active_app"] = "home"
            st.rerun()
        st.markdown("---")
        Papalote.app()

    # Si el usuario seleccionó KidZania
    elif st.session_state["active_app"] == "kidzania":
        if st.button("⬅️ Volver al Tablero Principal"):
            st.session_state["active_app"] = "home"
            st.rerun()
        st.markdown("---")
        KidZania.app()

if __name__ == "__main__":
    main()
