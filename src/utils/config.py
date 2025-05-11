import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    openai_api_key: str
    openai_base_url: str
    model_name: str
    session_name: str
    api_id: int
    api_hash: str
    bot_token: str
    db_path: str


def load_config() -> Config:
    load_dotenv()

    return Config(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        openai_base_url=os.environ["OPENAI_API_BASE_URL"],
        model_name=os.environ["MODEL"],
        session_name=os.environ["SESSION_NAME"],
        api_id=int(os.environ["TELEGRAM_API_ID"]),
        api_hash=os.environ["TELEGRAM_API_HASH"],
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        db_path=os.environ["DATABASE"],
    )
