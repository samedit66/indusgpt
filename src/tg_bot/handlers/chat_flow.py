import logging

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ContentType

from src.persistence.models import TopicGroup
from src.tg_bot import chat
from src.tg_bot import middlewares

router = Router()
router.message.middleware(middlewares.ExpectSuperGroupSetMiddleware())
router.message.middleware(middlewares.FinishedUsersMiddleware())
router.message.middleware(middlewares.CreateUserAndTopicGroupMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("start"), F.chat.type == "private")
async def start(message: types.Message) -> None:
    # В самый первый раз, когда пользователь введет /start,
    # ему отправится вся информация (`chat.INTRODUCTION`) и первый вопрос.
    # Во всех остальные разы, когда пользователь введет /start,
    # ему отправится только текущий вопрос
    await message.answer(await chat.current_question(message.from_user.id))


@router.message(F.content_type == ContentType.VOICE, F.chat.type == "private")
async def voice_message(message: types.Message):
    await message.answer(
        "Bro, please write the lyrics, I can't listen to it right now."
    )


@router.message(F.content_type != ContentType.TEXT, F.chat.type == "private")
async def not_text_message(message: types.Message):
    await message.answer("Bro, please write the lyrics")


@router.message(F.chat.type == "private")
async def handle_private_message(
    message: types.Message,
    supergroup_id: int,
    topic_group_id: int,
) -> None:
    await message.forward(chat_id=supergroup_id, message_thread_id=topic_group_id)
    logger.info(
        f"Forwarded user={message.from_user.full_name} (id: {message.from_user.id}) to topic={topic_group_id}"
    )

    bot_reply = await chat.reply(message.from_user.id, message.text)
    bot_message = await message.answer(bot_reply)
    await bot_message.send_copy(chat_id=supergroup_id, message_thread_id=topic_group_id)


@router.message(
    F.chat.type == "supergroup",
    lambda message: message.text is not None,
    lambda msg: msg.message_thread_id is not None,
)
async def handle_topic_reply(message: types.Message) -> None:
    topic = await TopicGroup.filter(topic_group_id=message.message_thread_id).first()
    if topic is None:
        return

    await message.bot.copy_message(
        chat_id=topic.user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
