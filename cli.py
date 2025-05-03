from dotenv import load_dotenv

from src.bot.bot import Bot


load_dotenv()

bot = Bot(model_name="google/gemma-3-4b-it")

while True:
    user_input = input("USER> ")
    print(bot.respond(user_input))
