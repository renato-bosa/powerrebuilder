#!/usr/bin/env python3
"""Script to demonstrate expression optimization on PowerBuilder code.

This script shows how the expression optimizer can simplify expressions
in parsed PowerBuilder code, improving performance and readability.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from model.expressions import (
    PBBinaryOperator,
    PBBooleanLiteral,
    PBNumberLiteral,
    PBStringLiteral,
    PBTernaryExpression,
    PBVariable,
)
from model.optimization.expression_optimizer import ExpressionOptimizer


def print_expression(expr, indent=0) -> None:




    """Pretty print an expression tree."""
    prefix = "  " * indent
    if isinstance(expr, PBNumberLiteral):
        print(f"{prefix}Number: {expr.value}")
    elif isinstance(expr, PBStringLiteral):
        print(f"{prefix}String: '{expr.value}'")
    elif isinstance(expr, PBBooleanLiteral):
        print(f"{prefix}Boolean: {expr.value}")
    elif isinstance(expr, PBVariable):
        print(f"{prefix}Variable: {expr.name}")
    elif isinstance(expr, PBBinaryOperator):
        print(f"{prefix}Binary: {expr.operator}")
        print_expression(expr.left, indent + 1)
        print_expression(expr.right, indent + 1)
    elif isinstance(expr, PBTernaryExpression):
        print(f"{prefix}Ternary:")
        print(f"{prefix}  Condition:")
        print_expression(expr.condition, indent + 2)
        print(f"{prefix}  True:")
        print_expression(expr.true_expr, indent + 2)
        print(f"{prefix}  False:")
        print_expression(expr.false_expr, indent + 2)
    else:
        print(f"{prefix}{type(expr).__name__}")


def main() -> None:







    """Demonstrate expression optimization."""
    optimizer = ExpressionOptimizer()

    print("Expression Optimization Examples")
    print("=" * 50)

    # Example 1: Constant folding
    print("\n1. Constant Folding: (2 + 3) * 4")
    expr1 = PBBinaryOperator(
        left=PBBinaryOperator(
            left=PBNumberLiteral(value=2),
            operator="+",
            right=PBNumberLiteral(value=3),
        ),
        operator="*",
        right=PBNumberLiteral(value=4),
    )

    print("Original:")
    print_expression(expr1)

    result1 = optimizer.optimize(expr1)
    print("\nOptimized:")
    print_expression(result1)
    print(f"Optimizations applied: {optimizer.optimizations_applied}")

    # Example 2: Algebraic simplification
    print("\n" + "=" * 50)
    print("\n2. Algebraic Simplification: x * 1 + 0")
    expr2 = PBBinaryOperator(
        left=PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="*",
            right=PBNumberLiteral(value=1),
        ),
        operator="+",
        right=PBNumberLiteral(value=0),
    )

    print("Original:")
    print_expression(expr2)

    result2 = optimizer.optimize(expr2)
    print("\nOptimized:")
    print_expression(result2)
    print(f"Optimizations applied: {optimizer.optimizations_applied}")

    # Example 3: Boolean optimization
    print("\n" + "=" * 50)
    print("\n3. Boolean Optimization: true AND x OR false")
    expr3 = PBBinaryOperator(
        left=PBBinaryOperator(
            left=PBBooleanLiteral(value=True),
            operator="AND",
            right=PBVariable(name="x"),
        ),
        operator="OR",
        right=PBBooleanLiteral(value=False),
    )

    print("Original:")
    print_expression(expr3)

    result3 = optimizer.optimize(expr3)
    print("\nOptimized:")
    print_expression(result3)
    print(f"Optimizations applied: {optimizer.optimizations_applied}")

    # Example 4: Ternary with constant condition
    print("\n" + "=" * 50)
    print("\n4. Ternary Optimization: false ? expensive_call() : 42")
    expr4 = PBTernaryExpression(
        condition=PBBooleanLiteral(value=False),
        true_expr=PBVariable(name="expensive_call()"),
        false_expr=PBNumberLiteral(value=42),
    )

    print("Original:")
    print_expression(expr4)

    result4 = optimizer.optimize(expr4)
    print("\nOptimized:")
    print_expression(result4)
    print(f"Optimizations applied: {optimizer.optimizations_applied}")

    # Example 5: String concatenation
    print("\n" + "=" * 50)
    print('\n5. String Concatenation: "Hello" + " " + "World"')
    expr5 = PBBinaryOperator(
        left=PBBinaryOperator(
            left=PBStringLiteral(value="Hello"),
            operator="+",
            right=PBStringLiteral(value=" "),
        ),
        operator="+",
        right=PBStringLiteral(value="World"),
    )

    print("Original:")
    print_expression(expr5)

    result5 = optimizer.optimize(expr5)
    print("\nOptimized:")
    print_expression(result5)
    print(f"Optimizations applied: {optimizer.optimizations_applied}")


if __name__ == "__main__":
    main()
