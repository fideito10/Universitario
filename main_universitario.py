"""
Sistema Principal del Club Universitario de La Plata
Centralización de Módulos: Área Médica, Nutrición y Física
Desarrollado con Streamlit
"""
import streamlit as st
import os
from datetime import datetime
import base64
from src.security.auth import AuthManager

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Configuración de la página
st.set_page_config(
    page_title="Club Universitario de La Plata - Sistema de Gestión",
    page_icon="escudo uni.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para el Universitario (Negro y Blanco)
def load_universitario_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    :root {
        --uni-black: #000000;
        --uni-white: #FFFFFF;
        --uni-gray-light: #F5F5F5;
        --uni-gray-dark: #2C2C2C;
        --uni-accent: #1A1A1A;
    }
    .stApp {
        font-family: 'Inter', sans-serif;
        background: #FFFFFF;
    }
    .main-header {
        background: linear-gradient(135deg, var(--uni-black) 0%, var(--uni-gray-dark) 100%);
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: var(--uni-white);
        font-family: 'Inter', sans-serif;
        border: 3px solid var(--uni-black);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        color: var(--uni-white);
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin: 0;
    }
    .main-header h3 {
        color: var(--uni-white);
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
    }
    .main-header p {
        color: var(--uni-white);
        opacity: 0.8;
        margin: 0.5rem 0 0 0;
    }
    .area-card {
        background: var(--uni-white);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        margin: 1rem 0;
        border: 2px solid var(--uni-black);
        border-left: 5px solid var(--uni-black);
    }
    .metric-card {
        background: linear-gradient(135deg, var(--uni-black) 0%, var(--uni-gray-dark) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: var(--uni-white);
        text-align: center;
        margin: 0.5rem 0;
        border: 2px solid var(--uni-white);
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--uni-white);
    }
    .metric-card p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.9;
        color: var(--uni-white);
    }
    .login-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border: 3px solid var(--uni-black);
    }
    .stButton > button {
        background: linear-gradient(45deg, var(--uni-black), var(--uni-gray-dark));
        color: var(--uni-white);
        border: 2px solid var(--uni-white);
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.4);
        background: linear-gradient(45deg, var(--uni-gray-dark), var(--uni-black));
    }
    .stSelectbox > div > div > select,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #E9ECEF;
    }
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    
    /* Responsive Design para Dashboard */
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .main-header h1 {
            font-size: 1.8rem;
        }
        .main-header h3 {
            font-size: 1.2rem;
        }
        .main-header img {
            width: 100px !important;
        }
        .area-card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def login_page():
    bg_image = get_base64_image("Fondo.JPG")
    
    # CSS personalizado para el login con imagen de fondo
    if bg_image:
        bg_style = f"""
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bg_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            font-family: 'Inter', sans-serif;
        }}
        """
    else:
        bg_style = """
        .stApp {
            background: linear-gradient(135deg, #1A1A1A 0%, #3D3D3D 100%);
            font-family: 'Inter', sans-serif;
        }
        """
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Ocultar elementos de Streamlit */
    .stApp > header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    
    /* Fondo con imagen */
    {bg_style}
    
    /* Overlay oscuro sobre la imagen */
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.65);
        z-index: 0;
    }}
    
    /* Contenedor principal */
    .main .block-container {{
        position: relative;
        z-index: 1;
        padding-top: 5rem;
        max-width: 500px;
        margin: 0 auto;
    }}
    
    /* Título principal */
    .login-title {{
        text-align: center;
        color: white;
        margin-bottom: 3rem;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.8);
    }}
    
    .login-title h1 {{
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    
    .login-title h2 {{
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0.5rem 0 0 0;
        letter-spacing: 8px;
        color: #FFFFFF;
    }}
    
    .login-subtitle {{
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.95;
        letter-spacing: 2px;
    }}
    
    /* Contenedor del formulario */
    .login-box {{
        background: rgba(255, 255, 255, 0.98);
        border-radius: 15px;
        padding: 1.5rem 1.5rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        max-width: 400px;
        margin: 0 auto;
    }}
    
    /* Ocultar espacios blancos de Streamlit */
    .main .block-container .element-container:has(.login-box) {{
        padding: 0;
        margin: 0;
    }}
    
    div[data-testid="stVerticalBlock"] > div:has(.login-box) {{
        gap: 0;
    }}
    
    /* Eliminar espacios dentro del login-box */
    .login-box + div {{
        display: none;
    }}
    
    div[data-testid="stVerticalBlock"]:has(.login-box) > div {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        gap: 0.5rem !important;
    }}
    
    div[data-testid="stVerticalBlock"]:has(.login-box) {{
        gap: 0.5rem !important;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input {{
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        max-width: 350px;
        width: 100%;
    }}
    
    .stTextInput > div {{
        max-width: 350px;
        margin: 0 auto;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #000000;
        box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
    }}
    

    /* Centrar el contenedor del botón */
    /* Centrar el contenedor del botón */
    div.stButton {{
        display: flex;
        justify-content: center;
    }}

    /* Botón de ingresar */
    .stButton > button {{
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        max-width: 350px;
        margin: 0 auto;
        display: block;
        margin-top: 1rem;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, #2C2C2C 0%, #000000 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    }}
    
    /* Link de olvidaste contraseña */
    .forgot-password {{
        text-align: center;
        margin-top: 1rem;
    }}
    
    .forgot-password a {{
        color: #333;
        text-decoration: none;
        font-size: 0.9rem;
        transition: color 0.3s ease;
    }}
    
    .forgot-password a:hover {{
        color: #000;
        text-decoration: underline;
    }}
    
    /* Responsive Design para Móviles */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-top: 2rem;
            max-width: 90%;
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        
        .login-title h1 {{
            font-size: 1.8rem;
            letter-spacing: 0.5px;
        }}
        
        .login-title h2 {{
            font-size: 2.5rem;
            letter-spacing: 4px;
        }}
        
        .login-subtitle {{
            font-size: 0.9rem;
            letter-spacing: 1px;
        }}
        
        .login-box {{
            padding: 1.5rem 1.25rem;
            border-radius: 12px;
        }}
        
        .stTextInput > div > div > input {{
            padding: 0.6rem 0.75rem;
            font-size: 0.9rem;
        }}
        
        .stButton > button {{
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
        }}
    }}
    
    @media (max-width: 480px) {{
        .login-title {{
            margin-bottom: 2rem;
        }}
        
        .login-title h1 {{
            font-size: 1.4rem;
        }}
        
        .login-title h2 {{
            font-size: 2rem;
            letter-spacing: 3px;
        }}
        
        .login-subtitle {{
            font-size: 0.8rem;
        }}
        
        .login-box {{
            padding: 1.25rem 1rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown("""
    <div class="login-title">
        <h1>Club Universitario de La Plata</h1>
        <h2>2026</h2>
        <p class="login-subtitle">ACCESO AL SISTEMA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login (sin contenedor blanco)
    auth_manager = AuthManager()
    
    username = st.text_input("USUARIO", placeholder="Ingresa tu usuario", label_visibility="collapsed", key="username_input")
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    
    password = st.text_input("CONTRASEÑA", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed", key="password_input")
    
    if st.button("INGRESAR"):
        if auth_manager.login(username, password):
            st.success("✅ Acceso exitoso")
            # Si el usuario es un jugador, enviarlo directo a su perfil
            if st.session_state.user.get('rol') == "Jugador":
                st.session_state.current_page = "perfil"
            else:
                st.session_state.current_page = "dashboard"
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    
    st.markdown("""
    <div class="forgot-password">
        <a href="#">¿Olvidaste tu contraseña?</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Credenciales de prueba (pequeño y discreto)
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.7); font-size: 0.85rem;">
        <p>🔑 Acceso Seguro mediante Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)

def main_dashboard():
    load_universitario_styles()
    auth_manager = AuthManager()
    user = st.session_state.user
    
    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #000000, #2C2C2C); 
                color: white; border-radius: 10px; margin-bottom: 1rem; border: 2px solid white;">
        <h3>👋 Bienvenido</h3>
        <p><strong>{user['nombre']}</strong></p>
        <p>🏷️ {user['rol']}</p>
        <p>🏉 Universitario - Sistema Digital</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### 🧭 Menú Principal")
    
    if st.sidebar.button("🏠 Portada", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
    
    if auth_manager.has_permission("perfil"):
        label_perfil = "👤 Mi Perfil" if st.session_state.user.get('rol') == "Jugador" else "👤 Perfil de Usuario"
        if st.sidebar.button(label_perfil, use_container_width=True):
            st.session_state.current_page = "perfil"
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Módulos")
    
    # Mapeo de botones a sus IDs de página
    modules = [
        ("🏥 Área Médica", "medica"),
        ("🥗 Área Nutrición", "nutricion"),
        ("🏋️ Área Física", "fisica"),
        ("📊 Dashboard 360°", "dashboard_360"),
        ("📝 Reporte Médico", "reporte_medico")
    ]
    
    for label, page_id in modules:
        if auth_manager.has_permission(page_id):
            if st.sidebar.button(label, use_container_width=True):
                st.session_state.current_page = page_id
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 Asistente")

    if auth_manager.has_permission("bot"):
        if st.sidebar.button("🧠 Asistente IA", use_container_width=True):
            st.session_state.current_page = "bot"
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Administración")
    
    if auth_manager.has_permission("administracion"):
        if st.sidebar.button("👥 Gestión Jugadores", use_container_width=True):
            st.session_state.current_page = "administracion"
            st.rerun()
    
    if auth_manager.has_permission("lista"):
        if st.sidebar.button("📋 Pasar Lista", use_container_width=True):
            st.session_state.current_page = "lista"
            st.rerun()
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("⬅️ Volver a Portada", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
        
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        auth_manager.logout()
    
    # Contenido principal - Enrutamiento
    page = st.session_state.get('current_page', 'dashboard')
    
    # Verificación de seguridad adicional
    if not auth_manager.has_permission(page):
        st.error("🚫 No tienes permiso para acceder a este módulo.")
        st.session_state.current_page = "dashboard"
        st.rerun()

    if page == "dashboard":
        dashboard_main()
    elif page == "medica":
        from src.modules.areamedica import main_streamlit
        main_streamlit()
    elif page == "nutricion":
        import src.modules.areanutricion as mod_nutricion
        import importlib
        importlib.reload(mod_nutricion)
        if hasattr(mod_nutricion, 'main_nutricion'):
            mod_nutricion.main_nutricion()
        else:
            st.error(f"Error: No se encuentra 'main_nutricion' en {mod_nutricion.__file__}")
            st.write("Funciones disponibles:", [f for f in dir(mod_nutricion) if not f.startswith('__')])
    elif page == "fisica":
        from src.modules.areafisica import physical_area
        physical_area()
    elif page == "dashboard_360":
        from src.modules.dashboard_360 import panel_profesional_jugador
        panel_profesional_jugador()
    elif page == "reporte_medico":
        from src.modules.reportemedico import main_reporte_medico
        main_reporte_medico()
    elif page == "bot":
        from src.modules.bot import main_bot
        main_bot()
    elif page == "administracion":
        from src.modules.administracion import main_administracion
        main_administracion()
    elif page == "perfil":
        from src.modules.perfil_jugador import main_perfil_jugador
        main_perfil_jugador()
    elif page == "lista":
        from src.modules.Lista import main_lista
        main_lista()

def dashboard_main():
    """Dashboard principal del Club Universitario"""
    auth_manager = AuthManager()
    
    # Cargar logo
    logo_b64 = get_base64_image("escudo uni.jpg")
    if logo_b64:
        img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width: 150px; margin-bottom: 1rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">'
    else:
        img_html = ""

    st.markdown(f"""
    <div class="main-header">
        {img_html}
        <h1>🏉 CLUB UNIVERSITARIO DE LA PLATA</h1>
        <h3>Sistema de Gestión Deportiva</h3>
        <p>Centralización de datos médicos, físicos y nutricionales</p>
        <div style="margin-top: 2rem; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);">
            <p style="font-size: 1.15rem; line-height: 1.8; max-width: 900px; margin: 0 auto; color: #E0E0E0; font-weight: 300;">
                Bienvenido al sistema integral del Club Universitario. 
                Tu rol como <strong>{st.session_state.user['rol']}</strong> te permite acceder a los módulos de gestión habilitados para tu perfil.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Secciones informativas dinámicas según permisos
    st.markdown("---")
    st.markdown("""
    <h2 style='color: #000000; text-align: center; margin: 2rem 0 1rem 0;'>
        🎯 Módulos Habilitados
    </h2>
    """, unsafe_allow_html=True)
    
    # Módulos informativos para el dashboard
    all_modules_info = [
        {
            "id": "medica",
            "label": "🏥 Área Médica",
            "desc": ["Registro de lesiones", "Historial médico", "Seguimiento de recuperación"]
        },
        {
            "id": "nutricion",
            "label": "🥗 Área Nutrición",
            "desc": ["Planes nutricionales", "Seguimiento de dietas", "Análisis de composición"]
        },
        {
            "id": "fisica",
            "label": "🏋️ Área Física",
            "desc": ["Planes de entrenamiento", "Evaluaciones físicas", "Métricas de rendimiento"]
        }
    ]
    
    allowed_info = [m for m in all_modules_info if auth_manager.has_permission(m["id"])]
    
    if allowed_info:
        cols = st.columns(len(allowed_info))
        for i, mod in enumerate(allowed_info):
            with cols[i]:
                st.markdown('<div class="area-card">', unsafe_allow_html=True)
                if st.button(mod["label"], use_container_width=True, key=f"dash_{mod['id']}_btn"):
                    st.session_state.current_page = mod["id"]
                    st.rerun()
                for d in mod["desc"]:
                    st.write(f"- {d}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #2C2C2C;">
        <p><strong>Club Universitario de La Plata</strong></p>
        <p>Sistema de Gestión Deportiva • © 2025</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Inicializar session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()