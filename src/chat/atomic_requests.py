from pydantic import BaseModel, Field

from .simple_agent import SimpleAgent


class UserRequests(BaseModel):
    requests: list[str] = Field(..., description="The list of atomic requests")


INSTRUCTIONS = """
You are an atomic "information - questions" separator.
Your task is to break down a user's message into individual questions and information.

For example:
Input: "I have a corporate bank account, but what's mean PSP?"
Output: Two atomic requests:
1. Information: "I have a corporate bank account"
2. Question: "what's mean PSP?"

Input: "Login is admin, password is 12345"
Output: One atomic request:
1. "Login is admin, password is 12345"

Input: "Yes sir in ICICI bank"
Output: One atomic request:
1. "Yes sir in ICICI bank"

Input: "Сompany is BrrBrrPatapimi Address is Russia Moscow Phone numebr +7949329432 Email is samedit66@aaaaaa.ru"
Output: One atomic request:
1. "Сompany is BrrBrrPatapimi Address is Russia Moscow Phone numebr +7949329432 Email is samedit66@aaaaaa.ru"
Rationale: User provided information about the company, it's all related, so it's one request.

Input: - Company Name  TechnoInds
- Registered Address. Jaipur 
- Contact Phone Number 6200290578
- Email Address kumaraadesh7443@gmail.com
Output: One atomic request:
- Company Name  TechnoInds
- Registered Address. Jaipur 
- Contact Phone Number 6200290578
- Email Address kumaraadesh7443@gmail.com
Rationale: User provided information about the company, it's all related, so it's one request.

Rules:
1. Each atomic request should be self-contained and meaningful
2. Separate statements about different topics into different requests
3. Separate questions from statements
4. Keep context when needed
5. If a statement is a single atomic request, return it as is
6. Do not split a single atomic request into multiple requests:
   Related information should be in the same request:
   "Login is admin, password is 12345" -> "Login is admin, password is 12345"
   "Yes sir in ICICI bank" -> "Yes sir in ICICI bank"

Return a list of atomic requests, each as a separate string.
"""


atomic_separator = SimpleAgent(
    instructions=INSTRUCTIONS,
    output_type=UserRequests,
)
