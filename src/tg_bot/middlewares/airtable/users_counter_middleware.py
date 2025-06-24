from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.tg_bot.middlewares.airtable import users_counter


class AirtableUsersCounterMiddleware(BaseMiddleware):
    """
    Middleware to inject the airtable users counter.
    """

    def __init__(self, counter: users_counter.AirtableUsersCounter):
        self.counter = counter

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        data["airtable_users_counter"] = self.counter
        return await handler(event, data)
