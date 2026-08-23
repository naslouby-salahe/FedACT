.PHONY: setup format lint typecheck dead-code depcheck unit architecture tests checks

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

unit:
	uv run pytest tests/unit tests/scientific

architecture:
	uv run pytest tests/architecture

tests: unit architecture

checks: lint typecheck dead-code depcheck tests
