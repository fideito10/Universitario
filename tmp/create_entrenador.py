import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

creds_path = "credentials/service_account.json"
creds = Credentials.from_service_account_file(creds_path, scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SHEET_ID)

ws_users = spreadsheet.worksheet("Usuarios")

# Verificar si ya existe el usuario entrenador
records = ws_users.get_all_records()
ya_existe = any(str(r.get("Usuario", "")).strip().lower() == "entrenador" for r in records)

if ya_existe:
    print("[OK] El usuario 'entrenador' ya existe en la planilla.")
else:
    # Nuevo usuario generico de entrenador
    nuevo_usuario = ["entrenador", "uni2026", "Entrenador", "Entrenador Universitario", "", ""]
    ws_users.append_row(nuevo_usuario)
    print("[OK] Usuario creado exitosamente.")

print("   Usuario:    entrenador")
print("   Contrasena: uni2026")
print("   Rol:        Entrenador")
print("   Nombre:     Entrenador Universitario")
print("")
print("Usuarios actuales en la planilla:")
records = ws_users.get_all_records()
for r in records:
    print(f"  - {r.get('Usuario')} | {r.get('Rol')} | {r.get('Nombre')}")
