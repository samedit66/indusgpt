import gspread
from google.oauth2.service_account import Credentials

from src.chat.info_extractor import UserInformation, extract_info
from src.persistence.models import User
from src import types


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client(credentials_path: str) -> gspread.Client:
    """Get an authorized Google Sheets client.

    Args:
        credentials_path: Path to Google credentials file

    Returns:
        An authorized gspread client
    """
    creds = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def flatten_user_info(user_name: str, tg: str, user_info: UserInformation) -> dict:
    """Flatten UserInformation for Google Sheets row.

    Args:
        user_name: Name of the user
        tg: Telegram URL of the user
        user_info: UserInformation object containing all user data

    Returns:
        Dictionary with flattened user information ready for Google Sheets
    """
    return {
        "user_name": user_name,
        "tg": tg,
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
        # Business activities
        "business_activities": user_info.business_activities.activities,
        # Hosting info
        "has_website": str(user_info.hosting.has_website),
        "hosting_access_details": user_info.hosting.access_details or "",
        # Profit sharing
        "profit_sharing": user_info.profit_sharing.agreement,
    }


class GoogleSheetsProcessor:
    """Processor that writes Q&A data to Google Sheets."""

    def __init__(
        self, credentials_path: str, sheet_url: str, worksheet_name: str
    ) -> None:
        """Initialize the Google Sheets processor.

        If such worksheet does not exist, the processor will create a new worksheet with the given name.

        Args:
            credentials_path: Path to Google credentials file
            sheet_url: URL of the Google Sheet to write to
            worksheet_name: Name of the worksheet within the sheet
        """
        self.credentials_path = credentials_path
        self.sheet_url = sheet_url
        self.worksheet_name = worksheet_name
        self.client = get_client(credentials_path)

    async def __call__(self, user_id: int, qa_pairs: list[types.QaPair]) -> None:
        """Process Q&A pairs by writing them to Google Sheets.

        Args:
            user_id: The ID of the user whose Q&A pairs are being processed
            qa_pairs: List of question-answer pairs to process
        """
        user_name = (await User.filter(id=user_id).first()).name
        tg = (await User.filter(id=user_id).first()).url
        user_info = await extract_info(qa_pairs)

        # Open the sheet by URL
        sheet = self.client.open_by_url(self.sheet_url)

        # Open or create the worksheet
        try:
            worksheet = sheet.worksheet(self.worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(
                title=self.worksheet_name, rows="100", cols="20"
            )
            # Set up header row
            headers = list(flatten_user_info(user_name, tg, user_info).keys())
            worksheet.append_row(headers)

        # Prepare and append row data
        row = list(flatten_user_info(user_name, tg, user_info).values())
        worksheet.append_row(row)
