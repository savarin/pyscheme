#!/bin/bash

# Stop on the first error
set -e

# Run ruff for formatting check and linting
echo "Running ruff format check..."
uv run ruff format --check .

echo "Running ruff linting..."
uv run ruff check .

# Run mypy for type checking
echo "Running mypy..."
uv run mypy --strict .

# Run pytest for running unit tests
echo "Running pytest..."
uv run pytest

echo "All checks passed!"
