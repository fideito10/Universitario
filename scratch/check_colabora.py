import os
import sys
import gspread
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.credentials import get_service_account_credentials
from scratch.check_rucks_distribution import clean_player, get_int

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

    tackles = sections.get("1 TACKLE", {}).get("rows", [])
    colabora_map = defaultdict(int)
    for r in tackles:
        is_colab = get_int(r.get("colabora"))
        if is_colab:
            raw_p = r.get("player") or r.get("jugador") or ""
            players = [clean_player(p.strip()) for p in raw_p.split("|") if p.strip()]
            for p in players:
                colabora_map[p] += 1
                
    print("TOP PLAYERS FOR 'COLABORA' IN TACKLE:")
    for p, c in sorted(colabora_map.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {p}: {c}")

if __name__ == "__main__":
    main()
