import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


def _get_env(key: str, default: Any | None = None) -> str:
    """
    Retrieve an environment variable and raise a clear error if it's missing or empty.
    """
    value = os.getenv(key, default=default)
    print(value)
    if not value:
        raise RuntimeError(f"Missing required environment variable: '{key}'")
    return value


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
    airtable_base_id_daily_tracker: str
    airtable_table_id_daily_tracker: str
    airtable_base_id_users_count: str
    airtable_table_id_users_count: str


def load_config() -> Config:
    load_dotenv()

    return Config(
        openai_api_key=_get_env("OPENAI_API_KEY"),
        openai_base_url=_get_env("OPENAI_API_BASE_URL"),
        model_name=_get_env("MODEL"),
        bot_token=_get_env("TELEGRAM_BOT_TOKEN"),
        db_file=_get_env("DATABASE_FILE", "db.sqlite3"),
        log_file=_get_env("LOG_FILE", "bot.log"),
        data_dir=_get_env("DATA_DIR", "data"),
        airtable_access_token=_get_env("AIRTABLE_ACCESS_TOKEN"),
        airtable_base_id=_get_env("AIRTABLE_BASE_ID"),
        airtable_table_id=_get_env("AIRTABLE_TABLE_ID"),
        excel_sheet_name=_get_env("EXCEL_SHEET_NAME", "accounts.xlsx"),
        airtable_base_id_daily_tracker=_get_env("AIRTABLE_BASE_ID_DAILY_TRACKER"),
        airtable_table_id_daily_tracker=_get_env("AIRTABLE_TABLE_ID_DAILY_TRACKER"),
        airtable_base_id_users_count=_get_env("AIRTABLE_BASE_ID_USERS_COUNT"),
        airtable_table_id_users_count=_get_env("AIRTABLE_TABLE_ID_USERS_COUNT"),
    )
