.PHONY: install lint format type-check test test-cov clean build docs all

install:
	pip install -e ".[dev]"

lint:
	ruff check orche tests

format:
	ruff format orche tests

type-check:
	mypy orche tests

test:
	pytest

test-cov:
	pytest -v --cov=orche --cov-report=term --cov-report=html

clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +

build:
	python -m build

docs:
	mkdocs serve

all: lint type-check test
