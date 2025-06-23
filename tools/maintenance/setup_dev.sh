#!/bin/bash
# Development environment setup using uv

set -e  # Exit on error

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "or: brew install astral/tap/uv"
    exit 1
fi

echo "Setting up development environment for sime-finch..."

# Sync project (this will create venv, install dependencies, and respect .python-version)
echo "Syncing project dependencies..."
uv sync --dev

# Success message
echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Available commands:"
echo "  uv run sime-finch     - Run the main CLI"
echo "  uv run pytest         - Run tests"
echo "  uv run ruff check .   - Run linter"
echo "  uv run ruff format .  - Format code"
echo "  uv run mypy .         - Run type checker"
echo ""
echo "To add dependencies:"
echo "  uv add <package>      - Add runtime dependency"
echo "  uv add --dev <package> - Add development dependency"