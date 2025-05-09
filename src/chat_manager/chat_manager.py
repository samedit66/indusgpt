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
    UserInformation,
)


class ChatManager:
    """
    Orchestrates per‑user ChatContext, DialogAgent interactions, and InfoExtractor usage.
    Manages conversation flow: asking questions, recording answers, extracting final data,
    and generating a closing reply.
    """

    def __init__(self, **agent_kwargs) -> None:
        self._dialog_agent = DialogAgent(**agent_kwargs)
        self._extractor = InfoExtactor(**agent_kwargs)
        self._storage = Storage()
        self._callbacks = []

    def reply(self, user_id: Any, user_input: str) -> str:
        """
        Process a user's message and return the agent's reply.

        Workflow:
        1. Load or initialize the ChatContext for `user_id`.
        2. If the context has a pending question:
           - Forward `user_input` along with the current question text and requirement
             to the DialogAgent.
           - Capture the agent's answer text.
           - If the answer indicates readiness for the next question, record
             the extracted data in the context and persist the updated context.
        3. If there are still unanswered questions:
           - Return the agent's answer followed by the next question text.
        4. Otherwise (no more questions):
           - Gather all recorded answers.
           - Clear the stored context for the user.
           - Concatenate answers into a single string.
           - Extract structured `integration_info` via the InfoExtractor.
           - Append a random goodbye phrase.
           - Return the final reply text.

        Args:
            user_id:       Unique identifier for the user/session.
            user_input:    The latest message from the user.

        Returns:
            A string containing the agent's reply, which may include:
              - The next question to ask.
              - A closing message with a goodbye phrase once all questions are answered.
        """
        # 1. Load (or auto‑init) context
        context = self._storage.get(user_id)

        # 2. If there’s a pending question, record the answer
        reply_text = None
        if context.current_question is not None:
            question, requirement = (
                context.current_question.text,
                context.current_question.requirement,
            )
            next_question = (
                context.next_question.text
                if context.next_question else None
            )

            answer = self._dialog_agent.reply(
                user_input,
                question,
                requirement,
                next_question,
            )
            reply_text = answer.text

            if answer.ready_for_next_question:
                context.record_answer(answer.extracted_data)
                self._storage.set(user_id, context)

        # 3. If more questions remain, just return the answer
        if context.has_more_questions():
            assert reply_text is not None, (
                "More questions implies that reply_text is not None, how that happened?"
            )
            return reply_text

        # 4. Otherwise, process all answers and extract info
        all_answers = context.get_answers()
        self._storage.clear(user_id)

        text_information = "\n".join(qa["answer"] for qa in all_answers)
        user_info = self._extractor.extract(text_information)
        self._notify_callbacks(user_id, user_info)
        return reply_text

    def _notify_callbacks(self, user_id, user_info: UserInformation) -> None:
        for callback in self._callbacks:
            callback(user_id, user_info)

    def current_question(self, user_id: Any) -> str:
        """
        Return the text of the user's current pending question.
        """
        return self._storage.get(user_id).current_question.text

    def on_info_ready(self, callback=None):
        """
        Register a callback to be invoked when integration info is ready.

        Can be used either as a decorator or by passing the callback directly.

        The callback will be called with two arguments:
          - user_id: the identifier of the user whose data was collected
          - integration_info: extracted integration data

        Usage:

        1. As a decorator:

            ```python
            @chat_manager.on_info_ready()
            def handle_info(user_id, integration_info):
                # process integration_info...
            ```

        2. By passing the function directly:

            ```python
            def handle_info(user_id, integration_info):
                # process integration_info...

            chat_manager.on_info_ready(handle_info)
            ```
        """
        # If used as direct registration
        if callback is not None:
            self._callbacks.append(callback)
            return callback

        # If used as a decorator
        def decorator(func):
            self._callbacks.append(func)
            return func

        return decorator

    @property
    def intro(self) -> str:
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
