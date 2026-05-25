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

    moviles = sections.get("2 MOVILES", {}).get("rows", [])
    appearances_map = defaultdict(int)
    for r in moviles:
        # Check own breakdown
        is_propio = get_int(r.get("propio"))
        team = r.get("team") or ""
        # Let's say if team is local (CULP / Universitario) or propio is 1
        if is_propio or "CULP" in team.upper() or "UNI" in team.upper() or not team:
            raw_p = r.get("player") or r.get("jugador") or ""
            players = [clean_player(p.strip()) for p in raw_p.split("|") if p.strip()]
            for p in players:
                appearances_map[p] += 1
                
    print("TOP PLAYERS FOR BREAKDOWN APPEARANCES (APOYOS):")
    for p, c in sorted(appearances_map.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {p}: {c}")

if __name__ == "__main__":
    main()
