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

    print("--- ALL CATEGORIES AND THEIR NON-EMPTY HEADERS ---")
    for cat, data in sections.items():
        headers = [h for h in data["headers"] if h.strip()]
        print(f"\n* CATEGORY: {cat}")
        print(f"  Headers ({len(headers)}): {headers}")
        # print unique non-empty player values if any
        players = set()
        for r in data["rows"]:
            p = r.get("player") or r.get("jugador") or r.get("name")
            if p and p.strip() and not p.startswith(cat):
                players.add(p.strip())
        if players:
            print(f"  Sample Players ({len(players)}): {list(players)[:5]}")

if __name__ == "__main__":
    main()
