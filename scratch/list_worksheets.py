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
    
    sheets = sh.worksheets()
    print("ALL WORKSHEETS IN GOOGLE SHEET:")
    for s in sheets:
        print(f"  - '{s.title}' (Rows: {s.row_count}, Cols: {s.col_count})")

if __name__ == "__main__":
    main()
