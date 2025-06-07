import logging
from typing import Callable, Iterable

from src import types

from .chat_state_manager import ChatStateManager
from .generate_response import ResponseToUser

type ResponseGenerator = Callable[[str, types.State], ResponseToUser]
"""
Callable which can generate a response to user.
Takes user input and current chat state.
Returns a `ResponseToUser`.
"""

type ReplyGenerator = Callable[[ResponseToUser, types.State], str]
"""
Callable which can produce a pretty reply to user.
Usually to get a pretty-looking reply you might want to add a next question,
or add a goodbye if conversation is finished -- more context needs to be provided.
This callable takes a `ResponeToUser` to enrich the context and current chat state.
Based on them, it returns a natural reply.
"""

logger = logging.getLogger(__name__)


class ChatManager:
    """
    Manages a multi-step Q&A conversation.
    """

    def __init__(
        self,
        question_list: types.QuestionList,
        user_answer_storage: types.UserAnswerStorage,
        context: types.Context,
        generate_response: ResponseGenerator,
        generate_reply: ReplyGenerator,
        on_all_finished: Iterable[types.QaProcessor] | None = None,
    ) -> None:
        """
        Initialize ChatManager with question sequence, persistence layer, and response generators.

        Args:
            question_list (QuestionList): An ordered collection of Question objects
                defining the conversation flow.
            user_answer_storage (UserAnswerStorage): A storage interface for saving or retrieving
                user-provided answers between sessions.
            context (Context): A storage interface for saving or retrieving
                context between sessions.
            generate_response (ResponseGenerator): A callable that generates responses to user input
                based on the current chat state.
            generate_reply (ReplyGenerator): A callable that produces natural language replies
                by enriching responses with context like next questions.
            on_all_finished (Iterable[OnAllFinishedCallback]): A list of callback functions
                to be executed when a user finishes all questions.
        """
        self.generate_response = generate_response
        self.generate_reply = generate_reply
        self.context = context
        self.chat_state_manager = ChatStateManager(
            question_list=question_list,
            user_answer_storage=user_answer_storage,
            on_all_finished=on_all_finished,
        )

    async def has_user_started(self, user_id: int) -> bool:
        return await self.chat_state_manager.has_user_started(user_id)

    async def is_user_talking(self, user_id: int) -> bool:
        return await self.chat_state_manager.has_user_started(
            user_id
        ) and not await self.chat_state_manager.all_finished(user_id)

    async def has_user_finished(self, user_id: int) -> bool:
        return await self.chat_state_manager.all_finished(user_id)

    async def qa_pairs(self, user_id: int) -> list[types.QaPair]:
        """
        Returns all Q&A pairs for a given user.

        :param user_id: identifier for the conversation participant
        :return: list of Q&A pairs
        """
        return await self.chat_state_manager.qa_pairs(user_id)

    async def current_question(self, user_id: int) -> str | None:
        """
        Retrieve the current question for a user without advancing the state.

        Args:
            user_id (int): Unique identifier for the user session.

        Returns:
            str | None: The text of the current question. Returns None if all
                questions have been answered or user is not registered.
        """
        if await self.chat_state_manager.all_finished(user_id):
            return None
        _, q, _ = await self.chat_state_manager.current_state(user_id)
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
        # If conversation is finished, no further replies
        if await self.chat_state_manager.has_user_started(
            user_id
        ) and await self.chat_state_manager.all_finished(user_id):
            return None

        # Invoke the dialog agent and update state
        agent_response = await self._talk(user_id, user_input)
        logger.info(f"Agent response: {agent_response!r}")
        await self._update_state(user_id, agent_response)

        # Build the outgoing reply
        current_state = await self.chat_state_manager.current_state(user_id)
        return await self.generate_reply(agent_response, current_state)

    async def stop_talking_with(self, user_id: int) -> None:
        await self.chat_state_manager.stop_talking_with(user_id)

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
        _, question, partial_answer = await self.chat_state_manager.current_state(
            user_id
        )
        instructions = await self.context.get()
        answer = await self.generate_response(
            user_input=user_input,
            question=question,
            context=partial_answer,
            instructions=instructions,
        )
        return answer

    async def _update_state(self, user_id: int, agent_responce: ResponseToUser) -> None:
        """
        Update the ChatStateManager based on whether the agent has indicated
        readiness to move to the next question or needs more user input.

        Args:
            user_id (int): Identifier of the user session.
            agent_answer (Answer): The response from DialogAgent containing
                a boolean 'ready_for_next_question' and the latest user_input.
        """
        current_question = await self.current_question(user_id)
        context = f"Question: '{current_question}'\nUser responded: '{agent_responce.user_input}'"

        if agent_responce.extracted_data is not None:
            context += f"\nInferred information from user response: {agent_responce.extracted_data}\n"

        context += "\n"
        await self.chat_state_manager.update_answer(user_id, context)
        if agent_responce.ready_for_next_question:
            await self.chat_state_manager.finish_question(user_id)

    async def learn(
        self,
        instructions: str,
        incorrect_example: str | None = None,
    ) -> None:
        """
        Learn new information about how to answer questions.
        """
        instructions_text = f"""
Your answers needs to be modified to fit the following instructions:
'{instructions}'
"""
        if incorrect_example:
            instructions_text += f"""
You last answer did not follow them, do not repeat the same mistakes:
'{incorrect_example}'
"""
        await self.context.append(instructions_text)
