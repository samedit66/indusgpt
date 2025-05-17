from abc import ABC, abstractmethod
from collections import namedtuple

Question = namedtuple("Question", ["text", "answer_requirement"])

QaPair = namedtuple("AqPair", ["question", "answer"])


class QuestionList(ABC):
    """
    Outlines methods for delivering questions in order and tracking completion per user.
    """

    @abstractmethod
    def register_user(self, user_id: int) -> None:
        """
        Registers a new user in the storage.
        Nothing happens if the user is already registered.

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
    def current_question(self, user_id: int) -> Question | None:
        """
        Provides the next pending question for a user without advancing the pointer.

        :param user_id: identifier for the conversation participant
        :return: a Question tuple containing the prompt and any metadata
            (None if all questions are answered or user is not registered)
        """

    @abstractmethod
    def forth(self, user_id: int, answer: str) -> None:
        """
        Accepts a finalized answer and steps forward to the subsequent question.
        Does nothing if the user is not registered.

        :param user_id: identifier for the conversation participant
        :param answer: the completed response to the current question
        """

    @abstractmethod
    def all_finished(self, user_id: int) -> bool:
        """
        Checks whether the user has answered every question in the list.

        :param user_id: identifier for the conversation participant
        :return: True if there are no further questions, False otherwise
        """

    @abstractmethod
    def qa_pairs(self, user_id: int) -> list[QaPair]:
        """
        Returns a list of currently answered questions and their corresponding answers.

        :param user_id: identifier for the conversation participant
        :return: a list of tuples containing the question and its answer
            (empty if the user is not registered)
        """
