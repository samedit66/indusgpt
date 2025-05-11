import logging

from pyrogram import filters
from pyrogram.types import Message

from src.ai import ChatManager, UserInformation
from src.utils.support_bot import SupportBot
from src.utils.config import load_config


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

config = load_config()

app = SupportBot(
    db_path=config.db_path,
    name=config.session_name,
    api_id=config.api_id,
    api_hash=config.api_hash,
)
chat_manager = ChatManager(
    model_name=config.model_name,
    api_key=config.openai_api_key,
    base_url=config.openai_base_url,
)


@chat_manager.on_info_ready()
@app.db.connect()
async def save_information(db, user_id, info: UserInformation) -> None:
    await db.execute(
        """
        INSERT OR REPLACE INTO extracted_info (user_id, info_json)
        VALUES (?, ?)
        """,
        (user_id, info.model_dump_json()),
    )
    logger.info("Saved information about user=%s", user_id)


@app.on_message(filters.text)
async def talk(client, message: Message) -> None:
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_input = message.text

    logger.info(
        "Received message from user_id=%s in chat_id=%s: %s",
        user_id,
        chat_id,
        user_input,
    )

    if await is_complete_user(user_id):
        logger.debug("User %s has already completed interaction. Ignoring.", user_id)
        return

    await log_message(chat_id, user_id, user_input)

    bot_reply = await chat_manager.reply(user_id, user_input)
    logger.info("Replying to user_id=%s: %s", user_id, bot_reply)
    await message.reply(bot_reply)
    await log_message(chat_id, None, bot_reply)

    if not chat_manager.is_talking_with(user_id):
        await complete_user(user_id)
        logger.info("Conversation completed for user_id=%s", user_id)


@app.on_message(~filters.text)
async def not_text(client, message: Message):
    logger.warning(
        "Non-text message received in chat_id=%s. Message: %s", message.chat.id, message
    )
    await message.reply("That's not a text message bro")


@app.db.before()
async def init_db(db) -> None:
    logger.info("Initializing database with foreign keys and tables.")
    await db.execute("PRAGMA foreign_keys = ON;")

    await db.execute("""
        CREATE TABLE IF NOT EXISTS complete_users (
            user_id INTEGER PRIMARY KEY
        );
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            chat_id    INTEGER     NOT NULL,
            user_id    INTEGER     NULL,
            message    TEXT        NOT NULL,
            created_at TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ','NOW'))
        );
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS extracted_info (
            user_id   INTEGER PRIMARY KEY,
            info_json TEXT        NOT NULL
        );
    """)

    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_chat ON conversation_history(chat_id);"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_user ON conversation_history(user_id);"
    )


@app.db.connect()
async def is_complete_user(db, user_id: int) -> bool:
    """Return True if `user_id` is already in the complete_users table."""
    async with db.execute(
        "SELECT 1 FROM complete_users WHERE user_id = ?;", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
    result = row is not None
    logger.debug("is_complete_user(%s) -> %s", user_id, result)
    return result


@app.db.connect()
async def complete_user(db, user_id: int) -> None:
    """Insert a user into complete_users (ignore if exists)."""
    await db.execute(
        "INSERT OR IGNORE INTO complete_users (user_id) VALUES (?);", (user_id,)
    )
    logger.debug("complete_user inserted or ignored for user_id=%s", user_id)


@app.db.connect()
async def log_message(db, chat_id: int, user_id: int | None, message: str) -> None:
    """Log a message into conversation_history."""
    await db.execute(
        """
        INSERT INTO conversation_history (chat_id, user_id, message)
        VALUES (?, ?, ?);
        """,
        (chat_id, user_id, message),
    )
    logger.debug("Logged message for chat_id=%s, user_id=%s", chat_id, user_id)


@app.db.connect()
async def upsert_info(db, user_id: int, info: UserInformation) -> None:
    """Insert or update extracted_info for a user."""
    json_blob = info.model_json_schema()
    await db.execute(
        """
        INSERT INTO extracted_info (user_id, info_json)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET info_json=excluded.info_json;
        """,
        (user_id, json_blob),
    )
    logger.debug("Upserted extracted_info for user_id=%s", user_id)


if __name__ == "__main__":
    logger.info("Starting SupportBot application.")
    app.run()
