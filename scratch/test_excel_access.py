import pandas as pd
import requests

sheet_id = '1Te9jH1VhUgT3r1lSv9XLZPmcaZw_64i-'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'

print(f"Probando acceso a: {url}")
try:
    # Intentar descargar el contenido primero para ver si es accesible
    response = requests.get(url)
    if response.status_code == 200:
        print("Acceso exitoso al archivo Excel.")
        df_dict = pd.read_excel(url, sheet_name=None)
        print("Hojas encontradas:", list(df_dict.keys()))
    else:
        print(f"Error de acceso: Status {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
