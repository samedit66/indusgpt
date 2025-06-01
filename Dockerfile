# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Create directory for PDF exports
RUN mkdir -p /app/exports

# Enable bytecode compilation for better performance
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy requirements first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using the lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy project files
COPY . .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Default environment variables
ENV MODEL="gpt-4.1-2025-04-14"
ENV DATABASE_URL="sqlite://db.sqlite3"
ENV OPENAI_API_BASE_URL="https://api.openai.com/v1"
ENV LOG_FILE="bot.log"
ENV GOOGLE_SHEET_WORKSHEET_NAME="UserInfo"

# These should be provided at runtime
ARG OPENAI_API_KEY
ARG TELEGRAM_BOT_TOKEN
ARG GOOGLE_CREDENTIALS_PATH
ARG GOOGLE_SHEET_URL

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint
ENTRYPOINT []

# Run the bot
CMD ["python", "main.py"] 
