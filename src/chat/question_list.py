from abc import ABC, abstractmethod
from collections import namedtuple

Question = namedtuple("Question", ["text", "answer_requirement"])

QaPair = namedtuple("AqPair", ["question", "answer"])


class QuestionList(ABC):
    """
    Outlines methods for delivering questions in order and tracking completion per user.
    """

    @abstractmethod
    async def has_user_started(self, user_id: int) -> bool:
        """
        Checks if the user has ever started answering questions.

        :param user_id: identifier for the conversation participant
        :return: True if the user has started answering questions, False otherwise
        """

    @abstractmethod
    async def current_question(self, user_id: int) -> Question | None:
        """
        Provides the next pending question for a user without advancing the pointer.
        If user has not started answering questions, returns the first question.

        :param user_id: identifier for the conversation participant
        :return: a Question tuple containing the prompt and any metadata
            (None if all questions are answered or user is not registered)
        """

    @abstractmethod
    async def advance(self, user_id: int, answer: str) -> None:
        """
        Accepts a finalized answer and steps forward to the next question.
        Nothing happens if all questions are answered.

        :param user_id: identifier for the conversation participant
        :param answer: the completed response to the current question
        """

    @abstractmethod
    async def all_finished(self, user_id: int) -> bool:
        """
        Checks whether the user has answered all questions.

        :param user_id: identifier for the conversation participant
        :return: True if there are no further questions, False otherwise
        """

    @abstractmethod
    async def qa_pairs(self, user_id: int) -> list[QaPair]:
        """
        Returns a list of currently answered questions and their corresponding answers.

        :param user_id: identifier for the conversation participant
        :return: a list of tuples containing the question and its answer
        """
