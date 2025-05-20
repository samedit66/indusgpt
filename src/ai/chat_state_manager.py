from typing import Any, Callable, Iterable

from .question_list import QuestionList, QaPair
from .user_answer_storage import UserAnswerStorage

from .chat_state import State, StateType

type OnAllFinishedCallback = Callable[[int, list[QaPair]], Any]


class ChatStateManager:
    """
    Coordinates the flow of questions and user responses, maintaining per-user progress.
    """

    def __init__(
        self,
        question_list: QuestionList,
        user_answer_storage: UserAnswerStorage,
        on_all_finished: Iterable[OnAllFinishedCallback] = None,
    ) -> None:
        """
        :param question_list: Source of questions and navigation controls
        :param user_answer_storage: Storage for accumulating each user’s in-progress answer
        :param on_all_finished: Iterable of callbacks to be executed when a user finishes all questions
        """
        self.question_list = question_list
        self.user_answer_storage = user_answer_storage
        self.on_all_finished_callbacks = on_all_finished or ()

    def start(self, user_id: int) -> None:
        """
        Initializes tracking for a new user by registering them in both the question sequence
        and answer-storage systems.

        :param user_id: identifier for the conversation participant
        """
        self.question_list.register_user(user_id)
        self.user_answer_storage.register_user(user_id)

    def has_started(self, user_id: int) -> bool:
        """
        Checks if the conversation with the specified user has been ever started.

        :param user_id: identifier for the conversation participant
        :return: True if the user is in progress or completed all the questions; False otherwise
        """
        return self.question_list.contains_user(
            user_id
        ) and not self.question_list.all_finished(user_id)

    def current_state(self, user_id: int) -> State:
        """
        Fetches the active question and any saved partial answer for a given user.

        :param user_id: identifier for the conversation participant
        :return: a State namedtuple of (question, partial_answer)
        """
        question = self.question_list.current_question(user_id)
        if question is None:
            return State(StateType.FINISHED, None, None)

        partial_answer = self.user_answer_storage.get(user_id)
        return State(StateType.IN_PROGRESS, question, partial_answer)

    def update_answer(self, user_id: int, partial_answer: str) -> None:
        """
        Persists the latest draft of the user’s response.

        :param user_id: identifier for the conversation participant
        :param partial_answer: text to store as the current, incomplete answer
        """
        self.user_answer_storage.append(user_id, partial_answer)

    def finish_question(self, user_id: int) -> None:
        """
        Finalizes the current answer, clears the draft, and advances to the next question.
        If all questions are answered, triggers any registered callbacks.

        :param user_id: identifier for the conversation participant
        """
        answer = self.user_answer_storage.get(user_id)
        self.user_answer_storage.clear(user_id)
        self.question_list.forth(user_id, answer)

        # TODO: Возможно, стоит делать это в отдельном методе...
        if self.all_finished(user_id):
            for callback in self.on_all_finished_callbacks:
                callback(user_id, self.question_list.qa_pairs(user_id))

    def all_finished(self, user_id: int) -> bool:
        """
        Determines whether the user has completed every question in the sequence.

        :param user_id: identifier for the conversation participant
        :return: True if no further questions remain, False otherwise
        """
        return self.question_list.all_finished(user_id)
