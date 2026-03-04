.PHONY: help typecheck test lint format check clean

help:
	@echo "Available commands:"
	@echo "  make typecheck    - Run mypy type checking"
	@echo "  make test         - Run pytest tests"
	@echo "  make lint         - Run ruff linting"
	@echo "  make format       - Format code with ruff"
	@echo "  make check        - Run all checks (typecheck + lint + test)"
	@echo "  make clean        - Remove cache files"

typecheck:
	@echo "Running mypy type checking..."
	uv run mypy rag/ yt_sync/ config/

typecheck-rag:
	@echo "Running mypy on rag module..."
	uv run mypy rag/

typecheck-yt-sync:
	@echo "Running mypy on yt_sync module..."
	uv run mypy yt_sync/

test:
	@echo "Running tests..."
	uv run pytest

test-rag:
	@echo "Running RAG tests..."
	uv run pytest rag/

test-yt-sync:
	@echo "Running yt_sync tests..."
	uv run pytest yt_sync/

lint:
	@echo "Running ruff linting..."
	uv run ruff check .

format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

check: typecheck lint test
	@echo "All checks passed!"

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
