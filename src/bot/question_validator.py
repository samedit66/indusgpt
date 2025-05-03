from __future__ import annotations
from typing import Literal, Union

from pydantic import BaseModel, Field

from src.agent import Agent
from src.faq_agent.faq_agent import faq


class QuestionValidator:
    
    def __init__(self, **kwargs) -> str:
        self._validator = Agent(
            instructions=f"""
You work in the company which works with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions.
The company is looking to buy or rent corporate accounts in India that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.

You do validation of user answers according to the given question.
When validation is okay, you extract asked data from the user answer.
Extracted data should be as concrete as possible.
---

**Examples**
Correct:
- Q: I have a bisuness account in Sber -> extracted data is "bank account in sber"

Incorrect:
- Q: I have an account in bank -> no concrete data, invalid answer
---

Look to FAQ if you are not sure:
{faq()}
""",
            **kwargs
        )

    def validate(self, user_answer: str, question: str) -> ValidationResult:
        query_template = f"""
Does the user answer '{user_answer}' correspond to the given question '{question}'?
Tell me yes/no with brief explanation.
"""
        return self._validator.chat(query_template, output_type=ValidationResult)


class ValidationResult(BaseModel):
    question: str = Field(
        ..., description="Exact question for user."
    )
    user_answer: str = Field(
        ..., description="Exact user answer."
    )
    is_valid_user_answer: Union[YesAnswer, NoAnswer] = Field(
        ..., description="Validation result."
    )


class YesAnswer(BaseModel):
    answer_kind: Literal["yes"]
    extracted_data: str = Field(
        ..., description="Consice and concrete user answer to the given question."
    )


class NoAnswer(BaseModel):
    answer_kind: Literal["no"]
    reason_why_invalid: str = Field(
        ..., description="Brief explanation why the user answer is not correct according to the question."
    )
