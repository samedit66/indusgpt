from typing import Iterable

from src import types


class ChatStateManager:
    """
    Coordinates the flow of questions and user responses, maintaining per-user progress.
    """

    def __init__(
        self,
        question_list: types.QuestionList,
        user_answer_storage: types.UserAnswerStorage,
        on_all_finished: Iterable[types.QaProcessor] | None = None,
    ) -> None:
        """
        :param question_list: Source of questions and navigation controls
        :param user_answer_storage: Storage for accumulating each user’s in-progress answer
        :param on_all_finished: Iterable of callbacks to be executed when a user finishes all questions
        """
        self.question_list = question_list
        self.user_answer_storage = user_answer_storage
        self.on_all_finished_callbacks = on_all_finished or ()

    async def has_user_started(self, user_id: int) -> bool:
        """
        Checks if the conversation with the specified user has been ever started.

        :param user_id: identifier for the conversation participant
        :return: True if the user is in progress or completed all the questions; False otherwise
        """
        return await self.question_list.has_user_started(user_id)

    async def current_state(self, user_id: int) -> types.State:
        """
        Fetches the active question and any saved partial answer for a given user.

        :param user_id: identifier for the conversation participant
        :return: a State namedtuple of (question, partial_answer)
        """
        question = await self.question_list.current_question(user_id)
        if question is None:
            return types.State(types.StateType.FINISHED, None, None)

        partial_answer = await self.user_answer_storage.get(user_id)
        return types.State(types.StateType.IN_PROGRESS, question, partial_answer)

    async def update_answer(self, user_id: int, partial_answer: str) -> None:
        """
        Persists the latest draft of the user’s response.

        :param user_id: identifier for the conversation participant
        :param partial_answer: text to store as the current, incomplete answer
        """
        await self.user_answer_storage.append(user_id, partial_answer)

    async def finish_question(self, user_id: int) -> None:
        """
        Finalizes the current answer, clears the draft, and advances to the next question.
        If all questions are answered, triggers any registered callbacks.

        :param user_id: identifier for the conversation participant
        """
        answer = await self.user_answer_storage.get(user_id)
        await self.user_answer_storage.clear(user_id)
        await self.question_list.advance(user_id, answer)

        # TODO: Возможно, стоит делать это в отдельном методе...
        if await self.all_finished(user_id):
            for callback in self.on_all_finished_callbacks:
                await callback(user_id, await self.question_list.qa_pairs(user_id))

    async def all_finished(self, user_id: int) -> bool:
        """
        Determines whether the user has completed every question in the sequence.

        :param user_id: identifier for the conversation participant
        :return: True if no further questions remain, False otherwise
        """
        return await self.question_list.all_finished(user_id)

    async def qa_pairs(self, user_id: int) -> list[types.QaPair]:
        """
        Returns all Q&A pairs for a given user.

        :param user_id: identifier for the conversation participant
        :return: list of Q&A pairs
        """
        return await self.question_list.qa_pairs(user_id)

    async def stop_talking_with(self, user_id: int) -> None:
        """
        Stops the conversation with the specified user.

        :param user_id: identifier for the conversation participant
        """
        await self.user_answer_storage.clear(user_id)
        await self.question_list.stop_talking_with(user_id)
