import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.persistence.models import SuperGroup


logger = logging.getLogger(__name__)


class ExpectSuperGroupSetMiddleware(BaseMiddleware):
    """
    Expect the super group to be set.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        if not await SuperGroup.filter().exists():
            logger.error(
                "No supergroup selected. Use /attach in a supergroup first. "
                "Messages will be ignored. "
                f"Request from user {event.from_user.full_name} (id: {event.from_user.id})"
            )
            return
        data["supergroup_id"] = (await SuperGroup.filter().first()).group_id
        return await handler(event, data)
