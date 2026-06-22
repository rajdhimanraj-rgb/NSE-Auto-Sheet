#SPREADSHEET_ID = "1QC4I4LUhPkNUl3SRPz5wrU3Sm2U2pBM_vbzbOkkM3lE" 
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import json

# ==========================
# GOOGLE SHEETS CONNECTION
# ==========================

creds_json = os.environ.get('GCP_CREDENTIALS')

if not creds_json:
    print("ERROR: GCP_CREDENTIALS secret missing!")
    exit(1)

creds_dict = json.loads(creds_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

spreadsheet_id = "1QC4I4LUhPkNUl3SRPz5wrU3Sm2U2pBM_vbzbOkkM3lE"

try:
    ws = client.open_by_key(spreadsheet_id).worksheet("FOChange")
except Exception as e:
    print(f"Sheet Connection Error: {e}")
    exit(1)

# ==========================
# NSE DATA FETCH
# ==========================

def fetch_oi_spurts():

    url = "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings"

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        # NSE Cookie Initialization
        session.get(
            "https://www.nseindia.com",
            headers=headers,
            timeout=20
        )

        response = session.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        # Most NSE APIs return records under "data"
        records = data.get("data", [])

        if not records:
            print("No data received from NSE.")
            return None

        df = pd.DataFrame(records)

        return df

    except Exception as e:
        print(f"NSE Fetch Error: {e}")
        return None


# ==========================
# UPDATE SHEET
# ==========================

df = fetch_oi_spurts()

if df is not None and not df.empty:

    try:

        # Clear existing sheet
        ws.clear()

        # Prepare data
        headers = df.columns.tolist()
        values = df.fillna("").astype(str).values.tolist()

        # Update sheet
        ws.update(
            "A1",
            [headers] + values
        )

        ist_now = (
            datetime.utcnow() +
            timedelta(hours=5, minutes=30)
        ).strftime("%d-%b-%Y %H:%M:%S")

        ws.update(
            "O2",
            [[f"Last Update : {ist_now} IST"]]
        )

        print(
            f"SUCCESS: {len(df)} records updated in FOChange sheet."
        )

    except Exception as e:
        print(f"Google Sheet Update Error: {e}")

else:
    print("FAILED: No data fetched from NSE.")
