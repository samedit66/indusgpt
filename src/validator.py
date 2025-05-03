from __future__ import annotations
from typing import Literal, Union

from pydantic import BaseModel, Field

from src.agent import Agent


class Validator:
    
    def __init__(self, **kwargs) -> None:
        instructions = (
            "You are a validator that checks if an agent's response correctly follows "
            "the given instructions. "
            "Answer only in JSON with two fields:\n"
            "  - is_model_answer_correct: an object with:\n"
            "      * answer_kind: \"Yes\" or \"No\"\n"
            "      * reasoning: a brief explanation.\n"
            "Do NOT include any extra keys or prose."
        )
        self._validator = Agent(
            instructions=instructions,
            **kwargs,
        )

    def validate(self, model_response: str, agent_instructions: str) -> ValidationResult:
        user_input = (
            f"Instructions:\n{agent_instructions}\n\n"
            f"Agent response:\n{model_response}\n\n"
            "Does the response follow the instructions?"
        )

        return self._validator.chat(
            user_input,
            output_type=ValidationResult,
        )
    
    @staticmethod
    def guided_prompt(
        user_input: str,
        model_response: str,
    ) -> str:
        prompt = (
            "You attempted to follow instructions but made a mistake.\n\n"
            "User input that caused the error:\n"
            f"{user_input}\n\n"
            "Your (incorrect) response:\n"
            f"{model_response}\n\n"
            "Please identify which parts of the original instructions the agent overlooked "
            "or misunderstood, and suggest precise clarifications or additions so the agent "
            "will correctly handle this example. Keep the overall instruction structure intact.\n\n"
        )
        return prompt


class ValidationResult(BaseModel):
    is_model_answer_correct: Union[YesAnswer, NoAnswer] = Field(
        ..., description="Validation result."
    )

    def is_okay(self) -> bool:
        return self.is_model_answer_correct.answer_kind == "Yes"


class YesAnswer(BaseModel):
    answer_kind: Literal["Yes"]
    reasoning: str


class NoAnswer(BaseModel):
    answer_kind: Literal["No"]
    reasoning: str
