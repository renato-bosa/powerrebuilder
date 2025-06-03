.PHONY: help install dev test lint format type-check clean run

help:
	@echo "Available commands:"
	@echo "  make install    - Install runtime dependencies"
	@echo "  make dev        - Install all dependencies (including dev)"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter (ruff check)"
	@echo "  make format     - Format code (ruff format)"
	@echo "  make type-check - Run type checker (mypy)"
	@echo "  make clean      - Clean up cache files"
	@echo "  make run        - Run the main CLI"

install:
	uv sync

dev:
	uv sync --dev

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage

run:
	uv run sime-finch --help