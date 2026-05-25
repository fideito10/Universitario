from src.sheets.google_sheets_manager import GoogleSheetsManager
gsm = GoogleSheetsManager()
sheet_id = '1hYAD7j4DIibW37hVyB7fAVOl_dzoMcg-cHJaP6MX2jo'
ss = gsm.client.open_by_key(sheet_id)
for ws in ss.worksheets():
    try:
        val = ws.acell("A1").value
        print(f"Sheet: {ws.title} | Cell A1: {val}")
    except:
        pass
