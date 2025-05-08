import logging
from collections import defaultdict
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from src.dialog_agent import DialogAgent, Answer

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Please set TELEGRAM_API_TOKEN")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
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
    ready_for_next_question BOOLEAN,
    extracted_data TEXT,
    timestamp TEXT
)
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


async def log_interaction(
    msg: Message, answer: Answer, question: str, conn: sqlite3.Connection
):
    ts = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO messages
          (user_id, user_name, user_message, bot_response, ready_for_next_question, extracted_data, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            msg.from_user.id,
            msg.from_user.username or "",
            msg.text,
            answer.answer,
            answer.ready_for_next_question,
            answer.extracted_data,
            ts,
        ),
    )
    conn.commit()
    logger.info(f"Logged interaction for {msg.from_user.id}: question={question}")


# Define questionnaire
questions_and_rules = [
    {
        "question": "Do you have corporate (business) accounts? In which banks?",
        "val_rule": """
User response **must** confirm that they have a corporate/business bank account and say the bank name.
Examples:
- I have a corporate account in Sber bank.
- I got a business account in Bank of Baroda.
""",
    },
    {
        "question": "Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?",
        "val_rule": """
User response **must** include the name of the **PSP** to which their corporate account is connected.
Examples:
- Yes my account is connected to Razorpay.
- Yes it is PayU.
- My PSP is Gatepay.
""",
    },
    {
        "question": "Can you provide login and password access to the PSP account?",
        "val_rule": """
User response **must** clearly answer “yes” or “no” and, if yes, indicate readiness to **share login credentials**.
Collect any additional information user may provide about their PSP account.
Examples:
- Yes, my login is admin, password is 123341.
""",
    },
    {
        "question": (
            "Do you already have a website approved by the PSP?\n"
            "If yes — please give us hosting access (we may need to adjust code or API)\n"
            "If not — we will create the website ourselves"
        ),
        "val_rule": """
User response **must** answer “yes” or “no.” If “yes,” they **must** mention they can provide **hosting access**. If "no", only "no" is required.
Examples:
- No.
- Yes. Next goes any details about hosting access.
""",
    },
    {
        "question": "Are you open to working under a profit‑sharing model (5% of transaction volume) instead of a one‑time deal?",
        "val_rule": """
User response **must** clearly say "yes" or "no".
Examples:
- Yes.
- No.
- Of course.
- Sure.
""",
    },
]


# Create FSM states
class Questionnaire(StatesGroup):
    q0 = State()
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()


agent = DialogAgent(model_name=os.environ["MODEL"])
info = defaultdict(list)


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    intro = (
        "Hi there! 🙏\n\n"
        "We work with high-volume traffic and process over ₹12,000,000 daily. "
        "We're looking to buy or rent corporate accounts in India connected to a PSP.\n\n"
        "Let's get started. Please answer the following questions one by one."
    )
    await message.answer(intro)

    # Move to first state and ask Q0
    await state.set_state(Questionnaire.q0)
    await message.answer(questions_and_rules[0]["question"])


@dp.message(F.text)
async def handle_answers(message: Message, state: FSMContext):
    current = await state.get_state()  # e.g. "Questionnaire:q0"
    if not current:
        # Not in our flow—ignore or prompt
        return

    # Map state strings to their index
    mapping = {
        Questionnaire.q0: 0,
        Questionnaire.q1: 1,
        Questionnaire.q2: 2,
        Questionnaire.q3: 3,
        Questionnaire.q4: 4,
    }
    idx = mapping.get(current)
    if idx is None:
        return

    q = questions_and_rules[idx]
    answer: Answer = agent.reply(
        user_input=message.text,
        question=q["question"],
        val_rule=q["val_rule"],
    )

    # Reply & log
    await message.reply(answer.text)
    await log_interaction(message, answer, q["question"], dp["db_conn"])

    # Advance or finish
    if idx + 1 < len(questions_and_rules):
        if answer.ready_for_next_question:
            info[message.from_user.id].append(answer.extracted_data)
            next_state = getattr(Questionnaire, f"q{idx + 1}")
            await state.set_state(next_state)
            await message.answer(questions_and_rules[idx + 1]["question"])
    else:
        await message.answer("Thank you! We have collected all the info.")
        await message.answer("\n".join(info[message.from_user.id]))
        await state.clear()


async def on_startup():
    dp["db_conn"] = init_db()
    logger.info("Database initialized.")


async def on_shutdown():
    dp["db_conn"].close()
    logger.info("Database connection closed.")


if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.run_polling(bot, skip_updates=True)
