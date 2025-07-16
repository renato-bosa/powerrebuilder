# Configuration Files Guide

This document explains the purpose of each configuration file in the project root.

## Python Project Configuration

### `pyproject.toml`
- **Purpose**: Modern Python project configuration (PEP 517/518)
- **Contains**: Project metadata, dependencies, build system, tool configurations
- **Must stay in root**: Yes, required by Python packaging tools

### `setup.cfg`
- **Purpose**: Legacy Python setup configuration
- **Contains**: Additional package configuration, test settings
- **Must stay in root**: Yes, for backward compatibility

### `uv.lock`
- **Purpose**: Dependency lock file for reproducible installs
- **Contains**: Exact versions of all dependencies
- **Must stay in root**: Yes, required by UV package manager

### `.uvrc`
- **Purpose**: UV package manager configuration
- **Contains**: UV-specific settings
- **Must stay in root**: Yes

## Linting and Formatting

### `.markdownlint.json`
- **Purpose**: Markdown linter configuration
- **Contains**: Rules for markdown file formatting
- **Must stay in root**: Yes, linters look for it here

## Version Control

### `.gitignore`
- **Purpose**: Tells Git which files/folders to ignore
- **Contains**: Patterns for files that shouldn't be committed
- **Must stay in root**: Yes, required by Git

## IDE Configuration

### `.vscode/`
- **Purpose**: VS Code workspace settings
- **Contains**: Editor preferences, Python interpreter path, etc.
- **Already hidden**: Yes (dot prefix)

### `.claude/`
- **Purpose**: Claude AI assistant settings
- **Contains**: Project-specific AI instructions
- **Already hidden**: Yes (dot prefix)

## Generated Files (Safe to Delete)

These are automatically regenerated and should be ignored:

- `__pycache__/` - Python bytecode cache
- `.pytest_cache/` - Pytest cache
- `.ruff_cache/` - Ruff linter cache
- `.mypy_cache/` - MyPy type checker cache
- `htmlcov/` - Coverage HTML reports
- `.coverage` - Coverage data
- `*.egg-info/` - Python package metadata
- `.venv/` - Virtual environment (recreate with `uv venv`)
- `.uv/` - UV package manager cache

## Scripts

- `scripts/setup_dev.sh` - Development environment setup script