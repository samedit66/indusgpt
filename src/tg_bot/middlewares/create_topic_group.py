from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram import exceptions

from src.persistence.models import TopicGroup, User


class CreateUserAndTopicGroupMiddleware(BaseMiddleware):
    """
    Ensure that:
      1) A corresponding User row exists.
      2) A TopicGroup row exists for that User.
         • If none exists → create a new forum topic and save its thread ID.
         • If one exists but its `topic_group_id` doesn’t match
           the incoming Message’s thread (or the Message is not in any thread)
           → create a brand‐new forum topic and overwrite the old ID.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict,
    ) -> Any:
        # 1) Make sure the User row is there.
        name = event.from_user.full_name or event.from_user.username
        user, _ = await User.get_or_create(
            id=event.from_user.id,
            defaults={
                "name": name,
                "url": event.from_user.url,
            },
        )

        # 2) Grab `supergroup_id` from data.
        supergroup_id = data["supergroup_id"]

        # 3) Try to load an existing TopicGroup for this user.
        topic_group = await TopicGroup.get_or_none(user=user)

        if topic_group is None:
            # 4.1) No TopicGroup at all → create a new forum topic and insert a row.
            forum_topic = await event.bot.create_forum_topic(
                chat_id=supergroup_id,
                name=event.from_user.full_name,
            )
            new_thread_id = forum_topic.message_thread_id

            topic_group = await TopicGroup.create(
                user=user,
                topic_group_id=new_thread_id,
            )
        else:
            bot = event.bot

            # 4.2) If it exists, verify the forum topic is still valid.
            try:
                # Attempt to get the existing forum topic via Telegram API.
                await bot.edit_forum_topic(
                    chat_id=supergroup_id,
                    message_thread_id=topic_group.topic_group_id,
                )
            except exceptions.TelegramBadRequest:
                # Topic was not found; create a new forum topic.
                new_topic = await bot.create_forum_topic(
                    chat_id=supergroup_id,
                    name=name,
                )
                # Update the TopicGroup with the new topic ID.
                topic_group.topic_group_id = new_topic.message_thread_id
                await topic_group.save()

        # 5) Stick the (now‐valid) thread ID into `data` so downstream handlers can use it.
        data["topic_group_id"] = topic_group.topic_group_id

        # 6) Call the next handler in the chain.
        return await handler(event, data)
