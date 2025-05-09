from __future__ import annotations
from typing import Literal, Union

from pydantic import BaseModel, Field

from src.agent import Agent
from src.router.router import Router, Intent
from src.faq_agent import FAQAgent, faq
from src.dialog_agent.answer_generator import AnswerGenerator


class DialogAgent:
    def __init__(self, **kwargs) -> None:
        self._kwargs = kwargs
        self._router = Router(**kwargs)
        self._faq_agent = FAQAgent(**kwargs)
        self._answer_generator = AnswerGenerator(**kwargs)

    def reply(
        self,
        user_input: str,
        question: str,
        val_rule: str,
        next_question: str | None = None,
    ) -> Answer:
        intent = self._router.classify(user_input)
        match intent:
            case Intent(category="faq"):
                return self._generate_faq_answer(user_input, question)
            case Intent(category="information"):
                return self._generate_question_answer(
                    intent, question, val_rule, next_question
                )

    def _generate_faq_answer(self, user_input: str, question: str) -> Answer:
        return Answer(
            text=self._faq_agent.reply(user_input, question),
            ready_for_next_question=False,
            extracted_data=None,
        )

    def _validate(
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
        val_result = validator.chat(
            user_input=query_template,
            output_type=ValidationResult,
        )
        return val_result

    def _generate_question_answer(
        self,
        intent: Intent,
        question: str,
        val_rule: str,
        next_question: str | None = None,
    ) -> Answer:
        val_result = self._validate(
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
Include into your replay information that you've received everything you need
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
                "Seems like the user didn't provide a correct answer or wishes to stop the dialogue. "
                + postfix
            )

        answer = self._answer_generator.generate_answer(prompt)
        return Answer(
            text=answer,
            ready_for_next_question=ready_for_next_question,
            extracted_data=extracted_data,
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
