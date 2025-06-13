import asyncio
from dataclasses import dataclass, field
import logging

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ContentType

from src import chat
from src.tg_bot import middlewares
from src.tg_bot import chat_settings
from src.persistence.models import Manager, UserManager, User


@dataclass
class UserMessageBuffer:
    supergroup_id: int
    topic_group_id: int
    chat_manager: chat.ChatManager
    stored_messages: list[types.Message] = field(default_factory=list)

    def store(self, message: types.Message) -> None:
        self.stored_messages.append(message)

    def clear(self) -> None:
        self.stored_messages.clear()


router = Router()
router.message.middleware(middlewares.ExpectSuperGroupSetMiddleware())
router.message.middleware(middlewares.CreateUserAndTopicGroupMiddleware())
router.message.middleware(middlewares.FinishedUsersMiddleware())

logger = logging.getLogger(__name__)

message_buffer: dict[int, UserMessageBuffer] = {}


@router.message(Command("start"), F.chat.type == "private")
async def start(
    message: types.Message,
    supergroup_id: int,
    topic_group_id: int,
    chat_manager: chat.ChatManager,
) -> None:
    bot_msg = await message.answer(chat_settings.INTRODUCTION)
    await bot_msg.send_copy(
        chat_id=supergroup_id,
        message_thread_id=topic_group_id,
    )

    bot_msg = await message.answer(
        await chat_manager.current_question(message.from_user.id)
    )
    await bot_msg.send_copy(
        chat_id=supergroup_id,
        message_thread_id=topic_group_id,
    )


@router.message(F.content_type == ContentType.VOICE, F.chat.type == "private")
async def voice_message(
    message: types.Message,
    supergroup_id: int,
    topic_group_id: int,
) -> None:
    bot_msg = await message.answer(
        "Bro, please write the lyrics, I can't listen to it right now."
    )
    await bot_msg.send_copy(
        chat_id=supergroup_id,
        message_thread_id=topic_group_id,
    )


@router.message(F.content_type != ContentType.TEXT, F.chat.type == "private")
async def not_text_message(
    message: types.Message,
    supergroup_id: int,
    topic_group_id: int,
) -> None:
    bot_msg = await message.answer("Bro, please write the lyrics")
    await bot_msg.send_copy(
        chat_id=supergroup_id,
        message_thread_id=topic_group_id,
    )


@router.message(F.chat.type == "private")
async def handle_message_from_user(
    message: types.Message,
    supergroup_id: int,
    topic_group_id: int,
    chat_manager: chat.ChatManager,
) -> None:
    user_id = message.from_user.id

    # If this is the first time we've seen this user, create their buffer and start its task
    if user_id not in message_buffer:
        buf = UserMessageBuffer(
            supergroup_id=supergroup_id,
            topic_group_id=topic_group_id,
            chat_manager=chat_manager,
        )
        message_buffer[user_id] = buf

        # Create a per‐user flushing coroutine
        buf.flushing_task = asyncio.create_task(_per_user_flusher(user_id))

    # Store the incoming text into that user's buffer
    message_buffer[user_id].store(message)


async def _per_user_flusher(user_id: int) -> None:
    """
    This task wakes up every 30 seconds and—*for this single user*—checks
    if there are buffered messages. If there are, it calls chat_manager.reply(),
    sends the reply, copies it to the supergroup, notifies manager if finished,
    and clears the buffer. Once the dialog is finished, or if we fail repeatedly,
    it simply returns (exits).
    """
    buf = message_buffer[user_id]

    need_to_sleep = True
    try:
        while True:
            if need_to_sleep:
                await asyncio.sleep(30)  # wait 30 seconds between flushes
                need_to_sleep = False

            # If the user buffer has no messages, just loop again
            if not buf.stored_messages:
                # But first check if the dialog is finished; if yes, exit the loop
                try:
                    finished = await buf.chat_manager.has_user_finished(user_id)
                except Exception as e:
                    logger.error(f"Error checking finished status for {user_id}: {e}")
                    # If we can't even check, it might be safer to exit
                    finished = True

                if finished:
                    break
                continue

            # 1) Combine all pending texts
            stored_messages = buf.stored_messages.copy()
            combined_user_text = " ".join(
                msg.text for msg in stored_messages if msg.text
            ).strip()

            # 2) Ask chat_manager for a reply
            try:
                reply_text = await buf.chat_manager.reply(user_id, combined_user_text)
            except Exception as e:
                logger.error(f"Error generating reply for user {user_id}: {e}")
                # If chat_manager is broken, just clear and exit
                buf.clear()
                break

            # 2.1) Check if user write anything new - they may have provided new information,
            # which we need for a complete answer
            if len(stored_messages) < len(buf.stored_messages):
                need_to_sleep = False
                continue
            else:
                need_to_sleep = True
                buf.clear()

            # 3) Send the reply under the last user message
            last_user_msg = stored_messages[-1]
            try:
                bot_msg = await last_user_msg.answer(reply_text)
            except Exception as e:
                logger.error(f"Error sending reply to {user_id}: {e}")
                buf.clear()
                break

            # 4) Copy that bot message into the supergroup/topic
            try:
                await bot_msg.send_copy(
                    chat_id=buf.supergroup_id,
                    message_thread_id=buf.topic_group_id,
                )
            except Exception as e:
                logger.error(
                    f"Error copying bot message for user {user_id} "
                    f"into supergroup {buf.supergroup_id}, topic {buf.topic_group_id}: {e}"
                )

            # 5) If finished, notify the manager
            try:
                finished = await buf.chat_manager.has_user_finished(user_id)
            except Exception as e:
                logger.error(f"Error checking finished status for user {user_id}: {e}")
                finished = False

            if finished:
                try:
                    user = await User.filter(id=user_id).first()
                    user_manager = (
                        await UserManager.filter(user=user).first()
                        or await Manager.first()
                    )
                    if user_manager:
                        bot_msg = await last_user_msg.answer(
                            f"Your personal manager {user_manager.manager_link} will contact you soon."
                        )
                    else:
                        bot_msg = await last_user_msg.answer(
                            "A personal manager will contact you soon."
                        )
                    await bot_msg.send_copy(
                        chat_id=buf.supergroup_id,
                        message_thread_id=buf.topic_group_id,
                    )
                except Exception as e:
                    logger.error(
                        f"Error sending manager notification to {user_id}: {e}"
                    )
                # Once finished, break out of the loop
                buf.clear()
                need_to_sleep = True
                break

            # 6) Clear the buffer (we’ve just processed all pending messages)
            if len(stored_messages) < len(buf.stored_messages):
                need_to_sleep = False
                continue
            else:
                need_to_sleep = True
                buf.clear()

    except asyncio.CancelledError:
        # If someone externally cancels the task, just clean up and exit
        buf.clear()
    finally:
        # Remove the buffer and task from our dict so we don't leak
        del message_buffer[user_id]
