# IndusGPT Bot

A Telegram bot designed to facilitate user onboarding through interactive conversations.

## Features

- Interactive conversations with users
- Dynamic learning capabilities
- User management system
- Export functionality for conversation data
- Topic-based chat organization

## Bot Commands

### General Chat Commands
Commands that should be used in the main/general chat:

- `/attach` - Set up the bot for this supergroup if not already configured
- `/detach` - Remove the bot from this supergroup
- `/set_manager @manager` - Set the default manager for all new users
- `/export` - Generate a PDF report of all unfinished users' conversations

### Topic Chat Commands
Commands that should be used within topic chats:

- `/set_manager @manager` - Assign a specific manager to the user in this topic
- `/learn <instructions>` - Teach the bot new information
  - Use directly: `/learn <instructions>` to add new instructions
  - Reply to a message: `/learn <instructions>` to learn from both the instructions and the message
- `/instructions` - View current bot instructions
- `/forget` - Clear all learned instructions
- `/stop` - End the conversation with the current user

## Setup

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/indusgpt_dev.git
cd indusgpt_dev
```

2. Install required packages:
```bash
uv sync
```

### Option 2: Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/indusgpt_dev.git
cd indusgpt_dev
```

2. Build the Docker image:
```bash
docker build -t indusgpt .
```

3. Run the container with environment variables:
```bash
docker run -d --name indusgpt \
  -e TELEGRAM_BOT_TOKEN="your_telegram_bot_token" \
  -e OPENAI_API_KEY="your_openai_api_key" \
  -e DATABASE_URL="sqlite://db.sqlite3" \
  -e MODEL="gpt-4.1-2025-04-14" \
  -e OPENAI_API_BASE_URL="https://api.openai.com/v1" \
  -e LOG_FILE="bot.log" \
  -e GOOGLE_CREDENTIALS_PATH="path_to_credentials" \
  -e GOOGLE_SHEET_URL="your_sheet_url" \
  -e GOOGLE_SHEET_WORKSHEET_NAME="UserInfo" \
  indusgpt
```

4. View logs:
```bash
docker logs -f indusgpt
```

5. Stop the bot:
```bash
docker stop indusgpt
```

## Environment Variables

The bot can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token (required) | - |
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `MODEL` | OpenAI model to use | `gpt-4.1-2025-04-14` |
| `DATABASE_URL` | Database connection URL | `sqlite://db.sqlite3` |
| `OPENAI_API_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `LOG_FILE` | Log file path | `bot.log` |
| `GOOGLE_CREDENTIALS_PATH` | Path to Google service account credentials (required) | - |
| `GOOGLE_SHEET_URL` | Google Sheet URL for user information (required) | - |
| `GOOGLE_SHEET_WORKSHEET_NAME` | Name of the worksheet in Google Sheet | `UserInfo` |

## Running the Bot

### Local Run
```bash
# Set required environment variables
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export OPENAI_API_KEY="your_openai_api_key"
export GOOGLE_CREDENTIALS_PATH="path_to_credentials"
export GOOGLE_SHEET_URL="your_sheet_url"
# Optional: configure other variables as needed

uv run main.py
```

### Docker Run (after stopping)
```bash
docker start indusgpt
```

## Technical Details

The bot uses:
- aiogram for Telegram bot functionality
- FPDF2 for PDF report generation
- SQLite with Tortoise ORM for data persistence
- Topic groups for organized conversation management

For developers: The codebase follows a modular structure with separate handlers for supergroup commands, chat flow, and user interactions.
