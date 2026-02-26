import streamlit as st
import pandas as pd
import unicodedata
from src.sheets.google_sheets_manager import GoogleSheetsManager

def normalize_text(text):
    """Normaliza texto: elimina acentos, convierte a minúsculas y quita espacios."""
    if not text:
        return ""
    text = str(text)
    # Eliminar acentos
    text = unicodedata.normalize('NFD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return text.lower().strip()

def robust_dni_match(stored_dni, input_dni):
    """Compara DNIs de forma robusta eliminando puntos, espacios y sufijos .0"""
    def clean(s):
        s = str(s).strip()
        if s.endswith('.0'): s = s[:-2]
        import re
        return re.sub(r'\D', '', s)
    return clean(stored_dni) == clean(input_dni)

class AuthManager:
    def __init__(self):
        self.gs_manager = GoogleSheetsManager()
        # Intentar obtener sheet_id de secrets o usar el ID por defecto
        self.sheet_id = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"
        
        # Sincronizar con el manager si detectó uno en secrets
        if self.gs_manager.credentials_loaded and self.gs_manager.sheet_config.get("sheet_id"):
            self.sheet_id = self.gs_manager.sheet_config["sheet_id"]
            
        self.worksheet_name = "Usuarios"
        
        # Estructura de permisos según requerimientos del usuario
        self.permissions = {
            "Administrador": [
                "dashboard", "perfil", "medica", "nutricion", "fisica", 
                "dashboard_360", "reporte_medico", "bot", 
                "administracion", "lista"
            ],
            "Entrenador": [
                "dashboard", "perfil", "medica", "nutricion", "fisica", 
                "dashboard_360", "reporte_medico", "bot", 
                "administracion", "lista"
            ],
            "Preparador Físico": [
                "dashboard", "perfil", "fisica", "dashboard_360", "bot", "lista"
            ],
            "Nutricionista": [
                "dashboard", "perfil", "nutricion", "dashboard_360", "bot"
            ],
            "Jugador": [
                "dashboard", "perfil", "dashboard_360", "nutricion", "fisica"
            ]
        }

    def _get_users_df(self):
        """Obtiene la tabla de usuarios de Google Sheets"""
        try:
            if not self.gs_manager.credentials_loaded:
                return pd.DataFrame()
            
            spreadsheet = self.gs_manager.client.open_by_key(self.sheet_id)
            try:
                worksheet = spreadsheet.worksheet(self.worksheet_name)
            except:
                # Si no existe, la creamos (primera ejecución)
                worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=100, cols=6)
                headers = ["Usuario", "Clave", "Rol", "Nombre", "DNI", "Email"]
                worksheet.append_row(headers)
                # Agregar admin por defecto si está vacío
                worksheet.append_row(["admin", "admin123", "Administrador", "Admin Sistema", "", ""])
            
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error al cargar usuarios: {e}")
            return pd.DataFrame()

    def login(self, username, password):
        """Valida credenciales y establece la sesión"""
        username_raw = str(username).strip()
        password_raw = str(password).strip()
        
        # 0. Fallback local por seguridad (Administrador de emergencia)
        if username_raw.lower() == "admin" and password_raw == "admin123":
            st.session_state.authenticated = True
            st.session_state.user = {
                "username": "admin",
                "rol": "Administrador",
                "nombre": "Admin Sistema",
                "dni": ""
            }
            return True

        # 1. Intentar login estándar en la tabla Usuarios (coincidencia exacta)
        users_df = self._get_users_df()
        valid_user = pd.DataFrame()
        
        if not users_df.empty:
            valid_user = users_df[
                (users_df['Usuario'].astype(str).str.strip() == username_raw) & 
                (users_df['Clave'].astype(str).str.strip() == password_raw)
            ]
        
        # 2. Búsqueda alternativa para Jugadores: DNI (limpio) como usuario y contraseña
        if valid_user.empty:
            # Limpiar entradas de puntos, espacios y otros caracteres no numéricos
            clean_u = "".join(filter(str.isdigit, username_raw))
            clean_p = "".join(filter(str.isdigit, password_raw))
            
            # Solo proceder si ambos son iguales (DNI como usuario y pass) y no están vacíos
            if clean_u != "" and clean_u == clean_p:
                # A. Buscar en la tabla Usuarios por DNI (limpio)
                if not users_df.empty and 'DNI' in users_df.columns:
                    for idx, row in users_df.iterrows():
                        stored_dni = str(row.get('DNI', '')).strip()
                        if stored_dni.endswith('.0'): stored_dni = stored_dni[:-2]
                        stored_dni_clean = "".join(filter(str.isdigit, stored_dni))
                        stored_rol = str(row.get('Rol', '')).strip()
                        
                        # Si el DNI coincide y es un Jugador
                        if stored_dni_clean == clean_u and normalize_text(stored_rol) == "jugador":
                            valid_user = users_df.loc[[idx]]
                            break
                
                # B. SI NO SE ENCONTRÓ EN USUARIOS, BUSCAR EN JUGADORES_MAESTRO
                if valid_user.empty:
                    if not self.gs_manager.credentials_loaded:
                        return False
                    try:
                        # Usar el ID de la base maestra directamente para asegurar
                        spreadsheet = self.gs_manager.client.open_by_key(self.sheet_id)
                        master_sheet = spreadsheet.worksheet("Jugadores_Maestro")
                        master_records = master_sheet.get_all_records()
                        master_df = pd.DataFrame(master_records)
                        
                        if not master_df.empty and 'DNI' in master_df.columns:
                            # Stricter cleaning of the column
                            master_df['DNI_CLEAN'] = master_df['DNI'].astype(str).apply(lambda x: "".join(filter(str.isdigit, x.replace('.0', ''))))
                            
                            for _, row in master_df.iterrows():
                                stored_dni_clean = row['DNI_CLEAN']
                                
                                if stored_dni_clean == clean_u:
                                    # Jugador encontrado en Base Maestra, creamos sesión activa
                                    st.session_state.authenticated = True
                                    nombre = str(row.get('Nombre', '')).strip()
                                    apellido = str(row.get('Apellido', '')).strip()
                                    st.session_state.user = {
                                        "username": clean_u,
                                        "rol": "Jugador",
                                        "nombre": f"{nombre} {apellido}".strip() or f"Jugador {clean_u}",
                                        "dni": clean_u
                                    }
                                    return True
                    except Exception as e:
                        pass
        
        # 3. Finalizar sesión si se encontró un usuario válido en la tabla Usuarios
        if not valid_user.empty:
            user_data = valid_user.iloc[0].to_dict()
            st.session_state.authenticated = True
            st.session_state.user = {
                "username": str(user_data.get("Usuario", "")).strip(),
                "rol": str(user_data.get("Rol", "Invitado")).strip(),
                "nombre": str(user_data.get("Nombre", "")).strip() or str(user_data.get("Usuario", "")).strip(),
                "dni": str(user_data.get("DNI", "")).strip()
            }
            return True
            
        return False

    def logout(self):
        """Limpia la sesión"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    def has_permission(self, page_name):
        """Verifica si el usuario actual tiene permiso para una página"""
        if not st.session_state.get('authenticated', False):
            return False
        
        rol_input = normalize_text(st.session_state.user.get('rol', 'Invitado'))
        
        # Búsqueda ultra-robusta en el mapa de permisos
        allowed_pages = ["dashboard"]
        for p_rol, p_pages in self.permissions.items():
            if normalize_text(p_rol) == rol_input:
                allowed_pages = p_pages
                break
                
        return page_name in allowed_pages

    def get_allowed_modules(self):
        """Retorna lista de módulos permitidos para el rol actual"""
        if not st.session_state.get('authenticated', False):
            return ["dashboard"]
            
        rol_input = normalize_text(st.session_state.user.get('rol', 'Invitado'))
        
        for p_rol, p_pages in self.permissions.items():
            if normalize_text(p_rol) == rol_input:
                return p_pages
                
        return ["dashboard"]

    def is_role(self, *target_roles):
        """Verifica si el usuario actual tiene alguno de los roles indicados (robusto)"""
        if not st.session_state.get('authenticated', False):
            return False
            
        user_rol = normalize_text(st.session_state.user.get('rol', ''))
        return any(normalize_text(r) == user_rol for r in target_roles)
