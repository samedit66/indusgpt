from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.persistence.models import TopicGroup, User


class CreateUserAndTopicGroupMiddleware(BaseMiddleware):
    """
    Create a user and a topic group for the user if it doesn't exist.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        user, _ = await User.get_or_create(
            id=event.from_user.id,
            defaults={
                "name": event.from_user.full_name,
                "url": event.from_user.url,
            },
        )

        supergroup_id = data["supergroup_id"]
        if not await TopicGroup.filter(user=user).exists():
            topic = await event.bot.create_forum_topic(
                chat_id=supergroup_id,
                name=event.from_user.full_name,
            )
            thread_id = topic.message_thread_id
            await TopicGroup.create(user=user, topic_group_id=thread_id)

        data["topic_group_id"] = (
            await TopicGroup.filter(user=user).first()
        ).topic_group_id
        return await handler(event, data)
