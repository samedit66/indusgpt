from __future__ import annotations
from typing import Any

from src.dialog_agent import (
    DialogAgent,
)
from src.chat_manager.chat_context import (
    ChatContext,
    default_context,
)
from src.chat_manager.info_extractor import (
    InfoExtactor,
    UserInformation,
)


class ChatManager:
    """
    Manages a user's multi-step chat session: prompts questions, collects answers,
    extracts final data, and triggers callbacks with the assembled information.
    """

    def __init__(self, **agent_kwargs) -> None:
        """
        Initialize DialogAgent, InfoExtractor, and in-memory Storage.

        Args:
            **agent_kwargs: forwarded to DialogAgent and InfoExtractor.
        """
        self._dialog_agent = DialogAgent(**agent_kwargs)
        self._extractor = InfoExtactor(**agent_kwargs)
        self._storage = Storage()
        self._callbacks = []

    def is_talking_with(self, user_id) -> bool:
        """
        Check if a chat context exists for the given user.

        Args:
            user_id: identifier for the session.

        Returns:
            True if the user has an active context, False otherwise.
        """
        return self._storage.contains(user_id)

    def reply(self, user_id: Any, user_input: str) -> str:
        """
        Process incoming message, advance the dialog, and return the agent's response.

        Workflow:
          1. Retrieve or create chat context for user_id.
          2. If awaiting an answer:
             a. Send user_input plus question info to DialogAgent.
             b. If agent signals readiness, store extracted answer.
          3. If more questions remain, return agent's prompt/answer.
          4. Otherwise, compile all answers, clear context, extract structured data,
             invoke callbacks, and return final message.

        Args:
            user_id: session identifier.
            user_input: text from the user.

        Returns:
            Agent's reply, which may include the next question or a closing message.
        """
        # 1. Load or init context
        context = self._storage.get(user_id)

        # 2. If a question is pending, handle answer
        reply_text = None
        if context.current_question is not None:
            question = context.current_question.text
            requirement = context.current_question.requirement
            next_question = (
                context.next_question.text if context.next_question else None
            )

            answer = self._dialog_agent.reply(
                user_input, question, requirement, next_question
            )
            reply_text = answer.text

            if answer.ready_for_next_question:
                context.record_answer(answer.extracted_data)
                self._storage.set(user_id, context)

        # 3. Continue with next question if any
        if context.has_more_questions():
            return reply_text

        # 4. Finalize when all questions answered
        all_answers = context.get_answers()
        self._storage.clear(user_id)

        concatenated = "\n".join(qa["answer"] for qa in all_answers)
        integration_info = self._extractor.extract(concatenated)
        self._notify_callbacks(user_id, integration_info)
        return reply_text

    def _notify_callbacks(self, user_id, user_info: UserInformation) -> None:
        """
        Invoke all registered callbacks with collected user information.

        Args:
            user_id: session identifier whose data is ready.
            user_info: structured data extracted from answers.
        """
        for callback in self._callbacks:
            callback(user_id, user_info)

    def current_question(self, user_id: Any) -> str:
        """
        Get the text of the next pending question for the user.

        Args:
            user_id: session identifier.

        Returns:
            The question text.
        """
        return self._storage.get(user_id).current_question.text

    def on_info_ready(self, callback=None):
        """
        Register a function to receive final user data when ready.

        Usage:
          - As decorator: @chat_manager.on_info_ready()
          - Direct: chat_manager.on_info_ready(func)

        The callback will be called as callback(user_id, integration_info).

        Args:
            callback: optional function to register immediately.

        Returns:
            The original function when used as decorator or callback.
        """
        if callback:
            self._callbacks.append(callback)
            return callback

        def decorator(func):
            self._callbacks.append(func)
            return func

        return decorator

    @property
    def intro(self) -> str:
        """
        Text of the offer we provide to users.

        Exists in case when this information needs to be sent automatically.

        Returns:
            Text of the offer.
        """
        return """
Hi brother!  
Thanks for reaching out 🙏  

**We work with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions.**  
We are looking to **buy or rent corporate accounts in India** that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.  
We are ready for long-term cooperation and offer **up to 5% of the profit** for stable account performance.  
_For example: ₹500,000 daily volume = ₹25,000 your share (5%)._  

---

## 🛠️ Our Work Process

1. **Access to PSP account**  
   - You share the login + password (e.g. Razorpay)  
   - We review dashboard, limits, API access, status  

2. **Website check**  
   - If already available — great, we’ll need hosting access  
   - If not — we’ll create a bridge website (services, education, consulting, etc.)  

3. **Submit for moderation**  
   - We use your account + our site  
   - Fill forms, upload docs, complete verification  

4. **API integration**  
   - Our dev team integrates PSP to our backend  
   - We test deposit flow, webhook, and transaction statuses  

5. **Start working**  
   - Begin with small volumes, check stability  
   - If everything is good — we scale  

---
If you’re ready:

- **Share PSP login + password**
- **Let us know if you already have a website**  
  - → *If yes* — provide hosting access  
  - → *If not* — we’ll handle it
- **Confirm if you can provide company documents**  
  - GST, PAN, etc.

---

Let’s build a **strong** and **profitable** partnership 💪

> ❗️ **PLEASE WRITE AND ANSWER ALL THE QUESTIONS!**  
> So that our communication and work is productive.  
> *If you answer all the questions — I will reply to you.*
"""


class Storage:
    """
    In‑memory storage of ChatContext objects by user_id.
    Automatically initializes a context if none exists.
    """

    def __init__(self) -> None:
        self._store: dict[Any, ChatContext] = {}

    def contains(self, user_id) -> bool:
        return user_id in self._store

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
