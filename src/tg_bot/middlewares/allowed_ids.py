from typing import Iterable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.persistence import models


class AllowedIdsMiddleware(BaseMiddleware):
    """
    Middleware that only allows certain user IDs to invoke the /attach command.
    If a user not in allowed_ids attempts to send "/attach", the middleware
    will simply drop the update (no reply or handler execution).
    """

    def __init__(self, allowed_ids: Iterable[int]):
        """
        :param allowed_ids: An iterable of Telegram user IDs that are permitted
                            to run the /attach command.
        """
        super().__init__()
        self.allowed_ids: set[int] = set(allowed_ids)

    async def __call__(self, handler, event, data):
        # Only process Message events in a supergroup
        if (
            isinstance(event, Message)
            and event.text
            and event.chat.type == "supergroup"
        ):
            # Extract the command part (e.g., "/attach" or "/attach@YourBotName")
            command = event.text.lstrip().split()[0]

            # We care about both "/attach" and "/detach" (with or without @BotName)
            if (
                command == "/attach"
                or command.startswith("/attach@")
                or command == "/detach"
                or command.startswith("/detach@")
                or command == "/set_manager"
                or command.startswith("/set_manager@")
                or command == "/unset_manager"
                or command.startswith("/unset_manager")
            ):
                # 1) Fetch all telegram_id values from Manager and UserManager
                manager_ids_from_manager = await models.Manager.all().values_list(
                    "manager_link", flat=True
                )
                manager_ids_from_usermanager = (
                    await models.UserManager.all().values_list(
                        "manager_link", flat=True
                    )
                )

                # Combine them into a single set for quick membership testing
                managers_links = set(manager_ids_from_manager) | set(
                    manager_ids_from_usermanager
                )

                # 2) Must be either in allowed_ids OR in managers_ids
                user_id = event.from_user.id
                username = f"@{event.from_user.username}"
                if not (user_id in self.allowed_ids or username in managers_links):
                    # Drop the update (no reply, no handler invocation)
                    return

        # For all other updates (or if checks passed), proceed as normal
        return await handler(event, data)
