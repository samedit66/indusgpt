export VIRTUAL_ENV=".venv-local"
uv sync --active
uv run --active main.py
