from aiogram import Router, F, types
from aiogram.filters import Command

from src.persistence.models import SuperGroup


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
