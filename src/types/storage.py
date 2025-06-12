from abc import ABC, abstractmethod


class UserAnswerStorage(ABC):
    """
    Defines the interface for storing, retrieving, and clearing a user’s in-progress answer.
    """

    @abstractmethod
    async def append(self, user_id: int, partial_answer: str) -> None:
        """
        Appends the draft response for a given user.

        :param user_id: identifier for the conversation participant
        :param partial_answer: the latest text to record
        """

    @abstractmethod
    async def get(self, user_id: int) -> str | None:
        """
        Retrieves the current draft response, if any.

        :param user_id: identifier for the conversation participant
        :return: the stored partial answer (None if nothing was stored)
        """

    @abstractmethod
    async def clear(self, user_id: int) -> None:
        """
        Removes any saved draft for the specified user.

        :param user_id: identifier for the conversation participant
        """

    @abstractmethod
    async def replace(self, user_id: int, new_answer: str) -> None:
        """
        Replaces current saved draft for the specified user with new one.

        :param user_id: identifier for the conversation participant
        :param new_answer: new draft answer
        """
