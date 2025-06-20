from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.tg_bot.middlewares.airtable import daily_tracker


class AirtableDailyTrackerMiddleware(BaseMiddleware):
    """
    Middleware to inject the airtable processor into the message handler.
    """

    def __init__(self, tracker: daily_tracker.AirtableDailyTracker):
        self.tracker = tracker

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        data["airtable_daily_tracker"] = self.tracker
        return await handler(event, data)
