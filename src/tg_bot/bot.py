import logging

from aiogram import Bot, Dispatcher

from src.persistence import init_db
from src.utils.config import load_config

from src.tg_bot.handlers import supergroup, chat_flow


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

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp.include_routers(supergroup.router, chat_flow.router)

    await init_db("sqlite://db.sqlite3", ["src.persistence.models"])

    await bot.set_description("Hi! To start the conversation, use /start command.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
