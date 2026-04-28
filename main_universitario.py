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

def inject_mobile_meta():
    """Inyecta metadatos para que la app se vea bien en dispositivos móviles (icono PWA)"""
    logo_b64 = get_base64_image("escudo uni.jpg")
    if logo_b64:
        st.markdown(f"""
        <script>
            try {{
                function updateHeadTag(tagName, attributes) {{
                    var head = window.parent.document.head;
                    var selector = tagName;
                    if (attributes.rel) selector += "[rel='" + attributes.rel + "']";
                    if (attributes.name) selector += "[name='" + attributes.name + "']";
                    
                    var element = window.parent.document.querySelector(selector) || window.parent.document.createElement(tagName);
                    for (var key in attributes) {{
                        element.setAttribute(key, attributes[key]);
                    }}
                    if (!element.parentNode) head.appendChild(element);
                }}

                updateHeadTag('link', {{
                    rel: 'apple-touch-icon',
                    href: 'data:image/jpeg;base64,{logo_b64}'
                }});

                updateHeadTag('link', {{
                    rel: 'shortcut icon',
                    href: 'data:image/jpeg;base64,{logo_b64}'
                }});

                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-capable', content: 'yes' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-title', content: 'Universitario' }});
                updateHeadTag('meta', {{ name: 'mobile-web-app-capable', content: 'yes' }});
            }} catch (e) {{
                console.warn("Mobile meta injection blocked or failed:", e);
            }}
        </script>
        """, unsafe_allow_html=True)

# Configuración de la página
st.set_page_config(
    page_title="Club Universitario de La Plata - Sistema de Gestión",
    page_icon="escudo uni.jpg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para el Universitario (Negro y Blanco)
def load_universitario_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== VARIABLES ===== */
    :root {
        --uni-black: #000000;
        --uni-white: #FFFFFF;
        --uni-gray-light: #F5F5F5;
        --uni-gray-dark: #2C2C2C;
    }

    /* ===== BASE ===== */
    * { box-sizing: border-box; }
    .stApp { font-family: 'Inter', sans-serif !important; background: #FFFFFF; }

    /* ===== OCULTAR ELEMENTOS DE STREAMLIT ===== */
    .stDeployButton { display: none !important; }
    footer { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }

    /* ===== SIDEBAR — DESKTOP ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%) !important;
    }
    [data-testid="stSidebar"] * { color: white !important; }

    /* Sidebar buttons — compact on desktop */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.07) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
        height: 38px !important;
        min-height: unset !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        margin-bottom: 3px !important;
        padding: 0 0.75rem !important;
        transition: background 0.15s ease !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.15) !important;
        transform: none !important;
    }
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: rgba(255,255,255,0.45) !important;
        font-size: 0.68rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        margin: 0.9rem 0 0.35rem 0 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
        margin: 0.4rem 0 !important;
    }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ===== BOTONES GENERALES — DESKTOP ===== */
    .stButton > button {
        background: linear-gradient(135deg, #000000, #2C2C2C) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        height: 38px !important;
        min-height: unset !important;
        padding: 0 1.25rem !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: opacity 0.2s ease, transform 0.1s ease !important;
        -webkit-tap-highlight-color: transparent !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }
    .stButton > button:active { transform: scale(0.98) !important; }

    /* ===== INPUTS — DESKTOP ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border-radius: 8px !important;
        border: 2px solid #E9ECEF !important;
        font-size: 0.9rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #000000 !important;
        box-shadow: 0 0 0 2px rgba(0,0,0,0.07) !important;
    }
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 2px solid #E9ECEF !important;
    }

    /* ===== HEADER ===== */
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%);
        padding: 2rem 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    .main-header h1 { color: white; font-size: clamp(1.3rem, 3.5vw, 2rem); margin: 0; }
    .main-header h3 { color: rgba(255,255,255,0.85); font-size: clamp(0.95rem, 2vw, 1.2rem); margin: 0.35rem 0 0; }
    .main-header p  { color: rgba(255,255,255,0.65); font-size: 0.9rem; margin: 0.25rem 0 0; }

    /* ===== CARDS ===== */
    .area-card {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.09);
        margin: 0.75rem 0;
        border-left: 5px solid #000000;
    }
    .metric-card {
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%);
        padding: 1.25rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-3px); }
    .metric-card h3 { margin: 0; font-size: 2rem; font-weight: 700; color: white; }
    .metric-card p  { margin: 0.3rem 0 0; font-size: 0.88rem; opacity: 0.85; color: white; }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] { gap: 6px !important; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        height: 38px !important;
    }

    /* ===== DATAFRAMES — scroll horizontal siempre ===== */
    [data-testid="stDataFrame"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* ===== PLOTLY — responsive ===== */
    .js-plotly-plot { max-width: 100% !important; }

    /* ===== BOTTOM NAV — hidden by default ===== */
    .mobile-bottom-nav { display: none !important; }

    /* ==================================================
       RESPONSIVE — TABLET (≤ 900px)
    ================================================== */
    @media (max-width: 900px) {
        .main .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }

    /* ==================================================
       RESPONSIVE — MOBILE (≤ 640px)
    ================================================== */
    @media (max-width: 640px) {
        /* Espacio para bottom nav */
        .main .block-container {
            padding: 0.5rem 0.5rem 5rem !important;
        }

        .main-header { padding: 1.1rem 0.9rem; border-radius: 10px; }
        .area-card   { padding: 0.9rem; }

        /* Touch targets grandes en móvil */
        .stButton > button {
            height: 50px !important;
            font-size: 1rem !important;
            border-radius: 10px !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            height: 48px !important;
            font-size: 0.95rem !important;
        }
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            min-height: 48px !important;
            font-size: 1rem !important;
        }

        /* Tabs scrollables */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: none !important;
        }
        .stTabs [data-baseweb="tab"] {
            white-space: nowrap !important;
            height: 44px !important;
        }

        /* Charts full width */
        .js-plotly-plot, .plot-container { width: 100% !important; }

        /* BOTTOM NAV — visible en móvil */
        .mobile-bottom-nav {
            display: flex !important;
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 9999 !important;
            background: #000000 !important;
            justify-content: space-around !important;
            align-items: center !important;
            padding: 0.45rem 0.2rem !important;
            box-shadow: 0 -3px 16px rgba(0,0,0,0.35) !important;
            border-top: 1px solid rgba(255,255,255,0.08) !important;
        }
        .mobile-bottom-nav a {
            color: rgba(255,255,255,0.65) !important;
            text-decoration: none !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            font-size: 0.62rem !important;
            font-weight: 500 !important;
            min-width: 48px !important;
            padding: 0.2rem !important;
            -webkit-tap-highlight-color: transparent !important;
        }
        .mobile-bottom-nav a span.icon { font-size: 1.35rem !important; }
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
    st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)
    password = st.text_input("CONTRASEÑA", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed", key="password_input")
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    # Botón centrado usando columnas
    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        login_clicked = st.button("INGRESAR", use_container_width=True, key="login_btn")

    if login_clicked:
        if auth_manager.login(username, password):
            st.success("✅ Acceso exitoso")
            if st.session_state.user.get('rol') == "Jugador":
                st.session_state.current_page = "wellness"
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
    
    # Estado de la conexión (Solo visible para diagnóstico si falla)
    if not auth_manager.gs_manager.credentials_loaded:
        st.error("⚠️ Error: No se detectaron credenciales de Google. Los jugadores no podrán ingresar.")
        st.info("Asegúrate de haber configurado las variables GOOGLE_CLIENT_EMAIL y GOOGLE_PRIVATE_KEY en Railway.")
    else:
        # Mostrar discretamente el email de servicio para verificar permisos
        try:
            email = auth_manager.gs_manager.client.auth.signer_email
            st.markdown(f"""
            <div style="text-align: center; margin-top: 1rem; color: rgba(255,255,255,0.4); font-size: 0.7rem;">
                Conectado como: {email}
            </div>
            """, unsafe_allow_html=True)
        except: pass

    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.7); font-size: 0.85rem;">
        <p>🔑 Acceso Seguro mediante Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)

def main_dashboard():
    load_universitario_styles()
    auth_manager = AuthManager()
    user = st.session_state.user

    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:1rem 0.5rem 0.75rem; margin-bottom:0.5rem;">
            <div style="font-size:2.5rem;">🏉</div>
            <div style="font-weight:700; font-size:1.05rem; color:white; margin-top:0.25rem;">
                {user['nombre']}
            </div>
            <div style="font-size:0.8rem; color:rgba(255,255,255,0.55); margin-top:0.15rem;">
                {user['rol']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🧭 Navegación")
        if st.button("🏠 Inicio", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()
        if auth_manager.has_permission("perfil"):
            label_perfil = "👤 Mi Perfil" if user.get('rol') == "Jugador" else "👤 Perfil"
            if st.button(label_perfil, use_container_width=True):
                st.session_state.current_page = "perfil"
                st.rerun()

        st.markdown("#### 📋 Módulos")
        modules = [
            ("🏥 Área Médica",    "medica"),
            ("🥗 Nutrición",      "nutricion"),
            ("🏋️ Área Física",   "fisica"),
            ("📝 Wellness",      "wellness"),
            ("📊 Dashboard 360°", "dashboard_360"),
            ("📝 Reporte Médico", "reporte_medico"),
        ]
        for label, page_id in modules:
            if auth_manager.has_permission(page_id):
                if st.button(label, use_container_width=True):
                    st.session_state.current_page = page_id
                    st.rerun()

        st.markdown("#### ⚙️ Admin")
        if auth_manager.has_permission("bot"):
            if st.button("🧠 Asistente IA", use_container_width=True):
                st.session_state.current_page = "bot"
                st.rerun()
        if auth_manager.has_permission("administracion"):
            if st.button("👥 Gestión Jugadores", use_container_width=True):
                st.session_state.current_page = "administracion"
                st.rerun()
        if auth_manager.has_permission("lista"):
            if st.button("📋 Pasar Lista", use_container_width=True):
                st.session_state.current_page = "lista"
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            auth_manager.logout()

    # ===== MOBILE BOTTOM NAV =====
    # Build nav items from permitted pages
    nav_items = [("🏠", "Inicio", "dashboard")]
    if auth_manager.has_permission("perfil"):
        nav_items.append(("👤", "Perfil", "perfil"))
    if auth_manager.has_permission("fisica"):
        nav_items.append(("🏋️", "Física", "fisica"))
    if auth_manager.has_permission("medica"):
        nav_items.append(("🏥", "Médica", "medica"))
    if auth_manager.has_permission("nutricion"):
        nav_items.append(("🥗", "Nutrición", "nutricion"))
    if auth_manager.has_permission("wellness"):
        nav_items.append(("📝", "Wellness", "wellness"))

    # Limit to 5 for bottom nav
    nav_items = nav_items[:5]

    # ===== MOBILE BOTTOM NAV: botones ocultos para ruteo =====
    # Técnica: ponemos un span marcador, luego los botones en columnas.
    # CSS usa el selector de hermano (+) para ocultar el bloque de columnas
    # sin afectar el resto del contenido.
    st.markdown('<span id="nav-row-marker" style="display:none;"></span>', unsafe_allow_html=True)
    st.markdown("""
        <style>
        /* Ocultar la fila de columnas que viene inmediatamente después del marcador */
        div[data-testid="stElementContainer"]:has(#nav-row-marker) + div[data-testid="stHorizontalBlock"],
        div[data-testid="stElementContainer"]:has(#nav-row-marker) + div[data-testid="stColumns"],
        div[data-testid="stElementContainer"]:has(#nav-row-marker) + div {
            position: absolute !important;
            top: -9999px !important;
            left: -9999px !important;
            opacity: 0 !important;
            pointer-events: none !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        /* Permitir clicks en los botones aunque estén fuera de pantalla */
        div[data-testid="stElementContainer"]:has(#nav-row-marker) + div button {
            pointer-events: all !important;
        }
        /* Tambien ocultar el propio marcador */
        div[data-testid="stElementContainer"]:has(#nav-row-marker) {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Fila de botones nativos de Streamlit (se oculta via CSS pero siguen siendo clickeables)
    nav_btn_cols = st.columns(len(nav_items))
    for i, (icon, label, page_id) in enumerate(nav_items):
        with nav_btn_cols[i]:
            if st.button(label, key=f"mob_nav_{page_id}", use_container_width=True):
                st.session_state.current_page = page_id
                st.rerun()

    # ===== HTML BOTTOM NAV BAR (pure HTML, fijo al fondo) =====
    current_page = st.session_state.get("current_page", "dashboard")
    nav_links_html = ""
    for icon, label, page_id in nav_items:
        active_class = "active" if current_page == page_id else ""
        # JS: encuentra el boton de Streamlit por su texto y le hace click
        js_click = f"event.preventDefault(); (function(){{ var btns=document.querySelectorAll('div.nav-hidden-btn-row button'); for(var i=0;i<btns.length;i++){{ if(btns[i].innerText.trim()==='{label}') {{ btns[i].click(); break; }} }} }})();"
        nav_links_html += f'<a href="#" onclick="{js_click}" class="mbn-item {active_class}"><span class="mbn-icon">{icon}</span><span class="mbn-label">{label}</span></a>'

    st.markdown(f"""
        <style>
        /* Desktop: ocultar la barra */
        .mobile-bottom-nav {{ display: none !important; }}

        /* Mobile: mostrar fija al fondo */
        @media (max-width: 768px) {{
            .mobile-bottom-nav {{
                display: flex !important;
                flex-direction: row !important;
                position: fixed !important;
                bottom: 0 !important;
                left: 0 !important;
                right: 0 !important;
                width: 100% !important;
                z-index: 999999 !important;
                background: #0d0d0d !important;
                border-top: 1px solid rgba(255,255,255,0.1) !important;
                box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
                padding: 6px 0 8px !important;
                margin: 0 !important;
                justify-content: space-around !important;
                align-items: center !important;
            }}
            .mbn-item {{
                flex: 1 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 3px !important;
                padding: 4px 2px !important;
                color: rgba(255,255,255,0.45) !important;
                text-decoration: none !important;
                font-family: inherit !important;
                transition: color 0.15s ease !important;
                -webkit-tap-highlight-color: transparent !important;
            }}
            .mbn-item.active,
            .mbn-item:active {{
                color: #ffffff !important;
            }}
            .mbn-icon {{
                font-size: 1.3rem !important;
                line-height: 1 !important;
            }}
            .mbn-label {{
                font-size: 0.6rem !important;
                font-weight: 500 !important;
                letter-spacing: 0.02em !important;
                text-transform: uppercase !important;
            }}
            .mbn-item.active .mbn-label {{
                font-weight: 700 !important;
                color: #4fc3f7 !important;
            }}
            .mbn-item.active .mbn-icon {{
                color: #4fc3f7 !important;
            }}
            /* Espacio al final para que el contenido no quede tapado */
            section.main > div.block-container {{
                padding-bottom: 90px !important;
            }}
        }}
        </style>
        <div class="mobile-bottom-nav">
            {nav_links_html}
        </div>
    """, unsafe_allow_html=True)

    # ===== ROUTING =====
    page = st.session_state.get('current_page', 'dashboard')
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
            st.error(f"Error: No se encuentra 'main_nutricion'")
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
    elif page == "wellness":
        from src.modules.wellness import wellness_module
        wellness_module()
    elif page == "lista":
        from src.modules.Lista import main_lista
        main_lista()


def dashboard_main():
    """Dashboard principal del Club Universitario"""
    auth_manager = AuthManager()

    # Header
    logo_b64 = get_base64_image("escudo uni.jpg")
    img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width:clamp(80px,15vw,130px); margin-bottom:0.75rem; border-radius:10px; box-shadow:0 4px 15px rgba(0,0,0,0.3);">' if logo_b64 else ""

    st.markdown(f'<div class="main-header">{img_html}<h1>🏉 CLUB UNIVERSITARIO DE LA PLATA</h1><h3>Sistema de Gestión Deportiva</h3><p>Bienvenido, <strong>{st.session_state.user["nombre"]}</strong> · {st.session_state.user["rol"]}</p></div>', unsafe_allow_html=True)

    # All modules info
    all_modules_info = [
        {"id": "medica",       "icon": "🏥", "label": "Área Médica",    "color": "#dc3545",
         "desc": "Registro de lesiones, historial clínico y seguimiento de recuperación."},
        {"id": "nutricion",    "icon": "🥗", "label": "Nutrición",      "color": "#28a745",
         "desc": "Antropometría, planes nutricionales y composición corporal."},
        {"id": "fisica",       "icon": "🏋️", "label": "Área Física",   "color": "#fd7e14",
         "desc": "Evaluaciones físicas, tests y métricas de rendimiento."},
        {"id": "wellness",     "icon": "📝", "label": "Wellness",       "color": "#000000",
         "desc": "Monitoreo diario de sueño, fatiga y esfuerzo percibido."},
        {"id": "dashboard_360","icon": "📊", "label": "Dashboard 360°", "color": "#0d6efd",
         "desc": "Vista integral del jugador: médico, físico y nutricional."},
        {"id": "reporte_medico","icon":"📝", "label": "Reporte Médico", "color": "#6f42c1",
         "desc": "Consulta y emisión de reportes médicos detallados."},
        {"id": "bot",          "icon": "🧠", "label": "Asistente IA",   "color": "#20c997",
         "desc": "Consultor inteligente con acceso en tiempo real a los datos del club."},
        {"id": "administracion","icon":"👥", "label": "Gestión Jugadores","color": "#6c757d",
         "desc": "Alta, baja y modificación de jugadores en la base de datos."},
        {"id": "lista",        "icon": "📋", "label": "Pasar Lista",    "color": "#e83e8c",
         "desc": "Control de asistencia a entrenamientos y partidos."},
    ]

    allowed = [m for m in all_modules_info if auth_manager.has_permission(m["id"])]

    if not allowed:
        st.info("No tenés módulos habilitados para tu rol.")
        return

    # Responsive CSS grid (1 col mobile, 2 tablet, 3 desktop)
    cards_html = "".join([f'<div class="mod-card"><div class="mod-icon" style="background:{m["color"]}20; color:{m["color"]};">{m["icon"]}</div><div class="mod-label">{m["label"]}</div><div class="mod-desc">{m["desc"]}</div></div>' for m in allowed])

    st.markdown(f'<style>.mod-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr)); gap: 1rem; margin: 1.5rem 0; }} .mod-card {{ background: white; border-radius: 14px; padding: 1.5rem 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.09); border: 1px solid #f0f0f0; transition: all 0.2s ease; }} .mod-card:hover {{ box-shadow: 0 6px 20px rgba(0,0,0,0.14); transform: translateY(-2px); }} .mod-icon {{ width: 54px; height: 54px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin-bottom: 0.9rem; }} .mod-label {{ font-weight: 700; font-size: 1.05rem; color: #111; margin-bottom: 0.4rem; }} .mod-desc {{ font-size: 0.88rem; color: #666; line-height: 1.5; }}</style><div class="mod-grid">{cards_html}</div>', unsafe_allow_html=True)

    # Streamlit buttons below grid (they handle the actual navigation)
    st.markdown("#### 👇 Tocá el botón del módulo al que querés entrar:")
    cols_per_row = 3
    rows = [allowed[i:i+cols_per_row] for i in range(0, len(allowed), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, mod in zip(cols, row):
            with col:
                if st.button(f"{mod['icon']} {mod['label']}", use_container_width=True, key=f"dash_go_{mod['id']}"):
                    st.session_state.current_page = mod["id"]
                    st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:1.5rem; color:#888; font-size:0.85rem;">
        <strong>Club Universitario de La Plata</strong> · Sistema de Gestión Deportiva · © 2026
    </div>
    """, unsafe_allow_html=True)


def main():
    # Inicializar session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    inject_mobile_meta()
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()