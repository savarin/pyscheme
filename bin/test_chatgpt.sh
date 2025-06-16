#!/bin/bash

# Stop on the first error
set -e

# Run ruff for formatting check and linting
echo "Running ruff format check..."
uv run ruff format --check versions/chatgpt/.

echo "Running ruff linting..."
uv run ruff check versions/chatgpt/.

# Run mypy for type checking
echo "Running mypy..."
uv run mypy --strict versions/chatgpt/.

# Run pytest for running unit tests
echo "Running pytest..."
uv run pytest versions/chatgpt/.

echo "All checks passed!"
