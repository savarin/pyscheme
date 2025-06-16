#!/bin/bash

# Stop on the first error
set -e

# Run ruff for formatting check and linting
echo "Running ruff format check..."
uv run ruff format --check versions/claude/.

echo "Running ruff linting..."
uv run ruff check versions/claude/.

# Run mypy for type checking
echo "Running mypy..."
uv run mypy --strict versions/claude/.

# Run pytest for running unit tests
echo "Running pytest..."
uv run pytest versions/claude/.

echo "All checks passed!"
