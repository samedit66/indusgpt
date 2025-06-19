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
4. **ignore**

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


### 4. ignore

Label a message **ignore** only in situation when a follow-up reply by agent is not needed.
Use this option only if the input provided by user does not look like answer to the given question.

Example dialogue №1:
- Agent: Okay bro, I need to know if you have a corporate account connected to a PSP and the name of that PSP. Without this info, we can't move forward. Hit me back when you have it, alright?
- User: Ok
Rationale: User told that they'll hit back as soon as they get info about PSP, no follow-up answer is needed.

Example dialogue №2:
- Agent: Do you have any corporate accounts? In which banks?
- User: I don't have any.
- Agent: Sorry bro, we only work with corporate accounts connected to a PSP—can’t proceed.
- User: Okay.
Rationale: User told that they don't have what corporate account and we told him we couldn't work with that and user agreed - no follow-up is needed.

Example dialogue №2:
- Agent: Please provide the details of the company linked to your payment-gateway account: Company Name, Registered Address, Contact Phone Number, Email Address
- User: Give me some time, Let me find - & tell you.
Rationale: User told us that they need time to tell so asling the question again is redundant - no follow up is needed.

Example dialogue №3:
- Agent: Do you already have a website approved by the PSP? If yes — please give us hosting access (we may need to adjust code or API) If not — we will create the website ourselves
- User: No
Rationale: This is NOT ignore (it's actually 'information') because user has answered the question - they do not have website.
"""


class Intent(BaseModel):
    user_input: str = Field(
        ..., description="The exact text message received from the user."
    )
    category: Literal["faq", "information", "start", "ignore"] = Field(
        ..., description="Category of user input."
    )
    reasoning: str = Field(
        ..., description="Consice reasoning why you selected `category`."
    )


def expand_query(
    user_input: str,
    context: str | None = None,
    instructions: str | None = None,
    question: str | None = None,
) -> str:
    query = (
        f"Take into account the context: {context}.\n"
        f"The asked question was: {question}\n"
        f"Classify the following user request: {user_input}"
    )
    if instructions:
        query = f"Strictly follow these instructions before classifying: {instructions}\n\n{query}"
    return query


router = SimpleAgent(
    instructions=INSTRUCTIONS,
    expand_query=expand_query,
    output_type=Intent,
)
