# IndusGPT Bot

A Telegram bot designed to handle automated conversations and Q&A sessions with users in a structured way. The bot manages user interactions through topic groups, tracks progress, and provides manager assignment capabilities.

## Features

- Automated Q&A sessions with users
- Topic-based conversation management in supergroups
- Manager assignment system (default and per-user)
- PDF export functionality for unfinished user conversations
- Voice message handling with appropriate responses
- Progress tracking for user conversations

## Prerequisites

- Python 3.12 or higher
- uv package manager ([installation guide](https://github.com/astral-sh/uv))

## Installation

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
  -e MODEL="gpt-4o" \
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
| `DATABASE_URL` | Database connection URL | `sqlite://db.sqlite3` |
| `MODEL` | OpenAI model to use | `gpt-4o` |
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_API_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `LOG_FILE` | Log file path | `bot.log` |
| `GOOGLE_CREDENTIALS_PATH` | Path to Google service account credentials | - |
| `GOOGLE_SHEET_URL` | Google Sheet URL for user information | - |
| `GOOGLE_SHEET_WORKSHEET_NAME` | Name of the worksheet in Google Sheet | `UserInfo` |

## Running the Bot

### Local Run
```bash
# Set required environment variables
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export OPENAI_API_KEY="your_openai_api_key"
# Optional: configure other variables as needed

uv run main.py
```

### Docker Run (after stopping)
```bash
docker start indusgpt
```

## Available Commands

### Supergroup Management
- `/attach` - Set the current supergroup as the default for the bot (must be called in General chat)
- `/detach` - Remove the current supergroup as the default for the bot

### Manager Assignment
- `/set_manager @username` - Set the default manager for all new users (in General chat)
- `/set_manager @username` - Set a specific manager for a user (in topic chat)

### Export Functionality
- `/export` - Generate a PDF report of all unfinished users' Q&A sessions
  - Creates a timestamped PDF file
  - Includes all Q&A pairs for users who haven't completed the process
  - Automatically sends the report in the chat
  - Cleans up the file after sending

### User Interaction
- `/start` - Initiates the conversation with the bot (in private chat)
  - Sends introduction message
  - Begins the Q&A session
  - Manages user progress through questions

## Notes

- Voice messages are not supported - users will be prompted to write text responses
- Non-text messages are not accepted - users will be asked to provide text
- When a user completes all questions, they will be connected with their assigned manager
- If no specific manager is assigned, the default manager will be used

## Technical Details

The bot uses:
- aiogram for Telegram bot functionality
- FPDF2 for PDF report generation
- SQLite with Tortoise ORM for data persistence
- Topic groups for organized conversation management

For developers: The codebase follows a modular structure with separate handlers for supergroup commands, chat flow, and user interactions.
