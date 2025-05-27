.PHONY: run
run:
	uv run main.py

.PHONY: precommit
precommit:
	uv run pre-commit install
	uv run pre-commit run --all-files
