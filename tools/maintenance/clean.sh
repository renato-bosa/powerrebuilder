#!/bin/bash
# Clean script to remove all generated files and caches

echo "🧹 Cleaning generated files and caches..."

# Remove Python caches
find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -not -path "./.venv/*" -delete 2>/dev/null || true

# Remove tool caches
rm -rf .pytest_cache
rm -rf .ruff_cache
rm -rf .mypy_cache
rm -rf htmlcov
rm -f .coverage

# Remove package metadata
rm -rf *.egg-info

echo "✨ Cleanup complete!"
echo ""
echo "Note: The following were NOT removed:"
echo "  - .venv/ (virtual environment)"
echo "  - .uv/ (UV cache)"
echo "  - logs/ (log files)"
echo "  - output/ (extraction outputs)"
echo ""
echo "To remove these, run:"
echo "  rm -rf .venv .uv logs/* output/*"