# Grammar Consolidation - Next Steps

## Phase 1 ✓ Complete
- Moved experimental grammars to `experimental/` subdirectory
- Updated test files to use new paths
- Created documentation for experimental grammars

## Phase 2 - Immediate Actions

### 1. Fix Hardcoded Grammar Paths
The following files need to be updated to use GrammarManager instead of hardcoded paths:

**parse/parse_coordinator.py**:
- Line 185: `with open(self.base_path / "parse/datawindow.lark", encoding="utf-8") as f:`
- Line 255: `with open(self.base_path / "parse/sql.lark", encoding="utf-8") as f:`

These should use the GrammarManager from grammar.py instead.

### 2. Decide on common_grammar.lark
Currently `common_grammar.lark` is not being used by any grammar. Options:
1. **Remove it** - All grammars already import from Lark's common module
2. **Use it** - Refactor grammars to import shared PowerBuilder-specific rules from it

Recommendation: Remove it since Lark's common module already provides the needed functionality.

### 3. Fix datawindow.lark Imports
Currently imports from both common and powerbuilder.lark:
```lark
%import common.CNAME -> IDENTIFIER
%import .powerbuilder.STRING
%import .powerbuilder.COMMENT
```

Should be refactored to only import from common or create shared tokens.

## Phase 3 - Code Updates

### Update parse_coordinator.py to use GrammarManager

Replace hardcoded grammar loading with:

```python
from .grammar import get_default_manager

class PowerBuilderDataWindowParser(PowerBuilderBaseParser):
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path.cwd()
        self.grammar_manager = get_default_manager()
        
        # Use GrammarManager instead of direct file loading
        self.parser = self.grammar_manager.load_grammar(
            "datawindow",
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True
        )
```

Similar changes needed for PowerBuilderQueryParser.

## Phase 4 - Grammar Optimization

### 1. Review and Remove Duplicates
Based on syntax_errors_analysis.md, powerbuilder.lark has many duplicate rules that need consolidation.

### 2. Modularize powerbuilder.lark
Consider breaking it into logical modules:
- `pb_types.lark` - Type definitions and declarations
- `pb_expressions.lark` - Expression rules
- `pb_statements.lark` - Statement rules
- `pb_structures.lark` - Window, menu, user object structures

### 3. Standardize Token Naming
Ensure consistent token naming across all grammars.

## Testing Plan

After each phase:
1. Run parser tests: `pytest tests/test_parse/ -v`
2. Test specific file parsing with each parser type
3. Verify no performance regression
4. Check that grammar caching works properly

## Priority Order

1. **High Priority**: Fix hardcoded paths (breaks modularity)
2. **Medium Priority**: Remove/repurpose common_grammar.lark (clarity)
3. **Medium Priority**: Fix datawindow imports (reduce coupling)
4. **Low Priority**: Modularize large grammars (nice to have)

## Estimated Time
- Phase 2: 30 minutes
- Phase 3: 45 minutes  
- Phase 4: 2 hours
- Testing: 30 minutes

Total: ~3.5 hours