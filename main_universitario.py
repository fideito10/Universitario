import streamlit as st
import streamlit.components.v1 as components
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
                    for (var key in attributes) {{ element.setAttribute(key, attributes[key]); }}
                    if (!element.parentNode) head.appendChild(element);
                }}
                updateHeadTag('link', {{ rel: 'apple-touch-icon', href: 'data:image/jpeg;base64,{logo_b64}' }});
                updateHeadTag('link', {{ rel: 'shortcut icon', href: 'data:image/jpeg;base64,{logo_b64}' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-capable', content: 'yes' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }});
                updateHeadTag('meta', {{ name: 'apple-mobile-web-app-title', content: 'Universitario' }});
                window.parent.document.title = "Universitario - Sistema de Gestión";
            }} catch (e) {{}}
        </script>
        """, unsafe_allow_html=True)

st.set_page_config(
    page_title="Universitario - Sistema de Gestión",
    page_icon="escudo uni.jpg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def load_universitario_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    :root { --uni-black: #000000; --uni-white: #FFFFFF; }
    .stApp { font-family: 'Inter', sans-serif !important; background: #FFFFFF; }
    .stDeployButton, footer, #MainMenu { display: none !important; }
    
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #000000 0%, #1a1a1a 100%) !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.07) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
        text-align: left !important;
        margin-bottom: 3px !important;
    }
    
    /* ===== ESTILO DE TARJETAS PARA BOTONES NATIVOS ===== */
    .mod-card-container .stButton > button {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 15px !important;
        padding: 2rem 1.5rem !important;
        height: auto !important;
        min-height: 180px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .mod-card-container .stButton > button:hover {
        border-color: #000000 !important;
        transform: translateY(-5px) !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
    }
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%);
        color: white;
        padding: 3.5rem 2rem;
        border-radius: 0 0 40px 40px;
        text-align: center;
        margin-bottom: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)

def login_page():
    load_universitario_styles()
    auth_manager = AuthManager()
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    logo_b64 = get_base64_image("escudo uni.jpg")
    if logo_b64:
        st.markdown(f'<div style="text-align: center; margin-bottom: 2rem;"><img src="data:image/jpeg;base64,{logo_b64}" style="width: 120px;"></div>', unsafe_allow_html=True)
    
    username = st.text_input("USUARIO", placeholder="Usuario", key="username_input")
    password = st.text_input("CONTRASEÑA", type="password", placeholder="Contraseña", key="password_input")
    
    if st.button("INGRESAR", use_container_width=True):
        if auth_manager.login(username, password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

def main_dashboard():
    load_universitario_styles()
    auth_manager = AuthManager()
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"### 🏉 {user['nombre']}")
        st.markdown(f"*{user['rol']}*")
        if st.button("🏠 Inicio", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📋 Staff Técnico")
        if auth_manager.has_permission("analisis_partido"):
            if st.button("📊 Análisis de Partido", use_container_width=True):
                st.session_state.current_page = "analisis_partido"; st.rerun()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    page = st.session_state.get('current_page', 'dashboard')
    
    if page == "dashboard":
        dashboard_main()
    elif page == "analisis_partido":
        from src.modules.analisis_partido import rugby_analysis_module
        rugby_analysis_module()
    # ... (resto de módulos se cargan igual)

def dashboard_main():
    auth_manager = AuthManager()
    logo_b64 = get_base64_image("escudo uni.jpg")
    img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width:100px;">' if logo_b64 else ""
    st.markdown(f'<div class="main-header">{img_html}<h1>CLUB UNIVERSITARIO DE LA PLATA</h1></div>', unsafe_allow_html=True)

    all_modules = [
        {"id": "analisis_partido", "icon": "📊", "label": "Análisis de Partido", "desc": "Estadísticas tácticas y rendimiento."},
        {"id": "medica", "icon": "🏥", "label": "Área Médica", "desc": "Seguimiento de lesiones."},
        {"id": "fisica", "icon": "🏋️", "label": "Área Física", "desc": "Evaluaciones y tests."},
        {"id": "nutricion", "icon": "🥗", "label": "Nutrición", "desc": "Planes y composición."},
        {"id": "wellness", "icon": "📝", "label": "Bienestar", "desc": "Monitoreo diario."},
    ]
    
    allowed = [m for m in all_modules if auth_manager.has_permission(m["id"])]
    
    st.markdown('<div class="mod-card-container">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, m in enumerate(allowed):
        with cols[i % 3]:
            # El botón real que Streamlit reconoce al instante
            if st.button(f"{m['icon']}\n\n{m['label']}\n\n{m['desc']}", key=f"btn_{m['id']}", use_container_width=True):
                st.session_state.current_page = m['id']
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'current_page' not in st.session_state: st.session_state.current_page = "dashboard"
    inject_mobile_meta()
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()