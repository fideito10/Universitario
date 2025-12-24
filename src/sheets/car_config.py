"""
Configuración y utilidades para el sistema CAR
"""

import streamlit as st
import json
from datetime import datetime

class SessionManager:
    """Gestión de sesiones de usuario"""
    
    @staticmethod
    def init_session():
        """Inicializar variables de sesión"""
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
    
    @staticmethod
    def is_logged_in():
        """Verificar si el usuario está logueado"""
        return st.session_state.get('logged_in', False)
    
    @staticmethod
    def logout():
        """Cerrar sesión"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    @staticmethod
    def require_login():
        """Decorador para requerir login"""
        if not SessionManager.is_logged_in():
            st.error("🔒 Debe iniciar sesión para acceder a esta página")
            st.stop()

# Configuración del tema CAR
CAR_THEME = {
    'primary_color': '#1A2C56',
    'secondary_color': '#6BB4E8',
    'background_color': '#FFFFFF',
    'text_color': '#2C4A7A',
    'success_color': '#28A745',
    'error_color': '#DC3545',
    'warning_color': '#FFC107'
}

def apply_car_theme():
    """Aplicar tema visual del CAR"""
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {CAR_THEME['primary_color']} 0%, 
                                           {CAR_THEME['secondary_color']} 100%);
    }}
    </style>
    """, unsafe_allow_html=True)