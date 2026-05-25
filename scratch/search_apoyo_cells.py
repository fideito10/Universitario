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
    
    found = []
    for r_idx, row in enumerate(rows_list):
        for c_idx, val in enumerate(row):
            if "apoyo" in str(val).lower():
                found.append((r_idx + 1, c_idx + 1, val))
                
    print(f"Total occurrences of 'apoyo' in sheet cells: {len(found)}")
    for f in found[:30]:
        print(f"  Row {f[0]}, Col {f[1]}: '{f[2]}'")

if __name__ == "__main__":
    main()
