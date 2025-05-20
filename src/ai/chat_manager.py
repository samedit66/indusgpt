from typing import Callable, Iterable

from .question_list import QuestionList
from .user_answer_storage import UserAnswerStorage
from .chat_state import State
from .chat_state_manager import ChatStateManager, OnAllFinishedCallback

from .handle_user_message import ResponseToUser

type ResponseGenerator = Callable[[str, State], ResponseToUser]
"""
Callable which can generate a response to user.
Takes user input and current chat state.
Returns a `ResponseToUser`.
"""

type ReplyGenerator = Callable[[ResponseToUser, State], str]
"""
Callable which can produce a pretty reply to user.
Usually to get a pretty-looking reply you might want to add a next question,
or add a goodbye if conversation is finished -- more context needs to be provided.
This callable takes a `ResponeToUser` to enrich the context and current chat state.
Based on them, it returns a natural reply.
"""


class ChatManager:
    """
    Manages a multi-step Q&A conversation.
    """

    def __init__(
        self,
        question_list: QuestionList,
        user_answer_storage: UserAnswerStorage,
        handle_user_message: ResponseGenerator,
        build_reply: ReplyGenerator,
        on_all_finished: Iterable[OnAllFinishedCallback] = None,
    ) -> None:
        """
        Initialize ChatManager with question sequence and persistence layer for answers.

        Args:
            question_list (QuestionList): An ordered collection of Question objects
                defining the conversation flow.
            user_answer (UserAnswerStorage): A storage interface for saving or retrieving
                user-provided answers between sessions.
            on_all_finished (Iterable[OnAllFinishedCallback]): A list of callback functions
                to be executed when a user finishes all questions.
            **model_settings: Arbitrary keyword settings used to configure the
                underlying DialogAgent (e.g., model name, temperature).
        """
        self.handle_user_message = handle_user_message
        self.build_reply = build_reply
        self.chat_state_manager = ChatStateManager(
            question_list=question_list,
            user_answer_storage=user_answer_storage,
            on_all_finished=on_all_finished,
        )

    def current_question(self, user_id: int) -> str | None:
        """
        Retrieve the current question for a user without advancing the state.

        Args:
            user_id (int): Unique identifier for the user session.

        Returns:
            str | None: The text of the current question. Returns None if all
                questions have been answered or user is not registered.
        """
        if self.chat_state_manager.all_finished(user_id):
            return None
        q, _ = self.chat_state_manager.current_state(user_id)
        return q.text

    async def reply(self, user_id: int, user_input: str) -> str | None:
        """
        Process a single user message, advance the Q&A state, and generate
        the next bot reply combining the agent's text and the following question.

        Workflow:
        1. Start or resume the session for the given user_id.
        2. If all questions are answered, return None to indicate completion.
        3. Send the user input (with context) to the DialogAgent via _talk().
        4. Update conversation state (mark question finished or store partial answer).
        5. Build and return the combined reply text with the next question or closing message.

        Args:
            user_id (int): Unique identifier for the user session.
            user_input (str): The latest message from the user.

        Returns:
            The text the bot should reply with, including the next
            question or a final summary. Returns None if the Q&A is complete.
        """
        # Start session if needed
        if not self.chat_state_manager.has_started(user_id):
            self.chat_state_manager.start(user_id)

        # If conversation is finished, no further replies
        if self.chat_state_manager.all_finished(user_id):
            return None

        # Invoke the dialog agent and update state
        agent_response = await self._talk(user_id, user_input)
        self._update_state(user_id, agent_response)

        # Build the outgoing reply
        current_state = self.chat_state_manager.current_state(user_id)
        return self.build_reply(agent_response.response_text, current_state)

    async def _talk(self, user_id: int, user_input: str) -> ResponseToUser:
        """
        Retrieve the current question and partial answer, compose a prompt,
        and query the DialogAgent for its next fragment of reply.

        Args:
            user_id (int): Session identifier to fetch current state.
            user_input (str): The textual input provided by the user.

        Returns:
            Answer: The agent's response object, containing the generated text,
                a flag 'ready_for_next_question', and the processed user_input.
        """
        _, question, partial_answer = self.chat_state_manager.current_state(user_id)
        answer = await self.handle_user_message(
            user_input=user_input,
            question=question,
            context=partial_answer,
        )
        return answer

    def _update_state(self, user_id: int, agent_responce: ResponseToUser) -> None:
        """
        Update the ChatStateManager based on whether the agent has indicated
        readiness to move to the next question or needs more user input.

        Args:
            user_id (int): Identifier of the user session.
            agent_answer (Answer): The response from DialogAgent containing
                a boolean 'ready_for_next_question' and the latest user_input.
        """
        if agent_responce.extracted_data is not None:
            self.chat_state_manager.update_answer(
                user_id,
                agent_responce.extracted_data,
            )

        if agent_responce.ready_for_next_question:
            self.chat_state_manager.finish_question(user_id)
