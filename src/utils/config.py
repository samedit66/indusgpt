import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    openai_api_key: str
    openai_base_url: str
    model_name: str
    bot_token: str
    db_file: str
    log_file: str
    data_dir: str
    airtable_access_token: str
    airtable_base_id: str
    airtable_table_id: str
    excel_sheet_name: str


def load_config() -> Config:
    load_dotenv()

    return Config(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        openai_base_url=os.environ["OPENAI_API_BASE_URL"],
        model_name=os.environ["MODEL"],
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        db_file=os.environ["DATABASE_FILE"],
        log_file=os.environ["LOG_FILE"],
        data_dir=os.environ["DATA_DIR"],
        airtable_access_token=os.environ["AIRTABLE_ACCESS_TOKEN"],
        airtable_base_id=os.environ["AIRTABLE_BASE_ID"],
        airtable_table_id=os.environ["AIRTABLE_TABLE_ID"],
        excel_sheet_name=os.environ["EXCEL_SHEET_NAME"],
    )
