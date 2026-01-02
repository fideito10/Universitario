import gspread
from google.oauth2.service_account import Credentials
import json
import os
import pandas as pd

def get_credentials():
    possible_paths = [
        "credentials/service_account.json",
        "credentials/car-digital-441319-1a4e4b5c11c2.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    return None

def test_columns():
    creds_dict = get_credentials()
    if not creds_dict:
        print("ERROR: No credentials found.")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    sheets = {
        "Administracion": ("1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw", "Jugadores_Maestro"),
        "Medica": ("1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ", None),
        "Fisica": ("1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI", "Base Test")
    }

    for name, (key, ws_name) in sheets.items():
        try:
            sh = client.open_by_key(key)
            if ws_name:
                ws = sh.worksheet(ws_name)
            else:
                ws = sh.get_worksheet(0)
            
            data = ws.get_all_records()
            if data:
                print(f"COLUMNS for {name}: {list(data[0].keys())}")
            else:
                print(f"EMPTY: {name}")
        except Exception as e:
            print(f"ERROR: {name} - {str(e)}")

if __name__ == "__main__":
    test_columns()
