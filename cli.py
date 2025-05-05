from dotenv import load_dotenv

from src.dialog_flow_agent.dialog_flow_agent import DialogFlowAgent


load_dotenv()

bot = DialogFlowAgent(model_name="google/gemma-3-4b-it")
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
"""
    },
    {
        "question": "Can you provide login and password access to the PSP account?",
        "val_rule": """
User response **must** clearly answer “yes” or “no” and, if yes, indicate readiness to **share login credentials**.
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
"""
    },
    {
        "question": "Are you open to working under a profit‑sharing model (5% of transaction volume) instead of a one‑time deal?",
        "val_rule": """
User response **must** clearly say "yes" or "no".
"""
    }
]


while True:
    # iterate through each Q&A in order
    for qa in questions_and_rules:
        user_input = input(f"USER> ({qa['question']}) ")
        print(bot.respond(user_input, qa["question"], qa["val_rule"]), end="\n\n")
        break
