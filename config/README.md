# Configuration Files

This directory contains configuration files for the PowerRebuilder project.

## Files

- `performance.yaml` - Performance tuning configuration
- `security.yaml` - Security settings and policies
- `importlinter.ini` - Import linter configuration (if present)

## Usage

These configuration files are used by various tools and components of the PowerRebuilder project:

1. **Performance Configuration**: Used to tune extraction, parsing, and generation performance
2. **Security Configuration**: Defines security policies for file handling and code generation
3. **Import Linter**: Enforces import rules and dependencies between modules

## Adding New Configuration

When adding new configuration files:
1. Use YAML format for complex configurations
2. Use INI format for tool-specific configurations
3. Document any new configuration options in this README