from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.chat import ChatManager


class ChatManagerMiddleware(BaseMiddleware):
    """
    Middleware to inject the chat manager into the message handler.
    """

    def __init__(self, chat_manager: ChatManager):
        self.chat_manager = chat_manager

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        data["chat_manager"] = self.chat_manager
        return await handler(event, data)
