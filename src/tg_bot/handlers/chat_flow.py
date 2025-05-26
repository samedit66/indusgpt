import logging

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ContentType

from src.persistence.models import SuperGroup, TopicGroup, User
from src.tg_bot import chat

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_chat(message: types.Message) -> None:
    user_id = message.from_user.id
    if not await chat.has_user_started(user_id):
        user, _ = await User.get_or_create(
            id=user_id, defaults={"name": message.from_user.full_name}
        )
        await message.answer(await chat.current_question(user_id))
        return

    await handle_private_message(message)


@router.message(F.content_type == ContentType.VOICE, F.chat.type == "private")
async def voice_message(message: types.Message):
    supergroup = await SuperGroup.filter().first()
    if supergroup is None:
        logger.warning(
            "No supergroup selected. Use /attach in a supergroup first. "
            f"Request from user {message.from_user.full_name} (id: {message.from_user.id})"
        )
        return

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user, _ = await User.get_or_create(id=user_id, defaults={"name": user_name})

    if not await TopicGroup.filter(user=user).exists():
        topic = await message.bot.create_forum_topic(
            chat_id=supergroup.group_id,
            name=user_name,
        )
        thread_id = topic.message_thread_id
        await TopicGroup.create(user=user, topic_group_id=thread_id)
    else:
        topic = await TopicGroup.filter(user=user).first()
        thread_id = topic.topic_group_id
    await message.forward(chat_id=supergroup.group_id, message_thread_id=thread_id)

    if not await chat.is_user_talking(message.from_user.id):
        return

    await message.answer(
        "Bro, please write the lyrics, I can't listen to it right now."
    )


@router.message(F.content_type != ContentType.TEXT, F.chat.type == "private")
async def not_text_message(message: types.Message):
    supergroup = await SuperGroup.filter().first()
    if supergroup is None:
        logger.warning(
            "No supergroup selected. Use /attach in a supergroup first. "
            f"Request from user {message.from_user.full_name} (id: {message.from_user.id})"
        )
        return

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user, _ = await User.get_or_create(id=user_id, defaults={"name": user_name})

    if not await TopicGroup.filter(user=user).exists():
        topic = await message.bot.create_forum_topic(
            chat_id=supergroup.group_id,
            name=user_name,
        )
        thread_id = topic.message_thread_id
        await TopicGroup.create(user=user, topic_group_id=thread_id)
    else:
        topic = await TopicGroup.filter(user=user).first()
        thread_id = topic.topic_group_id
    await message.forward(chat_id=supergroup.group_id, message_thread_id=thread_id)

    if not await chat.is_user_talking(message.from_user.id):
        return

    await message.answer("Bro, please write the lyrics")


@router.message(F.chat.type == "private")
async def handle_private_message(message: types.Message) -> None:
    if await chat.has_user_finished(message.from_user.id):
        return

    user_id = message.from_user.id
    user_input = message.text
    user_name = message.from_user.full_name

    supergroup = await SuperGroup.filter().first()
    if supergroup is None:
        logger.warning(
            "No supergroup selected. Use /attach in a supergroup first. "
            f"Request from user {user_name} (id: {user_id})"
        )
        return

    user, _ = await User.get_or_create(id=user_id, defaults={"name": user_name})

    if not await TopicGroup.filter(user=user).exists():
        topic = await message.bot.create_forum_topic(
            chat_id=supergroup.group_id,
            name=user_name,
        )
        thread_id = topic.message_thread_id
        await TopicGroup.create(user=user, topic_group_id=thread_id)
    else:
        topic = await TopicGroup.filter(user=user).first()
        thread_id = topic.topic_group_id

    await message.forward(chat_id=supergroup.group_id, message_thread_id=thread_id)
    logger.info(f"Forwarded user={user_name} (id: {user_id}) to topic={thread_id}")

    bot_reply = await chat.reply(user_id, user_input)
    bot_message = await message.answer(bot_reply)
    await bot_message.send_copy(
        chat_id=supergroup.group_id, message_thread_id=thread_id
    )


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
