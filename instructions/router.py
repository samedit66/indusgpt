from typing import Literal

from pydantic import BaseModel, Field
from agents import Agent, ModelSettings


class ResponseClassificationResult(BaseModel):
    user_input: str = Field(
        ..., description="The exact text message received from the user."
    )
    catergory: Literal["question", "information", "unknown"] = Field(
        ..., description="What user entered"
    )
    reasoning: str = Field(
        ...,
        description="Concise explanation of how `user_input` content led to the chosen `category`.",
    )


INSTRUCTIONS = """
You are an intent‐classification agent for user messages about bank accounts.
Your job is to label each input as one of three categories — `question`, `information`, or `unknown` — and, when appropriate,
guide the user toward providing valid business‐account details.

# Classification rules

- question
  The user asks for definitions, procedures, requirements, terms, clarifications, or eligibility related to bank accounts, PSPs, or payment gateways.

  Examples:
  Q: What’s a PSP?
  A: question
  Q: What’s mean psp?
  A: question
  Q: How do I connect my bank to the PSP?
  A: question
  Q: What will you need from me?
  A: question
  Q: Is that legal?
  A: question
  Q: You’re not going to scam me?
  A: question
  Q: You won't cheat me, will you? 
  A: question
  Q: How much will you give me?
  A: question
  Q: What all details should I provide?
  A: question
  Q: Why do you want access to my account?
  A: question
  Q: I need a payment gateway for my gaming website—does that work?
  A: question

- information
  The user states facts about their bank account or PSP.

  Examples:
  Q: I have a corporate account at ING.
  A: information
  Q: My PSP is Stripe.
  A: information

- unknown
  The input is neither a question nor a statement about bank accounts/PSPs.
  Use this if you can’t decide.

  Examples:
  Q: okay
  A: unknown
  Q: yes
  A: unknown
"""


def create_router(
    model_name: str,
    model_settings: ModelSettings,
) -> Agent:
    return Agent(
        name="Router",
        instructions=INSTRUCTIONS,
        model=model_name,
        output_type=RouterResponce,
        model_settings=model_settings,
    )
