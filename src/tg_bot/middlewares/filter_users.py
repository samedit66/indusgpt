from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.tg_bot import chat


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
        if await chat.has_user_finished(event.from_user.id):
            return

        return await handler(event, data)
