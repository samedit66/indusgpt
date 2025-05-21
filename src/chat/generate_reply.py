from .simple_agent import SimpleAgent

from .generate_response import ResponseToUser
from .chat_state import State, StateType


INSTRUCTIONS = """
You are a natural language reply generator that produces friendly, natural-sounding responses.

TONE:
- Casual & friendly "bro" style while maintaining professionalism
- Direct and concise
- Respectful at all times

RESPONSE STRUCTURE:
1. Maintain key information from original response while adjusting phrasing as needed
2. For partial answers: modify follow-up to ask only missing details
3. For completed questions: exclude "move to next" phrases
4. Never repeat questions about information already provided
5. Response should not be long, 4-5 sentences max
6. Exclude any carriage returns or other formatting

FORMAT RULES:
- No Markdown formatting
- Keep responses brief and to the point
- No mocking or arguing
- No questions except follow-ups when needed
"""


async def generate_reply(response: ResponseToUser, state: State) -> str:
    prompt = f"Tell user the following: {response.response_text}"
    match state.type:
        case StateType.IN_PROGRESS:
            prompt += f"Include a follow-up question in the reply. Question: '{state.question}'"
        case StateType.FINISHED:
            prompt += "Add a polite message that you need to check the information and get back to the user."

    return await reply_generator(prompt)


reply_generator = SimpleAgent(instructions=INSTRUCTIONS)
