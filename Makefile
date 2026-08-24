.PHONY: setup format lint typecheck dead-code depcheck imports unit architecture quality tests checks

setup:
	uv sync

format:
	uv run ruff format src tests

lint:
	uv run ruff check src tests

typecheck:
	uv run pyright

dead-code:
	uv run vulture src tests --min-confidence 80

depcheck:
	uv run deptry .

imports:
	uv run lint-imports

unit:
	uv run pytest tests/unit

architecture:
	uv run pytest tests/architecture

quality:
	uv run pytest tests/quality

tests:
	uv run pytest --cov=fedact --cov-fail-under=85

checks: lint typecheck dead-code depcheck imports architecture quality tests
