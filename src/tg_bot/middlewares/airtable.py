from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src import processors


class AirtableMiddleware(BaseMiddleware):
    """
    Middleware to inject the airtable processor into the message handler.
    """

    def __init__(self, processor: processors.AirtableProcessor):
        self.processor = processor

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        data["airtable_processor"] = self.processor
        return await handler(event, data)
