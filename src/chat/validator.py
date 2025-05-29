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


def expand_query(user_input: str, question: types.Question, context: str) -> str:
    return f"""
User was asked: {question.text}.
Requirement: {question.answer_requirement}
Earlier we found out that: {context}.
Using that information and the current user's answer {user_input}, validate it.
Do not validate only user answer, validate
both combined what we found out about user earlier and the current user's answer.
Do not be too strict, infer required information.
If user is unsure about his answer, do not infer information - make user confirm.
"""


validator = SimpleAgent(
    instructions=INSTRUCTIONS,
    expand_query=expand_query,
    output_type=ValidationResult,
)
