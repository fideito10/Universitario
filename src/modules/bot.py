import streamlit as st
import pandas as pd
import requests
import os
import json
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from datetime import datetime
from src.utils.credentials import get_credentials_dict, get_service_account_credentials

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
    """Obtiene credenciales de GCP usando el módulo centralizado."""
    return get_credentials_dict()

def get_gspread_client():
    """Autentica y devuelve cliente gspread"""
    creds = get_service_account_credentials()
    if not creds:
        return None
    return gspread.authorize(creds)

def get_gemini_api_key():
    """Obtiene la Gemini API Key desde secrets o variables de entorno."""
    # 1. st.secrets (local / Streamlit Cloud)
    try:
        secrets = st.secrets
        if "gemini_api_key" in secrets:
            return secrets["gemini_api_key"]
        if "google" in secrets and secrets["google"].get("gemini_api_key"):
            return secrets["google"]["gemini_api_key"]
    except Exception:
        pass
    # 2. Variables de entorno (Railway)
    return os.getenv("GEMINI_API_KEY", "")


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
        <h1 style="color: white; margin: 0;">Asistente Inteligente Universitario</h1>
        <p style="color: #E0E0E0; margin: 0.5rem 0 0 0;">Analiza datos de jugadores, informes médicos y métricas físicas en tiempo real para brindarte respuestas precisas.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Configuración de IA ---
    gemini_api_key = get_gemini_api_key()

    # --- Sidebar ---
    with st.sidebar:
        if st.button("🗑️ Limpiar Conversación", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.info("💡 Pregunta sobre jugadores, lesiones o métricas físicas.")
        
        # Configuración discreta si falla la conexión automática
        with st.expander("⚙️ Configuración Avanzada", expanded=False):
            manual_key = st.text_input("Ingresar nueva Gemini API Key:", type="password", help="Si el asistente no responde, ingresa una clave válida aquí.")
            if manual_key:
                gemini_api_key = manual_key
                st.success("Clave manual activada")

        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            st.success("✨ IA (Gemini) Conectada")
        else:
            st.warning("⚠️ Sin API Key configurada")

    # --- Historial de Chat ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Cargar Contexto ---
    if "data_context" not in st.session_state:
        with st.spinner("🔄 Conectando con bases de datos..."):
            st.session_state.data_context = load_all_data()

    # --- Mostrar Chat ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Input de Usuario ---
    if prompt := st.chat_input("Escribe tu consulta aquí..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                # 1. Selección robusta de modelo
                try:
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                except:
                    available_models = []
                
                # Prioridades: flash-latest -> flash -> pro
                target_model = "gemini-pro" # Fallback ultra-seguro
                
                if available_models:
                    # Buscamos la versión más moderna de flash primero
                    flash_variants = [m for m in available_models if "1.5-flash" in m]
                    if flash_variants:
                        target_model = flash_variants[0]
                    else:
                        pro_variants = [m for m in available_models if "pro" in m]
                        if pro_variants:
                            target_model = pro_variants[0]

                model = genai.GenerativeModel(target_model)
                
                # 2. Preparar el envío con la personalidad de Consultor
                full_prompt = f"""ERES: Consultor Estratégico y Analista Deportivo Senior del Club Universitario de La Plata.
                {st.session_state.data_context}
                
                SOLICITUD: {prompt}
                
                REGLAS:
                - Tono formal y ejecutivo.
                - Usa tablas y listas si es necesario.
                - Responde siempre en ESPAÑOL."""

                response = model.generate_content(full_prompt, stream=True)
                
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
                error_msg = str(e)
                if "403" in error_msg and "leaked" in error_msg:
                    st.error("🔒 **Error de Seguridad:** Tu API Key ha sido bloqueada por Google por estar filtrada en internet.")
                    st.info("👉 **Solución:** Genera una clave nueva gratis aquí: [Google AI Studio](https://aistudio.google.com/app/apikey) y pégala en 'Configuración Avanzada' de la barra lateral.")
                else:
                    st.error(f"Error Gemini: {e}")

if __name__ == "__main__":
    check_standalone()
    main_bot()
