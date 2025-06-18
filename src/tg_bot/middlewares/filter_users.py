from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src import chat


DEFAULT_MESSAGE = (
    "Bro, your information has been recorded and is under review. "
    "Please wait to be contacted by a manager, and discuss all further questions with them."
)


class FinishedUsersMiddleware(BaseMiddleware):
    """
    Filter users who have finished the conversation.
    They are not allowed to interact with the AI anymore.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        # Пересылаем сообщение пользователя в топик-группу
        # в любом случае, даже если пользователь закончил диалог
        await event.forward(
            chat_id=data["supergroup_id"],
            message_thread_id=data["topic_group_id"],
        )

        chat_manager: chat.ChatManager = data["chat_manager"]
        if await chat_manager.has_user_finished(event.from_user.id):
            return await event.answer(DEFAULT_MESSAGE)

        return await handler(event, data)
