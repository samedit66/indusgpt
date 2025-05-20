import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ContentType

# from src.ai import ChatManager, UserInformation
from src.ai.chat_manager import ChatManager
from src.ai.question_list import Question
from src.ai.in_memory import InMemoryQuestionList, InMemoryUserAnswerStorage
from src.utils.db import Database
from src.utils.config import load_config


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
questions = [
    Question(
        text="Do you have corporate (business) accounts? In which banks?",
        answer_requirement=(
            "User response **must** confirm that they have a corporate/business bank account "
            "and say the bank name.\nExamples:\n"
            "- Yes corporate account in ICICI\n"
            "- Yes "
            "- I have a corporate account in Sber bank.\n"
            "- I got a business account in Bank of Baroda."
        ),
    ),
    Question(
        text="Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?",
        answer_requirement=(
            "User response **must** include the name of the **PSP** to which their corporate account "
            "is connected.\nExamples:\n"
            "- Yes my account is connected to Razorpay.\n"
            "- Yes it is PayU.\n"
            "- My PSP is Gatepay.\n"
            "- I have a Razorpay\n"
            "- Razorpay.\n"
        ),
    ),
    Question(
        text="Can you provide login and password access to the PSP account?",
        answer_requirement=(
            "User response **must** clearly answer “yes” or “no” and, if yes, indicate readiness to "
            "**share login credentials**.\nCollect any additional information user may provide about their PSP account.\n"
            "Examples:\n"
            "- Yes, my login is admin, password is 123341."
        ),
    ),
    Question(
        text=(
            "Do you already have a website approved by the PSP?\n"
            "If yes — please give us hosting access (we may need to adjust code or API)\n"
            "If not — we will create the website ourselves"
        ),
        answer_requirement=(
            "User response **must** answer “yes” or “no.” If “yes,” they **must** mention they can "
            'provide **hosting access**. If "no", only "no" is required.\nExamples:\n'
            "- No.\n"
            "- Yes. Next goes any details about hosting access."
        ),
    ),
    Question(
        text="Are you open to working under a profit-sharing model (5% of transaction volume) instead of a one-time deal?",
        answer_requirement=(
            'User response **must** clearly say "yes" or "no".\nExamples:\n'
            "- Yes.\n"
            "- No.\n"
            "- Of course\n"
            "- Sure."
        ),
    ),
]
quesiton_list = InMemoryQuestionList(questions)
user_answer_storage = InMemoryUserAnswerStorage()
chat_manager = ChatManager(
    question_list=quesiton_list,
    user_answer_storage=user_answer_storage,
    on_all_finished=[lambda user_id, qa_pairs: print(user_id, "\n", qa_pairs)],
)


@dp.message(Command("attach"), F.chat.type == "supergroup")
async def attach(message: types.Message) -> None:
    """
    Set the default supergroup for this bot if not already configured, or inform that it is set.
    Command `/attach` needs to be called in the General chat to attach the bot to the supergroup.
    """
    group_id = await get_super_group_id()
    if group_id is None:
        group_id = message.chat.id
        await set_super_group_id(group_id)
        reply = f"Default supergroup set to {group_id}"
    else:
        reply = f"Supergroup already set: {group_id}"

    await message.reply(reply)


@dp.message(Command("detach"), F.chat.type == "supergroup")
async def detach(message: types.Message) -> None:
    """
    Unset default supergroup for this bot.
    Command `/detach` should be called in case you want to stop using bot for this supergroup.
    """
    group_id = await get_super_group_id()
    if group_id is None:
        reply = "Default supergroup is not set"
    else:
        await set_super_group_id(None)
        reply = f"Supergroup ({group_id}) unset"

    await message.reply(reply)


@db.connect()
async def get_super_group_id(db) -> int | None:
    async with db.execute("SELECT group_id FROM super_groups") as cursor:
        row = await cursor.fetchone()

    if row:
        return row["group_id"]

    return None


@db.connect()
async def set_super_group_id(db, group_id: int | None) -> None:
    if group_id is None:
        await db.execute("DELETE FROM super_groups;")
        return

    await db.execute("INSERT INTO super_groups (group_id) VALUES (?)", [group_id])


@dp.message(F.content_type == ContentType.VOICE, F.chat.type == "private")
async def voice_message(message: types.Message):
    await message.answer(
        "Bro, please write the lyrics, I can't listen to it right now. "
    )


@dp.message(F.content_type != ContentType.TEXT, F.chat.type == "private")
async def not_text_message(message: types.Message):
    await message.answer("Bro, please write the lyrics")


@dp.message(F.chat.type == "private")
async def handle_private_message(message: types.Message) -> None:
    group_id = await get_super_group_id()
    if group_id is None:
        await message.reply(
            "No supergroup selected. Use /attach in a supergroup first."
        )
        return

    user_id = message.from_user.id
    user_input = message.text
    user_name = message.from_user.full_name
    topic_group_id = await create_or_get_user_topic(user_id, user_name)

    await bot.forward_message(
        chat_id=group_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        message_thread_id=topic_group_id,
    )
    logger.info(f"Forwarded user={user_id} to topic={topic_group_id}")
    await log_message(message.chat.id, user_id, message.text)

    if await is_complete_user(user_id):
        logger.info("User %s has already completed interaction. Ignoring.", user_id)
        return

    bot_reply = await chat_manager.reply(user_id, user_input)
    bot_message = await message.answer(bot_reply)
    await log_message(message.chat.id, None, bot_reply)
    await bot.copy_message(
        chat_id=group_id,
        from_chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        message_thread_id=topic_group_id,
    )

    # if not chat_manager.is_talking_with(user_id):
    #    await complete_user(user_id)
    #    user_info = await get_user_info(user_id)
    #    if user_info:
    #        formatted_info = format_user_info(user_info)
    #        await bot.send_message(
    #            chat_id=group_id,
    #            message_thread_id=topic_group_id,
    #            text=formatted_info,
    #        )
    #        logger.info("Conversation completed for user_id=%s", user_id)
    #    else:
    #        logger.warning(
    #            "Somehow user %s has not provided any information... That should not happen",
    #            user_id,
    #        )


@db.connect()
async def create_or_get_user_topic(db, user_id: int, user_name: str) -> int:
    async with db.execute(
        "SELECT topic_group_id FROM topic_groups WHERE user_id = ?;", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if row:
        logger.info(f"Found existing topic {row['topic_group_id']} for user {user_id}")
        return row["topic_group_id"]

    group_id = await get_super_group_id()
    topic = await bot.create_forum_topic(
        chat_id=group_id,
        name=make_topic_group_name(user_name),
    )
    thread_id = topic.message_thread_id
    await db.execute(
        "INSERT INTO topic_groups (user_id, topic_group_id) VALUES (?, ?);",
        (user_id, thread_id),
    )

    logger.info(f"Created new topic {thread_id} for user {user_id}")
    return thread_id


def make_topic_group_name(user_name: str) -> str:
    """Exists in a case if `user_name` will need to be, for example, highlighted."""
    return user_name


# @db.connect()
# async def get_user_info(db, user_id: int) -> UserInformation | None:
#    """Get user information from the database."""
#    async with db.execute(
#        "SELECT info_json FROM extracted_info WHERE user_id = ?;", (user_id,)
#    ) as cursor:
#        row = await cursor.fetchone()
#
#    if row:
#        return UserInformation.model_validate_json(row["info_json"])
#
#    return None


# def format_user_info(user: UserInformation) -> str:
#    """
#    Makes up a human-readable string from the user information.
#    """
#    lines = []
#
#    if user.accounts:
#        lines.append("Корпоративные банковские счета:")
#        for i, account in enumerate(user.accounts, 1):
#            lines.append(f"  {i}. Банк: {account.bank_name}")
#    else:
#        lines.append("Корпоративных банковских счетов не указано.")
#
#    if user.psps:
#        lines.append("\nПодключенные PSP:")
#        for i, psp in enumerate(user.psps, 1):
#            lines.append(f"  {i}. PSP: {psp.psp_name}")
#            lines.append(f"     Логин: {psp.login}")
#            lines.append(f"     Пароль: {psp.password}")
#            if psp.details:
#                lines.append(f"     Дополнительно: {psp.details}")
#    else:
#        lines.append("\nPSP аккаунты не указаны.")
#
#    lines.append("\nИнформация по хостингу:")
#    if user.hosting.has_website:
#        lines.append("  Пользователь имеет одобренный веб-сайт с PSP.")
#        if user.hosting.access_details:
#            lines.append(f"  Данные доступа: {user.hosting.access_details}")
#        else:
#            lines.append("  Данные доступа не предоставлены.")
#    else:
#        lines.append("  У пользователя нет одобренного веб-сайта с PSP.")
#
#    lines.append("\nДоговор о распределении прибыли:")
#    if user.profit_sharing.agreement.lower() == "yes":
#        lines.append(
#            "  Пользователь согласен на модель распределения прибыли вместо разовой оплаты."
#        )
#    else:
#        lines.append(f"  Статус соглашения: {user.profit_sharing.agreement}")
#
#    return "\n".join(lines)


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


# @chat_manager.on_info_ready()
# @db.connect()
# async def save_information(db, user_id, info: UserInformation) -> None:
#    await db.execute(
#        """
#        INSERT OR REPLACE INTO extracted_info (user_id, info_json)
#        VALUES (?, ?)
#        """,
#        (user_id, info.model_dump_json()),
#    )
#    logger.info("Saved information about user=%s", user_id)


@db.before()
async def init_db(db) -> None:
    logger.info("Initializing database with foreign keys and tables.")

    await db.executescript("""
        PRAGMA foreign_keys = ON;
                               
        CREATE TABLE IF NOT EXISTS complete_users (
                user_id INTEGER PRIMARY KEY
        );
                               
        CREATE TABLE IF NOT EXISTS conversation_history (
            chat_id    INTEGER     NOT NULL,
            user_id    INTEGER     NULL,
            message    TEXT        NOT NULL,
            created_at TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ','NOW'))
        );
                               
        CREATE TABLE IF NOT EXISTS extracted_info (
            user_id   INTEGER PRIMARY KEY,
            info_json TEXT        NOT NULL
        );
                               
        CREATE TABLE IF NOT EXISTS topic_groups (
            user_id        INTEGER NOT NULL,
            topic_group_id INTEGER NOT NULL
        );
                               
        CREATE TABLE IF NOT EXISTS super_groups (
            group_id INTEGER NOT NULL
        );
                               
        CREATE INDEX IF NOT EXISTS idx_history_chat ON conversation_history(chat_id);
        CREATE INDEX IF NOT EXISTS idx_history_user ON conversation_history(user_id);                    
    """)


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


async def main():
    logger.info("Application start.")
    await bot.set_my_description("Hi! Greet me or just write /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
