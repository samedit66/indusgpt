.PHONY: run
run:
	uv run --active main.py

.PHONY: precommit
precommit:
	uv run --active pre-commit install
	uv run --active pre-commit run --all-files
