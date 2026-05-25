import os
import sys
import gspread

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.credentials import get_service_account_credentials

SHEET_ID = "1JXKJkDYcrOHRQ4fmC1uPkEW4crLNdJhzJLcwbMdOICU"

def main():
    creds = get_service_account_credentials()
    if not creds: return
    client = gspread.authorize(creds)
    sh = client.open_by_key(SHEET_ID)
    
    ws = sh.worksheet("San Albano")
    rows_list = ws.get_all_values()
    
    sections = {}
    current_cat = None
    current_headers = []
    for cols in rows_list:
        if not cols or not any(str(c).strip() for c in cols): continue
        cols = [str(c).strip() for c in cols]
        
        if cols[0].startswith("CATEGORY:"):
            current_cat = cols[0].replace("CATEGORY:", "").split(";")[0].strip()
            sections[current_cat] = {"headers": [], "rows": []}
            current_headers = []
            continue
        
        if current_cat is None: continue
        
        if not current_headers:
            header_keywords = ["name", "player", "equipo", "team", "jugador", "nro", "#"]
            if any(any(k in str(h).lower() for k in header_keywords) for h in cols[:4]):
                current_headers = [h.lower() for h in cols]
                sections[current_cat]["headers"] = current_headers
            continue
        
        row = dict(zip(current_headers, cols + [""] * (len(current_headers) - len(cols))))
        sections[current_cat]["rows"].append(row)

    target_categories = ["2 MOVILES", "03 POSESION", "PERSONAL (*)", "12 PUNTOS (-)", "11 PESCA (0)"]
    for target in target_categories:
        for cat, data in sections.items():
            if target.upper() in cat.upper():
                print(f"\n=====================================")
                print(f"CATEGORY: {cat}")
                headers = [h for h in data["headers"] if h.strip()]
                print("HEADERS:")
                print(headers)
                print("SAMPLE ROW:")
                if data["rows"]:
                    row_cleaned = {k: v for k, v in data["rows"][0].items() if k.strip() and v.strip()}
                    print(row_cleaned)
                else:
                    print("No rows found.")

if __name__ == "__main__":
    main()
