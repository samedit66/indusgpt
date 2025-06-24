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

    airtable_processor = processors.AirtableProcessor(
        access_token=config.airtable_access_token,
        base_id=config.airtable_base_id,
        table_id=config.airtable_table_id,
    )
    airtable_daily_tracker = middlewares.airtable.AirtableDailyTracker(
        access_token=config.airtable_access_token,
        base_id=config.airtable_base_id_daily_tracker,
        table_id=config.airtable_table_id_daily_tracker,
    )
    airtable_users_counter = middlewares.airtable.AirtableUsersCounter(
        access_token=config.airtable_access_token,
        base_id=config.airtable_base_id_users_count,
        table_id=config.airtable_table_id_users_count,
    )

    chat_manager = chat.ChatManager(
        question_list=persistence.TortoiseQuestionList(chat_settings.QUESTIONS),
        user_answer_storage=persistence.TortoiseUserAnswerStorage(),
        context=persistence.TortoiseContext(),
        generate_response=chat.generate_response,
        generate_reply=chat.generate_reply,
        on_all_finished=[
            airtable_processor,
        ],
    )

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    allowed_ids = [1457394519]
    dp.message.middleware(middlewares.AllowedIdsMiddleware(allowed_ids))
    dp.message.middleware(middlewares.ChatManagerMiddleware(chat_manager))
    dp.message.middleware(middlewares.AirtableMiddleware(airtable_processor))
    dp.message.middleware(
        middlewares.AirtableDailyTrackerMiddleware(airtable_daily_tracker)
    )
    dp.message.middleware(
        middlewares.AirtableUsersCounterMiddleware(airtable_users_counter)
    )
    dp.include_routers(supergroup.router, chat_flow.router)

    db_url = f"sqlite://{pathlib.Path(config.data_dir) / config.db_file}"
    await tortoise_config.init_db(db_url, ["src.persistence.models"])

    await bot.set_my_description("Hi! To start the conversation, use /start command.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
