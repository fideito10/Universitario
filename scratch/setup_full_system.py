import gspread
from google.oauth2.service_account import Credentials
import os

def setup_full_system_sheets():
    NEW_SHEET_ID = "10Gixz7_8AvtYqBMS6RWz-wlW_MSpPVbjoCdz1GRM1lU"
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    
    creds_path = "credentials/service_account.json"
    creds = Credentials.from_service_account_file(creds_path, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(NEW_SHEET_ID)
    
    # 1. Configurar Usuarios
    try:
        ws_users = spreadsheet.worksheet("Usuarios")
    except gspread.WorksheetNotFound:
        ws_users = spreadsheet.add_worksheet(title="Usuarios", rows=100, cols=6)
        ws_users.insert_row(["Usuario", "Clave", "Rol", "Nombre", "DNI", "Email"], 1)
        ws_users.append_row(["admin", "admin123", "Administrador", "Admin Sistema", "", ""])
        print("Hoja 'Usuarios' creada.")

    # 2. Configurar Jugadores_Maestro
    try:
        ws_master = spreadsheet.worksheet("Jugadores_Maestro")
    except gspread.WorksheetNotFound:
        ws_master = spreadsheet.add_worksheet(title="Jugadores_Maestro", rows=1000, cols=10)
        ws_master.insert_row(["DNI", "Nombre", "Apellido", "Division", "Fecha_Nacimiento", "Posicion", "Email", "Telefono", "Obra_Social", "Estado"], 1)
        # Agregar a Blas Rivera Cano para pruebas
        ws_master.append_row(["43870472", "Blas", "Rivera cano", "Primera", "2000-01-01", "Apertura", "blas@ejemplo.com", "", "", "Activo"])
        print("Hoja 'Jugadores_Maestro' creada con usuario de prueba Blas.")

    # 3. Configurar Wellness
    try:
        ws_wellness = spreadsheet.worksheet("Wellness_Jugador")
    except gspread.WorksheetNotFound:
        headers = ["ID", "Timestamp", "Email_Jugador", "Nombre_Jugador", "RPE", "Sueno", "DOMS", "Wellness_Score", "Fecha"]
        ws_wellness = spreadsheet.add_worksheet(title="Wellness_Jugador", rows=1000, cols=len(headers))
        ws_wellness.insert_row(headers, 1)
        print("Hoja 'Wellness_Jugador' creada.")

    # 4. Configurar Registros Médicos
    try:
        ws_medica = spreadsheet.worksheet("Registros_Medicos")
    except gspread.WorksheetNotFound:
        medical_headers = [
            "ID", "Timestamp", "Nombre_Profesional", "Email_Profesional",
            "Nombre_Paciente", "Division", "Diagnostico", "Fecha_Atencion",
            "Tipo_Lesion", "Severidad", "Parte_Cuerpo", "Tratamiento",
            "Tiempo_Recuperacion", "Puede_Entrenar", "Medicamentos",
            "Observaciones", "Proxima_Evaluacion", "Estado", "Fecha_Registro"
        ]
        ws_medica = spreadsheet.add_worksheet(title="Registros_Medicos", rows=1000, cols=len(medical_headers))
        ws_medica.insert_row(medical_headers, 1)
        print("Hoja 'Registros_Medicos' creada.")

if __name__ == "__main__":
    setup_full_system_sheets()
