#!/usr/bin/env python3
"""
cli.py

Interactive console script to drive and test ChatManager.
"""

import os
import sys
from dotenv import load_dotenv

from src.ai.chat_manager.chat_manager import (
    ChatManager,
    UserInformation,
)


COLOR_RESET = "\033[0m"
COLOR_BOT = "\033[32m"  # Green
COLOR_USER = "\033[36m"  # Cyan


def cli():
    # Load environment
    load_dotenv()

    # Required environment variables
    model_name = os.environ.get("MODEL")
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE_URL")

    missing = []
    if not model_name:
        missing.append("MODEL")
    if not api_key:
        missing.append("OPENAI_API_KEY")
    if not base_url:
        missing.append("OPENAI_API_BASE_URL")

    if missing:
        print(
            f"❗️ Please set the following environment variables: {', '.join(missing)}"
        )
        sys.exit(1)

    # Initialize ChatManager with API settings
    bot = ChatManager(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    # Register a simple callback to fire when all info is ready
    @bot.on_info_ready()
    def handle_final_info(user_id: int, info: UserInformation):
        print("\n" + "=" * 40)
        print(f"[Callback] Final info for user {user_id}:")
        print(info)
        print("=" * 40 + "\n")

    # Start conversation
    user_id = 1
    print("\n" + "=" * 40)
    print("🗨️  Welcome to the ChatManager tester!")
    print("=" * 40 + "\n")

    # Optionally show bot intro
    intro_text = bot.intro.strip()
    if intro_text:
        print(intro_text + "\n")

    # Prompt first question
    print(f"{COLOR_BOT}BOT>{COLOR_RESET} {bot.current_question(user_id)}\n")

    # Main REPL loop
    try:
        while True:
            user_input = input(f"{COLOR_USER}YOU>{COLOR_RESET} ").strip()
            if not user_input:
                # allow skipping or reprinting the bot intro
                print("(Type something—or press Enter to repeat last question.)\n")
            bot_response = bot.reply(user_id, user_input)
            if bot_response:
                print(f"\n{COLOR_BOT}BOT>{COLOR_RESET} {bot_response}\n")
            else:
                print("✅ All done. Exiting tester.")
                break
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Exiting. Goodbye!")
