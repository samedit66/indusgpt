import logging

from aiogram import Bot, Dispatcher

from src import persistence
from src.utils.config import load_config

from src import chat
from src.tg_bot.handlers import supergroup, chat_flow
from src.tg_bot import middlewares
from src.tg_bot import chat_settings


async def run_bot():
    config = load_config()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(config.log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    chat_manager = chat.ChatManager(
        question_list=persistence.TortoiseQuestionList(chat_settings.QUESTIONS),
        user_answer_storage=persistence.TortoiseUserAnswerStorage(),
        generate_response=chat.generate_response,
        generate_reply=chat.generate_reply,
        on_all_finished=[
            chat_settings.write_to_google_sheet,
        ],
    )

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp.message.middleware(middlewares.ChatManagerMiddleware(chat_manager))
    dp.include_routers(supergroup.router, chat_flow.router)

    await persistence.init_db("sqlite://db.sqlite3", ["src.persistence.models"])

    await bot.set_my_description("Hi! To start the conversation, use /start command.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
