from __future__ import annotations
from typing import Literal
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from src.ai.agent import Agent


QUERY_TEMPLATE = "Q: {}\nA:"


class Router:
    def __init__(self, **kwargs) -> None:
        self._router = Agent(
            instructions=router_instructions(),
            **kwargs,
        )

    async def classify(self, user_input: str) -> Intent:
        user_intent = await self._router.chat(
            user_input=QUERY_TEMPLATE.format(user_input),
            output_type=Intent,
        )
        return user_intent


class Intent(BaseModel):
    user_input: str = Field(
        ..., description="The exact text message received from the user."
    )
    category: Literal["faq", "information", "start"] = Field(
        ..., description="Category of user input."
    )
    reasoning: str = Field(
        ..., description="Consice reasoning why you selected `category`."
    )


@lru_cache
def router_instructions() -> str:
    instructions = f"""
You must classify each user input into one of three categories — `start`, `faq` or `information`
Respond **only** with the category name and explanation why you chose the selected category.

---
{classification_rules()}
"""
    return instructions


@lru_cache
def classification_rules() -> str:
    rules_text = (Path(__file__).parent / "classification_rules.md").read_text()
    return rules_text
