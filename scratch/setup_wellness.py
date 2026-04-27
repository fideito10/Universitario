import gspread
from google.oauth2.service_account import Credentials
import os

def setup_wellness_sheet():
    SHEET_ID = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    
    creds_path = "credentials/service_account.json"
    if not os.path.exists(creds_path):
        print(f"Error: No se encontró {creds_path}")
        return

    creds = Credentials.from_service_account_file(creds_path, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    
    wellness_name = "Wellness_Jugador"
    headers = ["ID", "Timestamp", "Email_Jugador", "Nombre_Jugador", "RPE", "Sueno", "DOMS", "Wellness_Score", "Fecha"]
    
    try:
        worksheet = spreadsheet.worksheet(wellness_name)
        print(f"La hoja '{wellness_name}' ya existe.")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=wellness_name, rows=1000, cols=len(headers))
        worksheet.insert_row(headers, 1)
        print(f"Hoja '{wellness_name}' creada exitosamente.")

if __name__ == "__main__":
    setup_wellness_sheet()
