from typing import Iterable

from aiogram import BaseMiddleware
from aiogram.types import Message


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
        """
        Intercept all incoming Message updates. If the text of the message is "/attach"
        (possibly with bot username), check if the sender is in allowed_ids. If not,
        do nothing (i.e., do not call the handler, do not send any reply). Otherwise,
        continue to the handler.
        """
        # Only process Message events
        if (
            isinstance(event, Message)
            and event.text
            and event.chat.type == "supergroup"
        ):
            # Extract the command part (e.g., "/attach" or "/attach@YourBotName")
            command = event.text.lstrip().split()[0]
            if (
                command == "/attach"
                or command.startswith("/attach@")
                or command == "/detach"
                or command.startswith("/attach@")
            ):
                # 2) Must be an allowed user ID
                user_id = event.from_user.id
                if user_id not in self.allowed_ids:
                    return  # drop

        # For all other updates (or allowed /attach), proceed as normal
        return await handler(event, data)
