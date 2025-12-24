import streamlit as st
import pandas as pd
import requests
import os
import json
import gspread
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
# GESTIÓN DE CREDENCIALES (Reutilizada)
# ==========================================
def get_credentials():
    """Obtiene credenciales de GCP"""
    try:
        # 1. Intentar desde st.secrets
        if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"])
            
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
# CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=3600)
def load_all_data():
    """Carga y consolida datos de todas las áreas"""
    client = get_gspread_client()
    if not client:
        return "No se pudieron cargar credenciales."

    context_text = "INFORMACIÓN ACTUAL DEL CLUB:\n\n"

    try:
        # 1. MÓDULO ADMINISTRACIÓN (Jugadores)
        # ID: 1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw
        sheet_admin = client.open_by_key("1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw")
        ws_jugadores = sheet_admin.worksheet("Jugadores_Maestro")
        data_jugadores = ws_jugadores.get_all_records()
        df_jugadores = pd.DataFrame(data_jugadores)
        
        context_text += f"=== BASE DE JUGADORES ({len(df_jugadores)} registros) ===\n"
        # Resumen simplificado para no saturar tokens
        if not df_jugadores.empty:
            summary = df_jugadores[['Nombre', 'Apellido', 'Posicion', 'Categoria', 'Estado']].to_string(index=False)
            context_text += summary + "\n\n"
        
        # 2. ÁREA MÉDICA
        # ID: 1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ (Default en area_medica.py)
        try:
            sheet_medica = client.open_by_key("1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ")
            ws_medica = sheet_medica.get_worksheet(0) # Primera hoja
            data_medica = ws_medica.get_all_records()
            df_medica = pd.DataFrame(data_medica)
            
            context_text += f"=== REGISTRO MÉDICO/LESIONES ({len(df_medica)} casos) ===\n"
            if not df_medica.empty:
                # Filtrar columnas relevantes si existen
                cols_med = [c for c in ['Nombre del Paciente', 'Diagnóstico', 'Severidad de la lesión', 'Fecha de la lesión', 'Estado'] if c in df_medica.columns]
                context_text += df_medica[cols_med].to_string(index=False) + "\n\n"
        except Exception as e:
            context_text += f"Error cargando Área Médica: {str(e)}\n\n"

        # 3. ÁREA FÍSICA
        # ID: 1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI
        try:
            sheet_fisica = client.open_by_key("1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI")
            # Buscar hoja "Base Test"
            try:
                ws_fisica = sheet_fisica.worksheet("Base Test")
            except:
                ws_fisica = sheet_fisica.get_worksheet(0)
                
            data_fisica = ws_fisica.get_all_records()
            df_fisica = pd.DataFrame(data_fisica)
            
            context_text += f"=== DATOS FÍSICOS/TESTS ({len(df_fisica)} registros) ===\n"
            if not df_fisica.empty:
                # Seleccionar columnas clave
                cols_fis = [c for c in ['Nombre y Apellido', 'Test', 'valor', 'unidad', 'Fecha'] if c in df_fisica.columns]
                context_text += df_fisica[cols_fis].head(100).to_string(index=False) + "\n(Limitado a los primeros 100 registros físicos por espacio)\n\n"
        except Exception as e:
            context_text += f"Error cargando Área Física: {str(e)}\n\n"
            
        return context_text

    except Exception as e:
        return f"Error general cargando datos: {str(e)}"

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
def main_bot():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; border: 1px solid #334155;">
        <h1 style="color: white; text-align: center; margin: 0;">🤖 Asistente Inteligente Universitario</h1>
        <p style="color: #94a3b8; text-align: center; margin: 0.5rem 0 0 0;">Consulta sobre Jugadores, Salud y Rendimiento Físico</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Configuración Ollama ---
    with st.sidebar:
        st.markdown("### 🦙 Configuración Ollama")
        
        # Selección de modelo
        model_options = ["llama3.1", "mistral", "gemma2", "phi3", "llama3", "llama2"]
        selected_model = st.selectbox("Seleccionar Modelo", model_options, index=0)
        
        # Configuración de URL (por defecto localhost)
        ollama_url = st.text_input("URL del Servidor Ollama", value="http://localhost:11434")
        
        st.markdown("---")
        st.caption("Asegúrate de tener Ollama corriendo (`ollama serve`) y el modelo descargado (`ollama pull llama3.1`).")

        # Verificación rápida de conexión (opcional)
        status_placeholder = st.empty()
        
        st.info("💡 Puedes preguntar:\n- ¿Quiénes son los pilares de la M19?\n- ¿Qué jugadores están lesionados actualmente?\n- ¿Cuál es el récord de Press Banca?\n- Resumen médico de Juan Perez")

    # Intentar verificar conexión al inicio (silencioso) o cuando se presiona un botón
    # Mantener simple: solo intentar llamar a la API cuando se pregunta.

    # --- Historial de Chat ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Cargar Contexto ---
    if "data_context" not in st.session_state:
        with st.spinner("🔄 Conectando con las bases de datos del club..."):
            st.session_state.data_context = load_all_data()
            if "Error" not in st.session_state.data_context:
                st.success("✅ Datos cargados correctamente en la memoria del agente.")
            else:
                st.error("⚠️ Hubo problemas cargando algunos datos.")

    # --- Mostrar Chat ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Input de Usuario ---
    if prompt := st.chat_input("Escribe tu consulta aquí..."):
        # 1. Mostrar mensaje usuario
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner(f"Pensando con {selected_model}..."):
                try:
                    # Construir prompt con contexto
                    full_prompt = f"""
                    Eres el asistente virtual oficial del Club Universitario de La Plata.
                    Tu misión es ayudar al cuerpo técnico y directivos respondiendo preguntas basadas en los datos del club.
                    
                    DATOS DISPONIBLES:
                    {st.session_state.data_context}
                    
                    PREGUNTA DEL USUARIO:
                    {prompt}
                    
                    INSTRUCCIONES:
                    - Responde de forma amable, profesional y concisa.
                    - Si la respuesta está en los datos, cítala.
                    - Si no encuentras la información, dilo honestamente.
                    - Formatea la respuesta usando Markdown (tablas, listas, negritas) para que sea legible.
                    """
                    
                    # Llamada a Ollama API
                    payload = {
                        "model": selected_model,
                        "prompt": full_prompt,
                        "stream": False
                    }
                    
                    try:
                        response = requests.post(f"{ollama_url}/api/generate", json=payload)
                        if response.status_code == 200:
                            response_text = response.json().get('response', "⚠️ La respuesta vino vacía.")
                            st.markdown(response_text)
                            st.session_state.messages.append({"role": "assistant", "content": response_text})
                        else:
                            st.error(f"Error Ollama ({response.status_code}): {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error(f"❌ No se pudo conectar a Ollama en {ollama_url}. \n\nAsegurate de:\n1. Tener [Ollama](https://ollama.com/) instalado.\n2. Estar ejecutando la aplicación (`ollama serve`).\n3. Haber descargado el modelo (ej: `ollama pull {selected_model}`).")
                    except Exception as req_err:
                         st.error(f"Error en la petición: {req_err}")

                except Exception as e:
                    st.error(f"Error generando respuesta: {e}")

    # Botón limpiar historial
    if len(st.session_state.messages) > 0:
        if st.button("🗑️ Borrar Historial", type="primary"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    check_standalone()
    main_bot()
