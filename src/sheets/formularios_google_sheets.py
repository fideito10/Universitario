"""
Sistema de Formularios Médicos con Google Sheets
Integración completa para captura y visualización de datos médicos
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import json


import os

class FormulariosGoogleSheets:
    def __init__(self):
        """Inicializar conexión con Google Sheets"""
        
        self.sheet_config = {
            'sheet_id': '1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w',
            'worksheet_name': 'Hoja 1'
        }
        
        self.gc = None
        self.client = None  # Alias para compatibilidad
        self.worksheet = None
        self.credentials_loaded = False
        
        # Intentar configurar conexión
        try:
            success, message = self._setup_connection()
            if success:
                self.credentials_loaded = True
            else:
                print(f"⚠️ Advertencia: {message}")
        except Exception as e:
            print(f"⚠️ Error inicial de conexión: {e}")
    
    def _setup_connection(self):
        """Configurar conexión autenticada con Google Sheets"""
        try:
            # Scopes necesarios
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Intentar cargar credenciales desde st.secrets (Streamlit Cloud)
            try:
                service_account_info = st.secrets["google"]
                credentials = Credentials.from_service_account_info(
                    service_account_info,
                    scopes=SCOPES
                )
            except Exception as e:
                # Si falla st.secrets, intentar archivo local
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                credentials_path = os.path.join(project_root, 'credentials', 'service_account.json')
                
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"No se encontró el archivo de credenciales: credentials/service_account.json\n"
                        f"💡 Asegúrese de que el archivo service_account.json esté en la carpeta credentials/"
                    )
                
                credentials = Credentials.from_service_account_file(
                    credentials_path,
                    scopes=SCOPES
                )
            
            # Autorizar cliente
            self.gc = gspread.authorize(credentials)
            self.client = self.gc  # Alias para compatibilidad
            self.credentials_loaded = True
            
            return True, "Conexión establecida exitosamente"
            
        except FileNotFoundError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error configurando conexión: {e}"
    def _ensure_worksheet_exists(self) -> bool:
        """
        Asegurar que existe la hoja de trabajo con las columnas correctas
        
        Returns:
            bool: True si la hoja existe o se creó correctamente
        """
        if not self.credentials_loaded:
            return False
        
        try:
            # Abrir el Google Sheet
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            
            # Intentar acceder a la hoja específica
            try:
                worksheet = spreadsheet.worksheet(self.sheet_config["worksheet_name"])
            except gspread.WorksheetNotFound:
                # Crear la hoja si no existe
                worksheet = spreadsheet.add_worksheet(
                    title=self.sheet_config["worksheet_name"],
                    rows=1000,
                    cols=20
                )
                
                # Agregar encabezados
                headers = [
                    "Timestamp", "Nombre_Profesional", "Email_Profesional",
                    "Nombre_Paciente", "Division", "Diagnostico", 
                    "Fecha_Atencion", "Tipo_Lesion", "Severidad",
                    "Parte_Cuerpo", "Tratamiento", "Tiempo_Recuperacion",
                    "Puede_Entrenar", "Medicamentos", "Observaciones",
                    "Proxima_Evaluacion", "Estado", "Fecha_Registro"
                ]
                
                worksheet.append_row(headers)
                st.success("✅ Hoja de trabajo creada con encabezados")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error configurando hoja de trabajo: {str(e)}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Probar conexión con Google Sheets con fallback a API pública
        
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        # Intentar conexión autenticada primero
        if self.credentials_loaded:
            try:
                spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
                worksheet = spreadsheet.worksheet(self.sheet_config["worksheet_name"])
                
                # Obtener información básica
                total_rows = len(worksheet.get_all_values())
                registros = max(0, total_rows - 1)  # Restar 1 por los encabezados
                
                return True, f"✅ Conectado: '{spreadsheet.title}' - {registros} registros"
                
            except Exception as e:
                # Si falla la autenticación, intentar API pública
                return self._try_public_api_connection()
        else:
            # Usar API pública directamente
            return self._try_public_api_connection()
    
    def submit_medical_form(self, form_data: Dict) -> Tuple[bool, str]:
        """
        Enviar datos del formulario médico a Google Sheets
        
        Args:
            form_data (Dict): Diccionario con los datos del formulario
            
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
            
            # Preparar fila de datos
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fecha_registro = datetime.now().strftime("%Y-%m-%d")
            
            row_data = [
                timestamp,
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
                self._determinar_estado(form_data.get("severidad", "")),
                fecha_registro
            ]
            
            # Enviar a Google Sheets
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet = spreadsheet.worksheet(self.sheet_config["worksheet_name"])
            
            worksheet.append_row(row_data)
            
            return True, "✅ Registro guardado exitosamente en Google Sheets"
            
        except Exception as e:
            return False, f"❌ Error al guardar: {str(e)}"
    
    def read_medical_records(self) -> Tuple[bool, List[Dict]]:
        """
        Leer todos los registros médicos desde Google Sheets con fallback
        
        Returns:
            Tuple[bool, List[Dict]]: (Success, Records)
        """
        # Intentar método autenticado primero
        if self.credentials_loaded:
            try:
                spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
                worksheet = spreadsheet.worksheet(self.sheet_config["worksheet_name"])
                
                # Obtener todos los registros como diccionarios
                records = worksheet.get_all_records()
                
                if not records:
                    return True, []
                
                # Procesar registros
                processed_records = []
                
                for i, record in enumerate(records):
                    processed_record = {
                        "id": f"gs_{i+1}",
                        "timestamp": record.get("Timestamp", ""),
                        "nombre_profesional": record.get("Nombre_Profesional", ""),
                        "email_profesional": record.get("Email_Profesional", ""),
                        "nombre_paciente": record.get("Nombre_Paciente", ""),
                        "division": record.get("Division", ""),
                        "diagnostico": record.get("Diagnostico", ""),
                        "fecha_atencion": record.get("Fecha_Atencion", ""),
                        "tipo_lesion": record.get("Tipo_Lesion", ""),
                        "severidad": record.get("Severidad", ""),
                        "parte_cuerpo": record.get("Parte_Cuerpo", ""),
                        "tratamiento": record.get("Tratamiento", ""),
                        "tiempo_recuperacion": record.get("Tiempo_Recuperacion", ""),
                        "puede_entrenar": record.get("Puede_Entrenar", ""),
                        "medicamentos": record.get("Medicamentos", ""),
                        "observaciones": record.get("Observaciones", ""),
                        "proxima_evaluacion": record.get("Proxima_Evaluacion", ""),
                        "estado": record.get("Estado", ""),
                        "fecha_registro": record.get("Fecha_Registro", "")
                    }
                    
                    processed_records.append(processed_record)
                
                return True, processed_records
                
            except Exception as e:
                print(f"Error con autenticación, intentando API pública: {e}")
                # Fallback a API pública
                return self.get_public_data()
        else:
            # Usar API pública directamente
            return self.get_public_data()
    
    def get_statistics(self) -> Dict:
        """
        Obtener estadísticas de los registros médicos
        
        Returns:
            Dict: Diccionario con estadísticas
        """
        success, records = self.read_medical_records()
        
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
            if record.get("nombre_profesional"):
                profesionales.add(record["nombre_profesional"])
            
            # Registros de hoy
            fecha_str = record.get("fecha_registro", "")
            if fecha_str:
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    if fecha == hoy:
                        registros_hoy += 1
                except:
                    pass
            
            # Casos graves
            severidad = record.get("severidad", "").lower()
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
    
    def _determinar_estado(self, severidad: str) -> str:
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
    
    def sync_with_car_system(self) -> int:
        """
        Sincronizar registros de Google Sheets con el sistema CAR local
        
        Returns:
            int: Número de registros sincronizados (-1 si error)
        """
        try:
            # Leer registros de Google Sheets
            success, gs_records = self.read_medical_records()
            
            if not success or not gs_records:
                return 0
            
            # Cargar registros existentes del sistema CAR
            from src.utils import load_json_data, save_medical_data
            
            existing_data = load_json_data('data/medical_records.json', {'injuries': []})
            
            # Crear set de timestamps existentes para evitar duplicados
            existing_timestamps = set()
            for injury in existing_data['injuries']:
                if 'timestamp' in injury:
                    existing_timestamps.add(injury['timestamp'])
            
            # Convertir registros de Google Sheets al formato CAR
            nuevos_registros = []
            
            for gs_record in gs_records:
                if gs_record['timestamp'] not in existing_timestamps:
                    car_record = {
                        "id": gs_record["id"],
                        "player_name": gs_record["nombre_paciente"],
                        "division": gs_record["division"],
                        "injury_type": gs_record["diagnostico"],
                        "severity": gs_record["severidad"],
                        "date_occurred": gs_record["fecha_atencion"],
                        "treatment": gs_record["tratamiento"],
                        "expected_recovery": gs_record["tiempo_recuperacion"],
                        "status": gs_record["estado"],
                        "notes": gs_record["observaciones"],
                        "doctor": gs_record["nombre_profesional"],
                        "timestamp": gs_record["timestamp"],
                        "source": "Google Sheets Form"
                    }
                    nuevos_registros.append(car_record)
            
            if nuevos_registros:
                # Agregar al sistema CAR
                existing_data['injuries'].extend(nuevos_registros)
                save_medical_data(existing_data['injuries'])
                return len(nuevos_registros)
            
            return 0
            
        except Exception as e:
            st.error(f"❌ Error en sincronización: {str(e)}")
            return -1

    def get_medical_statistics(self) -> Dict:
        """
        Obtener estadísticas médicas desde Google Sheets
        
        Returns:
            Dict: Estadísticas médicas calculadas
        """
        try:
            # Leer datos actuales
            success, records = self.read_medical_records()
            
            if not success or not records:
                return {
                    "lesiones_totales": 0,
                    "lesiones_activas": 0,
                    "registros_google": 0,
                    "casos_graves": 0,
                    "error": "No se pudieron cargar los datos"
                }
            
            # Calcular estadísticas
            lesiones_totales = len(records)
            lesiones_activas = len([r for r in records if r.get('estado', '').lower() in ['activa', 'active', 'en tratamiento']])
            casos_graves = len([r for r in records if r.get('severidad', '').lower() in ['grave', 'severa', 'critica']])
            
            return {
                "lesiones_totales": lesiones_totales,
                "lesiones_activas": lesiones_activas,
                "registros_google": lesiones_totales,
                "casos_graves": casos_graves,
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": None
            }
            
        except Exception as e:
            return {
                "lesiones_totales": 0,
                "lesiones_activas": 0,
                "registros_google": 0,
                "casos_graves": 0,
                "error": f"Error al calcular estadísticas: {str(e)}"
            }

    def check_sheets_connection(self) -> Tuple[bool, str]:
        """
        Verificar estado de conexión con Google Sheets
        
        Returns:
            Tuple[bool, str]: (Connected, Status message)
        """
        try:
            if not self.credentials_loaded:
                # Intentar método alternativo con API pública
                return self._try_public_api_connection()
            
            # Intentar acceder al sheet
            spreadsheet = self.client.open_by_key(self.sheet_config["sheet_id"])
            worksheet = spreadsheet.worksheet(self.sheet_config["worksheet_name"])
            
            # Obtener información básica
            total_rows = len(worksheet.get_all_values())
            return True, f"✅ Conectado - {max(0, total_rows - 1)} registros"
            
        except Exception as e:
            # Fallback a API pública si falla la autenticación
            return self._try_public_api_connection()
    
    def _try_public_api_connection(self) -> Tuple[bool, str]:
        """
        Intentar conexión usando API pública de Google Sheets
        
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        try:
            import requests
            
            # URL para obtener datos CSV públicos
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_config['sheet_id']}/export?format=csv&gid=0"
            
            response = requests.get(csv_url, timeout=10)
            response.raise_for_status()
            
            # Contar líneas para obtener número de registros
            lines = response.text.strip().split('\n')
            total_records = max(0, len(lines) - 1)  # -1 para excluir headers
            
            return True, f"✅ Conectado vía API pública - {total_records} registros"
            
        except Exception as e:
            return False, f"❌ Error al leer registros: {str(e)}"
    
    def get_public_data(self) -> Tuple[bool, List[Dict]]:
        """
        Obtener datos usando API pública de Google Sheets
        
        Returns:
            Tuple[bool, List[Dict]]: (Success, Data)
        """
        try:
            import requests
            
            # URL para CSV público
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_config['sheet_id']}/export?format=csv&gid=0"
            
            response = requests.get(csv_url, timeout=10)
            response.raise_for_status()
            
            # Procesar CSV
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                return True, []
            
            # Headers
            headers = [h.strip('"') for h in lines[0].split(',')]
            
            # Datos
            data = []
            for line in lines[1:]:
                if line.strip():
                    values = [v.strip('"') for v in line.split(',')]
                    if len(values) >= len(headers):
                        row_data = dict(zip(headers, values))
                        data.append(row_data)
            
            return True, data
            
        except Exception as e:
            print(f"Error en get_public_data: {e}")
            return False, []
    
    def get_statistics(self) -> Dict:
        """
        Obtener estadísticas mejoradas con fallback a API pública
        
        Returns:
            Dict: Estadísticas médicas
        """
        try:
            # Intentar método original primero
            if self.credentials_loaded:
                return self._get_authenticated_statistics()
            else:
                return self._get_public_statistics()
                
        except Exception as e:
            return self._get_public_statistics()
    
    def _get_public_statistics(self) -> Dict:
        """
        Obtener estadísticas usando API pública
        
        Returns:
            Dict: Estadísticas básicas
        """
        try:
            success, data = self.get_public_data()
            
            if not success or not data:
                return {
                    'total_registros': 0,
                    'registros_activos': 0,
                    'casos_graves': 0,
                    'ultima_actualizacion': 'Sin datos'
                }
            
            # Calcular estadísticas
            total_registros = len(data)
            registros_activos = 0
            casos_graves = 0
            
            for row in data:
                # Buscar estados activos (adaptable a diferentes columnas)
                for key, value in row.items():
                    if isinstance(value, str):
                        value_lower = value.lower()
                        if 'activ' in value_lower and key.lower() in ['estado', 'status']:
                            registros_activos += 1
                        if any(word in value_lower for word in ['grave', 'crítico', 'serio']) and key.lower() in ['severidad', 'gravedad']:
                            casos_graves += 1
            
            return {
                'total_registros': total_registros,
                'registros_activos': registros_activos,
                'casos_graves': casos_graves,
                'ultima_actualizacion': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
        except Exception as e:
            return {
                'total_registros': 0,
                'registros_activos': 0,
                'casos_graves': 0,
                'ultima_actualizacion': 'Error'
            }
    
    def _get_authenticated_statistics(self) -> Dict:
        """Estadísticas usando autenticación original"""
        # Método original existente
        return {
            'total_registros': 0,
            'registros_activos': 0,
            'casos_graves': 0,
            'ultima_actualizacion': datetime.now().strftime("%Y-%m-%d %H:%M")
        }