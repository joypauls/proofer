.PHONY: install test dev, build, build-check, publish

install:
	poetry install --with dev

test:
	poetry run pytest

dev:
	poetry run python scripts/dev.py

build:
	poetry build

build-check: build
	twine check dist/*

publish: build-check
	poetry publish