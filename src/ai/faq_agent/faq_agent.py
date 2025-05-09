from __future__ import annotations
from functools import lru_cache
from pathlib import Path

from src.ai.src.agent import Agent


QUERY_TEMPLATE = """
User was asked the following question: '{}'.
They replied: '{}'.
"""


class FAQAgent:
    def __init__(self, **kwargs) -> None:
        self._faq_agent = Agent(
            instructions=faq_instructions(),
            **kwargs,
        )

    def reply(self, user_input: str, question: str) -> str:
        return self._faq_agent.chat(
            user_input=QUERY_TEMPLATE.format(question, user_input),
        )


@lru_cache
def faq_instructions() -> str:
    instructions = f"""
You are an FAQ agent that answers user questions.
Your job is to give direct, casual (“Bro”) replies to users' request.
---

# Conversation Rules  
- Use casual, friendly “Bro” tone, but stay firm and concise.  
- Don’t over-explain—stick to the templates below.
- If the user asks about your identity (name, age), respond that it's beyond conversation.
- YOU REPLY **WITHOUT** 'A:' AT START!
- **DO NOT USE MARKDOWN IN YOUR RESPONSES**!
---

{faq()}
"""
    return instructions


@lru_cache
def faq() -> str:
    faq_text = (Path(__file__).parent / "faq.md").read_text()
    return faq_text
