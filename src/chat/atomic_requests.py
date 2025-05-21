from pydantic import BaseModel, Field

from .simple_agent import SimpleAgent


class UserRequests(BaseModel):
    requests: list[str] = Field(..., description="The list of atomic requests")


INSTRUCTIONS = """
You are an atomic request separator.
Your task is to break down a user's message into individual atomic requests.

For example:
Input: "I have a corporate bank account, but what's mean PSP?"
Output: Two atomic requests:
1. "I have a corporate bank account"
2. "what's mean PSP?"

Input: "Login is admin, password is 12345"
Output: One atomic request:
1. "Login is admin, password is 12345"

Rules:
1. Each atomic request should be self-contained and meaningful
2. Separate statements about different topics into different requests
3. Separate questions from statements
4. Keep context when needed
5. If a statement is a single atomic request, return it as is
6. Do not split a single atomic request into multiple requests:
   Related information should be in the same request:
   "Login is admin, password is 12345" -> "Login is admin, password is 12345"

Return a list of atomic requests, each as a separate string.
"""


atomic_separator = SimpleAgent(
    instructions=INSTRUCTIONS,
    output_type=UserRequests,
)
