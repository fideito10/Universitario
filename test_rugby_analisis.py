import streamlit as st
from src.modules.analisis_partido import rugby_analysis_module

# Configuración básica para la prueba
st.set_page_config(page_title="Prueba - Análisis de Rugby", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    </style>
""", unsafe_allow_html=True)

st.info("🚀 Iniciando módulo de prueba de Análisis de Rugby")

# Ejecutamos el módulo
try:
    rugby_analysis_module()
except Exception as e:
    st.error(f"Error al ejecutar el módulo: {e}")
