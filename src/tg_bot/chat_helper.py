from functools import lru_cache

from src.chat import (
    ChatManager,
    Question,
    generate_response,
    generate_reply,
)
from src.persistence import TortoiseQuestionList, TortoiseUserAnswerStorage


@lru_cache
def introduction() -> str:
    return """
Hi brother!  
Thanks for reaching out 🙏  

**We work with high-volume traffic (gaming-related) and process over ₹12,000,000+ in daily incoming transactions.**  
We are looking to **buy or rent corporate accounts in India** that can be connected to a PSP (such as Razorpay, Cashfree, PayU, Getepay, etc.) to accept payments.  
We are ready for long-term cooperation and offer **up to 5% of the profit** for stable account performance.  
_For example: ₹500,000 daily volume = ₹25,000 your share (5%)._  

---

## 🛠️ Our Work Process

1. **Access to PSP account**  
   - You share the login + password (e.g. Razorpay)  
   - We review dashboard, limits, API access, status  

2. **Website check**  
   - If already available — great, we’ll need hosting access  
   - If not — we’ll create a bridge website (services, education, consulting, etc.)  

3. **Submit for moderation**  
   - We use your account + our site  
   - Fill forms, upload docs, complete verification  

4. **API integration**  
   - Our dev team integrates PSP to our backend  
   - We test deposit flow, webhook, and transaction statuses  

5. **Start working**  
   - Begin with small volumes, check stability  
   - If everything is good — we scale  
---

Let’s build a **strong** and **profitable** partnership 💪
"""


@lru_cache
def questions() -> list[Question]:
    return [
        Question(
            text="Do you have corporate (business) accounts? In which banks?",
            answer_requirement=(
                "User response **must** confirm that they have a corporate/business bank account "
                "and say the bank name.\nExamples:\n"
                "- Yes corporate account in ICICI\n"
                "- I have a corporate account in Sber bank.\n"
                "- I got a business account in Bank of Baroda."
            ),
        ),
        Question(
            text="Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?",
            answer_requirement=(
                "User response **must** confirm they have a connected PSP and include the PSP name. If user says they don't have a PSP or it's not connected, the answer is invalid.\nExamples:\n"
                "- Yes, I have Razorpay connected.\n"
                "- My account is integrated with PayU.\n"
                "- We use Cashfree for payments."
                "- Razorpay is connected.\n",
                "- PayU.",
            ),
        ),
        Question(
            text="Can you provide login and password access to the PSP account?",
            answer_requirement=(
                "User response **must** provide actual login credentials (login and password) or confirm and commit to "
                "providing them. Any response indicating inability or unwillingness to share credentials is invalid.\n"
                "Examples of valid responses:\n"
                "- Login admin123, password test456\n"
                "- Username is merchant_1, pass is secure123, API key is abcd1234\n"
                "- Yes, I'll share them right now - login: mystore, password: shop2023\n"
                "- Of course, the credentials are: user=admin pass=12345\n\n"
                "Examples of invalid responses:\n"
                "- I'll check with my team first\n"
                "- I need to think about it\n"
                "- I don't have access right now\n"
                "- Let me get back to you on this\n"
                "- I can't share these details"
            ),
        ),
        Question(
            text=(
                "Do you already have a website approved by the PSP?\n"
                "If yes — please give us hosting access (we may need to adjust code or API)\n"
                "If not — we will create the website ourselves"
            ),
            answer_requirement=(
                "User response **must** clearly indicate if they have a website. If they have one, they **must** "
                "provide hosting access details (credentials, URL, etc). If they don't have a website or are unsure, "
                "that's perfectly fine.\n\n"
                "Examples of valid responses:\n"
                "- No, I don't have a website yet\n"
                "- Not sure, we're still working on it\n"
                "- Yes, here's the hosting access - username: admin, password: secure123\n"
                "- Yes, you can access it at mysite.com/admin with login: merchant, pass: shop2023\n"
                "- Yes, FTP details are host: ftp.mysite.com, user: ftpuser, pass: ftppass123\n\n"
                "Examples of invalid responses:\n"
                "- Yes (without providing access details)\n"
                "- I have a website but can't share access now\n"
                "- Maybe\n"
                "- I'll think about giving access\n"
                "- The website is www.mysite.com (but no access details)"
            ),
        ),
        Question(
            text="Are you open to working under a profit-sharing model (5% of transaction volume) instead of a one-time deal?",
            answer_requirement=(
                "User response **must** clearly indicate agreement or disagreement to the profit-sharing model.\n\n"
                "Examples of valid responses:\n"
                "- Yes, I agree to 5% profit sharing\n"
                "- Sure, that works for me\n"
                "- I accept those terms\n"
                "- Absolutely, let's do profit sharing\n\n"
                "Examples of invalid responses:\n"
                "- Maybe later\n"
                "- Need to think about it\n"
                "- What about 3%?\n"
                "- Let me check with my team\n"
                "- I prefer fixed price\n"
            ),
        ),
    ]


@lru_cache
def chat_manager() -> ChatManager:
    return ChatManager(
        question_list=TortoiseQuestionList(questions()),
        user_answer_storage=TortoiseUserAnswerStorage(),
        generate_response=generate_response,
        generate_reply=generate_reply,
    )
