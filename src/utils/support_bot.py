from pathlib import Path

from pyrogram import Client

from .db import Database


class SupportBot(Client):
    def __init__(self, db_path: str | Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db = Database(db_path)
