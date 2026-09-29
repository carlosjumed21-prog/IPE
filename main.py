import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Sistema de Compras - Fotografía Navidad 2026",
    page_icon="📸",
    layout="centered",
)


def main():
  st.title("🎄 Sistema de Gestión - Fotografía Navidad 2026")
  st.markdown("---")

  # Menú principal con botones
  st.sidebar.markdown("### Menú Principal")
  menu = st.sidebar.selectbox(
      "Selecciona una opción", ["Nueva Compra", "Consultar Compra"]
  )

  if menu == "Nueva Compra":
    import compra

    compra.app()
  elif menu == "Consultar Compra":
    import consulta

    consulta.app()


if __name__ == "__main__":
  main()
