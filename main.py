import asyncio
from dotenv import load_dotenv
from colorama import init, Fore, Style

from src.chat.question_list import Question, QaPair
from src.chat.in_memory import InMemoryQuestionList, InMemoryUserAnswerStorage
from src.chat.chat_manager import ChatManager
from src.chat.generate_response import generate_response
from src.chat.generate_reply import generate_reply
from src.chat.info_extractor import extract_info


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


async def console_chat():
    from pprint import pprint as pp

    # initialize colorama
    init(autoreset=True)

    # load any .env
    load_dotenv()

    async def on_all_finished(user_id: int, qa_pairs: list[QaPair]):
        info = await extract_info(qa_pairs)
        pp(info)

    # set up our in-memory Q&A manager
    questions = build_questions()
    qlist = InMemoryQuestionList(questions)
    storage = InMemoryUserAnswerStorage()
    cm = ChatManager(
        question_list=qlist,
        user_answer_storage=storage,
        generate_response=generate_response,
        generate_reply=generate_reply,
        on_all_finished=[on_all_finished],
    )

    user_id = 1  # single-console user

    print(Fore.GREEN + "🤖 Bot: Hello! Let's go through a few questions.\n")
    print(Fore.CYAN + "Bot: " + Style.BRIGHT + await cm.current_question(user_id))

    # Loop until ChatManager says we're finished
    while not await qlist.all_finished(user_id):
        # get next question text
        # q = cm.current_question(user_id)
        # print bot prompt
        answer = input(Fore.YELLOW + "You: ")
        bot_reply = await cm.reply(user_id, answer)
        print(Fore.CYAN + "Bot: " + Style.BRIGHT + bot_reply)
        # get user input


if __name__ == "__main__":
    asyncio.run(console_chat())
