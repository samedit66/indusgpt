from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram import enums as aiogram_enums
import os
from datetime import datetime

from src.persistence.models import (
    SuperGroup,
    TopicGroup,
    Manager,
    UserManager,
    User,
)

from src.chat import ChatManager
from src import processors


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
    group = await SuperGroup.first()

    if group is None:
        reply = "Default supergroup is not set"
    else:
        # Delete that one record
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
        await Manager.create(
            manager_link=manager_link,
        )
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
        await UserManager.create(
            user_id=user_id,
            manager_link=manager_link,
        )
        reply = f"Manager for this user set to {manager_link}"
    await message.reply(reply)


@router.message(
    Command("unset_manager"),
    F.chat.type == "supergroup",
    F.message_thread_id.is_(None),
)
async def unset_default_manager(message: types.Message) -> None:
    """
    Unset (remove) the default manager for every new user.
    Command `/unset_manager` needs to be called in the General chat.
    """
    # Try to fetch the single default Manager row
    default_manager = await Manager.first()
    if default_manager:
        await default_manager.delete()
        await message.reply("Default manager has been removed.")
    else:
        await message.reply("No default manager is currently set.")


@router.message(
    Command("unset_manager"),
    F.chat.type == "supergroup",
    F.text.is_not(None),
    F.message_thread_id.is_not(None),
)
async def unset_manager_for_user(message: types.Message) -> None:
    """
    Unset (remove) the manager for the specific user whose topic this is.
    Command `/unset_manager` needs to be called in a topic chat.
    """
    # First, find which user this topic belongs to
    topic = await TopicGroup.filter(topic_group_id=message.message_thread_id).first()
    if not topic:
        await message.reply("Could not identify which user this topic belongs to.")
        return

    # Look for an existing UserManager entry for that user
    user_manager = await UserManager.filter(user_id=topic.user_id).first()
    if user_manager:
        await user_manager.delete()
        await message.reply("Manager assignment for this user has been removed.")
    else:
        await message.reply("No manager is currently set for this user.")


@router.message(
    Command("learn"),
    F.chat.type == "supergroup",
    F.text.is_not(None),
    F.message_thread_id.is_not(None),
)
async def learn(
    message: types.Message,
    command: CommandObject,
    chat_manager: ChatManager,
) -> None:
    """
    Make bot learn new information about how to answer questions.
    Command must include instructions and can optionally reference a message:
    `/learn <instructions>` - learn using provided instructions
    Reply to a message with `/learn <instructions>` - learn using both the instructions and message content
    Must be called in the topic chat.
    """
    if not command.args:
        await message.reply("Instructions are required. Usage: `/learn <instructions>`")
        return

    instructions = command.args

    if message.reply_to_message and message.reply_to_message.text:
        await chat_manager.learn(
            instructions=instructions,
            incorrect_example=message.reply_to_message.text,
        )
    else:
        await chat_manager.learn(instructions=instructions)

    await message.reply("Instructions learned")


@router.message(
    Command("instructions"),
    F.chat.type == "supergroup",
    F.message_thread_id.is_not(None),
)
async def instructions(
    message: types.Message,
    chat_manager: ChatManager,
) -> None:
    """
    Get the instructions of the bot.
    Command `/instructions` - get the instructions of the bot.
    Must be called in the topic chat.
    """
    instructions = await chat_manager.context.get()
    if instructions:
        await message.reply(instructions)
    else:
        await message.reply("No instructions found")


@router.message(
    Command("forget"),
    F.chat.type == "supergroup",
    F.message_thread_id.is_not(None),
)
async def forget(
    message: types.Message,
    chat_manager: ChatManager,
) -> None:
    """
    Forget the instructions of the bot.
    Command `/forget` - forget the instructions of the bot.
    Must be called in the topic chat.
    """
    await chat_manager.context.clear()
    await message.reply("Instructions forgotten")


@router.message(
    Command("unfinished"),
    F.chat.type == "supergroup",
    F.message_thread_id.is_(None),
)
async def unfinished(message: types.Message, chat_manager: ChatManager) -> None:
    """
    Export all users who have not finished the onboarding process along with their answers.
    Command `/unfinished` needs to be called in the General chat to export the users.
    The function generates a PDF report containing all unfinished users' Q&A pairs.
    """
    users = await User.all()
    if not users:
        await message.reply("No users found")
        return

    unfinished_users = []
    for user in users:
        if await chat_manager.is_user_talking(user.id):
            unfinished_users.append(user)

    if not unfinished_users:
        await message.reply("No unfinished users found")
        return

    await message.reply(
        f"Found {len(unfinished_users)} unfinished users. Generating PDF report..."
    )

    # Collect Q&A pairs for all unfinished users
    qa_data = {}
    for user in unfinished_users:
        qa_pairs = await chat_manager.qa_pairs(user.id)
        if qa_pairs:  # Only include users who have at least started answering
            qa_data[user.id] = qa_pairs

    # Generate PDF report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"unfinished_users_{timestamp}.pdf"
    processor = processors.PdfProcessor(output_path=pdf_filename)
    await processor.process_multiple(qa_data)

    # Send the PDF file
    await message.reply_document(
        types.FSInputFile(pdf_filename),
        caption=f"Q&A report for {len(qa_data)} unfinished users",
    )

    # Clean up the file
    os.remove(pdf_filename)


@router.message(Command("export"), F.chat.type == "supergroup")
async def export(message: types.Message, chat_manager: ChatManager) -> None:
    """
    Export all users who have not finished the onboarding process along with their answers.
    Command `/export` needs to be called in the General chat to export the users.
    The function generates a PDF report containing all unfinished users' Q&A pairs.
    """
    users = await User.all()
    if not users:
        await message.reply("No users found")
        return

    await message.reply(
        f"Found {len(users)} unfinished users. Generating PDF report..."
    )

    # Collect Q&A pairs for all unfinished users
    qa_data = {}
    for user in users:
        qa_pairs = await chat_manager.qa_pairs(user.id)
        if qa_pairs:  # Only include users who have at least started answering
            qa_data[user.id] = qa_pairs

    # Generate PDF report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"unfinished_users_{timestamp}.pdf"
    processor = processors.PdfProcessor(output_path=pdf_filename)
    await processor.process_multiple(qa_data)

    # Send the PDF file
    await message.reply_document(
        types.FSInputFile(pdf_filename),
        caption=f"Q&A report for {len(qa_data)} users",
    )

    # Clean up the file
    os.remove(pdf_filename)


@router.message(
    Command("stop"),
    F.chat.type == "supergroup",
    F.text.is_not(None),
    F.message_thread_id.is_not(None),
)
async def stop_talking_with(message: types.Message, chat_manager: ChatManager) -> None:
    """
    Stop talking with a user.
    Command `/stop` needs to be called in the topic chat to stop talking with the user.
    """
    user = await User.filter(id=message.from_user.id).first()
    if not user:
        return

    topic = await TopicGroup.filter(topic_group_id=message.message_thread_id).first()
    if topic is None:
        return

    qa_data = await chat_manager.qa_pairs(user.id)
    if qa_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"user_{user.id}_qa_{timestamp}.pdf"
        processor = processors.PdfProcessor(output_path=pdf_filename)
        await processor(user.id, qa_data)

        link = f'<a href="{user.url}">user</a>'
        await message.reply_document(
            types.FSInputFile(pdf_filename),
            caption=f"Q&A report for {link}",
            parse_mode=aiogram_enums.ParseMode.HTML,
        )
        os.remove(pdf_filename)

    await chat_manager.stop_talking_with(user.id)

    user_manager = (
        await UserManager.filter(user_id=user.id).first() or await Manager.first()
    )
    if user_manager:
        reply = (
            f"Your personal manager {user_manager.manager_link} will contact you soon."
        )
    else:
        reply = "A personal manager will contact you soon."

    await message.bot.send_message(
        chat_id=topic.user_id,
        text=reply,
    )


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
