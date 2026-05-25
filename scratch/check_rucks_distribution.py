import os
import sys
import gspread
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.credentials import get_service_account_credentials
import re

def clean_player(val):
    if not val: return ""
    # simple clean
    val_str = str(val).strip().upper()
    val_str = re.sub(r'^\d+[-\s]*', '', val_str)
    
    replacements = {
        "Ã“": "Ó", "Ã\x8d": "Í", "Ã\x81": "Á", "Ã‰": "É", "Ãš": "Ú", "Ã‘": "Ñ",
        "Ã³": "Ó", "Ã­": "Í", "Ã¡": "Á", "Ã©": "É", "Ãº": "Ú", "Ã±": "Ñ",
        "Ã±": "Ñ", "Ã‘": "Ñ", "Ã¼": "Ü", "Ãœ": "Ü"
    }
    for bad, good in replacements.items():
        val_str = val_str.replace(bad, good)
        
    return val_str.strip()

SHEET_ID = "1JXKJkDYcrOHRQ4fmC1uPkEW4crLNdJhzJLcwbMdOICU"

def get_int(val):
    try:
        return int(float(str(val).strip().replace(",", ".")))
    except:
        return 0

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
    
    primero_map = defaultdict(int)
    segundo_map = defaultdict(int)
    
    for r in moviles:
        raw_p = r.get("player") or ""
        players = [clean_player(p.strip()) for p in raw_p.split("|") if p.strip()]
        if not players: continue
        
        is_first = get_int(r.get("1"))
        is_second = get_int(r.get("2"))
        
        # Scenario A: If 1 is marked, first player is 1st. If 2 is marked, second player (if any) or first player is 2nd.
        if is_first:
            primero_map[players[0]] += 1
        if is_second:
            p_seg = players[1] if len(players) > 1 else players[0]
            segundo_map[p_seg] += 1
            
    print("TOP 5 - PRIMERO EN EL RUCK:")
    for p, c in sorted(primero_map.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {p}: {c}")
        
    print("\nTOP 5 - SEGUNDO EN EL RUCK:")
    for p, c in sorted(segundo_map.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {p}: {c}")

if __name__ == "__main__":
    main()
