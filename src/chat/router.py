from typing import Literal

from pydantic import BaseModel, Field

from .simple_agent import SimpleAgent


INSTRUCTIONS = """
You must classify each user input into one of three categories — `start`, `faq` or `information`
Respond **only** with the category name and explanation why you chose the selected category.
Classify each user message into one of two categories:

1. **start**
2. **faq**  
3. **information**

Pay attention to the fact that users may not know English very well (see examples).
---

### 1. start

Label a message **start** if the user is greeting.
**Indicators**
- Contains a greeting word or phrase (e.g., “hello”, “hi”, “hey”, “good morning”, “good evening”).
- May include polite opening expressions (“how are you?”, “nice to meet you”, “greetings”).

**Examples**
- “Hello!”
- “Hi there!”
- “Hey, how’s it going?”
- “Good morning!”
- "Hii"
---

### 2. faq

Label a message **faq** if the user is asking for something or making any kind of request, reassurance even if it is not phrased as a question.

**Indicators**  
- The message asks a question (often ends with a question mark).  
- The message uses words like **how**, **what**, **when**, **where**, **who**, **why**, **can**, **is**, **are**, **please**, **tell me**, **show me**.  
- The user states a desire or need (e.g. “I want…”, “I need…”).  
- The user asks to perform an action on their behalf.
- The user may ask question in Hindi (e.g "Kay hai", "Ka hai" means "what is is?")

**Examples**  
- “What commission do you charge?”  
- “How do I connect my bank?”  
- “Is that legal?”  
- “Tell me details.”  
- “I want a 30% commission.”  
- “I don’t have a website—can I still sign up?"
- "Kay hai PSP"
- "PSP KAY HAY"
- "And I want to know, what business u do"
- "Current account also accept??
---

### 3. information

Label a message **information** if the user is just providing facts, confirmations, or any text that is not asking for anything.

**Indicators**  
- The message states a fact or status.  
- The message gives personal or login data.  
- The message acknowledges or confirms something.  
- The message is random or non‑sense text.

**Examples**  
- “I have a business account at HSBC.”  
- “My username is user123.”  
- “Okay.”  
- “Thanks.” 
- "Esaf connect with Gatepay"
- “xyz”  
- “u”
- “t”
"""


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


def expand_query(
    user_input: str, context: str | None = None, instructions: str | None = None
) -> str:
    query = f"Take into account the context: {context}.\nClassify the following user request: {user_input}"
    if instructions:
        query = f"Strictly follow these instructions before classifying: {instructions}\n\n{query}"
    return query


router = SimpleAgent(
    instructions=INSTRUCTIONS,
    expand_query=expand_query,
    output_type=Intent,
)
