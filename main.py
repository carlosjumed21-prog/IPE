import streamlit as st
import FotoNav

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
        st.markdown("Bienvenido al tablero principal. Selecciona el sistema o módulo que deseas ejecutar:")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.info("📸 **Sistema FotoNav**")
            st.markdown("Gestión de compras, registro y consulta para Fotografía Navidad 2026.")
            if st.button("Abrir FotoNav", use_container_width=True):
                st.session_state["active_app"] = "fotonav"
                st.rerun()

        with col2:
            st.warning("📊 **Reportes y Analítica**")
            st.markdown("Espacio reservado para estadísticas y métricas del sistema.")
            if st.button("Abrir Reportes", use_container_width=True):
                st.session_state["active_app"] = "reportes"
                st.rerun()

    # Si el usuario seleccionó FotoNav
    elif st.session_state["active_app"] == "fotonav":
        if st.button("⬅️ Volver al Tablero Principal"):
            st.session_state["active_app"] = "home"
            st.rerun()
        st.markdown("---")
        FotoNav.app()

    # Si el usuario seleccionó Reportes
    elif st.session_state["active_app"] == "reportes":
        if st.button("⬅️ Volver al Tablero Principal"):
            st.session_state["home" if "home" in st.session_state else "active_app"] = "home"
            st.session_state["active_app"] = "home"
            st.rerun()
        st.markdown("---")
        st.subheader("📊 Módulo de Reportes")
        st.write("Próximamente visualizaciones de datos y métricas en tiempo real.")

if __name__ == "__main__":
    main()
