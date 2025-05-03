import logging
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters.command import Command
from dotenv import load_dotenv
load_dotenv()

from src.router.router import classify_user_intent, UserIntent
from src.faq_agent.faq_agent import answer_faq


API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Please set TELEGRAM_API_TOKEN")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Bot & Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Database setup
DB_PATH = "bot_logs.db"
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    user_name TEXT,
    user_message TEXT,
    bot_response TEXT,
    intent_category TEXT,
    intent_reasoning TEXT,
    timestamp TEXT
)
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn

async def log_interaction(msg: Message, intent: UserIntent, response: str, conn: sqlite3.Connection):
    ts = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO messages
          (user_id, user_name, user_message, bot_response, intent_category, intent_reasoning, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            msg.from_user.id,
            msg.from_user.username or "",
            msg.text,
            response,
            intent.category,
            intent.reasoning,
            ts
        )
    )
    conn.commit()
    logger.info(f"Logged message from {msg.from_user.id}: intent={intent.category}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    start_message = """
Hi brother!  
Thanks for reaching out 🙏  

We work with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions. We are looking to buy or rent corporate accounts in India that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.

We are ready for long-term cooperation and offer up to 5% of the profit for stable account performance. For example: ₹500,000 daily volume = ₹25,000 your share (5%).

---

Please answer the following:

1. Do you have corporate accounts? In which banks?  
2. Are they connected to any PSP (Razorpay, Cashfree, PayU, etc.)?  
3. Can you provide login and password access to the PSP account?  
4. Do you already have a website approved by the PSP?  
  → If yes — please give us hosting access (we may need to adjust code or API)  
  → If not — we will create the website ourselves  
5. Are you open to working under a profit-sharing model instead of just a one-time deal?

---

Our Work Process:

1. Access to PSP account  
 – You share the login + password (e.g. Razorpay)  
 – We review dashboard, limits, API access, status

2. Website check  
 – If already available — great, we’ll need hosting access  
 – If not — we’ll create a bridge website (services, education, consulting, etc.)

3. Submit for moderation  
 – We use your account + our site  
 – Fill forms, upload docs, complete verification

4. API integration  
 – Our dev team integrates PSP to our backend  
 – We test deposit flow, webhook, and transaction statuses

5. Start working  
 – Begin with small volumes, check stability  
 – If everything is good — we scale

---

If you’re ready:

- Share PSP login + password  
- Let us know if you already have a website  
 → If yes — provide hosting access  
 → If not — we’ll handle it  
- Confirm if you can provide company documents (GST, PAN, etc.)

Let’s build a strong and profitable partnership 💪

❗️ PLEASE WRITE AND ANSWER ALL THE QUESTIONS! SO THAT OUR COMMUNICATION AND WORK IS PRODUCTIVE. IF YOU ANSWER ALL THE QUESTIONS — I WILL REPLY TO YOU.
"""
    await message.answer(start_message)

# Handlers
@dp.message(F.text)
async def handle_message(message: Message):
    intent = classify_user_intent(message.text)
    response = f"Intent: {intent.category}\nReasoning: {intent.reasoning}\nInput: {intent.user_input}"
    await message.reply(response, parse_mode="HTML")

    # Log once per process
    #await log_interaction(message, intent, response, dp['db_conn'])

async def on_startup():
    # Ensure DB and pass connection in dp storage
    dp['db_conn'] = init_db()
    logger.info("Database initialized.")

async def on_shutdown():
    dp['db_conn'].close()
    logger.info("Database connection closed.")

if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.run_polling(bot, skip_updates=True)
