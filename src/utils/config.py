import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    openai_api_key: str
    openai_base_url: str
    model_name: str
    bot_token: str
    db_path: str
    log_file: str


def load_config() -> Config:
    load_dotenv()

    return Config(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        openai_base_url=os.environ["OPENAI_API_BASE_URL"],
        model_name=os.environ["MODEL"],
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        db_path=os.environ["DATABASE"],
        log_file=os.environ["LOG_FILE"],
    )
