"""
Google Sheets Manager Mejorado
Sistema de gestión de datos médicos con Google Sheets API
Soporte para st.secrets y configuración segura
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import json
from src.utils.credentials import get_credentials_dict, get_service_account_credentials



class GoogleSheetsManager:
    """
    Manager mejorado para Google Sheets con soporte completo para st.secrets
    
    Funcionalidades:
    - Conexión segura usando st.secrets
    - Manejo de múltiples hojas de trabajo
    - Operaciones CRUD completas
    - Validación y formateo automático
    - Manejo de errores robusto
    """
    
    def __init__(self, use_secrets: bool = True):
        """
        Inicializar el manager de Google Sheets
        
        Args:
            use_secrets (bool): Usar st.secrets para credenciales
        """
        
        # Configuración de permisos para Google Sheets
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        
        self.client = None
        self.credentials_loaded = False
        self.use_secrets = use_secrets
        
        # Configuración por defecto del Google Sheet
        self.sheet_config = {
            "sheet_id": None,  # Se cargará desde secrets o config
            "worksheets": {
                "medical_records": "Registros_Medicos",
                "statistics": "Estadisticas",
                "config": "Configuracion",
                "wellness": "Wellness_Jugador"
            }
        }
        
        # Inicializar conexión
        self._setup_credentials()
    
    def _setup_credentials(self) -> bool:
        """
        Configurar credenciales de Google de forma segura
        
        Returns:
            bool: True si las credenciales se cargaron correctamente
        """
        try:
            # Primero intentar con secrets si están disponibles
            if self.use_secrets and hasattr(st, 'secrets'):
                try:
                    if self._setup_from_secrets():
                        return True
                except:
                    pass # Fallback al archivo
            
            # Si fallan los secrets o no están disponibles, intentar con archivo local
            return self._setup_from_file()
                
        except Exception as e:
            # Solo mostrar error si ambos métodos fallaron
            return False
    
    def _setup_from_secrets(self) -> bool:
        """
        Configurar credenciales usando el módulo centralizado de credenciales.
        Soporta st.secrets, variables de entorno (Railway) y archivos locales.

        Returns:
            bool: True si se configuró correctamente
        """
        try:
            creds = get_service_account_credentials(scopes=self.scope)
            if creds is None:
                return False

            self.client = gspread.authorize(creds)
            self.credentials_loaded = True
            return True

        except Exception:
            return False

    
    def _setup_from_file(self) -> bool:
        """
        Configurar credenciales usando archivo local
        
        Returns:
            bool: True si se configuró correctamente
        """
        try:
            # Buscar archivo de credenciales
            credentials_paths = [
                "car_google_credentials.json",
                "google_credentials.json",
                "credentials.json",
                "credentials/service_account.json",
                "credentials/google_credentials.json",
                "service_account.json"
            ]
            
            credentials_path = None
            for path in credentials_paths:
                if os.path.exists(path):
                    credentials_path = path
                    break
            
            if not credentials_path:
                return False
            
            # Cargar configuración si existe
            config_path = "config/google_sheets_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.sheet_config.update(config)
            else:
                # Usar configuración de Universitario por defecto
                self.sheet_config["sheet_id"] = "10Gixz7_8AvtYqBMS6RWz-wlW_MSpPVbjoCdz1GRM1lU"
            
            # Cargar y validar credenciales
            creds = Credentials.from_service_account_file(
                credentials_path, 
                scopes=self.scope
            )
            
            self.client = gspread.authorize(creds)
            self.credentials_loaded = True
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error cargando archivo: {str(e)}")
            return False
    
    def _get_secret_value(self, key_path: str) -> Optional[str]:
        """
        Obtener valor de st.secrets de forma segura
        
        Args:
            key_path (str): Ruta de la clave (ej: "google_sheets.project_id")
            
        Returns:
            Optional[str]: Valor de la secret o None
        """
        try:
            keys = key_path.split('.')
            value = st.secrets
            
            for key in keys:
                value = getattr(value, key, None)
                if value is None:
                    return None
            
            return str(value)
            
        except:
            return None
    
    def _ensure_worksheets_exist(self) -> bool:
        """
        Asegurar que existen las hojas de trabajo necesarias
        
        Returns:
            bool: True si las hojas existen o se crearon
        """
        if not self.credentials_loaded:
            return False
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            
            # Headers para la hoja de registros médicos
            medical_headers = [
                "ID", "Timestamp", "Nombre_Profesional", "Email_Profesional",
                "Nombre_Paciente", "Division", "Diagnostico", "Fecha_Atencion",
                "Tipo_Lesion", "Severidad", "Parte_Cuerpo", "Tratamiento",
                "Tiempo_Recuperacion", "Puede_Entrenar", "Medicamentos",
                "Observaciones", "Proxima_Evaluacion", "Estado", "Fecha_Registro"
            ]
            
            
            # Verificar/crear hoja de Wellness
            wellness_headers = [
                "ID", "Timestamp", "Email_Jugador", "Nombre_Jugador", 
                "RPE", "Sueno", "DOMS", "Wellness_Score", "Fecha"
            ]
            wellness_name = self.sheet_config["worksheets"]["wellness"]
            
            try:
                worksheet = spreadsheet.worksheet(wellness_name)
                first_row = worksheet.row_values(1)
                if not first_row or len(first_row) < 5:
                    worksheet.insert_row(wellness_headers, 1)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=wellness_name,
                    rows=1000,
                    cols=len(wellness_headers)
                )
                worksheet.insert_row(wellness_headers, 1)
                
            return True
            
        except Exception as e:
            st.error(f"❌ Error configurando hojas: {str(e)}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Probar conexión con Google Sheets
        
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if not self.credentials_loaded:
            return False, "❌ Credenciales no cargadas"
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet_name = self.sheet_config["worksheets"]["medical_records"]
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Obtener información básica
            total_rows = len(worksheet.get_all_values())
            registros = max(0, total_rows - 1)  # Restar header
            
            return True, f"✅ Conectado a '{spreadsheet.title}' - {registros} registros en '{worksheet_name}'"
            
        except Exception as e:
            return False, f"❌ Error de conexión: {str(e)}"
    
    def load_data_from_sheets(self) -> Tuple[bool, List[Dict]]:
        """
        Cargar todos los registros médicos desde Google Sheets
        
        Returns:
            Tuple[bool, List[Dict]]: (Success, Records)
        """
        if not self.credentials_loaded:
            return False, []
        
        try:
            # Asegurar que las hojas existen
            if not self._ensure_worksheets_exist():
                return False, []
            
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet_name = self.sheet_config["worksheets"]["medical_records"]
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Obtener todos los registros como diccionarios
            records = worksheet.get_all_records()
            
            if not records:
                return True, []
            
            # Procesar y limpiar registros
            processed_records = []
            
            for i, record in enumerate(records):
                # Limpiar valores vacíos y formatear
                cleaned_record = {}
                for key, value in record.items():
                    # Normalizar nombres de campos
                    clean_key = key.lower().replace(' ', '_')
                    cleaned_record[clean_key] = str(value).strip() if value else ""
                
                # Agregar ID único si no existe
                if not cleaned_record.get('id'):
                    cleaned_record['id'] = f"gs_{i+1}"
                
                # Asegurar timestamp
                if not cleaned_record.get('timestamp'):
                    cleaned_record['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                processed_records.append(cleaned_record)
            
            return True, processed_records
            
        except Exception as e:
            st.error(f"❌ Error leyendo datos: {str(e)}")
            return False, []
    
    def add_new_record(self, form_data: Dict) -> Tuple[bool, str]:
        """
        Agregar nuevo registro médico a Google Sheets
        
        Args:
            form_data (Dict): Datos del formulario médico
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if not self.credentials_loaded:
            return False, "❌ No hay conexión con Google Sheets"
        
        try:
            # Validar datos requeridos
            required_fields = ["nombre_profesional", "nombre_paciente", "diagnostico"]
            for field in required_fields:
                if not form_data.get(field):
                    return False, f"❌ Campo requerido faltante: {field}"
            
            # Asegurar que las hojas existen
            if not self._ensure_worksheets_exist():
                return False, "❌ Error configurando hojas de trabajo"
            
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet_name = self.sheet_config["worksheets"]["medical_records"]
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Generar ID único
            existing_records = worksheet.get_all_values()
            next_id = len(existing_records)  # Incluye header, así que es el siguiente ID
            
            # Preparar fila de datos
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fecha_registro = datetime.now().strftime("%Y-%m-%d")
            
            row_data = [
                next_id,  # ID
                timestamp,  # Timestamp
                form_data.get("nombre_profesional", ""),
                form_data.get("email_profesional", ""),
                form_data.get("nombre_paciente", ""),
                form_data.get("division", ""),
                form_data.get("diagnostico", ""),
                form_data.get("fecha_atencion", ""),
                form_data.get("tipo_lesion", ""),
                form_data.get("severidad", ""),
                form_data.get("parte_cuerpo", ""),
                form_data.get("tratamiento", ""),
                form_data.get("tiempo_recuperacion", ""),
                form_data.get("puede_entrenar", ""),
                form_data.get("medicamentos", ""),
                form_data.get("observaciones", ""),
                form_data.get("proxima_evaluacion", ""),
                self._determine_status(form_data.get("severidad", "")),
                fecha_registro
            ]
            
            # Agregar a Google Sheets
            worksheet.append_row(row_data)
            
            return True, f"✅ Registro #{next_id} guardado exitosamente"
            
        except Exception as e:
            return False, f"❌ Error al guardar: {str(e)}"
    
    def update_record(self, record_id: str, updated_data: Dict) -> Tuple[bool, str]:
        """
        Actualizar registro existente en Google Sheets
        
        Args:
            record_id (str): ID del registro a actualizar
            updated_data (Dict): Datos actualizados
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if not self.credentials_loaded:
            return False, "❌ No hay conexión con Google Sheets"
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet_name = self.sheet_config["worksheets"]["medical_records"]
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Buscar la fila del registro
            all_records = worksheet.get_all_values()
            headers = all_records[0]
            
            # Encontrar índice de columna ID
            id_col_index = None
            for i, header in enumerate(headers):
                if header.lower() in ['id', 'id_registro']:
                    id_col_index = i
                    break
            
            if id_col_index is None:
                return False, "❌ No se encontró columna de ID"
            
            # Buscar fila del registro
            row_index = None
            for i, row in enumerate(all_records[1:], start=2):  # Start=2 porque skippeamos header
                if len(row) > id_col_index and str(row[id_col_index]) == str(record_id):
                    row_index = i
                    break
            
            if row_index is None:
                return False, f"❌ No se encontró registro con ID: {record_id}"
            
            # Actualizar campos específicos
            for field, value in updated_data.items():
                # Mapear campo a columna
                field_col_index = None
                for i, header in enumerate(headers):
                    if header.lower().replace(' ', '_') == field.lower():
                        field_col_index = i + 1  # gspread usa 1-indexed
                        break
                
                if field_col_index:
                    worksheet.update_cell(row_index, field_col_index, value)
            
            return True, f"✅ Registro {record_id} actualizado"
            
        except Exception as e:
            return False, f"❌ Error actualizando: {str(e)}"
    
    def delete_record(self, record_id: str) -> Tuple[bool, str]:
        """
        Eliminar registro de Google Sheets
        
        Args:
            record_id (str): ID del registro a eliminar
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if not self.credentials_loaded:
            return False, "❌ No hay conexión con Google Sheets"
        
        try:
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet_name = self.sheet_config["worksheets"]["medical_records"]
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Buscar y eliminar fila
            all_records = worksheet.get_all_values()
            headers = all_records[0]
            
            # Encontrar fila del registro
            row_index = None
            for i, row in enumerate(all_records[1:], start=2):
                if len(row) > 0 and str(row[0]) == str(record_id):  # Asumiendo ID en primera columna
                    row_index = i
                    break
            
            if row_index is None:
                return False, f"❌ No se encontró registro con ID: {record_id}"
            
            worksheet.delete_rows(row_index)
            
            return True, f"✅ Registro {record_id} eliminado"
            
        except Exception as e:
            return False, f"❌ Error eliminando: {str(e)}"
    
    def get_statistics(self) -> Dict:
        """
        Obtener estadísticas de los registros médicos
        
        Returns:
            Dict: Diccionario con estadísticas
        """
        success, records = self.load_data_from_sheets()
        
        if not success or not records:
            return {
                "total_registros": 0,
                "registros_hoy": 0,
                "profesionales_activos": 0,
                "casos_graves": 0,
                "ultimo_registro": "N/A"
            }
        
        # Calcular estadísticas
        hoy = datetime.now().date()
        registros_hoy = 0
        profesionales = set()
        casos_graves = 0
        
        for record in records:
            # Profesionales únicos
            prof = record.get("nombre_profesional") or record.get("nombre_profesional", "")
            if prof:
                profesionales.add(prof)
            
            # Registros de hoy
            fecha_str = record.get("fecha_registro") or record.get("fecha_registro", "")
            if fecha_str:
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    if fecha == hoy:
                        registros_hoy += 1
                except:
                    pass
            
            # Casos graves
            severidad = (record.get("severidad") or record.get("severidad", "")).lower()
            if any(word in severidad for word in ["grave", "crítico", "severo"]):
                casos_graves += 1
        
        # Último registro
        ultimo_registro = "N/A"
        if records:
            ultimo_timestamp = records[-1].get("timestamp", "")
            if ultimo_timestamp:
                try:
                    dt = datetime.strptime(ultimo_timestamp, "%Y-%m-%d %H:%M:%S")
                    ultimo_registro = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    ultimo_registro = ultimo_timestamp[:16]
        
        return {
            "total_registros": len(records),
            "registros_hoy": registros_hoy,
            "profesionales_activos": len(profesionales),
            "casos_graves": casos_graves,
            "ultimo_registro": ultimo_registro
        }
    
    def _determine_status(self, severidad: str) -> str:
        """
        Determinar estado del paciente basado en severidad
        
        Args:
            severidad (str): Nivel de severidad
            
        Returns:
            str: Estado determinado
        """
        severidad_lower = severidad.lower()
        
        if any(word in severidad_lower for word in ["leve", "menor"]):
            return "Seguimiento"
        elif any(word in severidad_lower for word in ["moderada", "intermedio"]):
            return "Tratamiento activo"
        elif any(word in severidad_lower for word in ["grave", "severo", "crítico"]):
            return "Atención prioritaria"
        else:
            return "En evaluación"


# Función de compatibilidad con el sistema actual
class FormulariosGoogleSheets(GoogleSheetsManager):
    """Clase de compatibilidad con el sistema actual"""
    
    def __init__(self):
        super().__init__(use_secrets=True)
    
    def submit_medical_form(self, form_data: Dict) -> Tuple[bool, str]:
        """Compatibilidad con el método anterior"""
        return self.add_new_record(form_data)
    
    def read_medical_records(self) -> Tuple[bool, List[Dict]]:
        """Compatibilidad con el método anterior"""
        return self.load_data_from_sheets()