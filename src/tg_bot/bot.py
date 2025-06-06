import asyncio
import logging
import pathlib

from aiogram import Bot, Dispatcher

from src import persistence
from src.utils.config import load_config

from src import processors

from src import chat
from src.tg_bot.handlers import supergroup, chat_flow
from src.tg_bot import middlewares
from src.tg_bot import chat_settings
from src.tg_bot import tortoise_config


async def run_bot():
    config = load_config()

    log_file_path = pathlib.Path(config.data_dir) / config.log_file
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    chat_manager = chat.ChatManager(
        question_list=persistence.TortoiseQuestionList(chat_settings.QUESTIONS),
        user_answer_storage=persistence.TortoiseUserAnswerStorage(),
        context=persistence.TortoiseContext(),
        generate_response=chat.generate_response,
        generate_reply=chat.generate_reply,
        on_all_finished=[
            processors.GoogleSheetsProcessor(
                config.google_credentials_path,
                config.google_sheet_url,
                config.google_sheet_worksheet_name,
            ),
        ],
    )

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    allowed_ids = [1457394519]
    dp.message.middleware(middlewares.AllowedIdsMiddleware(allowed_ids))
    dp.message.middleware(middlewares.ChatManagerMiddleware(chat_manager))
    dp.include_routers(supergroup.router, chat_flow.router)

    asyncio.create_task(periodic_flush_task(30))

    db_url = f"sqlite://{pathlib.Path(config.data_dir) / config.db_file}"
    await tortoise_config.init_db(db_url, ["src.persistence.models"])

    await bot.set_my_description("Hi! To start the conversation, use /start command.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def periodic_flush_task(schedule_time: int) -> None:
    await asyncio.sleep(1)

    while True:
        await asyncio.sleep(schedule_time)
        await chat_flow.flush_all_buffers()
