import gspread
from google.oauth2.service_account import Credentials

from src.chat.info_extractor import extract_info
from src.persistence.models import User
from src import types
from src.processors import utils


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
            headers = list(utils.flatten_user_info(user_name, tg, user_info).keys())
            worksheet.append_row(headers)

        # Prepare and append row data
        row = list(utils.flatten_user_info(user_name, tg, user_info).values())
        worksheet.append_row(row)
