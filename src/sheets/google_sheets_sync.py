"""
Google Sheets Synchronization Module for CAR Rugby Club
Integra Google Sheets con el sistema de gestión del club
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime
import json
import re
import os

class GoogleSheetsCAR:
    def __init__(self):
        """Inicializar conexión con Google Sheets"""
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        self.client = None
        self.setup_credentials()
    
    def setup_credentials(self):
        """Configurar credenciales de Google desde st.secrets o archivo local"""
        try:
            # Primero intentar obtener desde st.secrets (para Streamlit Cloud)
            if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
                creds = Credentials.from_service_account_info(
                    dict(st.secrets["gcp_service_account"]), 
                    scopes=self.scope
                )
                self.client = gspread.authorize(creds)
                return True
            
            # Si estamos local, intentar cargar desde archivo
            creds_path = "data/car_google_credentials.json"
            if os.path.exists(creds_path):
                creds = Credentials.from_service_account_file(
                    creds_path, 
                    scopes=self.scope
                )
                self.client = gspread.authorize(creds)
                return True
            else:
                return False
        except Exception as e:
            st.error(f"❌ Error en credenciales: {e}")
            return False

    def extract_sheet_id(self, url):
        """Extraer ID de hoja de Google Sheets desde URL"""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        else:
            return None

    def test_connection(self, sheet_url):
        """Probar conexión con la hoja"""
        try:
            sheet_id = self.extract_sheet_id(sheet_url)
            if not sheet_id:
                return False, "URL inválida"
            
            spreadsheet = self.client.open_by_key(sheet_id)
            return True, f"Conectado a: {spreadsheet.title}"
        except Exception as e:
            return False, f"Error de conexión: {e}"

    def get_sheet_data(self, sheet_url, worksheet_name=None):
        """Obtener datos de la hoja"""
        try:
            sheet_id = self.extract_sheet_id(sheet_url)
            spreadsheet = self.client.open_by_key(sheet_id)
            
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            # Obtener todos los registros
            records = worksheet.get_all_records()
            
            if records:
                df = pd.DataFrame(records)
                return True, df
            else:
                return False, "Hoja vacía o sin encabezados"
                
        except Exception as e:
            return False, f"Error al leer datos: {e}"

    def sync_medical_data(self, sheet_url, doctor_name, worksheet_name=None):
        """Sincronizar datos médicos desde Google Sheets"""
        success, data = self.get_sheet_data(sheet_url, worksheet_name)
        
        if not success:
            return False, data
        
        df = data
        medical_records = []
        
        # Mapeo de columnas (flexible)
        column_mapping = {
            'jugador': 'player_name',
            'nombre': 'player_name',
            'player': 'player_name',
            'division': 'division',
            'categoria': 'division',
            'lesion': 'injury_type',
            'tipo_lesion': 'injury_type',
            'injury': 'injury_type',
            'severidad': 'severity',
            'gravedad': 'severity',
            'fecha': 'date_occurred',
            'fecha_lesion': 'date_occurred',
            'recuperacion': 'expected_recovery',
            'fecha_recuperacion': 'expected_recovery',
            'estado': 'status',
            'tratamiento': 'treatment',
            'observaciones': 'notes',
            'notas': 'notes'
        }
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        
        # Renombrar columnas
        df = df.rename(columns=column_mapping)
        
        # Procesar cada fila
        for index, row in df.iterrows():
            if pd.notna(row.get('player_name')) and row.get('player_name').strip():
                record = {
                    "id": f"gs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index}",
                    "player_name": str(row.get('player_name', '')).strip(),
                    "division": str(row.get('division', '')).strip(),
                    "injury_type": str(row.get('injury_type', '')).strip(),
                    "severity": str(row.get('severity', 'Moderada')).strip(),
                    "date_occurred": str(row.get('date_occurred', datetime.now().date())),
                    "expected_recovery": str(row.get('expected_recovery', '')),
                    "status": str(row.get('status', 'En tratamiento')).strip(),
                    "treatment": str(row.get('treatment', '')).strip(),
                    "doctor": doctor_name,
                    "notes": str(row.get('notes', '')).strip(),
                    "sync_source": "Google Sheets",
                    "sync_date": datetime.now().isoformat(),
                    "sheet_url": sheet_url
                }
                medical_records.append(record)
        
        return True, medical_records

    def sync_nutrition_data(self, sheet_url, nutritionist_name, worksheet_name=None):
        """Sincronizar datos nutricionales desde Google Sheets"""
        success, data = self.get_sheet_data(sheet_url, worksheet_name)
        
        if not success:
            return False, data
        
        df = data
        nutrition_records = []
        
        # Mapeo de columnas nutricionales
        column_mapping = {
            'jugador': 'player_name',
            'nombre': 'player_name',
            'division': 'division',
            'categoria': 'division',
            'plan': 'plan_type',
            'tipo_plan': 'plan_type',
            'calorias': 'calories_target',
            'proteinas': 'protein_target',
            'carbohidratos': 'carbs_target',
            'grasas': 'fat_target',
            'peso': 'current_weight',
            'altura': 'height',
            'objetivo': 'goal',
            'observaciones': 'notes',
            'notas': 'notes'
        }
        
        # Normalizar y renombrar
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        df = df.rename(columns=column_mapping)
        
        # Procesar cada fila
        for index, row in df.iterrows():
            if pd.notna(row.get('player_name')) and row.get('player_name').strip():
                record = {
                    "id": f"gs_nut_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index}",
                    "player_name": str(row.get('player_name', '')).strip(),
                    "division": str(row.get('division', '')).strip(),
                    "plan_type": str(row.get('plan_type', 'Plan General')).strip(),
                    "calories_target": self.safe_float(row.get('calories_target', 2500)),
                    "protein_target": self.safe_float(row.get('protein_target', 150)),
                    "carbs_target": self.safe_float(row.get('carbs_target', 300)),
                    "fat_target": self.safe_float(row.get('fat_target', 80)),
                    "current_weight": self.safe_float(row.get('current_weight', 0)),
                    "height": self.safe_float(row.get('height', 0)),
                    "goal": str(row.get('goal', 'Mantener peso')).strip(),
                    "nutritionist": nutritionist_name,
                    "notes": str(row.get('notes', '')).strip(),
                    "created_date": datetime.now().date().isoformat(),
                    "sync_source": "Google Sheets",
                    "sync_date": datetime.now().isoformat(),
                    "sheet_url": sheet_url
                }
                nutrition_records.append(record)
        
        return True, nutrition_records

    def sync_strength_data(self, sheet_url, trainer_name, worksheet_name=None):
        """Sincronizar datos de tests de fuerza desde Google Sheets"""
        success, data = self.get_sheet_data(sheet_url, worksheet_name)
        
        if not success:
            return False, data
        
        df = data
        strength_records = []
        
        # Mapeo de columnas para tests de fuerza
        column_mapping = {
            'jugador': 'player_name',
            'nombre': 'player_name',
            'division': 'division',
            'categoria': 'division',
            'fecha': 'test_date',
            'test_fecha': 'test_date',
            'tipo_test': 'test_type',
            'test_tipo': 'test_type',
            'ejercicio': 'test_type',
            'peso': 'weight',
            'kg': 'weight',
            'repeticiones': 'repetitions',
            'reps': 'repetitions',
            'series': 'series',
            'peso_corporal': 'body_weight',
            'altura': 'height',
            'grasa_corporal': 'body_fat',
            'masa_muscular': 'muscle_mass',
            'preparador': 'tester',
            'entrenador': 'tester',
            'observaciones': 'notes',
            'notas': 'notes'
        }
        
        # Normalizar y renombrar
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        df = df.rename(columns=column_mapping)
        
        # Procesar cada fila
        for index, row in df.iterrows():
            if pd.notna(row.get('player_name')) and row.get('player_name').strip():
                # Calcular 1RM estimado
                weight = self.safe_float(row.get('weight', 0))
                reps = max(1, int(self.safe_float(row.get('repetitions', 1))))
                one_rm = weight * (36 / (37 - reps)) if reps < 37 else weight
                
                record = {
                    "id": f"gs_str_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index}",
                    "player_name": str(row.get('player_name', '')).strip(),
                    "division": str(row.get('division', '')).strip(),
                    "test_date": str(row.get('test_date', datetime.now().date())),
                    "test_type": str(row.get('test_type', 'Bench Press')).strip(),
                    "weight": weight,
                    "repetitions": reps,
                    "series": max(1, int(self.safe_float(row.get('series', 1)))),
                    "one_rm_estimated": round(one_rm, 1),
                    "body_weight": self.safe_float(row.get('body_weight', 0)) or None,
                    "height": self.safe_float(row.get('height', 0)) or None,
                    "body_fat": self.safe_float(row.get('body_fat', 0)) or None,
                    "muscle_mass": self.safe_float(row.get('muscle_mass', 0)) or None,
                    "tester": trainer_name,
                    "notes": str(row.get('notes', '')).strip(),
                    "sync_source": "Google Sheets",
                    "sync_date": datetime.now().isoformat(),
                    "sheet_url": sheet_url,
                    "created_at": datetime.now().isoformat()
                }
                strength_records.append(record)
        
        return True, strength_records

    def sync_field_data(self, sheet_url, trainer_name, worksheet_name=None):
        """Sincronizar datos de tests de campo desde Google Sheets"""
        success, data = self.get_sheet_data(sheet_url, worksheet_name)
        
        if not success:
            return False, data
        
        df = data
        field_records = []
        
        # Mapeo de columnas para tests de campo
        column_mapping = {
            'jugador': 'player_name',
            'nombre': 'player_name',
            'division': 'division',
            'categoria': 'division',
            'fecha': 'test_date',
            'test_fecha': 'test_date',
            'tipo_test': 'test_type',
            'test_tipo': 'test_type',
            'prueba': 'test_type',
            'resultado': 'result',
            'tiempo': 'result',
            'distancia': 'result',
            'marca': 'result',
            'unidad': 'unit',
            'clima': 'weather',
            'temperatura': 'temperature',
            'superficie': 'surface',
            'humedad': 'humidity',
            'preparador': 'tester',
            'entrenador': 'tester',
            'observaciones': 'notes',
            'notas': 'notes'
        }
        
        # Normalizar y renombrar
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        df = df.rename(columns=column_mapping)
        
        # Procesar cada fila
        for index, row in df.iterrows():
            if pd.notna(row.get('player_name')) and row.get('player_name').strip():
                # Determinar unidad según tipo de test
                test_type = str(row.get('test_type', '')).strip()
                unit = str(row.get('unit', ''))
                
                if not unit:
                    if "sprint" in test_type.lower() or "velocidad" in test_type.lower():
                        unit = "segundos"
                    elif "salto" in test_type.lower():
                        unit = "cm"
                    elif "yo-yo" in test_type.lower() or "cooper" in test_type.lower():
                        unit = "metros"
                    else:
                        unit = "unidades"
                
                record = {
                    "id": f"gs_field_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index}",
                    "player_name": str(row.get('player_name', '')).strip(),
                    "division": str(row.get('division', '')).strip(),
                    "test_date": str(row.get('test_date', datetime.now().date())),
                    "test_type": test_type,
                    "result": self.safe_float(row.get('result', 0)),
                    "unit": unit,
                    "weather": str(row.get('weather', 'No especificado')).strip(),
                    "temperature": self.safe_float(row.get('temperature', 0)) or None,
                    "surface": str(row.get('surface', 'No especificado')).strip(),
                    "humidity": self.safe_float(row.get('humidity', 0)) or None,
                    "tester": trainer_name,
                    "notes": str(row.get('notes', '')).strip(),
                    "sync_source": "Google Sheets",
                    "sync_date": datetime.now().isoformat(),
                    "sheet_url": sheet_url,
                    "created_at": datetime.now().isoformat()
                }
                field_records.append(record)
        
        return True, field_records

    def safe_float(self, value, default=0):
        """Convertir valor a float de forma segura"""
        try:
            if pd.isna(value) or value == '':
                return default
            return float(str(value).replace(',', '.'))
        except:
            return default

    def get_worksheets(self, sheet_url):
        """Obtener lista de hojas de trabajo"""
        try:
            sheet_id = self.extract_sheet_id(sheet_url)
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheets = [ws.title for ws in spreadsheet.worksheets()]
            return True, worksheets
        except Exception as e:
            return False, f"Error: {e}"

# Funciones de utilidad
def save_sync_config(config):
    """Guardar configuración de sincronización"""
    with open('data/sync_config.json', 'w') as f:
        json.dump(config, f, indent=2)

def load_sync_config():
    """Cargar configuración de sincronización"""
    try:
        with open('data/sync_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "medical_sheets": [], 
            "nutrition_sheets": [],
            "strength_sheets": [],
            "field_sheets": []
        }