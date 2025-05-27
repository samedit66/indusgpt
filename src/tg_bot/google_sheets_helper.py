import gspread
from google.oauth2.service_account import Credentials

from src.chat.info_extractor import UserInformation


def flatten_user_info(user_name: str, user_info: UserInformation) -> dict:
    # Flatten UserInformation for Google Sheets row
    row = {
        "user_name": user_name,
        # Corporate accounts (comma-separated bank names)
        "accounts": ", ".join([acc.bank_name for acc in user_info.accounts]),
        # PSPs (comma-separated psp_name)
        "psps": ", ".join([psp.psp_name for psp in user_info.psps]),
        # PSP logins (comma-separated)
        "psp_logins": ", ".join([psp.login for psp in user_info.psps]),
        # PSP passwords (comma-separated)
        "psp_passwords": ", ".join([psp.password for psp in user_info.psps]),
        # PSP details (comma-separated)
        "psp_details": ", ".join([psp.details or "" for psp in user_info.psps]),
        # Company details (main)
        "company_name": user_info.company_details.name,
        "company_address": user_info.company_details.address,
        "company_phone": user_info.company_details.phone,
        "company_email": user_info.company_details.email,
        # Hosting info
        "has_website": str(user_info.hosting.has_website),
        "hosting_access_details": user_info.hosting.access_details or "",
        # Profit sharing
        "profit_sharing": user_info.profit_sharing.agreement,
    }
    return row


def write_user_info_to_sheet(
    user_name: str, user_info: UserInformation, credentials_path: str
):
    # Hardcoded sheet and worksheet names
    SHEET_NAME = "UserData"
    WORKSHEET_NAME = "UserInfo"

    # Authorize
    creds = Credentials.from_service_account_file(
        credentials_path,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    gc = gspread.authorize(creds)

    # Open or create the sheet
    try:
        sh = gc.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(SHEET_NAME)

    # Open or create the worksheet
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="20")
        # Set up header row
        headers = list(flatten_user_info(user_name, user_info).keys())
        ws.append_row(headers)

    # Prepare row data
    row = list(flatten_user_info(user_name, user_info).values())
    ws.append_row(row)
