import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
import streamlit as st

EXCEL_PATH = "assets/alumnosprimaria.xlsx"
FOLIOS_DIR = "assets/folios_papalote"
LOGO_PATH = "assets/logo.png"
QR_PATH = "assets/qr_ticket.png"
CSV_PATH = "assets/registros_compras_papalote.csv"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZnTwACPO9rxudYkd-J4aV9PLRMSKqbW4SDry4iKNLvM/edit?usp=sharing"


@st.cache_data
def cargar_alumnos_por_grupos():
    """Carga los alumnos estrictamente de 4to, 5to y 6to (hojas desde índice 6 en adelante),
    leyendo desde la columna B (índice 1) a partir de la fila 10.
    """
    if not os.path.exists(EXCEL_PATH):
        return None, f"No se encontró el archivo de Excel en la ruta: {EXCEL_PATH}"

    try:
        xls = pd.ExcelFile(EXCEL_PATH)
        todas_hojas = xls.sheet_names
        datos_grupos = {}

        for idx, hoja
