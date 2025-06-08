# PowerBuilder Parser to AST Implementation Plan

## Current State Analysis

### Problems Identified:
1. **Grammar Reduce/Reduce Conflicts**: The current grammar has 300+ reduce/reduce conflicts due to:
   - Overlapping expression rules (expression includes atom, but atom also includes array_access and function_call which are also in expression)
   - Ambiguous condition vs expression rules (both include comparison)
   - Multiple definitions of the same rules throughout the grammar

2. **Grammar Structure Issues**:
   - The grammar tries to combine multiple different grammar styles
   - It has rules from both procedural and declarative contexts mixed together
   - LALR parser cannot handle the current ambiguities

3. **Missing AST Transformation**:
   - No transformer classes to convert parse trees to AST nodes
   - No integration between parser output and existing AST node classes

## Solution Approach

### Phase 1: Fix Grammar Structure (Immediate)

1. **Restructure Expression Hierarchy**:
   ```lark
   // Clear precedence hierarchy
   expression: logical_or
   logical_or: logical_and (OR logical_and)*
   logical_and: comparison (AND comparison)*
   comparison: additive ((GT | LT | GE | LE | EQ | NE) additive)?
   additive: multiplicative ((PLUS | MINUS) multiplicative)*
   multiplicative: unary ((MULT | DIV | MOD) unary)*
   unary: (PLUS | MINUS | NOT)? power
   power: postfix (POWER postfix)*
   postfix: primary (DOT IDENTIFIER | LBRACK expression RBRACK | LPAR argument_list? RPAR)*
   primary: IDENTIFIER | INT | STRING | BOOLEAN | DATE_LIT | TIME_LIT 
           | LPAR expression RPAR | array_literal
   ```

2. **Separate Contexts**:
   - Create separate start rules for different file types
   - Use context-specific grammars that can be combined

3. **Remove Duplicate Rules**:
   - Consolidate all duplicate definitions
   - Use imports from common_grammar.lark

### Phase 2: Implement AST Transformation (Next)

1. **Create Transformer Classes**:
   ```python
   class PowerBuilderTransformer(Transformer):
       def expression(self, items):
           return create_appropriate_ast_node(items)
       
       def function_declaration(self, items):
           return FunctionNode(...)
   ```

2. **Map Parse Tree to AST Nodes**:
   - variable_declaration → VariableDeclarationNode
   - function_declaration → FunctionNode
   - if_statement → IfStatementNode
   - etc.

3. **Integration Points**:
   - Update PowerBuilderParser.parse() to return AST instead of parse tree
   - Connect to existing AST node classes in model/ast/

### Phase 3: Connect to Pipeline (Following)

1. **Update Parse Coordinator**:
   - Modify parse_coordinator.py to use new transformer
   - Ensure compatibility with existing pipeline stages

2. **Test with Real Files**:
   - Start with simple .srw files
   - Progress to complex constructs
   - Validate against existing test cases

## Implementation Steps

### Step 1: Create Modular Grammar (Today)
- Split grammar into modules: expressions.lark, statements.lark, declarations.lark
- Use clear precedence rules
- Test each module independently

### Step 2: Build Transformer (Tomorrow)
- Create base transformer class
- Implement transformation for each grammar rule
- Map to existing AST nodes

### Step 3: Integration Testing (Day 3)
- Test parser with all fixture files
- Ensure AST output matches expected structure
- Connect to decompilation pipeline

## Success Criteria

1. **Grammar**: Zero reduce/reduce conflicts
2. **Parser**: Successfully parses all test fixtures
3. **AST**: Generates correct AST nodes for all constructs
4. **Pipeline**: Integrates seamlessly with existing stages

## Risk Mitigation

1. **Backwards Compatibility**: Keep old parser available during transition
2. **Incremental Testing**: Test each component before integration
3. **Fallback Strategy**: Can use tree-sitter grammar as alternative if Lark proves unsuitable