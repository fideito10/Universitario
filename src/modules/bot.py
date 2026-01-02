import streamlit as st
import pandas as pd
import requests
import os
import json
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuración de página si se ejecuta directo
def check_standalone():
    try:
        if st.session_state.get('is_standalone', False):
            st.set_page_config(page_title="Asistente Universitario", page_icon="🤖", layout="wide")
    except:
        pass

# ==========================================
# GESTIÓN DE CREDENCIALES
# ==========================================
def get_credentials():
    """Obtiene credenciales de GCP para Google Sheets"""
    try:
        # 1. Intentar desde st.secrets
        if hasattr(st, 'secrets') and "google" in st.secrets:
            return dict(st.secrets["google"])
            
        # 2. Intentar desde archivos locales
        possible_paths = [
            "credentials/service_account.json",
            "../credentials/service_account.json",
            "credentials/car-digital-441319-1a4e4b5c11c2.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
                    
        return None
    except Exception as e:
        st.error(f"Error cargando credenciales: {e}")
        return None

def get_gspread_client():
    """Autentica y devuelve cliente gspread"""
    creds_dict = get_credentials()
    if not creds_dict:
        return None
        
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# ==========================================
# CARGA DE DATOS (Optimizada)
# ==========================================
@st.cache_data(ttl=3600)
def load_all_data():
    """Carga y consolida datos de todas las áreas de forma resumida y OPTIMIZADA"""
    client = get_gspread_client()
    if not client:
        return "No se pudieron cargar credenciales."

    context_text = "DATOS DEL CLUB:\n\n"

    try:
        # 1. MÓDULO ADMINISTRACIÓN (JUGADORES) - REDUCIDO
        sheet_admin = client.open_by_key("1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw")
        ws_jugadores = sheet_admin.worksheet("Jugadores_Maestro")
        data_jugadores = ws_jugadores.get_all_records()
        df_jugadores = pd.DataFrame(data_jugadores)
        
        if not df_jugadores.empty:
            context_text += f"JUGADORES ({len(df_jugadores)} total):\n"
            # Solo 50 jugadores más recientes para reducir tamaño
            cols_adm = [c for c in ['Nombre', 'Apellido', 'Posicion', 'Categoria', 'Estado'] if c in df_jugadores.columns]
            context_text += df_jugadores[cols_adm].head(50).to_string(index=False)
            context_text += "\n\n"
        
        # 2. ÁREA MÉDICA - REDUCIDO
        try:
            sheet_medica = client.open_by_key("1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ")
            ws_medica = sheet_medica.get_worksheet(0)
            data_medica = ws_medica.get_all_records()
            df_medica = pd.DataFrame(data_medica)
            
            if not df_medica.empty:
                context_text += f"MÉDICO (Últimos 30 casos):\n"
                cols_med = [c for c in ['Nombre del Paciente', 'Diagnóstico', 'Severidad de la lesión', 'Estado'] if c in df_medica.columns]
                context_text += df_medica[cols_med].tail(30).to_string(index=False)
                context_text += "\n\n"
        except: pass

        # 3. ÁREA FÍSICA - REDUCIDO
        try:
            sheet_fisica = client.open_by_key("1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI")
            ws_fisica = sheet_fisica.worksheet("Base Test")
            data_fisica = ws_fisica.get_all_records()
            df_fisica = pd.DataFrame(data_fisica)
            
            if not df_fisica.empty:
                context_text += f"FÍSICA (Últimos 50 tests):\n"
                # Solo últimos 50 registros
                df_resumen_fis = df_fisica[['Nombre y Apellido', 'Test', 'valor', 'unidad', 'Fecha']].tail(50)
                context_text += df_resumen_fis.to_string(index=False)
            else:
                context_text += "FÍSICA: Sin datos."
        except Exception as e:
            context_text += f"FÍSICA: Error ({str(e)})"
            
        return context_text

    except Exception as e:
        return f"Error cargando datos: {str(e)}"

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
def main_bot():
    # Estilos específicos para el chat
    st.markdown("""
    <style>
    .chat-header {
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 2px solid white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="chat-header">
        <h1 style="color: white; margin: 0;">✨ Asistente Inteligente Universitario</h1>
        <p style="color: #E0E0E0; margin: 0.5rem 0 0 0;">Potenciado por Google Gemini (Ultra Rápido)</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Configuración Gemini en Sidebar ---
    with st.sidebar:
        st.markdown("### 🔑 Configuración IA")
        
        # Intentar obtener API Key de secrets
        gemini_api_key = ""
        if hasattr(st, 'secrets') and "google" in st.secrets:
            # A veces se guarda como 'gemini_api_key' dentro de 'google' o solo en el root
            gemini_api_key = st.secrets["google"].get("gemini_api_key", "")
        
        if not gemini_api_key and "gemini_api_key" in st.secrets:
             gemini_api_key = st.secrets["gemini_api_key"]

        api_key_input = st.text_input("Gemini API Key", value="AIzaSyBEN8C00vWYXq4UGjFkGCRmyIjgoSSoSCQ", type="password", help="Consíguela gratis en Google AI Studio")
        
        if not api_key_input:
            st.warning("⚠️ Ingresa tu API Key para usar el asistente.")
            st.markdown("[Obtener API Key Gratis](https://aistudio.google.com/app/apikey)")
        else:
            genai.configure(api_key=api_key_input)
            st.success("✅ IA Conectada")
        
        st.markdown("---")
        if st.button("🗑️ Limpiar Conversación", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.info("💡 Pregunta sobre jugadores, lesiones o métricas físicas.")

    # --- Historial de Chat ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Cargar Contexto ---
    if "data_context" not in st.session_state:
        with st.spinner("🔄 Conectando con bases de datos..."):
            st.session_state.data_context = load_all_data()
            if "Error" not in st.session_state.data_context:
                st.success("✅ Información cargada.")
            else:
                st.error("⚠️ Problemas cargando datos.")

    # --- Mostrar Chat ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Input de Usuario ---
    if prompt := st.chat_input("Escribe tu consulta aquí..."):
        if not api_key_input:
            st.error("❌ Por favor, ingresa una API Key en la barra lateral.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    # 1. Buscar dinámicamente qué modelos están disponibles
                    available_models = []
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                    
                    if not available_models:
                        raise Exception("No se encontraron modelos disponibles.")
                    
                    # 2. Priorizar modelos Flash
                    target_model = None
                    for m in available_models:
                        if "1.5-flash" in m:
                            target_model = m
                            break
                    
                    if not target_model:
                        target_model = available_models[0]
                        
                    model = genai.GenerativeModel(target_model)
                    
                    # 3. Preparar el envío con la nueva personalidad de Consultor/Analista
                    full_prompt = f"""ERES: Consultor Estratégico y Analista Deportivo Senior del Club Universitario de La Plata.
                    OBJETIVO: Brindar análisis precisos, sintetizar información clave y generar reportes ejecutivos para reuniones de comisión directiva o cuerpo técnico.
                    
                    DATOS DEL CLUB (CONTEXTO REAL):
                    {st.session_state.data_context}
                    
                    SOLICITUD DEL USUARIO: {prompt}
                    
                    REGLAS DE ORO PARA TUS REPORTES:
                    1. PROFESIONALISMO: Usa un tono formal, ejecutivo y directo.
                    2. ESTRUCTURA DE REUNIÓN: Si te piden un reporte, usa:
                       - 📋 **Resumen Ejecutivo**: (Lo más importante en 2 párrafos)
                       - 📊 **Métricas Clave**: (Datos numéricos comparativos)
                       - ⚠️ **Puntos Críticos**: (Alertas médicas o bajas de rendimiento)
                       - ✅ **Conclusión/Sugerencia**: (Pasos a seguir)
                    3. CONCISIÓN: Evita párrafos largos. Usa listas (bullet points) y tablas.
                    4. VERACIDAD: Solo usa los datos proporcionados. Si no hay datos, indica: "Sin registros disponibles para análisis".
                    5. IDIOMA: Responde siempre en ESPAÑOL."""

                    response = model.generate_content(full_prompt, stream=True)
                    
                    # Generar respuesta
                    for chunk in response:
                        try:
                            if chunk.text:
                                full_response += chunk.text
                                response_placeholder.markdown(full_response + "▌")
                        except Exception:
                            break
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    st.error(f"Error Gemini: {e}")

if __name__ == "__main__":
    check_standalone()
    main_bot()
