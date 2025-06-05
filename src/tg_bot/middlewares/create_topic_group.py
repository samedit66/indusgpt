from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

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
        name = event.from_user.username or "N/A"
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

        # 4) We’ll compare against the ID of the thread in which this Message arrived.
        #    If `message_thread_id` is None, that means the user posted in the “main” group,
        #    so we definitely need to create (or re-create) their personal thread.
        incoming_thread = event.message_thread_id

        if topic_group is None:
            # No TopicGroup at all → create a new forum topic and insert a row.
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
            # We already have a TopicGroup row. Check whether:
            #   (a) the incoming message is in a different thread, or
            #   (b) it isn’t in any thread (incoming_thread is None).
            if topic_group.topic_group_id != incoming_thread:
                # Either “they’re posting somewhere else” or “no thread at all” → re-create it.
                forum_topic = await event.bot.create_forum_topic(
                    chat_id=supergroup_id,
                    name=event.from_user.full_name,
                )
                new_thread_id = forum_topic.message_thread_id

                topic_group.topic_group_id = new_thread_id
                await topic_group.save()

        # 5) Stick the (now‐valid) thread ID into `data` so downstream handlers can use it.
        data["topic_group_id"] = topic_group.topic_group_id

        # 6) Call the next handler in the chain.
        return await handler(event, data)
