.PHONY: install test lint format

install:
	python -m pip install --upgrade pip
	pip install -e .[dev]

test:
	pytest -q

lint:
	black --check .
	isort --check-only .
	flake8

format:
	black .
	isort .
