from __future__ import annotations
from typing import Literal
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from src.agent import Agent
from src.validator import Validator, ValidationResult


QUERY_TEMPLATE = "Q: {}\nA:"


class Router:

    def __init__(self, **kwargs) -> None:
        self._router = Agent(
            instructions=router_instructions(),
            **kwargs,
        )
        self._validator = Validator(**kwargs)

    def classify(self, user_input: str) -> UserIntent:
        user_intent = self._router.chat(
            user_input=QUERY_TEMPLATE.format(user_input),
            output_type=UserIntent,
        )
        return user_intent


class UserIntent(BaseModel):
    user_input: str = Field(
        ..., description="The exact text message received from the user."
    )
    category: Literal["faq", "information"] = Field(
        ..., description="Category of user input."
    )
    reasoning: str = Field(
        ..., description="Consice reasoning why you selected `category`."
    )


@lru_cache
def router_instructions() -> str:
    instructions = f"""
You must classify each user input into one of two categories — `faq` or `information`
Respond **only** with the category name and explanation why you chose the selected category.

---
{classification_rules()}
"""
    return instructions


@lru_cache
def classification_rules() -> str:
    rules_text = (Path(__file__).parent / "classification_rules.md").read_text()
    return rules_text
