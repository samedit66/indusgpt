import asyncio
from dotenv import load_dotenv
from colorama import init, Fore, Style

from src.ai.question_list import Question
from src.ai.in_memory import InMemoryQuestionList, InMemoryUserAnswerStorage
from src.ai.chat_manager import ChatManager


def build_questions():
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
                "User response **must** include the name of the **PSP**.\nExamples:\n"
                "- Yes, Razorpay.\n"
                "- My PSP is Gatepay."
            ),
        ),
        Question(
            text="Can you provide login and password access to the PSP account?",
            answer_requirement=(
                "User response **must** clearly answer “yes” or “no” and, if yes, indicate readiness to "
                "**share login credentials**.\nExamples:\n"
                "- Yes, login is admin, password is 123341."
            ),
        ),
        Question(
            text=(
                "Do you already have a website approved by the PSP?\n"
                "If yes — please give us hosting access (we may need to adjust code or API)\n"
                "If not — we will create the website ourselves"
            ),
            answer_requirement=(
                "User response **must** answer “yes” or “no.” If “yes,” they **must** mention they can "
                "provide **hosting access**.\nExamples:\n"
                "- No.\n"
                "- Yes, I can provide hosting credentials."
            ),
        ),
        Question(
            text="Are you open to working under a profit-sharing model (5% of transaction volume) instead of a one-time deal?",
            answer_requirement=(
                'User response **must** clearly say "yes" or "no".\nExamples:\n'
                "- Yes.\n"
                "- No."
            ),
        ),
    ]


async def console_chat():
    # initialize colorama
    init(autoreset=True)

    # load any .env
    load_dotenv()

    # set up our in-memory Q&A manager
    questions = build_questions()
    qlist = InMemoryQuestionList(questions)
    storage = InMemoryUserAnswerStorage()
    cm = ChatManager(
        question_list=qlist,
        user_answer_storage=storage,
        on_all_finished=[
            lambda user_id, qa: print(
                f"\n{Fore.MAGENTA}✅ All done! Stored {len(qa)} Q&A pairs."
            )
        ],
    )

    user_id = 1  # single-console user

    print(Fore.GREEN + "🤖 Bot: Hello! Let’s go through a few questions.\n")
    print(Fore.CYAN + "Bot: " + Style.BRIGHT + cm.current_question(user_id))

    # Loop until ChatManager says we're finished
    while not qlist.all_finished(user_id):
        # get next question text
        # q = cm.current_question(user_id)
        # print bot prompt
        answer = input(Fore.YELLOW + "You: ")
        bot_reply = await cm.reply(user_id, answer)
        print(Fore.CYAN + "Bot: " + Style.BRIGHT + bot_reply)
        # get user input

    # When done, dump all Q&A
    print("\n" + Fore.GREEN + Style.BRIGHT + "Here’s what you answered:\n")
    for idx, (question, answer) in enumerate(storage.get_all(user_id), start=1):
        print(Fore.CYAN + f"{idx}. Q: {question.text}")
        print(Fore.YELLOW + f"   A: {answer}\n")


if __name__ == "__main__":
    asyncio.run(console_chat())
