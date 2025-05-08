from __future__ import annotations
from typing import Any
import random

from src.dialog_agent import (
    DialogAgent,
)
from src.chat_manager.chat_context import (
    ChatContext,
    default_context,
)
from src.chat_manager.info_extractor import (
    InfoExtactor,
)


GOODBYE_PHRASES = [
    "I’ve received all the details—will review and be in touch soon!",
    "Got everything—checking now and will update you shortly!",
    "All data’s here—going through it and will get back ASAP!",
    "Thanks for the info—review in progress, talk soon!",
    "Received your answers—verifying now and will follow up!",
    "All set on my end—reviewing details and will reply shortly!",
]


class ChatManager:
    """
    Orchestrates per‑user ChatContext + the DialogAgent.
    """

    def __init__(self, **agent_kwargs) -> None:
        self._dialog_agent = DialogAgent(**agent_kwargs)
        self._extractor = InfoExtactor(**agent_kwargs)
        self._storage = Storage()

    def reply(self, user_id: Any, user_input: str) -> str:
        # 1. Load (or auto‑init) context
        context = self._storage.get(user_id)

        # 2. If there’s a pending question, record the answer
        reply_text = None
        if context.current_question is not None:
            question, requirement = (
                context.current_question.text,
                context.current_question.requirement,
            )
            answer = self._dialog_agent.reply(
                user_input,
                question,
                requirement,
            )
            reply_text = answer.text

            if answer.ready_for_next_question:
                context.record_answer(answer.extracted_data)
                self._storage.set(user_id, context)

        # 3. If more questions remain, just return the answer
        if context.has_more_questions():
            assert reply_text is not None, "More questions implies that reply_text is not None, how that happened?"
            return f"{reply_text}\n{self.current_question(user_id)}"

        # 4. Otherwise, process all answers and extract info
        all_answers = context.get_answers()
        self._storage.clear(user_id)

        text_information = "\n".join(qa["answer"] for qa in all_answers)
        integration_info = self._extractor.extract(text_information)
        # print(integration_info)

        goodbye = random.choice(GOODBYE_PHRASES)
        if reply_text is not None:
            reply_text += f"\n{goodbye}"
        else:
            reply_text = goodbye

        return reply_text

    def current_question(self, user_id: Any) -> str:
        return self._storage.get(user_id).current_question.text
    
    @property
    def intro(self) -> str:
        return """
Hi brother!  
Thanks for reaching out 🙏  
We work with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions.
We are looking to buy or rent corporate accounts in India that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.
We are ready for long-term cooperation and offer up to 5% of the profit for stable account performance. For example: ₹500,000 daily volume = ₹25,000 your share (5%).
"""


class Storage:
    """
    In‑memory storage of ChatContext objects by user_id.
    Automatically initializes a context if none exists.
    """

    def __init__(self) -> None:
        self._store: dict[Any, ChatContext] = {}

    def get(self, user_id: Any) -> ChatContext:
        """
        Return the existing ChatContext for user_id,
        or create & store a new one if not present.
        """
        if user_id not in self._store:
            self._store[user_id] = default_context()
        return self._store[user_id]

    def set(self, user_id: Any, context: ChatContext) -> None:
        self._store[user_id] = context

    def clear(self, user_id: Any) -> None:
        self._store.pop(user_id, None)
