# SQL Grammar Rules Without Transformer Methods Analysis

## Overview
This analysis identifies SQL grammar rules from `parse/grammar/sql.lark` that don't have corresponding transformer methods in `parse/visitors/sql_transformer.py`. These missing methods could cause `NotImplementedError` when parsing SQL statements.

## Missing Transformer Methods

### 1. **Expression Hierarchy Rules (Pass-through rules)**
These rules are part of the expression precedence hierarchy and are handled by the `__default__` method when they have a single child:

- `additive_expr` - Pass-through to arithmetic operations (bin_plus, bin_minus, concat) or mult_expr
- `mult_expr` - Pass-through to multiplication operations (multiply, divide, modulo) or unary_expr  
- `unary_expr` - Pass-through to unary operations (unary_minus, unary_plus, etc.) or primary_expr
- `logical_and_expr` - Pass-through to logical_and or equality_expr
- `logical_or_expr` - Pass-through to logical_or or logical_and_expr
- `comparison_expr` - Pass-through to comparison operations or additive_expr
- `equality_expr` - Pass-through to equality operations or comparison_expr

**Impact**: LOW - These are handled by `__default__` method which returns the single child for pass-through rules.

### 2. **Operator Helper Rules**
These are terminal/token rules that define operators used in other rules:

- `_comp_operator`: `"<" | ">" | "<=" | ">="`
- `_like_operator`: `"NOT"i? "LIKE"i`
- `_between_operator`: `"NOT"i? "BETWEEN"i`
- `_in_operator`: `"NOT"i? "IN"i`

**Impact**: LOW - These are consumed by parent rules (comp_op_list, like_op, between_op, in_op_list/in_op_subquery) which have transformer methods.

### 3. **Function Argument Helper Rules**
These help parse function arguments:

- `_fn_args_inner`: `expr` - Simple wrapper for expression arguments
- `_fn_args_etoile`: `STAR` - For COUNT(*) style functions
- `_fn_args_optional`: `_fn_args_inner | _fn_args_etoile`

**Impact**: LOW - These are handled within the `function_call` transformer method.

### 4. **Other Helper Rules**
- `_simple_column_list`: `simple_name (COMMA simple_name)*` - Used in USING clause of joins
- `_table_alias_spec`: `("AS"i)? table_alias` - Handled by a transformer method

**Impact**: LOW - Used as components in other rules.

### 5. **Important Missing Rules**

#### `distinct_clause: "DISTINCT"i | "ALL"i`
**Impact**: MEDIUM - Used in SELECT statements. Currently handled in `select_core` by checking token types directly, but could fail if the grammar changes.

#### `join_constraint: "ON"i expr | "USING"i LPAR _simple_column_list RPAR`
**Impact**: HIGH - Used in JOIN clauses. Missing transformer could cause NotImplementedError for queries with JOIN ON or JOIN USING.

#### `join_operator: "INNER"i? "JOIN"i -> simple_join | ...`
**Impact**: MEDIUM - Has aliased rules (simple_join, left_join, etc.) which DO have transformers, so the impact is reduced.

#### `result_column: STAR -> result_star | expr ("AS"i? column_alias)? -> result_expr`
**Impact**: MEDIUM - Has aliased rules (result_star, result_expr) which have transformers.

#### `table_name_ref: fully_qualified_name -> fqn_as_table_component | simple_name -> simple_name_as_table_component`
**Impact**: MEDIUM - Has aliased rules which have transformers.

## Most Critical Missing Transformers

The following missing transformers are most likely to cause `NotImplementedError` for common SQL statements:

1. **`join_constraint`** - Will fail on any JOIN with ON or USING clause
2. **`distinct_clause`** - Could fail if token handling changes in select_core
3. **Expression hierarchy rules** - Could fail if `__default__` method's pass-through logic breaks

## Recommendations

1. **Add `join_constraint` transformer** - This is the most critical missing method:
```python
def join_constraint(self, items: list[Any]) -> dict[str, Any]:
    """Transform join constraint (ON expr or USING columns)."""
    if items[0].type == "ON":
        return {"on": items[1]}  # expr
    else:  # USING
        # items: [USING, LPAR, column_list, RPAR]
        return {"using": items[2]}  # column list
```

2. **Add `distinct_clause` transformer** for cleaner handling:
```python
def distinct_clause(self, items: list[Any]) -> str:
    """Transform DISTINCT or ALL clause."""
    return items[0].value.upper()
```

3. **Consider adding explicit transformers for expression hierarchy rules** instead of relying on `__default__` for better error messages and debugging.