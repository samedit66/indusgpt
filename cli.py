import os
from dotenv import load_dotenv

from src.dialog_flow_agent.dialog_flow_agent import DialogFlowAgent


load_dotenv()

bot = DialogFlowAgent(model_name=os.environ["MODEL"])
questions_and_rules = [
    {
        "question": "Do you have corporate (business) accounts? In which banks?",
        "val_rule": """
User response **must** confirm that they have a corporate/business bank account and say the bank name.
Examples:
- I have a corporate account in Sber bank.
- I got a business account in Bank of Baroda.
"""
    },
    {
        "question": "Are your corporate accounts connected to any PSP (e.g., Razorpay, Cashfree, PayU, Getepay)?",
        "val_rule": """
User response **must** include the name of the **PSP** to which their corporate account is connected.
Examples:
- Yes my account is connected to Razorpay.
- Yes it is PayU.
- My PSP is Gatepay.
"""
    },
    {
        "question": "Can you provide login and password access to the PSP account?",
        "val_rule": """
User response **must** clearly answer “yes” or “no” and, if yes, indicate readiness to **share login credentials**.
Collect any additional information user may provide about their PSP account.
Examples:
- Yes, my login is admin, password is 123341.
"""
    },
    {
        "question": (
            "Do you already have a website approved by the PSP?\n"
            "If yes — please give us hosting access (we may need to adjust code or API)\n"
            "If not — we will create the website ourselves"
        ),
        "val_rule": """
User response **must** answer “yes” or “no.” If “yes,” they **must** mention they can provide **hosting access**. If "no", only "no" is required.
Examples:
- No.
- Yes. Next goes any details about hosting access.
"""
    },
    {
        "question": "Are you open to working under a profit‑sharing model (5% of transaction volume) instead of a one‑time deal?",
        "val_rule": """
User response **must** clearly say "yes" or "no".
Examples:
- Yes.
- No.
- Of course
- Sure.
"""
    }
]

data = []
while True:
    # iterate through each Q&A in order
    for qa in questions_and_rules:
        user_input = input(f"USER> ({qa['question']}) ")
        answer = bot.respond(user_input, qa["question"], qa["val_rule"])
        print(answer.answer)

        if answer.extracted_data is not None:
            data.append(answer.extracted_data)
    break


print("\n".join(data))
