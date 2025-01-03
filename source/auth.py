import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Define the scope for the Google Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Path to your service account key file
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE_PATH')

# Authenticate using the service account
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Initialize the gspread client
gsheet_client = gspread.authorize(credentials)
