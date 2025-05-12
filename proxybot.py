import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ContentType

from src.ai import ChatManager, UserInformation
from src.utils.db import Database
from src.utils.config import load_config


supergroup_id: int | None = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

config = load_config()
bot = Bot(token=config.bot_token)
dp = Dispatcher()
db = Database(config.db_path)
chat_manager = ChatManager(
    model_name=config.model_name,
    api_key=config.openai_api_key,
    base_url=config.openai_base_url,
)


@dp.message(Command("setdefault"), F.chat.type == "supergroup")
async def set_default(message: types.Message) -> None:
    global supergroup_id
    if supergroup_id is None:
        supergroup_id = message.chat.id
        await message.reply(f"Default supergroup set to {supergroup_id}")
    else:
        await message.reply(f"Supergroup already set: {supergroup_id}")


@dp.message(F.content_type != ContentType.TEXT, F.chat.type == "private")
async def not_text(message: types.Message):
    await message.reply("Please write lyrics, bro")


@dp.message(F.chat.type == "private")
async def handle_private_message(message: types.Message) -> None:
    global supergroup_id
    if supergroup_id is None:
        await message.reply(
            "No supergroup selected. Use /setdefault in a supergroup first."
        )
        return

    user_id = message.from_user.id
    user_input = message.text
    # TODO: логгирование сообщение пользователя
    user_name = message.from_user.full_name
    topic_group_id = await create_or_get_user_topic(user_id, user_name)

    await bot.forward_message(
        chat_id=supergroup_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        message_thread_id=topic_group_id,
    )
    logger.info(f"Forwarded user={user_id} to topic={topic_group_id}")

    if await is_complete_user(user_id):
        logger.info("User %s has already completed interaction. Ignoring.", user_id)
        return

    bot_reply = await chat_manager.reply(user_id, user_input)
    bot_message = await message.answer(bot_reply)
    await bot.copy_message(
        chat_id=supergroup_id,
        from_chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        message_thread_id=topic_group_id,
    )

    if not chat_manager.is_talking_with(user_id):
        await complete_user(user_id)
        logger.info("Conversation completed for user_id=%s", user_id)


@db.connect()
async def create_or_get_user_topic(db, user_id: int, user_name: str) -> int:
    async with db.execute(
        "SELECT topic_group_id FROM topic_groups WHERE user_id = ?;", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if row:
        logger.info(f"Found existing topic {row['topic_group_id']} for user {user_id}")
        return row["topic_group_id"]

    topic = await bot.create_forum_topic(
        chat_id=supergroup_id,
        name=user_name,
    )
    thread_id = topic.message_thread_id
    await db.execute(
        "INSERT INTO topic_groups (user_id, topic_group_id) VALUES (?, ?);",
        (user_id, thread_id),
    )

    logger.info(f"Created new topic {thread_id} for user {user_id}")
    return thread_id


@dp.message(
    F.chat.type == "supergroup",
    lambda message: message.text is not None,
    lambda msg: msg.message_thread_id is not None,
)
async def handle_topic_reply(message: types.Message) -> None:
    """
    Catch replies in forum threads and forward back to the original private user.
    """
    topic_group_id = message.message_thread_id
    user_id = await get_user_id_by_topic_id(topic_group_id)

    if user_id is None:
        return

    await bot.copy_message(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )


@db.connect()
async def get_user_id_by_topic_id(db, topic_group_id: int) -> int:
    async with db.execute(
        "SELECT user_id FROM topic_groups WHERE topic_group_id = ?;", (topic_group_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if row:
        return row["user_id"]

    return None


@chat_manager.on_info_ready()
@db.connect()
async def save_information(db, user_id, info: UserInformation) -> None:
    await db.execute(
        """
        INSERT OR REPLACE INTO extracted_info (user_id, info_json)
        VALUES (?, ?)
        """,
        (user_id, info.model_dump_json()),
    )
    logger.info("Saved information about user=%s", user_id)


@db.before()
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

    await db.execute("""
        CREATE TABLE IF NOT EXISTS topic_groups (
            user_id        INTEGER NOT NULL,
            topic_group_id INTEGER NOT NULL
        );
    """)

    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_chat ON conversation_history(chat_id);"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_user ON conversation_history(user_id);"
    )


@db.connect()
async def is_complete_user(db, user_id: int) -> bool:
    """Return True if `user_id` is already in the complete_users table."""
    async with db.execute(
        "SELECT 1 FROM complete_users WHERE user_id = ?;", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
    result = row is not None
    logger.debug("is_complete_user(%s) -> %s", user_id, result)
    return result


@db.connect()
async def complete_user(db, user_id: int) -> None:
    """Insert a user into complete_users (ignore if exists)."""
    await db.execute(
        "INSERT OR IGNORE INTO complete_users (user_id) VALUES (?);", (user_id,)
    )
    logger.debug("complete_user inserted or ignored for user_id=%s", user_id)


@db.connect()
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


@db.connect()
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
    logger.info("Application start.")
    dp.run_polling(bot)
