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

    pts_rows = sections.get("12 PUNTOS (-)", {}).get("rows", [])
    print(f"Total rows in PUNTOS: {len(pts_rows)}")
    
    player_points = defaultdict(int)
    for r in pts_rows:
        # Check if own team
        is_propio = get_int(r.get("propio"))
        # We can also check if team contains 'CULP' or 'UNI' or is not 'Hurling' / opponent
        is_rival = get_int(r.get("rival"))
        if is_rival and not is_propio:
            continue
            
        raw_p = r.get("player") or r.get("jugador") or ""
        p = clean_player(raw_p)
        if not p: continue
        
        tries = get_int(r.get("try"))
        goals = get_int(r.get("goal"))
        penals = get_int(r.get("penal"))
        drops = get_int(r.get("drop"))
        try_penal = get_int(r.get("try penal"))
        
        pts = tries * 5 + goals * 2 + penals * 3 + drops * 3 + try_penal * 7
        player_points[p] += pts
        print(f"  Player: {p} | Tries: {tries}, Goals: {goals}, Penals: {penals}, Drops: {drops}, Try Penal: {try_penal} | Pts added: {pts}")
        
    print("\nPOINTS BY PLAYER:")
    for p, pts in sorted(player_points.items(), key=lambda x: x[1], reverse=True):
        print(f"  {p}: {pts} pts")

if __name__ == "__main__":
    main()
