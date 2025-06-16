from __future__ import annotations
from typing import Literal, Union
import logging

from pydantic import BaseModel, Field

from src import types

from .simple_agent import SimpleAgent


INSTRUCTIONS = """
# Validator Agent Instructions

You are a validator agent. Your task is to assess whether the combined conversation context and the user’s current input satisfy the answer requirements for the question.

## Return one of:
- **yes** — fully meets the requirement  
- **needs more details** — partially meets the requirement  
- **no** — does not meet the requirement  

## Process
1. Review **both** the conversation context **and** the user’s current input.  
2. Compare them against the **answer requirement** for the question.  
3. If the user’s response (possibly spread over multiple messages) fully satisfies the requirement, return **yes** and **extract only the answer**.  
4. If it partially satisfies the requirement, return **needs more details**.  
5. If it does not satisfy the requirement at all, return **no**.  
6. Only ask for clarification if you **cannot** infer and extract a valid answer from the combined context and input.  

**Note:**
- Users may split their answer across several messages. Always read the entire chat history before deciding.
- Always try infer information before telling "needs more details" or "no" - user probably said what you need already.

**Examples:**
1. You have to validate the following:
   Context of conversation:
   - Question: 'Do you have corporate (business) accounts? In which banks?'
   - User responded: 'Hdfc'
   - Requirement: 'User must tell the bank name and share agreemnet/say yes/confirm they have a corporate account'.
   User's input: 'Yes I Have Corporate Account'.
   Validation result:
       User mentioned 'HDFC' bank which indicates that they have an account there.
       Later user told us that they have a corporate account.
       That means that they successfully answered: bank name told, corporate account confimed (all according to the requirement).
2. You have to validate the following:
   Context of conversation:
   - Question: 'Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?'
   - User responded: 'Cashfree'
   - Requirement: 'User response **must** confirm they have a connected PSP and include the PSP name'.
   Validation result:
       User mentioned alone 'Cashfree' which indicates that they have an account there.
       So, explicit confirmation is not required.
       That means that they successfully answered: PSP name told and confirmed.
3. You have to validate the following:
   Context of conversation:
   - Question: 'Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?'
   - User responded: 'Cashfree'
   - Requirement: 'User response **must** confirm they have a connected PSP and include the PSP name'.
   Validation result:
       User mentioned alone 'Cashfree' which indicates that they have an account there.
       So, explicit confirmation is not required.
       That means that they successfully answered: PSP name told and confirmed.
4. You have to validate the following:
   Context of conversation:
   - Question: 'Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?'
   - User responded: 'Ok'
   - Requirement: 'User response **must** confirm they have a connected PSP and include the PSP name'.
   Validation result:
       User just told 'Ok' which is invalid because we cannot determine if they really have a PSP connected.
       That means that they failed to response and provide any useful information.
"""


class ValidationResult(BaseModel):
    user_input: str = Field(..., description="Exact user answer.")
    question: str = Field(..., description="Question for user.")
    is_valid: Union[ValidAnswer, NeedsMoreDetails, InvalidAnswer] = Field(
        ..., description="Validation result."
    )


class ValidAnswer(BaseModel):
    answer_kind: Literal["Valid."]
    extracted_user_answer: str = Field(
        ...,
        description=(
            "Consice and concrete user's answer "
            "to the given question starting with 'User responded that...'."
        ),
    )


class NeedsMoreDetails(BaseModel):
    answer_kind: Literal["Needs more details."]
    reason_why_incomplete: str = Field(
        ...,
        description=(
            "Explanation why the user's answer does not fully complete the given question."
        ),
    )


class InvalidAnswer(BaseModel):
    answer_kind: Literal["Invalid."]
    reason_why_invalid: str = Field(
        ...,
        description="Explanation why the user's answer doesn't correspond to the given question.",
    )


logger = logging.getLogger(__name__)


def expand_query(
    user_input: str,
    question: types.Question,
    context: str | None = None,
    instructions: str | None = None,
) -> str:
    query = f"""
**Context of conversation (messages that were in the chat earlier):**  
{context}
Quesiton: "{question.text}"
User responded: "{user_input}"

**Requirement:**  
"{question.answer_requirement}"

Analyze and validate the whole context of conversation.
It's important to validate the whole context because user's may answer partially across several messages.
If answer to the question can be inferred from the whole context, infer it, and extract information which is needed by the requirement.
If you cannot infer the needed information from the context, explain why, but try your best to infer it.
"""
    if instructions:
        prompt = (
            f"**Strictly follow these instructions before validating**:\n{instructions}"
        )
        query = prompt + "\n\n" + query
    logging.info(f"Validator query\n{query!r}\n")
    return query


validator = SimpleAgent(
    instructions=INSTRUCTIONS,
    expand_query=expand_query,
    output_type=ValidationResult,
)
