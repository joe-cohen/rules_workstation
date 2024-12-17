import requests
import pandas as pd
from supabase import create_client, Client
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread
import os
import openpyxl

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # Replace with your Supabase API key
TABLE_NAME = "rules"  # Replace with your table name in Supabase
SERVICE_ACCOUNT_FILE = "/Users/josephcohen/Documents/rules_workstation/googleSheetsReader/rulesheetreader-975279076d7f.json"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_j154XhDgS_i4dEcwMkx_J_x0MQYcU_Vtr4GxF6IhO4/edit?gid=820606572#gid=820606572"
SHEET_NAME = "FOR REVIEW: Indication Defintion"
API_KEY = os.getenv("GOOGEL_API_KEY")

# Google Sheets API Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def extract_sheet_id_from_url(url):
    """Extract the Google Sheet ID from the URL."""
    match = re.search(r"/d/(.*?)/", url)
    if match:
        return match.group(1)
    raise ValueError("Invalid Google Sheet URL")


def authenticate_with_oauth():
    """Authenticate and return OAuth 2.0 credentials."""
    credentials_file = "/Users/josephcohen/Documents/rules_workstation/googleSheetsReader/client_secret_302397593962-9qpothmsg96hq9b701u54go88ij9devb.apps.googleusercontent.com.json"
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(f"The file {credentials_file} does not exist.")
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def get_google_sheet_data(sheet_url, sheet_name, creds):
    """Fetch data from a Google Sheet using OAuth 2.0 credentials."""
    sheet_key = extract_sheet_id_from_url(sheet_url)

    # Authenticate using OAuth credentials
    client = gspread.authorize(creds)

    # Open the Google Sheet and fetch data
    sheet = client.open_by_key(sheet_key)
    worksheet = sheet.worksheet(sheet_name)
    
    # Handle duplicate headers by forcing unique headers
    raw_data = worksheet.get_all_values()
    headers = raw_data[0]
    unique_headers = []
    seen = {}
    for h in headers:
        if h in seen:
            seen[h] += 1
            unique_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_headers.append(h)
    
    # Convert to DataFrame
    data = pd.DataFrame(raw_data[1:], columns=unique_headers)
    data = data.where(data != "", None)  
    data.columns = data.columns.str.strip()
    data.rename(columns={"Indication ID": "indication_id"}, inplace=True)
    return data

def get_max_rule_id(supabase_url, supabase_key, table_name):
    """Get the maximum rule_id from Supabase."""
    supabase: Client = create_client(supabase_url, supabase_key)
    response = supabase.table(table_name).select("rule_id").order("rule_id", desc=True).limit(1).execute()
    
    if response.data and len(response.data) > 0:
        return int(response.data[0]["rule_id"])
    else:
        # If there's no data in the table, we can start from 0 or any desired start
        return 0
    
def get_max_indcation_id(supabase_url, supabase_key, table_name):
    """Get the maximum rule_id from Supabase."""
    supabase: Client = create_client(supabase_url, supabase_key)
    response = supabase.table(table_name).select("indication_id").order("rule_id", desc=True).limit(1).execute()
    
    if response.data and len(response.data) > 0:
        return int(response.data[0]["indication_id"])
    else:
        # If there's no data in the table, we can start from 0 or any desired start
        return 0
    



def upload_to_supabase(supabase_url, supabase_key, table_name, data):
    """Upload a DataFrame to Supabase."""
    supabase: Client = create_client(supabase_url, supabase_key)
    data_dicts = data.to_dict(orient='records')

    for record in data_dicts:
        response = supabase.table(table_name).insert(record).execute()
        print(f"Uploaded record: {response}")


def main():
    # Authenticate with OAuth 2.0
    print("Authenticating with Google OAuth 2.0...")
    creds = authenticate_with_oauth()

    # Fetch Google Sheets Data
    print("Fetching Google Sheet data...")
    sheet_data = get_google_sheet_data(SHEET_URL, SHEET_NAME, creds)

    # Get the current maximum rule_id from Supabase
    print("Fetching current max rule_id from Supabase...")
    max_rule_id = get_max_rule_id(SUPABASE_URL, SUPABASE_KEY, TABLE_NAME)
    max_indication_id = get_max_indcation_id(SUPABASE_URL, SUPABASE_KEY, TABLE_NAME)

    sheet_data['rule_id'] = int(max_indication_id) + 1

    # Assign rule_id as integers
    sheet_data['indication_id'] = range(int(max_rule_id) + 1, int(max_rule_id) + 1 + len(sheet_data))

    # Ensure both rule_id and indication_id are integers
    sheet_data['rule_id'] = sheet_data['rule_id'].astype(int)
    sheet_data['indication_id'] = sheet_data['indication_id'].astype(int)

    # Upload Data to Supabase
    print("Uploading data to Supabase...")
    upload_to_supabase(SUPABASE_URL, SUPABASE_KEY, TABLE_NAME, sheet_data)
    print("Data upload complete.")

if __name__ == "__main__":
    main()
