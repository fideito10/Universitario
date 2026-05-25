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

    moviles = sections.get("2 MOVILES", {}).get("rows", [])
    print(f"Total rows in 2 MOVILES: {len(moviles)}")
    
    # Print sample of rows where 'ruck' is 1
    ruck_rows = [r for r in moviles if r.get("ruck") == "1"]
    print(f"Rows where 'ruck' is 1: {len(ruck_rows)}")
    
    # Print some rows where '1' or '2' is 1
    one_or_two = [r for r in moviles if r.get("1") == "1" or r.get("2") == "1" or r.get("1") or r.get("2")]
    print(f"Rows with non-empty '1' or '2': {len(one_or_two)}")
    for idx, r in enumerate(one_or_two[:15]):
        cleaned = {k: v for k, v in r.items() if k.strip() and v.strip()}
        print(f" Row {idx+1}: {cleaned}")

if __name__ == "__main__":
    main()
