"""
Sistema de Autenticación para Formularios Médicos
Control de acceso seguro para profesionales médicos
"""

import streamlit as st
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class AuthManager:
    """
    Gestor de autenticación para el sistema médico
    
    Funcionalidades:
    - Login seguro con hash de contraseñas
    - Gestión de sesiones
    - Control de roles (Médico, Administrador)
    - Registro de accesos
    """
    
    def __init__(self):
        """Inicializar el sistema de autenticación"""
        self.users_file = "data/medical_users.json"
        self.session_duration = timedelta(hours=8)  # 8 horas de sesión
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Crear archivo de usuarios si no existe"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except FileNotFoundError:
            # Crear usuarios por defecto
            default_users = {
                "users": [
                    {
                        "id": 1,
                        "username": "dr.garcia",
                        "email": "dr.garcia@carrugby.com",
                        "full_name": "Dr. Juan García",
                        "role": "medico",
                        "password_hash": self._hash_password("medico123"),
                        "active": True,
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "last_login": None
                    },
                    {
                        "id": 2,
                        "username": "admin.car",
                        "email": "admin@carrugby.com", 
                        "full_name": "Administrador CAR",
                        "role": "admin",
                        "password_hash": self._hash_password("admin123"),
                        "active": True,
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "last_login": None
                    },
                    {
                        "id": 3,
                        "username": "dra.lopez",
                        "email": "dra.lopez@carrugby.com",
                        "full_name": "Dra. María López",
                        "role": "medico",
                        "password_hash": self._hash_password("nutricion123"),
                        "active": True,
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "last_login": None
                    }
                ],
                "login_logs": []
            }
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password: str) -> str:
        """
        Crear hash seguro de la contraseña
        
        Args:
            password (str): Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        # Usar salt fijo para simplificar (en producción usar salt aleatorio)
        salt = "car_rugby_salt_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Autenticar usuario
        
        Args:
            username (str): Nombre de usuario
            password (str): Contraseña
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success, User_Data)
        """
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            password_hash = self._hash_password(password)
            
            for user in data['users']:
                if (user['username'] == username and 
                    user['password_hash'] == password_hash and 
                    user['active']):
                    
                    # Actualizar último login
                    user['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Registrar login
                    data['login_logs'].append({
                        "username": username,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "ip": "local",  # En producción, obtener IP real
                        "success": True
                    })
                    
                    # Guardar cambios
                    with open(self.users_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    return True, user
            
            # Registrar intento fallido
            data['login_logs'].append({
                "username": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ip": "local",
                "success": False
            })
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return False, None
            
        except Exception as e:
            st.error(f"Error en autenticación: {e}")
            return False, None
    
    def is_session_valid(self) -> bool:
        """
        Verificar si la sesión actual es válida
        
        Returns:
            bool: True si la sesión es válida
        """
        if 'authenticated' not in st.session_state:
            return False
        
        if not st.session_state.authenticated:
            return False
        
        # Verificar tiempo de sesión
        if 'login_time' in st.session_state:
            login_time = datetime.fromisoformat(st.session_state.login_time)
            if datetime.now() - login_time > self.session_duration:
                self.logout()
                return False
        
        return True
    
    def login(self, user_data: Dict):
        """
        Iniciar sesión del usuario
        
        Args:
            user_data (Dict): Datos del usuario autenticado
        """
        st.session_state.authenticated = True
        st.session_state.user_id = user_data['id']
        st.session_state.username = user_data['username']
        st.session_state.full_name = user_data['full_name']
        st.session_state.email = user_data['email']
        st.session_state.role = user_data['role']
        st.session_state.login_time = datetime.now().isoformat()
    
    def logout(self):
        """Cerrar sesión del usuario"""
        keys_to_remove = [
            'authenticated', 'user_id', 'username', 'full_name', 
            'email', 'role', 'login_time'
        ]
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Obtener datos del usuario actual
        
        Returns:
            Optional[Dict]: Datos del usuario o None
        """
        if not self.is_session_valid():
            return None
        
        return {
            'id': st.session_state.get('user_id'),
            'username': st.session_state.get('username'),
            'full_name': st.session_state.get('full_name'),
            'email': st.session_state.get('email'),
            'role': st.session_state.get('role')
        }
    
    def require_auth(self) -> bool:
        """
        Requerir autenticación para acceder a una página
        
        Returns:
            bool: True si el usuario está autenticado
        """
        if not self.is_session_valid():
            self.show_login_page()
            return False
        return True
    
    def show_login_page(self):
        """Mostrar página de login"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>🏥 Sistema Médico CAR Rugby Club</h1>
            <h3>Acceso para Profesionales Médicos</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario de login
        with st.form("login_form"):
            st.subheader("🔐 Iniciar Sesión")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                username = st.text_input(
                    "👤 Usuario:", 
                    placeholder="Ingrese su usuario"
                )
                
                password = st.text_input(
                    "🔑 Contraseña:", 
                    type="password",
                    placeholder="Ingrese su contraseña"
                )
                
                submit_button = st.form_submit_button(
                    "🚀 Ingresar", 
                    use_container_width=True
                )
        
        if submit_button:
            if username and password:
                with st.spinner("Verificando credenciales..."):
                    success, user_data = self.authenticate(username, password)
                
                if success:
                    self.login(user_data)
                    st.success(f"✅ Bienvenido, {user_data['full_name']}!")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            else:
                st.warning("⚠️ Por favor ingrese usuario y contraseña")
        
        # Información de usuarios de prueba
        with st.expander("🔍 Usuarios de Prueba", expanded=False):
            st.markdown("""
            **Para probar el sistema:**
            
            **👨‍⚕️ Médico:**
            - Usuario: `dr.garcia`
            - Contraseña: `medico123`
            
            **👩‍⚕️ Nutricionista:**
            - Usuario: `dra.lopez`
            - Contraseña: `nutricion123`
            
            **👨‍💼 Administrador:**
            - Usuario: `admin.car`
            - Contraseña: `admin123`
            """)
    
    def show_user_info(self):
        """Mostrar información del usuario logueado"""
        user = self.get_current_user()
        if user:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👤 Usuario Actual")
            st.sidebar.markdown(f"**Nombre:** {user['full_name']}")
            st.sidebar.markdown(f"**Usuario:** {user['username']}")
            st.sidebar.markdown(f"**Rol:** {user['role'].title()}")
            
            if st.sidebar.button("🚪 Cerrar Sesión"):
                self.logout()
                st.rerun()
    
    def has_permission(self, required_role: str = None) -> bool:
        """
        Verificar si el usuario tiene permisos para una acción
        
        Args:
            required_role (str): Rol requerido ('admin', 'medico', etc.)
            
        Returns:
            bool: True si tiene permisos
        """
        if not self.is_session_valid():
            return False
        
        if not required_role:
            return True
        
        user_role = st.session_state.get('role', '')
        
        # Admin tiene acceso a todo
        if user_role == 'admin':
            return True
        
        # Verificar rol específico
        return user_role == required_role