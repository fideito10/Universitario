"""
Sistema de Login para el Club Argentino de Rugby (CAR)
Desarrollado con Streamlit
Autor: Sistema de Digitalización CAR
Fecha: Octubre 2025
"""

import streamlit as st
import pandas as pd
import json
import hashlib
import os
from PIL import Image
import base64
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="CAR - Club Argentino de Rugby",
    page_icon="🏉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Archivo de credenciales
CREDENTIALS_FILE = "users_credentials.json"

class AuthManager:
    """Clase para manejar la autenticación de usuarios"""
    
    def __init__(self):
        self.credentials_file = CREDENTIALS_FILE
        self.load_credentials()
    
    def load_credentials(self):
        """Cargar credenciales desde archivo JSON"""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            # Crear usuario administrador por defecto
            self.users = {
                "admin": {
                    "password": self.hash_password("admin123"),
                    "name": "Administrador",
                    "email": "admin@car.com.ar",
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            }
            self.save_credentials()
    
    def save_credentials(self):
        """Guardar credenciales en archivo JSON"""
        with open(self.credentials_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2, ensure_ascii=False)
    
    def hash_password(self, password):
        """Encriptar contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_credentials(self, username, password):
        """Verificar credenciales de usuario"""
        if username in self.users:
            hashed_password = self.hash_password(password)
            if self.users[username]["password"] == hashed_password:
                return True, self.users[username]
        return False, None
    
    def register_user(self, username, password, name, email):
        """Registrar nuevo usuario"""
        if username in self.users:
            return False, "El usuario ya existe"
        
        self.users[username] = {
            "password": self.hash_password(password),
            "name": name,
            "email": email,
            "role": "user",
            "created_at": datetime.now().isoformat()
        }
        self.save_credentials()
        return True, "Usuario creado exitosamente"

def load_css():
    """Cargar estilos CSS personalizados"""
    st.markdown("""
    <style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables de colores CAR */
    :root {
        --car-blue: #1A2C56;
        --car-light-blue: #6BB4E8;
        --car-white: #FFFFFF;
        --car-gray: #F8F9FA;
        --car-dark-gray: #495057;
    }
    
    /* Ocultar elementos de Streamlit */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #1A2C56 0%, #2C4A7A 50%, #6BB4E8 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Container principal */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        margin: 2rem auto;
        max-width: 500px;
    }
    
    /* Logo container */
    .logo-container {
        text-align: right;
        margin-bottom: 1rem;
    }
    
    /* Título principal */
    .main-title {
        color: #1A2C56;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Subtítulo */
    .subtitle {
        color: #6BB4E8;
        font-size: 1.1rem;
        font-weight: 400;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Campos de entrada */
    .stTextInput > div > div > input {
        border: 2px solid #E9ECEF;
        border-radius: 10px;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background-color: #F8F9FA;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6BB4E8;
        box-shadow: 0 0 0 0.2rem rgba(107, 180, 232, 0.25);
        background-color: white;
    }
    
    /* Botones personalizados */
    .custom-button {
        background: linear-gradient(45deg, #1A2C56, #6BB4E8);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.5rem 0;
    }
    
    .custom-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(107, 180, 232, 0.4);
    }
    
    /* Checkbox personalizado */
    .stCheckbox {
        margin: 1rem 0;
    }
    
    /* Mensajes de éxito y error */
    .stSuccess {
        background-color: #D4EDDA;
        border: 1px solid #C3E6CB;
        color: #155724;
        border-radius: 10px;
    }
    
    .stError {
        background-color: #F8D7DA;
        border: 1px solid #F5C6CB;
        color: #721C24;
        border-radius: 10px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #6C757D;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E9ECEF;
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .main-container {
            margin: 1rem;
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def get_base64_image(image_path):
    """Convertir imagen a base64 para mostrar en HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def show_logo():
    """Mostrar logo del club"""
    logo_path = "car.jpg"
    
    if os.path.exists(logo_path):
        try:
            # Cargar y mostrar la imagen
            image = Image.open(logo_path)
            # Redimensionar manteniendo proporción
            image.thumbnail((100, 100), Image.Resampling.LANCZOS)
            
            st.markdown("""
            <div class="logo-container">
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col3:
                st.image(image, width=100)
            
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            # Si hay error con la imagen, mostrar placeholder
            st.markdown("""
            <div class="logo-container">
                <div style="background: #1A2C56; color: white; padding: 10px 20px; 
                           border-radius: 10px; display: inline-block; font-weight: bold;">
                    🏉 CAR
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Placeholder si no existe la imagen
        st.markdown("""
        <div class="logo-container">
            <div style="background: #1A2C56; color: white; padding: 10px 20px; 
                       border-radius: 10px; display: inline-block; font-weight: bold;">
                🏉 CAR
            </div>
        </div>
        """, unsafe_allow_html=True)

def login_screen():
    """Pantalla principal de login"""
    
    # Cargar CSS personalizado
    load_css()
    
    # Container principal
    st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
    
    # Logo
    show_logo()
    
    # Título y subtítulo
    st.markdown("""
    <h1 class="main-title">CLUB ARGENTINO DE RUGBY</h1>
    <p class="subtitle">Digitalización de los Clubes</p>
    """, unsafe_allow_html=True)
    
    # Inicializar el gestor de autenticación
    auth_manager = AuthManager()
    
    # Tabs para Login y Registro
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta"])
    
    with tab1:
        st.markdown("### Acceso al Sistema")
        
        # Formulario de login
        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingrese su nombre de usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
            
            col1, col2 = st.columns(2)
            with col1:
                remember_me = st.checkbox("🔄 Recordarme")
            
            submit_login = st.form_submit_button("🚀 INGRESAR", use_container_width=True)
            
            if submit_login:
                if not username or not password:
                    st.error("⚠️ Por favor, complete todos los campos")
                else:
                    success, user_data = auth_manager.verify_credentials(username, password)
                    
                    if success:
                        # Guardar estado de sesión
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_data = user_data
                        
                        if remember_me:
                            st.session_state.remember_session = True
                        
                        st.success(f"✅ ¡Bienvenido al sistema del Club Argentino de Rugby, {user_data['name']}!")
                        st.balloons()
                        
                        # Mostrar información de bienvenida
                        st.markdown("""
                        <div style="background: linear-gradient(45deg, #1A2C56, #6BB4E8); 
                                   color: white; padding: 20px; border-radius: 10px; 
                                   text-align: center; margin: 20px 0;">
                            <h3>🎉 Acceso Exitoso</h3>
                            <p>Has ingresado correctamente al sistema de digitalización del CAR</p>
                            <p><strong>Rol:</strong> {}</p>
                            <p><strong>Último acceso:</strong> {}</p>
                        </div>
                        """.format(
                            user_data.get('role', 'Usuario').title(),
                            datetime.now().strftime("%d/%m/%Y %H:%M")
                        ), unsafe_allow_html=True)
                        
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
    
    with tab2:
        st.markdown("### Registro de Nuevo Usuario")
        
        with st.form("register_form"):
            new_username = st.text_input("👤 Nombre de Usuario", placeholder="Elija un nombre de usuario")
            new_name = st.text_input("👨‍💼 Nombre Completo", placeholder="Su nombre completo")
            new_email = st.text_input("📧 Email", placeholder="correo@ejemplo.com")
            new_password = st.text_input("🔒 Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            confirm_password = st.text_input("🔒 Confirmar Contraseña", type="password", placeholder="Repita la contraseña")
            
            submit_register = st.form_submit_button("✨ CREAR CUENTA", use_container_width=True)
            
            if submit_register:
                # Validaciones
                if not all([new_username, new_name, new_email, new_password, confirm_password]):
                    st.error("⚠️ Por favor, complete todos los campos")
                elif len(new_password) < 6:
                    st.error("⚠️ La contraseña debe tener al menos 6 caracteres")
                elif new_password != confirm_password:
                    st.error("⚠️ Las contraseñas no coinciden")
                elif "@" not in new_email:
                    st.error("⚠️ Ingrese un email válido")
                else:
                    success, message = auth_manager.register_user(new_username, new_password, new_name, new_email)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info("🔄 Ahora puede iniciar sesión con sus credenciales")
                    else:
                        st.error(f"❌ {message}")
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© 2025 Club Argentino de Rugby | Sistema de Gestión Digitalizada</p>
        <p>🏉 Desarrollado con ❤️ para la digitalización deportiva</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    """Aplicación principal después del login"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🏉 Bienvenido al Sistema CAR</h1>
        <h3>Panel Principal - Club Argentino de Rugby</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Cerrar Sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def main():
    """Función principal de la aplicación"""
    
    # Verificar si el usuario está logueado
    if st.session_state.get('logged_in', False):
        main_app()
    else:
        login_screen()

if __name__ == "__main__":
    main()