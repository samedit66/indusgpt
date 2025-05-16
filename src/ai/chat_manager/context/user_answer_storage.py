from abc import ABC, abstractmethod


class UserAnswerStorage(ABC):
    """
    Defines the interface for storing, retrieving, and clearing a user’s in-progress answer.
    """

    @abstractmethod
    def register_user(self, user_id: int) -> None:
        """
        Registers a new user in the storage.

        :param user_id: identifier for the conversation participant
        """

    @abstractmethod
    def delete_user(self, user_id: int) -> None:
        """
        Removes the user from the storage.
        Nothing happens if the user is not registered.

        :param user_id: identifier for the conversation participant
        """

    @abstractmethod
    def contains_user(self, user_id: int) -> bool:
        """
        Checks if the user is registered in the storage.

        :param user_id: identifier for the conversation participant
        :return: True if the user is registered, False otherwise
        """

    @abstractmethod
    def append(self, user_id: int, partial_answer: str) -> None:
        """
        Appends the draft response for a given user.

        :param user_id: identifier for the conversation participant
        :param partial_answer: the latest text to record
        """

    @abstractmethod
    def get(self, user_id: int) -> str | None:
        """
        Retrieves the current draft response, if any.

        :param user_id: identifier for the conversation participant
        :return: the stored partial answer (None if nothing was stored)
        """

    @abstractmethod
    def clear(self, user_id: int) -> None:
        """
        Removes any saved draft for the specified user.

        :param user_id: identifier for the conversation participant
        """
