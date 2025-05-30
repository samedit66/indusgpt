from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject

from src.persistence.models import (
    SuperGroup,
    TopicGroup,
    Manager,
    UserManager,
)


router = Router()


@router.message(Command("attach"), F.chat.type == "supergroup")
async def attach(message: types.Message) -> None:
    """
    Set the default supergroup for this bot if not already configured, or inform that it is set.
    Command `/attach` needs to be called in the General chat to attach the bot to the supergroup.
    """
    group = await SuperGroup.filter(group_id=message.chat.id).first()
    if group is None:
        group = await SuperGroup.create(group_id=message.chat.id)
        reply = f"Default supergroup set to {group.group_id}"
    else:
        reply = f"Supergroup already set: {group.group_id}"

    await message.reply(reply)


@router.message(Command("detach"), F.chat.type == "supergroup")
async def detach(message: types.Message) -> None:
    """
    Unset default supergroup for this bot.
    Command `/detach` should be called in case you want to stop using bot for this supergroup.
    """
    group = await SuperGroup.filter(group_id=message.chat.id).first()
    if group is None:
        reply = "Default supergroup is not set"
    else:
        await group.delete()
        reply = f"Supergroup ({group.group_id}) unset"

    await message.reply(reply)


@router.message(
    Command("set_manager"),
    F.chat.type == "supergroup",
    F.message_thread_id.is_(None),
)
async def set_default_manager(message: types.Message, command: CommandObject) -> None:
    """
    Set the default manager for every new user.
    Command `/set_manager` needs to be called in the General chat to set the default manager.
    Usage: /set_manager @manager
    """
    args = command.args
    if not args or not args.strip().startswith("@"):
        await message.reply("Usage: /set_manager @manager")
        return

    manager_link = args.strip()
    manager = await Manager.first()
    if manager:
        manager.manager_link = manager_link
        await manager.save()
        reply = f"Default manager updated to {manager_link}"
    else:
        await Manager.create(manager_link=manager_link)
        reply = f"Default manager set to {manager_link}"
    await message.reply(reply)


@router.message(
    Command("set_manager"),
    F.chat.type == "supergroup",
    F.text.is_not(None),
    F.message_thread_id.is_not(None),
)
async def set_manager_for_user(message: types.Message, command: CommandObject) -> None:
    """
    Set the manager for a specific user.
    Command `/set_manager` needs to be called in the topic chat to set the manager for the user.
    Usage: /set_manager @manager
    """
    args = command.args
    if not args or not args.strip().startswith("@"):
        await message.reply("Usage: /set_manager @manager")
        return

    topic = await TopicGroup.filter(topic_group_id=message.message_thread_id).first()
    user_id = topic.user_id
    user_manager = await UserManager.filter(user_id=user_id).first()
    manager_link = args.strip()
    if user_manager:
        user_manager.manager_link = manager_link
        await user_manager.save()
        reply = f"Manager for this user updated to {manager_link}"
    else:
        await UserManager.create(user_id=user_id, manager_link=manager_link)
        reply = f"Manager for this user set to {manager_link}"
    await message.reply(reply)


@router.message(
    F.chat.type == "supergroup",
    F.text.is_not(None),
    F.message_thread_id.is_not(None),
)
async def handle_message_from_topic(message: types.Message) -> None:
    topic = await TopicGroup.filter(topic_group_id=message.message_thread_id).first()
    if topic is None:
        return

    await message.bot.copy_message(
        chat_id=topic.user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
