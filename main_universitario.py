"""
Sistema Principal del Club Universitario de La Plata
Centralización de Módulos: Área Médica, Nutrición y Física
Desarrollado con Streamlit
"""
import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime
import base64
from src.security.auth import AuthManager, get_auth_manager
from src.security import remember
from src.utils.cache import cache_si_ok

@cache_si_ok(ttl=3600)
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
        # components.html ejecuta el JS (st.markdown no ejecuta <script>)
        components.html(f"""
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

                // Icono para iPhone (Apple Touch Icon)
                updateHeadTag('link', {{
                    rel: 'apple-touch-icon',
                    href: 'data:image/jpeg;base64,{logo_b64}'
                }});

                // Icono para Android y otros
                updateHeadTag('link', {{
                    rel: 'shortcut icon',
                    href: 'data:image/jpeg;base64,{logo_b64}'
                }});

                // Configuración PWA para iPhone
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-capable', content: 'yes' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-title', content: 'Universitario' }});
                updateHeadTag('meta', {{ name: 'mobile-web-app-capable', content: 'yes' }});
                updateHeadTag('meta', {{ name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' }});
                updateHeadTag('meta', {{ name: 'theme-color', content: '#000000' }});
                updateHeadTag('meta', {{ name: 'format-detection', content: 'telephone=no' }});
                
                // Forzar el título del navegador
                window.parent.document.title = "Universitario - Sistema de Gestión";

                // Crear un manifiesto dinámico para que aparezca el logo al instalar
                const manifest = {{
                    "name": "Club Universitario de La Plata",
                    "short_name": "Universitario",
                    "start_url": "/",
                    "display": "standalone",
                    "background_color": "#000000",
                    "theme_color": "#000000",
                    "icons": [
                        {{
                            "src": "data:image/jpeg;base64,{logo_b64}",
                            "sizes": "192x192",
                            "type": "image/jpeg"
                        }},
                        {{
                            "src": "data:image/jpeg;base64,{logo_b64}",
                            "sizes": "512x512",
                            "type": "image/jpeg"
                        }}
                    ]
                }};
                const stringManifest = JSON.stringify(manifest);
                const blob = new Blob([stringManifest], {{type: 'application/json'}});
                const manifestURL = window.parent.URL.createObjectURL(blob);
                updateHeadTag('link', {{ rel: 'manifest', href: manifestURL }});

            }} catch (e) {{
                console.warn("Mobile meta injection failed:", e);
            }}
        </script>
        """, height=0)

# Configuración de la página - DEBE SER EL PRIMER COMANDO DE ST
st.set_page_config(
    page_title="Universitario - Sistema de Gestión",
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
    .stDeployButton, [data-testid="stAppDeployButton"], [data-testid="stToolbar"] { display: none !important; }
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

    /* ===== BOTTOM NAV - hidden by default ===== */
    .mobile-bottom-nav { display: none !important; }

    /* ==================================================
       MOBILE (<= 768px) - CSS GLOBAL PARA TODOS LOS MODULOS
       Clases utiles: .uni-scroll-x (scroll horizontal), .uni-hide-mobile,
       .uni-show-mobile, .uni-keep-cols (no apilar columnas),
       .uni-grid-2 (marcador dentro de una columna: fila en 2 por fila),
       .uni-nav-card (tarjeta de navegacion)
    ================================================== */
    .uni-show-mobile { display: none !important; }
    @media (max-width: 768px) {
        html, body { overflow-x: hidden !important; -webkit-text-size-adjust: 100%; }
        .stApp { overflow-x: hidden !important; }
        .uni-hide-mobile { display: none !important; }
        .uni-show-mobile { display: block !important; }

        /* Chrome de Streamlit */
        [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="stStatusWidget"], .stDeployButton, #MainMenu, footer {
            display: none !important;
        }
        [data-testid="stHeader"] { display: none !important; }

        /* Contenedor principal */
        .main .block-container, [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {
            padding: 0.5rem 0.75rem calc(2rem + env(safe-area-inset-bottom)) !important;
            max-width: 100% !important;
        }
        [data-testid="stVerticalBlock"] { gap: 0.75rem !important; }

        /* Columnas apiladas */
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.75rem !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
            width: 100% !important;
        }
        /* Excepcion: grilla 2 por fila (navegacion, metricas chicas) */
        [data-testid="stHorizontalBlock"]:has(.uni-grid-2) > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:has(.uni-grid-2) > [data-testid="column"] {
            min-width: calc(50% - 0.5rem) !important;
            flex: 1 1 calc(50% - 0.5rem) !important;
            width: calc(50% - 0.5rem) !important;
        }
        /* Excepcion: no apilar */
        [data-testid="stHorizontalBlock"]:has(.uni-keep-cols) { flex-wrap: nowrap !important; }
        [data-testid="stHorizontalBlock"]:has(.uni-keep-cols) > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:has(.uni-keep-cols) > [data-testid="column"] {
            min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;
        }

        /* Tipografia */
        h1 { font-size: 1.5rem !important; line-height: 1.25 !important; }
        h2 { font-size: 1.3rem !important; line-height: 1.25 !important; }
        h3 { font-size: 1.1rem !important; }
        h4, h5 { font-size: 1rem !important; }
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { font-size: 0.95rem; }
        [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
        [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
        [data-testid="stCaptionContainer"] { font-size: 0.78rem !important; }

        /* Botones y controles tactiles >= 44px */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            min-height: 48px !important;
            height: auto !important;
            width: 100% !important;
            font-size: 1rem !important;
            padding: 0.5rem 1rem !important;
            border-radius: 10px !important;
            white-space: normal !important;
        }
        .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input,
        .stTimeInput input, .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            min-height: 46px !important;
            font-size: 16px !important; /* evita zoom automatico en iOS */
        }
        .stNumberInput button { min-height: 46px !important; min-width: 40px !important; }
        .stCheckbox, .stRadio label, .stToggle { min-height: 44px; display: flex; align-items: center; }
        .stSlider { padding: 0 0.5rem; }

        /* Tabs con scroll horizontal */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto !important; flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch !important; scrollbar-width: none !important;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
        .stTabs [data-baseweb="tab"] {
            white-space: nowrap !important; min-height: 44px !important;
            height: 44px !important; padding: 0 0.9rem !important; flex: 0 0 auto !important;
        }

        /* Tablas / dataframes: scroll horizontal */
        [data-testid="stDataFrame"], [data-testid="stDataEditor"], [data-testid="stTable"],
        .stTable, .uni-scroll-x {
            overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; max-width: 100% !important;
        }
        [data-testid="stTable"] table { font-size: 0.8rem; }
        [data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; max-width: 100%; }

        /* Imagenes y graficos */
        img, video, canvas, svg { max-width: 100% !important; }
        [data-testid="stImage"] img { height: auto !important; }
        .js-plotly-plot, .plot-container, .plotly, .stPlotlyChart { width: 100% !important; max-width: 100% !important; }
        [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] { overflow-x: auto; }

        /* Expanders, alertas, formularios */
        [data-testid="stExpander"] summary { min-height: 48px; }
        [data-testid="stForm"] { padding: 0.75rem !important; }
        [data-testid="stAlert"] { font-size: 0.9rem; }
        div[role="dialog"] { max-width: 96vw !important; }

        /* Sidebar como panel tactil */
        [data-testid="stSidebar"] { width: min(85vw, 320px) !important; min-width: 0 !important; }
        [data-testid="stSidebar"] .stButton > button {
            min-height: 48px !important; height: 48px !important; font-size: 0.95rem !important;
            text-align: left !important; justify-content: flex-start !important;
        }
        [data-testid="stSidebarCollapseButton"] button, [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"] button { min-width: 44px; min-height: 44px; }

        /* Header y cards propios */
        .main-header { padding: 1rem 0.85rem; border-radius: 12px; margin-bottom: 1rem; }
        .main-header h1 { font-size: 1.15rem !important; }
        .main-header h3 { font-size: 0.9rem !important; }
        .main-header p  { font-size: 0.8rem; }
        .area-card { padding: 0.9rem; }
        .metric-card h3 { font-size: 1.5rem; }

        .main-header { padding: 1.1rem 0.9rem !important; }
    }
    /* Item actual del menu */
    .st-key-topnav .stButton > button[kind="primary"] {
        background: #FFFFFF !important; color: #000 !important; border: 2px solid #000 !important; font-weight: 800 !important;
    }
    @media (max-width: 768px) {
        /* Barra superior fija y compacta */
        .st-key-topnav { position: sticky; top: 0; z-index: 999; background: rgba(255,255,255,0.97); padding: 0.4rem 0 0.5rem; margin: -0.5rem 0 0.25rem; border-bottom: 1px solid #eee; }
        .st-key-topnav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.5rem !important; }
        .st-key-topnav [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }
        .st-key-topnav .stButton > button { min-height: 48px !important; padding: 0.3rem 0.5rem !important; }
        .st-key-topnav .stButton > button p { font-size: 0.9rem !important; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .st-key-topnav [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
        .st-key-topmenu { max-height: 60vh; overflow-y: auto; padding-top: 0.25rem; }
    }

    /* ===== GRILLA DEL HOME ===== */
    .st-key-navgrid, .st-key-navgrid > [data-testid="stVerticalBlock"] { display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
    [class*="st-key-navcard_"] { position: relative; }
    [class*="st-key-navcard_"] [data-testid="stMarkdownContainer"], [class*="st-key-navcard_"] [data-testid="stMarkdown"] { height: auto; }
    [class*="st-key-navcard_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
    .uni-nav-card {
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%); color: #fff; border-radius: 14px;
        padding: 1.25rem 1.1rem 1.1rem; box-shadow: 0 4px 14px rgba(0,0,0,0.18), inset 0 4px 0 var(--accent, #000); text-align: center; transition: transform .15s ease;
    }
    [class*="st-key-navcard_"]:hover .uni-nav-card { transform: translateY(-3px); }
    .uni-nav-icon { font-size: 1.9rem; margin-bottom: 0.4rem; }
    .uni-nav-label { font-weight: 800; font-size: 0.95rem; color: #fff; text-transform: uppercase; letter-spacing: .4px; line-height: 1.2; margin-bottom: 0.3rem; }
    .uni-nav-desc { font-size: 0.78rem; color: rgba(255,255,255,.65); line-height: 1.4; }
    .uni-nav-go { margin-top: .6rem; font-size: .72rem; font-weight: 700; letter-spacing: 1px; color: var(--accent, #fff); }
    /* boton invisible que cubre toda la tarjeta */
    [class*="st-key-btn_grid_"] { position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important; z-index: 2; }
    [class*="st-key-btn_grid_"] .stButton, [class*="st-key-btn_grid_"] button { width: 100% !important; height: 100% !important; min-height: 100% !important; opacity: 0 !important; cursor: pointer; }
    .st-key-topnav [data-testid="stElementContainer"]:has(.uni-keep-cols), .st-key-topnav [data-testid="stMarkdown"]:has(.uni-keep-cols) { display: none !important; }
    .main-header h1, .main-header h3 { padding: 0 !important; margin: 0 !important; }
    .main-header h3 { margin-top: .3rem !important; }
    .main-header img { display: block; margin: 0 auto 0.75rem; }
    .main-header h1 { letter-spacing: .5px; text-transform: uppercase; line-height: 1.25; }
    .main-header .uni-greet { display: inline-block; margin-top: .7rem; padding: .35rem .9rem; border-radius: 999px; background: rgba(255,255,255,.12); font-size: .85rem; color: #fff; }
    @media (max-width: 768px) {
        .st-key-navgrid, .st-key-navgrid > [data-testid="stVerticalBlock"] { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 0.6rem !important; }
        .st-key-navgrid > *:last-child:nth-child(odd) { grid-column: 1 / -1; }
        .uni-nav-card { padding: 1.1rem 0.6rem 1rem !important; }
        .uni-nav-card .uni-nav-icon { font-size: 1.7rem !important; margin-bottom: 0.3rem !important; }
        .uni-nav-card .uni-nav-label { font-size: 0.78rem !important; }
        .uni-nav-card .uni-nav-desc, .uni-nav-card .uni-nav-go { display: none; }
        .main-header h1 { font-size: 1.05rem !important; }
    }
    @media (max-width: 380px) {
        .main .block-container, [data-testid="stMainBlockContainer"] { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        h1 { font-size: 1.3rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)


def login_page():
    bg_image = get_base64_image("assets/fondo_login.jpg")
    
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
    .stDeployButton, [data-testid="stAppDeployButton"], [data-testid="stToolbar"], [data-testid="stHeader"], [data-testid="stDecoration"] {{display: none !important;}}
    .login-title, .login-title h1, .login-title h2, .login-subtitle {{text-align: center !important; width: 100%;}}
    .forgot-password {{text-align: center;}}
    .forgot-password a {{color: rgba(255,255,255,0.9) !important; text-shadow: 0 1px 4px rgba(0,0,0,0.8); font-size: 0.9rem; display: inline-block; padding: 0.5rem;}}
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
            font-size: 16px;
            min-height: 48px;
            max-width: 100%;
        }}

        .stTextInput > div {{
            max-width: 100%;
        }}

        .stButton > button {{
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            min-height: 50px;
            width: 100%;
            max-width: 100%;
        }}

        /* Columna del boton INGRESAR a ancho completo */
        div[data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:not(:has(.stButton)),
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:not(:has(.stButton)) {{
            display: none !important;
        }}

        .main .block-container {{
            padding-bottom: calc(2rem + env(safe-area-inset-bottom));
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
    auth_manager = get_auth_manager()

    # Inyectar atributos autocomplete para que Safari/Chrome ofrezca Face ID / Touch ID
    st.markdown("""
        <script>
        setTimeout(function() {
            var inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(function(inp) {
                if (inp.type === 'password') {
                    inp.setAttribute('autocomplete', 'current-password');
                    inp.setAttribute('name', 'password');
                } else if (inp.type === 'text' || inp.type === 'email') {
                    if (!inp.getAttribute('autocomplete')) {
                        inp.setAttribute('autocomplete', 'username');
                        inp.setAttribute('name', 'username');
                    }
                }
            });
        }, 300);
        </script>
    """, unsafe_allow_html=True)

    username = st.text_input("USUARIO", placeholder="Ingresa tu usuario", label_visibility="collapsed", key="username_input")
    st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)
    password = st.text_input("CONTRASEÑA", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed", key="password_input")
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

    # Botón centrado usando columnas
    recordar = False
    if remember.habilitado():
        recordar = st.checkbox("Recordarme en este dispositivo", value=True, key="recordar_input")

    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        login_clicked = st.button("INGRESAR", use_container_width=True, key="login_btn")

    if login_clicked:
        if auth_manager.login(username, password):
            st.success("✅ Acceso exitoso")
            if recordar:
                st.session_state["_guardar_cookie"] = remember.crear_token(st.session_state.user.get("username"))
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
    
    # Estado de la conexión (Solo visible para diagnóstico si falla)
    from src.data import backend
    if not backend.use_postgres() and not auth_manager.gs_manager.credentials_loaded:
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

def get_modules_info(rol):
    """Catálogo de módulos (usado por la grilla del inicio y por el menú superior)."""
    return [
        {"id": "perfil",       "icon": "👤", "label": "Mi Perfil" if rol == "Jugador" else "Perfil", "color": "#000000",
         "desc": "Información personal, datos de contacto y ficha técnica."},
        {"id": "medica",       "icon": "🏥", "label": "Área Médica",    "color": "#dc3545",
         "desc": "Registro de lesiones, historial clínico y seguimiento de recuperación."},
        {"id": "nutricion",    "icon": "🥗", "label": "Nutrición",      "color": "#28a745",
         "desc": "Antropometría, planes nutricionales y composición corporal."},
        {"id": "fisica",       "icon": "🏋️", "label": "Área Física",   "color": "#fd7e14",
         "desc": "Evaluaciones físicas, tests y métricas de rendimiento."},
        {"id": "wellness",     "icon": "📝", "label": "Bienestar",       "color": "#000000",
         "desc": "Monitoreo diario de sueño, fatiga y esfuerzo percibido."},
        {"id": "dashboard_360","icon": "📊", "label": "Panel de control 360°", "color": "#0d6efd",
         "desc": "Vista integral del jugador: médico, físico y nutricional."},
        {"id": "reporte_medico","icon":"📝", "label": "Informe Médico", "color": "#6f42c1",
         "desc": "Consulta y emisión de reportes médicos detallados."},
        {"id": "bot",          "icon": "🧠", "label": "Asistente IA",   "color": "#20c997",
         "desc": "Consultor inteligente con acceso en tiempo real a los datos del club."},
        {"id": "administracion","icon":"👥", "label": "Gestión Jugadores","color": "#6c757d",
         "desc": "Alta, baja y modificación de jugadores en la base de datos."},
        {"id": "analisis_partido","icon": "📊", "label": "Análisis de Partido", "color": "#17a2b8",
         "desc": "Estadísticas detalladas de acciones, intensidad y eficiencia por partido."},
        {"id": "lista",        "icon": "📋", "label": "Pasar Lista",    "color": "#e83e8c",
         "desc": "Control de asistencia a entrenamientos y partidos."},
    ]


def render_top_nav(auth_manager, current_page):
    """Barra fija: [Inicio] [Menu]; el menu se despliega debajo en 2 columnas (pensado para el pulgar)."""
    rol = st.session_state.user.get('rol')
    allowed = [m for m in get_modules_info(rol) if auth_manager.has_permission(m["id"])]
    actual = next((m for m in allowed if m["id"] == current_page), None)
    if st.session_state.get("_menu_for") != current_page:
        st.session_state["_menu_for"] = current_page
        st.session_state["menu_open"] = False
    abierto = st.session_state.get("menu_open", False)

    with st.container(key="topnav"):
        col_home, col_menu = st.columns(2)
        with col_home:
            st.markdown('<span class="uni-keep-cols"></span>', unsafe_allow_html=True)
            if st.button("🏠 Inicio", use_container_width=True, key="topnav_home"):
                st.session_state.menu_open = False
                st.session_state.current_page = "dashboard"
                st.rerun()
        with col_menu:
            lbl = ("✕ Cerrar" if abierto else "☰ " + (actual["label"] if actual else "Menú"))
            if st.button(lbl, use_container_width=True, key="topnav_toggle"):
                st.session_state.menu_open = not abierto
                st.rerun()
        if abierto:
            with st.container(key="topmenu"):
                for i in range(0, len(allowed), 2):
                    cols = st.columns(2)
                    for c, m in zip(cols, allowed[i:i + 2]):
                        with c:
                            if m is allowed[i]:
                                st.markdown('<span class="uni-keep-cols"></span>', unsafe_allow_html=True)
                            if st.button(f"{m['icon']} {m['label']}", use_container_width=True, key=f"topnav_{m['id']}",
                                         type="primary" if m["id"] == current_page else "secondary"):
                                st.session_state.menu_open = False
                                st.session_state.current_page = m["id"]
                                st.rerun()


def render_bottom_nav():
    """Botón para volver al inicio al final de cada pantalla."""
    st.markdown("---")
    if st.button("🏠 Volver al inicio", use_container_width=True, key="bottomnav_home"):
        st.session_state.current_page = "dashboard"
        st.rerun()


def dashboard_main():
    """Dashboard principal del Club Universitario"""
    auth_manager = get_auth_manager()

    # Header
    logo_b64 = get_base64_image("escudo uni.jpg")
    img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width:clamp(80px,15vw,130px); margin-bottom:0.75rem; border-radius:10px; box-shadow:0 4px 15px rgba(0,0,0,0.3);">' if logo_b64 else ""

    st.markdown(f'<div class="main-header">{img_html}<h1>🏉 CLUB UNIVERSITARIO DE LA PLATA</h1><h3>Sistema de Gestión Deportiva</h3><div class="uni-greet">Bienvenido, <strong>{st.session_state.user["nombre"]}</strong> · {st.session_state.user["rol"]}</div></div>', unsafe_allow_html=True)

    from src.data import backend
    backend.mostrar_frescura()

    allowed = [m for m in get_modules_info(st.session_state.user.get('rol')) if auth_manager.has_permission(m["id"])]

    if not allowed:
        st.info("No tenés módulos habilitados para tu rol.")
        return


    # --- Grilla de tarjetas: cada tarjeta es un unico elemento clickeable (boton transparente encima) ---
    with st.container(key="navgrid"):
        for m in allowed:
            with st.container(key="navcard_" + m['id']):
                acc = m['color'] if m['color'] != '#000000' else '#ffffff'
                st.markdown(f"""
                <div class="uni-nav-card" style="--accent:{acc};">
                    <div class="uni-nav-icon">{m['icon']}</div>
                    <div class="uni-nav-label">{m['label']}</div>
                    <div class="uni-nav-desc">{m['desc']}</div>
                    <div class="uni-nav-go">ABRIR →</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button('Ir a ' + m['label'], key='btn_grid_' + m['id'], use_container_width=True):
                    st.session_state.current_page = m['id']
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

    # "Recordarme": restaurar la sesion desde la cookie (salvo si se acaba de cerrar sesion)
    if (not st.session_state.authenticated and not st.session_state.get("_borrar_cookie")
            and remember.habilitado()):
        usuario_recordado = remember.validar_token(remember.token_de_cookies())
        if usuario_recordado and get_auth_manager().restore_session(usuario_recordado):
            rol = st.session_state.user.get('rol')
            st.session_state.current_page = "perfil" if rol == "Jugador" else "dashboard"

    # Escribir/borrar la cookie pedida por el login o el logout (necesita renderizar JS)
    token_nuevo = st.session_state.pop("_guardar_cookie", None)
    if token_nuevo:
        components.html(remember.js_guardar_cookie(token_nuevo), height=0)
    if st.session_state.pop("_borrar_cookie", None):
        components.html(remember.js_borrar_cookie(), height=0)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

    if not st.session_state.authenticated:
        login_page()
    else:
        # Usuario autenticado: cargar estilos y mostrar app
        load_universitario_styles()
        auth_manager = get_auth_manager()
        user = st.session_state.user

        # Verificar navegación por parámetros de URL (desde los botones del dashboard)
        if "nav" in st.query_params:
            new_page = st.query_params["nav"]
            if auth_manager.has_permission(new_page):
                st.session_state.current_page = new_page
            st.query_params.clear()
            st.rerun()

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
            if st.button("🏠 Inicio", use_container_width=True, key="btn_inicio_top"):
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
                ("📝 Bienestar",      "wellness"),
                ("📝 Informe Médico", "reporte_medico"),
            ]
            for label, page_id in modules:
                if auth_manager.has_permission(page_id):
                    if st.button(label, use_container_width=True):
                        st.session_state.current_page = page_id
                        st.rerun()

            st.markdown("#### 📋 Staff Técnico")
            staff_modules = [
                ("📊 Análisis de Partido", "analisis_partido"),
                ("📊 Panel de control 360°", "dashboard_360"),
            ]
            for label, page_id in staff_modules:
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

            from src.data import backend
            backend.boton_sincronizar(user.get('rol'))

            st.markdown("---")
            if st.button("🏠 Volver al Inicio", use_container_width=True, key="btn_volver_inicio_bottom"):
                st.session_state.current_page = "dashboard"
                st.rerun()
            if st.button("🚪 Cerrar Sesión", use_container_width=True, key="btn_cerrar_sesion_bottom"):
                auth_manager.logout()

        # ===== ROUTING =====
        page = st.session_state.get('current_page', 'dashboard')
        if not auth_manager.has_permission(page):
            st.error("🚫 No tienes permiso para acceder a este módulo.")
            st.session_state.current_page = "dashboard"
            st.rerun()

        if page != "dashboard":
            render_top_nav(auth_manager, page)

        if page == "dashboard":
            dashboard_main()
        elif page == "medica":
            from src.modules.areamedica import main_streamlit
            main_streamlit()
        elif page == "nutricion":
            import src.modules.areanutricion as mod_nutricion
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
        elif page == "analisis_partido":
            from src.modules.panel_partido import rugby_analysis_module
            rugby_analysis_module()
        elif page == "lista":
            from src.modules.Lista import main_lista
            main_lista()

        if page != "dashboard":
            render_bottom_nav()

if __name__ == "__main__":
    main()