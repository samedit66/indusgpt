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
    user_id = message.from_user.id

    if user_id not in message_buffer:
        message_buffer[user_id] = UserMessageBuffer(
            supergroup_id=supergroup_id,
            topic_group_id=topic_group_id,
            chat_manager=chat_manager,
        )

    message_buffer[user_id].store(message)


async def flush_all_buffers() -> None:
    """
    Для каждого Buffer, хранящего непустой список stored_messages:
      1) Собираем все тексты из stored_messages в одну строку.
      2) Вызываем chat_manager.reply(...) для этого объединенного текста и получаем ответ.
      3) Берем последнее сохраненное сообщение пользователя (Buffer.stored_messages[-1])
         и через его .answer() отправляем бот‐сообщение пользователю.
      4) Копируем это бот‐сообщение в супергруппу/топик-группу.
      5) Если пользователь завершил диалог, уведомляем личного менеджера.
      6) Очищаем stored_messages в этом Buffer.
    """
    to_clear: list[int] = []

    for user_id, buffer in message_buffer.items():
        if not buffer.stored_messages:
            continue

        # 1) Объединяем тексты всех сообщений пользователя
        combined_user_text = " ".join(
            msg.text for msg in buffer.stored_messages if msg.text
        ).strip()

        # 2) Получаем ответ от chat_manager
        try:
            reply_text = await buffer.chat_manager.reply(user_id, combined_user_text)
        except Exception as e:
            logger.error(f"Error generating reply for user {user_id}: {e}")
            to_clear.append(user_id)
            continue

        # 3) Берем последнее сообщение пользователя, чтобы через него послать ответ
        last_user_msg = buffer.stored_messages[-1]
        try:
            bot_msg = await last_user_msg.answer(reply_text)
        except Exception as e:
            logger.error(f"Error sending combined reply to {user_id}: {e}")
            to_clear.append(user_id)
            continue

        # 4) Копируем бот‐сообщение в супергруппу/топик-группу
        try:
            await bot_msg.send_copy(
                chat_id=buffer.supergroup_id,
                message_thread_id=buffer.topic_group_id,
            )
        except Exception as e:
            logger.error(
                f"Error copying bot message for user {user_id} "
                f"into supergroup {buffer.supergroup_id}, topic {buffer.topic_group_id}: {e}"
            )

        # 5) Если диалог завершен, уведомляем личного менеджера
        try:
            finished = await buffer.chat_manager.has_user_finished(user_id)
        except Exception as e:
            logger.error(f"Error checking finished status for user {user_id}: {e}")
            finished = False

        if finished:
            try:
                user = await User.filter(id=user_id).first()
                user_manager = (
                    await UserManager.filter(user=user).first() or await Manager.first()
                )
                if user_manager:
                    await last_user_msg.answer(
                        f"Your personal manager {user_manager.manager_link} will contact you soon."
                    )
                else:
                    await last_user_msg.answer(
                        "A personal manager will contact you soon."
                    )
            except Exception as e:
                logger.error(f"Error sending manager notification to {user_id}: {e}")

        # 6) Помечаем этот Buffer на очистку
        to_clear.append(user_id)

    # Очищаем все stored_messages в тех Buffer-ах, которые обработали
    for user_id in to_clear:
        message_buffer[user_id].clear()
