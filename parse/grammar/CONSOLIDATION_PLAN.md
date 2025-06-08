# Grammar Consolidation Plan

## Overview
This document outlines the plan to consolidate and organize the PowerBuilder grammar files in the parse/grammar directory.

## Current State Analysis

### Active Grammars (Keep and Refine)
1. **powerbuilder.lark** - Main PowerBuilder grammar
   - Used by: PowerBuilderParser in parse_coordinator.py
   - Purpose: Parse .sra, .srw, .sru, .srf, .srm, .srs files
   - Status: Keep as main grammar

2. **datawindow.lark** - DataWindow specific grammar  
   - Used by: PowerBuilderDataWindowParser
   - Purpose: Parse .srd DataWindow files
   - Status: Keep but fix imports

3. **sql.lark** - SQL grammar
   - Used by: SQLParser in sql_parser.py
   - Purpose: Parse SQL queries and .srq files
   - Status: Keep as-is

4. **pseudocode.lark** - Pseudocode grammar
   - Used by: Tests in test_pseudocode.py
   - Purpose: Parse pseudocode/pcode
   - Status: Keep for pcode parsing

### Experimental Grammars (Remove or Archive)
1. **powerbuilder_fixed.lark** - Experimental version
2. **powerbuilder_fixed_v2.lark** - Another experimental version
3. **powerbuilder_simple.lark** - Simplified test version
4. **powerbuilder_core.lark** - Core rules version
5. **powerbuilder_js.lark** - JavaScript-style variant

### Unused Grammar
1. **common_grammar.lark** - Created but not imported
   - Status: Either use it properly or remove it

## Consolidation Steps

### Phase 1: Clean Up Experimental Files
1. Archive experimental grammars to a subdirectory:
   ```
   parse/grammar/experimental/
   ├── powerbuilder_fixed.lark
   ├── powerbuilder_fixed_v2.lark
   ├── powerbuilder_simple.lark
   ├── powerbuilder_core.lark
   └── powerbuilder_js.lark
   ```

2. Update test files to use the main grammars or move them to experimental tests

### Phase 2: Implement Common Grammar Usage
1. Refactor common rules into `common_grammar.lark`:
   - Common tokens (identifiers, numbers, strings)
   - Common operators
   - Whitespace handling
   - Basic expressions

2. Update main grammars to import from common_grammar:
   ```lark
   %import .common_grammar.identifier
   %import .common_grammar.number
   %import .common_grammar.string
   %import .common_grammar.operators
   ```

### Phase 3: Fix Import Issues
1. Fix datawindow.lark imports:
   - Change from importing specific tokens from powerbuilder.lark
   - Import from common_grammar.lark instead

2. Ensure all grammars use consistent import paths

### Phase 4: Update Parser Code
1. Modify parse_coordinator.py to use GrammarManager:
   ```python
   from .grammar import get_default_manager
   
   class PowerBuilderParser(PowerBuilderBaseParser):
       def __init__(self, base_path: Path | None = None) -> None:
           self.grammar_manager = get_default_manager()
           self.parser = self.grammar_manager.load_grammar("powerbuilder")
   ```

2. Remove hardcoded grammar file paths

3. Update PowerBuilderDataWindowParser and PowerBuilderQueryParser similarly

### Phase 5: Grammar Optimization
1. Consolidate the main powerbuilder.lark:
   - Remove duplicate rules identified in syntax_errors_analysis.md
   - Organize rules into logical sections
   - Add clear comments for each section

2. Create modular grammar structure:
   ```
   powerbuilder.lark (main entry, imports others)
   ├── imports common_grammar
   ├── imports pb_types
   ├── imports pb_expressions  
   ├── imports pb_statements
   └── imports pb_declarations
   ```

## Expected Benefits
1. **Reduced Confusion**: Clear separation between active and experimental grammars
2. **Better Maintainability**: Common rules in one place
3. **Improved Performance**: Grammar caching through GrammarManager
4. **Easier Testing**: Consistent grammar usage across tests
5. **Cleaner Codebase**: No hardcoded paths, proper dependency management

## Implementation Order
1. Create experimental directory and move files (5 minutes)
2. Update test files to point to new locations (10 minutes)
3. Refactor common rules into common_grammar.lark (20 minutes)
4. Update imports in main grammars (15 minutes)
5. Modify parser classes to use GrammarManager (30 minutes)
6. Test all parsers to ensure nothing breaks (20 minutes)
7. Clean up and optimize main grammars (30 minutes)

Total estimated time: ~2 hours

## Testing Strategy
1. Run existing parser tests to ensure compatibility
2. Create specific tests for common_grammar imports
3. Verify all file types still parse correctly
4. Check that grammar caching works properly
5. Ensure no performance regression

## Rollback Plan
If issues arise:
1. Git history provides full rollback capability
2. Keep backup of current working grammars
3. Implement changes incrementally with testing at each step