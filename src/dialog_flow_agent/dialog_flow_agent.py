from __future__ import annotations
from typing import Literal, Union

from pydantic import BaseModel, Field

from src.agent import Agent
from src.router.router import Router
from src.faq_agent import FAQAgent, faq
from src.dialog_flow_agent.answer_generator import AnswerGenerator


class DialogFlowAgent:
    
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self._router = Router(**kwargs)
        self._faq_agent = FAQAgent(**kwargs)
        self._agenerator = AnswerGenerator(**kwargs)

    def respond(
        self,
        user_input: str,
        question: str,
        validation_rule: str,
    ) -> DialogFlowAgentAnswer:
        user_intent = self._router.classify(user_input)

        ready_for_next_question = False
        extracted_data = None
        match user_intent.category:
            case "faq":
                answer = self._faq_agent.respond(user_input)
            case "information":
                print(user_intent, end="\n\n")
                val_result = self._validate(user_input, question, user_intent.reasoning, validation_rule)
                print(val_result, end="\n\n")

                if val_result.is_valid_user_answer.answer_kind == "yes":
                    answer = self._agenerator.generate_answer(
                        "User succesfully responded correct."
                        f"Their answer: {val_result.is_valid_user_answer.extracted_data}"
                    )
                    extracted_data = val_result.is_valid_user_answer.extracted_data
                    ready_for_next_question = True
                else:
                    answer = self._agenerator.generate_answer(
                        val_result.is_valid_user_answer.reason_why_invalid
                    )
            case x:
                raise RuntimeError(f"This should not happen, got unknown category '{x}'")

        return DialogFlowAgentAnswer(
            answer=answer,
            ready_for_next_question=ready_for_next_question,
            extracted_data=extracted_data,
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
        **self.kwargs,
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


class DialogFlowAgentAnswer(BaseModel):
    answer: str
    ready_for_next_question: bool
    extracted_data: Union[str, None]
    

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
        ..., description="Consice and concrete user answer to the given question starting with 'User responded that...'."
    )


class NoAnswer(BaseModel):
    answer_kind: Literal["no"]
    reason_why_invalid: str = Field(
        ..., description="Explanation why the user answer doesn't correspond to the given question."
    )
