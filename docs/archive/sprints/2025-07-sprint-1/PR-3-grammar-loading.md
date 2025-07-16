# PR #3: Fix Grammar Loading Issues

## Summary
- Replace hardcoded grammar paths with GrammarManager
- Consolidate parser classes to eliminate naming conflicts
- Ensure all grammar files are properly loaded
- Fix parser initialization issues

## Problem
1. ParseCoordinator uses hardcoded paths instead of GrammarManager
2. Conflicting PowerBuilderParser and EnhancedPowerBuilderParser classes
3. Grammar files not loading properly
4. Inconsistent parser initialization

## Solution
1. Use GrammarManager for all grammar loading
2. Consolidate parser classes into single EnhancedPowerBuilderParser
3. Fix grammar path resolution
4. Add comprehensive grammar validation

## Implementation Details

### Fix 1: Use GrammarManager in ParseCoordinator
```python
# In ParseCoordinator.__init__() around line 111
# Replace:
grammar_file = GRAMMAR_DIR / "definitions" / "powerbuilder.lark"
with open(grammar_file) as f:
    grammar_content = f.read()

# With:
from src.parse.grammar.loader import GrammarManager
manager = GrammarManager()
self.parser = manager.load_grammar("powerbuilder", parser=self.parser_type)
```

### Fix 2: Consolidate parser classes
```python
# Remove duplicate parser references
# Keep only EnhancedPowerBuilderParser
# Update all imports throughout codebase
# Ensure PowerBuilderBaseParser is used as parent
```

### Fix 3: Grammar validation script
```python
# validate_grammars.py
from lark import Lark
from pathlib import Path

grammar_dir = Path("src/parse/grammar/definitions")
for grammar_file in grammar_dir.glob("*.lark"):
    try:
        with open(grammar_file) as f:
            Lark(f.read(), parser='lalr')
        print(f"✓ {grammar_file.name} valid")
    except Exception as e:
        print(f"✗ {grammar_file.name}: {e}")
```

## Test Plan
- [ ] Verify all grammar files exist in correct location
- [ ] Run grammar validation script
- [ ] Test parser initialization with GrammarManager
- [ ] Parse sample PowerBuilder files of each type
- [ ] Ensure no hardcoded paths remain

## Grammar Files to Validate
- powerbuilder.lark
- common_grammar.lark  
- datawindow.lark
- sql.lark
- All extension grammars

## Estimated Time: 17-24 hours

## Branch: `fix/grammar-loading-issues`