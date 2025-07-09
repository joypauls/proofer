.PHONY: install test dev

install:
	poetry install --with dev

test:
	poetry run pytest

# below are development utilities

dev:
	poetry run python scripts/dev.py