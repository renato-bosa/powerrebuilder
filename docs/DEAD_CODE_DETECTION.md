# Dead Code Detection with Vulture

This document describes how we use Vulture to detect dead code in the PowerRebuilder project.

## Overview

Vulture is a static code analyzer that finds unused code in Python programs. We've configured it to reduce false positives from common patterns in our codebase.

## Configuration

Our vulture configuration is defined in two places:

### 1. pyproject.toml

The `[tool.vulture]` section in `pyproject.toml` contains the main configuration:

```toml
[tool.vulture]
min_confidence = 80  # Only report items with 80%+ confidence
verbose = false
paths = ["src/", ".vulture_whitelist.py"]
ignore_names = [...]  # Pattern-based ignores
ignore_decorators = [...]  # Decorator-based ignores
exclude = [...]  # Directory exclusions
```

### 2. .vulture_whitelist.py

This file contains dummy definitions for names that are intentionally unused but shouldn't be flagged:

- Parser framework parameters (items, children, meta)
- Token parameters (lparen, rparen, etc.)
- Visitor pattern methods
- Protocol/interface required parameters
- Dataclass fields
- Dynamic/framework methods

## Common Patterns Whitelisted

### 1. Parser/Transformer Parameters

Lark transformers often have parameters that aren't used in every method:

```python
def some_rule(self, items):
    # 'items' might not be used if we only care about the rule match
    return None
```

### 2. Token Parameters

Grammar rules often produce token parameters that aren't needed:

```python
def function_call(self, name, lparen, args, rparen):
    # We only need 'name' and 'args', not the parentheses
    return FunctionCall(name, args)
```

### 3. Visitor Pattern

Visitor methods might not use the node parameter:

```python
def visit_default(self, node):
    # Default visitor might just pass through
    return node
```

### 4. Protocol Requirements

Interface methods must accept certain parameters even if unused:

```python
def __exit__(self, exc_type, exc_value, traceback):
    # Context manager protocol requires these parameters
    self.cleanup()
    return False
```

## Running Vulture

### Quick Check

```bash
# Run with our configuration
python scripts/check_dead_code.py

# Run on specific directory
python -m vulture src/parse/ .vulture_whitelist.py --min-confidence 80

# Run with verbose output
python -m vulture src/ .vulture_whitelist.py --min-confidence 80 --verbose
```

### CI Integration

Vulture can be integrated into CI to catch dead code:

```yaml
- name: Check for dead code
  run: |
    pip install vulture
    python scripts/check_dead_code.py
```

## Interpreting Results

When vulture finds potential dead code, consider:

1. **Is it truly unused?** - Check for dynamic imports, reflection, or framework usage
2. **Is it part of an API?** - Public APIs might not be used internally
3. **Is it for future use?** - Document with a comment if keeping for future features
4. **Is it test/debug code?** - Consider moving to appropriate locations

## Adding New Whitelist Entries

If you encounter false positives:

1. **Pattern-based**: Add to `ignore_names` in pyproject.toml for patterns
2. **Specific names**: Add dummy usage to `.vulture_whitelist.py`
3. **Decorators**: Add to `ignore_decorators` for decorator-based ignores

Example additions:

```python
# In .vulture_whitelist.py
class _NewPatternWhitelist:
    def my_framework_method(self, required_param): pass
    
# In pyproject.toml
ignore_names = [
    # ...
    "my_*",  # My framework methods
]
```

## Best Practices

1. **Regular Checks**: Run vulture periodically to catch accumulating dead code
2. **Before Major Releases**: Clean up dead code to reduce maintenance burden
3. **Document Exceptions**: If keeping apparently dead code, document why
4. **Review Whitelist**: Periodically review whitelist entries for relevance

## Limitations

Vulture can't detect:
- Code used via `eval()` or `exec()`
- Dynamic attribute access via `getattr()`
- Code imported by external packages
- Code used only in configuration files

Always manually verify before removing code!