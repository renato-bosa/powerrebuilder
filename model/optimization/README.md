# Expression Optimization in PowerBuilder Model

This directory contains expression optimization functionality for the PowerBuilder AST model. The optimizers transform expressions to improve performance and readability while maintaining semantic equivalence.

## Overview

The optimization system consists of two main components:

1. **ExpressionOptimizer** - Basic expression optimizer with fundamental optimizations
2. **AdvancedExpressionOptimizer** - Extended optimizer with sophisticated techniques

## Basic Optimizations (ExpressionOptimizer)

### Constant Folding
Evaluates operations on literal values at compile time:
- Arithmetic: `2 + 3` → `5`
- String concatenation: `"Hello" + " World"` → `"Hello World"`
- Boolean operations: `true AND false` → `false`
- Comparisons: `5 > 3` → `true`
- Power operations: `2 ^ 3` → `8`

### Algebraic Simplification
Applies mathematical identities:
- Addition: `x + 0` → `x`, `0 + x` → `x`
- Subtraction: `x - 0` → `x`, `x - x` → `0`
- Multiplication: `x * 1` → `x`, `x * 0` → `0`
- Division: `x / 1` → `x`
- Power: `x ^ 0` → `1`, `x ^ 1` → `x`

### Boolean Optimization
Simplifies boolean expressions:
- AND operations: `true AND x` → `x`, `false AND x` → `false`
- OR operations: `false OR x` → `x`, `true OR x` → `true`
- Double negation: `NOT NOT x` → `x`

### Ternary Expression Optimization
Evaluates ternary expressions with constant conditions:
- `true ? a : b` → `a`
- `false ? a : b` → `b`

### Null Handling
Properly handles null values in operations according to PowerBuilder semantics.

## Advanced Optimizations (AdvancedExpressionOptimizer)

### Strength Reduction
Converts expensive operations to cheaper equivalents:
- `x * 2` → `x + x` (addition is often faster than multiplication)
- Identifies opportunities for bit shifts (logged for code generation)

### Distributive Law
Applies distribution when beneficial:
- `2 * (x + 3)` → `2 * x + 6` (allows constant folding)

### Associative Law
Rearranges expressions to group constants:
- `(x + 2) + 3` → `x + 5`
- `(y * 2) * 3` → `y * 6`

### Common Subexpression Elimination (CSE)
Identifies repeated subexpressions that could be computed once and reused.
Currently detects and logs opportunities for future implementation.

### Pattern Matching
Framework for applying complex pattern-based transformations.
Extensible system for adding new optimization patterns.

## Usage

### Basic Optimization
```python
from model.optimization.expression_optimizer import ExpressionOptimizer
from model.entities.expressions import PBBinaryOperator, PBNumberLiteral

# Create an expression: 2 + 3
expr = PBBinaryOperator(
    left=PBNumberLiteral(value=2),
    operator="+",
    right=PBNumberLiteral(value=3)
)

# Optimize it
optimizer = ExpressionOptimizer()
result = optimizer.optimize(expr)
# result is PBNumberLiteral(value=5)
```

### Advanced Optimization
```python
from model.optimization.advanced_expression_optimizer import optimize_expression_advanced

# Create a complex expression
expr = create_complex_expression()

# Apply advanced optimizations
result = optimize_expression_advanced(expr)
```

## Implementation Details

### Expression Hashing
The advanced optimizer uses expression hashing to identify common subexpressions.
Hashes are based on expression type, operator/value, and child hashes.

### Optimization Passes
Optimizations are applied in multiple passes:
1. Common subexpression collection
2. Basic optimizations (constant folding, algebraic, boolean)
3. Advanced optimizations (strength reduction, distributive, associative)
4. Pattern matching
5. Common subexpression elimination

### Recursion
All optimizations recursively process subexpressions, ensuring nested expressions
are fully optimized.

## Testing

Comprehensive test suites are provided:
- `test_expression_optimizer.py` - Tests for basic optimizations
- `test_advanced_expression_optimizer.py` - Tests for advanced optimizations

Run tests with:
```bash
pytest tests/test_model/test_optimization/
```

## Future Enhancements

Potential improvements for future versions:
1. Full CSE implementation with temporary variable generation
2. More sophisticated pattern matching with a DSL
3. Loop-invariant code motion
4. Dead code elimination
5. Type-specific optimizations
6. Profile-guided optimization
7. Optimization level controls

## Performance Considerations

- Optimizations are applied during AST construction, not at runtime
- The optimizer tracks the number of optimizations applied for debugging
- Complex expressions may require multiple optimization passes
- Some optimizations may increase code size while reducing computation

## PowerBuilder-Specific Considerations

The optimizers respect PowerBuilder semantics:
- Null propagation in operations
- 1-based array indexing
- PowerBuilder-specific operators (`=` for equality, `<>` for inequality)
- Case-insensitive comparisons for strings (when applicable)