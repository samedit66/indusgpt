from __future__ import annotations
from typing import Literal, Union

from pydantic import BaseModel, Field

from src import types

from .simple_agent import SimpleAgent


INSTRUCTIONS = """
You are a validator agent.
Your task is to validate information provided by user to the given question.
Assess it against the question and requirements.

Return one of:
  • yes — fully meets the requirement
  • needs more details — partially meets it
  • no — does not meet it

Provide a concise rationale.
If the answer is valid or partially valid, extract the needed data.
"""


class ValidationResult(BaseModel):
    user_input: str = Field(..., description="Exact user answer.")
    question: str = Field(..., description="Question for user.")
    is_valid: Union[ValidAnswer, NeedsMoreDetails, InvalidAnswer] = Field(
        ..., description="Validation result."
    )


class ValidAnswer(BaseModel):
    answer_kind: Literal["Valid."]
    extracted_data: str = Field(
        ...,
        description=(
            "Consice and concrete user's answer "
            "to the given question starting with 'User responded that...'."
        ),
    )


class NeedsMoreDetails(BaseModel):
    answer_kind: Literal["Needs more details."]
    extracted_data: str = Field(
        ...,
        description=(
            "Consice and concrete partial user's answer "
            "to the given question starting with 'User responded that...'."
        ),
    )
    reason_why_incomplete: str = Field(
        ...,
        description=(
            "Explanation why the user's answer does not fully complete the given question."
        ),
    )


class InvalidAnswer(BaseModel):
    answer_kind: Literal["Invalid."]
    extracted_data: None = Field(
        None, description="No data was extracted from the user input."
    )
    reason_why_invalid: str = Field(
        ...,
        description="Explanation why the user's answer doesn't correspond to the given question.",
    )


def expand_query(
    user_input: str,
    question: types.Question,
    context: str,
    instructions: str | None = None,
) -> str:
    query = f"""
User was asked: {question.text}.
Requirement: {question.answer_requirement}
Earlier we found out that: {context}.
Using that information and the current user's answer '{user_input}', validate it.
Do not validate only user answer, validate both combined what we found out about user earlier and the current user's answer.
Do not be too strict, infer required information.

Try to infer information from text - if user provides 'Yes', 'Ok' or 'No' he may have answered the question.
wich already asked and partially answered.
Correct examples:
1. Context: User respnonded that they have Paytm connected but you are unsure is that really a PSP.
   The asked question:
   Hey bro, you mentioned Paytm as a PSP before, but I need you to confirm it again and name the PSP clearly. Also, are your corporate accounts connected to any other PSPs like Razorpay, Cashfree, PayU, or Getepay?
   User answer: Yes
   That means that user ANSWERED the question and they have Paytm as connected PSP.
2. Context: User responded that they have an account in SBI
   Question: Alright, bro, you've got the bank name down, but I need to know if it's a corporate account. Do you have corporate (business) accounts? If so, which banks are they with?
   User answer: Yes
   That means that user ANSWERED the question and told us that they have a corporate account in SBI.
"""
    if instructions:
        prompt = f"Strictly follow these instructions before validating: {instructions}"
        query = prompt + "\n\n" + query
    return query


validator = SimpleAgent(
    instructions=INSTRUCTIONS,
    expand_query=expand_query,
    output_type=ValidationResult,
)
