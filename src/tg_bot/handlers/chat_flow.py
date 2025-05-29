import logging

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ContentType

from src import chat
from src.tg_bot import middlewares
from src.tg_bot import chat_settings

router = Router()
router.message.middleware(middlewares.ExpectSuperGroupSetMiddleware())
router.message.middleware(middlewares.CreateUserAndTopicGroupMiddleware())
router.message.middleware(middlewares.FinishedUsersMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("start"), F.chat.type == "private")
async def start(message: types.Message, chat_manager: chat.ChatManager) -> None:
    await message.answer(chat_settings.INTRODUCTION)
    await message.answer(await chat_manager.current_question(message.from_user.id))


@router.message(F.content_type == ContentType.VOICE, F.chat.type == "private")
async def voice_message(message: types.Message):
    await message.answer(
        "Bro, please write the lyrics, I can't listen to it right now."
    )


@router.message(F.content_type != ContentType.TEXT, F.chat.type == "private")
async def not_text_message(message: types.Message):
    await message.answer("Bro, please write the lyrics")


@router.message(F.chat.type == "private")
async def handle_message_from_user(
    message: types.Message,
    supergroup_id: int,
    topic_group_id: int,
    chat_manager: chat.ChatManager,
) -> None:
    # Генерируем ответ для пользователя
    reply = await chat_manager.reply(message.from_user.id, message.text)
    bot_message = await message.answer(reply)

    # Копируем ответ бота в топик-группу
    await bot_message.send_copy(
        chat_id=supergroup_id,
        message_thread_id=topic_group_id,
    )
