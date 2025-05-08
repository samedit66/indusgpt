import os
from dotenv import load_dotenv

from src.chat_manager.chat_manager import ChatManager


load_dotenv()

bot = ChatManager(model_name=os.environ["MODEL"])
user_id = 1

print(f"BOT> {bot.current_question(user_id)}")
while True:
    user_input = input("USER> ")
    print(f"BOT> {bot.reply(user_id, user_input)}")
