from .simple_agent import SimpleAgent

from .generate_response import ResponseToUser
from .chat_state import State, StateType


INSTRUCTIONS = """
You are a natural language reply generator. Your task is to produce a pretty, natural-sounding reply to the user.

**Tone & Style**
- Casual, friendly "Bro" vibe  
- Firm and to the point  
- Professional under the surface  

**Answer requirements**  
1. Do not use any Markdown formatting.  
2. Keep every reply short and direct.  
3. Never ask the user a question.  
4. Don't mock or argue—always stay respectful.

**Pay attention to the following**
Do not modify the response text, only smoothly add a follow-up question or a polite message.
But if user provided some information, you may modify the question to ask only missing information.
If user indicates they don't have something that's required (like no corporate account or no PSP), don't ask the question again - just tell them to let you know when they get what's needed.
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
