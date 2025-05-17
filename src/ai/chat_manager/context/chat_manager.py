from typing import Iterable

from src.ai.dialog_agent import (
    DialogAgent,
    Answer,
)

from .question_list import QuestionList
from .user_answer_storage import UserAnswerStorage
from .chat_state_manager import ChatStateManager, OnAllFinishedCallback


class ChatManager:
    """
    Manages a multi-step Q&A conversation.
    """

    def __init__(
        self,
        question_list: QuestionList,
        user_answer_storage: UserAnswerStorage,
        on_all_finished: Iterable[OnAllFinishedCallback] = None,
        **model_settings,
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
        self.dialog_agent = DialogAgent(**model_settings)
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
                questions have been answered.
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
        agent_answer = await self._talk(user_id, user_input)
        self._update_state(user_id, agent_answer)

        # Build the outgoing reply
        reply_text = self._build_reply_text(user_id, agent_answer.text)
        return reply_text

    async def _talk(self, user_id: int, user_input: str) -> Answer:
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
        question, partial_answer = self.chat_state_manager.current_state(user_id)
        prompt = prompt_for_dialog_agent(user_input, partial_answer)
        answer = await self.dialog_agent.reply(
            user_input=prompt,
            question=question.text,
            val_rule=question.answer_requirement,
        )
        return answer

    def _update_state(self, user_id: int, agent_answer: Answer) -> None:
        """
        Update the ChatStateManager based on whether the agent has indicated
        readiness to move to the next question or needs more user input.

        Args:
            user_id (int): Identifier of the user session.
            agent_answer (Answer): The response from DialogAgent containing
                a boolean 'ready_for_next_question' and the latest user_input.
        """
        if agent_answer.ready_for_next_question:
            self.chat_state_manager.finish_question(user_id)
            return

        partial_answer = f"{agent_answer.user_input}\n{agent_answer.extracted_data}\n"
        self.chat_state_manager.update_answer(
            user_id,
            partial_answer,
        )

    def _build_reply_text(self, user_id: int, agent_answer_text: str) -> str:
        """
        Combine the latest agent-generated text with either the next question
        prompt or a final closing message if all questions are answered.

        Args:
            user_id (int): Session identifier to check state progress.
            agent_answer_text (str): Text produced by the DialogAgent for this turn.

        Returns:
            str: A single string containing the agent's answer and the next
                question, or a well-formed closing paragraph once complete.
        """
        if not self.chat_state_manager.all_finished(user_id):
            next_q, _ = self.chat_state_manager.current_state(user_id)
            return f"{agent_answer_text}\n{next_q.text}"

        closing = (
            "Got all the info I need from you. "
            "I'll check everything out and get back to you soon. "
            "Looking forward to working together!"
        )
        separator = "" if agent_answer_text.endswith(".") else " "
        return f"{agent_answer_text}{separator}{closing}"


def prompt_for_dialog_agent(user_input: str, partial_answer: str | None) -> str:
    """
    Construct the input prompt for the DialogAgent by appending the latest user input
    to any existing partial answer from previous turns.

    Args:
        user_input (str): The new message provided by the user.
        partial_answer (str | None): Previously collected or partially generated text,
            which can provide context to the agent. If None, starts fresh.

    Returns:
        str: A unified prompt string combining partial_answer (if any) and user_input,
            separated by a newline.
    """
    prompt = partial_answer or ""
    prompt += f"\n{user_input}"
    return prompt
