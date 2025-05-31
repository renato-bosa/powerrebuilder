#!/bin/bash
# Script to set up the development environment using uv

set -e  # Exit on error

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "Setting up development environment for sime-finch..."

# Create directories
mkdir -p .uv/pythons

# Install Python if needed
if [ ! -d ".uv/pythons/3.13" ]; then
    echo "Installing Python 3.13..."
    uv python install 3.13
fi

# Create or update virtual environment
echo "Creating/updating virtual environment..."
uv venv -p 3.13 .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Install dev dependencies
echo "Installing development dependencies..."
uv pip install -e ".[dev,docs]"

# Success message
echo "Development environment setup complete!"
echo "Activate the virtual environment with: source .venv/bin/activate" 