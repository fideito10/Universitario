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
    
    categories = set()
    for cols in rows_list:
        if not cols or not any(str(c).strip() for c in cols): continue
        if cols[0].startswith("CATEGORY:"):
            cat = cols[0].replace("CATEGORY:", "").split(";")[0].strip()
            categories.add(cat)
            
    print("CATEGORIES IN SAN ALBANO MATCH:")
    for c in sorted(categories):
        print(f" - {c}")

if __name__ == "__main__":
    main()
