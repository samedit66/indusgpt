from __future__ import annotations
from typing import Literal, Union

from pydantic import BaseModel, Field

from src.ai.agent import Agent
from src.ai.router.router import Router, Intent
from src.ai.faq_agent import FAQAgent, faq
from src.ai.dialog_agent.answer_generator import AnswerGenerator
from src.ai.dialog_agent.introduction import introduction


class DialogAgent:
    def __init__(self, **kwargs) -> None:
        self._kwargs = kwargs
        self._router = Router(**kwargs)
        self._faq_agent = FAQAgent(**kwargs)
        self._answer_generator = AnswerGenerator(**kwargs)
        self._requests_splitter = Agent(
            instructions="You split user input into separate requests. "
            "Each request should be a single question or answer. "
            "If the user input is a single question or answer, return it as is. "
            "If the user input is empty, return an empty list.",
            **kwargs,
        )

    async def reply(
        self,
        user_input: str,
        question: str,
        val_rule: str,
        next_question: str | None = None,
    ) -> Answer:
        """
        Process user input and generate a response.

        Args:
            user_input: The user's input message.
            question: The question to be asked.
            val_rule: The validation rule for the answer.
            next_question: The next question to be asked (if any).

        Returns:
            An Answer object containing the generated response.
        """
        # 1. Split into atomic requests
        splitter_prompt = (
            f"Split user input into separate requests.\nUser input: '{user_input}'"
        )
        requests = await self._requests_splitter.chat(
            splitter_prompt,
            output_type=Requests,
        )

        # 2. Handle each slice
        raw_parts = []
        extracted_data = []
        ready_for_next = False

        for req in requests.requests:
            ans = await self._single_reply(req, question, val_rule, next_question)
            raw_parts.append(f"User request: '{req}'\nAnswer: '{ans.text}'\n\n")

            if ans.extracted_data:
                extracted_data.append(ans.extracted_data)
            if ans.ready_for_next_question:
                ready_for_next = True

        # 3. Combine the raw pieces
        combined_text = "\n".join(raw_parts)
        combined_data = "\n".join(extracted_data) if extracted_data else None

        # 4. Polish with the AnswerGenerator
        polish_prompt = (
            "Please merge the following individual replies into one concise, coherent, and friendly message: "
            "- Preserve any prompts for a next question at the end. "
            "- If a reply shows that the user has already answered the asked question, remove any restatement of that question. "
            f"Asked question: {question}\n"
            "Replies:\n\n"
            f"{combined_text}"
        )
        polished = await self._answer_generator.generate_answer(polish_prompt)

        # 5. Return the polished answer
        return Answer(
            text=polished,
            ready_for_next_question=ready_for_next,
            extracted_data=combined_data,
        )

    async def _single_reply(
        self,
        user_input: str,
        question: str,
        val_rule: str,
        next_question: str | None = None,
    ) -> Answer:
        intent = await self._router.classify(user_input)
        match intent:
            case Intent(category="start"):
                return await self._generate_greeting(user_input)
            case Intent(category="faq"):
                return await self._generate_faq_answer(user_input, question)
            case Intent(category="information"):
                return await self._generate_question_answer(
                    intent, question, val_rule, next_question
                )

    async def _generate_greeting(self, user_input: str) -> Answer:
        query_template = f"""
You greet the user and provide him with **FULL** information described in Introduction.
The last paragraph should be a gentle asking to start the dialog and answer the first question.
User input: '{user_input}'
---
# Last paragraph example
Let’s build a strong and profitable partnership 💪
Please answer the following questions one by one.
Do you have corporate/business accounts? In which banks?

---

# Introduction
{introduction()}
---

# Required Questions
1. Do you have corporate/business accounts? In which banks?  
2. Are they connected to any PSP (Razorpay, Cashfree, PayU, etc.)?  
3. Can you provide login and password access to the PSP account?  
4. Do you already have a website approved by the PSP?  
  → If yes — please give us hosting access (we may need to adjust code or API)  
  → If not — we will create the website ourselves  
5. Are you open to working under a profit-sharing model instead of just a one-time deal?
"""
        return Answer(
            text=await self._answer_generator.generate_answer(query_template),
            ready_for_next_question=True,
            extracted_data=None,
        )

    async def _generate_faq_answer(self, user_input: str, question: str) -> Answer:
        return Answer(
            text=await self._faq_agent.reply(user_input, question),
            ready_for_next_question=False,
            extracted_data=None,
        )

    async def _validate(
        self,
        user_input: str,
        question: str,
        model_reason: str,
        validation_rule: str,
    ) -> ValidationResult:
        validator = Agent(
            instructions=f"""
You work in the company which works with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions.
The company is looking to buy or rent corporate accounts in India that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.

You do validation of user answers according to the given question.
When validation is okay, you extract asked data from the user answer.
Extracted data should be as concrete as possible.
---

Look to FAQ if you are not sure:
{faq()}
""",
            **self._kwargs,
        )

        query_template = f"""
Evaluate the following user response: '{user_input}'
Question: '{question}'
Analysis from another agent: '{model_reason}'
Validation criteria: '{validation_rule}'
Does the user's response appropriately address the question and meet the validation criteria?
Provide a 'yes' or 'no' answer, followed by a brief explanation.
"""
        val_result = await validator.chat(
            user_input=query_template,
            output_type=ValidationResult,
        )
        return val_result

    async def _generate_question_answer(
        self,
        intent: Intent,
        question: str,
        val_rule: str,
        next_question: str | None = None,
    ) -> Answer:
        val_result = await self._validate(
            intent.user_input,
            question,
            intent.reasoning,
            val_rule,
        )

        ready_for_next_question = False
        extracted_data = None
        if val_result.user_answered_properly():
            ready_for_next_question = True
            extracted_data = val_result.is_valid_user_answer.extracted_data
            prompt = (
                "User succesfully provided required information. "
                f"Their answer: {extracted_data}. "
            )

            if next_question:
                prompt += f"Include next question into your reply: '{next_question}'"
            else:
                prompt += """
Include into your reply information that you've received everything you need
and that you're going to check/analyze/verify and talk back soon.
"""
        else:
            if isinstance(val_result.is_valid_user_answer, NoAnswer):
                postfix = f"Analysis from other agent: '{val_result.is_valid_user_answer.reason_why_invalid}'"
            else:
                postfix = (
                    f"Asked question: '{question}'\nUser input: '{intent.user_input}'"
                )
            prompt = (
                "Seems like the user didn't provide a correct answer or wishes to stop the dialogue.\n"
                "If user answer looks like it could be an answer, but not precise, tell him to answer more precisely.\n"
                + postfix
            )

        answer = await self._answer_generator.generate_answer(prompt)
        return Answer(
            text=answer,
            ready_for_next_question=ready_for_next_question,
            extracted_data=extracted_data,
        )


class Requests(BaseModel):
    requests: list[str] = Field(
        ...,
        description="List of user requests to be processed. They may include questions, answers, or other types of messages.",
    )


class Answer(BaseModel):
    text: str
    ready_for_next_question: bool
    extracted_data: Union[str, None]


class ValidationResult(BaseModel):
    question: str = Field(..., description="Exact question for user.")
    user_answer: str = Field(..., description="Exact user answer.")
    is_valid_user_answer: Union[YesAnswer, NoAnswer] = Field(
        ..., description="Validation result."
    )
    wants_to_continue: WantsToContinue = Field(
        ..., description="User's desire to conitnue the dialogue."
    )

    def user_answered_properly(self) -> bool:
        return (
            self.wants_to_continue.status
            and self.is_valid_user_answer.answer_kind == "yes"
        )


class YesAnswer(BaseModel):
    answer_kind: Literal["yes"]
    extracted_data: str = Field(
        ...,
        description="Consice and concrete user answer to the given question starting with 'User responded that...'.",
    )


class NoAnswer(BaseModel):
    answer_kind: Literal["no"]
    reason_why_invalid: str = Field(
        ...,
        description="Explanation why the user answer doesn't correspond to the given question.",
    )


class WantsToContinue(BaseModel):
    status: bool = Field(..., description="Does the user want to continue?")
    reasoning: str = Field(
        ..., description="Explanation why the user wants or not to continue."
    )
