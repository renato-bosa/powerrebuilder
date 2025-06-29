#!/usr/bin/env python3
"""Test that the expression evaluator is complete and handles all expression types."""

from model.expressions.evaluator import EvaluationContext, ExpressionEvaluator
from model.expressions import (
    PBNumberLiteral, PBStringLiteral, PBBooleanLiteral, PBNullLiteral,
    PBVariable, PBFieldReference, PBBinaryOperator, PBUnaryOperator,
    PBArrayAccess, PBFunctionCall, PBMethodCall, PBConstructorCall,
    PBCastExpression, PBTernaryExpression, PBThisExpression,
    PBParentExpression, PBSuperExpression, PBConcatenationOperator,
    PBPowerOperator, PBSqlVariableExpression, PBDynamicSqlExpression
)
from model.utils.errors import ModelError
import pytest


def test_literal_expressions():






    """Test evaluation of literal expressions."""
    evaluator = ExpressionEvaluator()

    # Number literal
    num_expr = PBNumberLiteral(value=42.5)
    assert evaluator.evaluate(num_expr) == 42.5

    # String literal
    str_expr = PBStringLiteral(value="Hello, World!")
    assert evaluator.evaluate(str_expr) == "Hello, World!"

    # Boolean literal
    bool_expr = PBBooleanLiteral(value=True)
    assert evaluator.evaluate(bool_expr) is True

    # Null literal
    null_expr = PBNullLiteral()
    assert evaluator.evaluate(null_expr) is None

    print("✓ All literal expressions evaluated correctly")


def test_variable_and_field_access():






    """Test variable references and field access."""
    context = EvaluationContext(
        variables={
            "user": {"name": "John", "age": 30},
            "count": 10
        }
    )
    evaluator = ExpressionEvaluator(context)

    # Variable reference
    var_expr = PBVariable(name="count")
    assert evaluator.evaluate(var_expr) == 10

    # Field reference
    field_expr = PBFieldReference(
        object=PBVariable(name="user"),
        field_name="name"
    )
    assert evaluator.evaluate(field_expr) == "John"

    print("✓ Variable and field access working correctly")


def test_binary_operations():






    """Test binary operations."""
    evaluator = ExpressionEvaluator()

    # Arithmetic operations
    add_expr = PBBinaryOperator(
        left=PBNumberLiteral(value=10),
        right=PBNumberLiteral(value=5),
        operator="+"
    )
    assert evaluator.evaluate(add_expr) == 15

    # String concatenation
    concat_expr = PBBinaryOperator(
        left=PBStringLiteral(value="Hello "),
        right=PBStringLiteral(value="World"),
        operator="+"
    )
    assert evaluator.evaluate(concat_expr) == "Hello World"

    # Comparison (PowerBuilder = maps to ==)
    eq_expr = PBBinaryOperator(
        left=PBNumberLiteral(value=10),
        right=PBNumberLiteral(value=10),
        operator="="
    )
    assert evaluator.evaluate(eq_expr) is True

    # PowerBuilder not equal (<>)
    ne_expr = PBBinaryOperator(
        left=PBNumberLiteral(value=10),
        right=PBNumberLiteral(value=5),
        operator="<>"
    )
    assert evaluator.evaluate(ne_expr) is True

    print("✓ Binary operations working correctly")


def test_unary_operations():






    """Test unary operations."""
    evaluator = ExpressionEvaluator()

    # Negation
    neg_expr = PBUnaryOperator(
        operand=PBNumberLiteral(value=42),
        operator="-"
    )
    assert evaluator.evaluate(neg_expr) == -42

    # Boolean not
    not_expr = PBUnaryOperator(
        operand=PBBooleanLiteral(value=True),
        operator="not"
    )
    assert evaluator.evaluate(not_expr) is False

    print("✓ Unary operations working correctly")


def test_array_access():






    """Test array access expressions."""
    context = EvaluationContext(
        variables={
            "array": [10, 20, 30, 40],
            "matrix": [[1, 2], [3, 4]]
        }
    )
    evaluator = ExpressionEvaluator(context)

    # Single dimension array (PowerBuilder uses 1-based indexing)
    array_expr = PBArrayAccess(
        array=PBVariable(name="array"),
        indices=[PBNumberLiteral(value=2)]
    )
    assert evaluator.evaluate(array_expr) == 20  # Index 2 -> position 1

    # Multi-dimensional array
    matrix_expr = PBArrayAccess(
        array=PBVariable(name="matrix"),
        indices=[PBNumberLiteral(value=2), PBNumberLiteral(value=1)]
    )
    assert evaluator.evaluate(matrix_expr) == 3  # [2,1] -> [1,0]

    print("✓ Array access working correctly")


def test_function_calls():






    """Test function call expressions."""
    def add_numbers(a, b):

        return a + b

    def get_length(s):


        return len(s)

    context = EvaluationContext(
        functions={
            "add": add_numbers,
            "len": get_length
        }
    )
    evaluator = ExpressionEvaluator(context)

    # Function call with arguments
    func_expr = PBFunctionCall(
        function_name="add",
        arguments=[
            PBNumberLiteral(value=10),
            PBNumberLiteral(value=20)
        ]
    )
    assert evaluator.evaluate(func_expr) == 30

    # Function call with string argument
    len_expr = PBFunctionCall(
        function_name="len",
        arguments=[PBStringLiteral(value="Hello")]
    )
    assert evaluator.evaluate(len_expr) == 5

    print("✓ Function calls working correctly")


def test_method_calls():






    """Test method call expressions."""
    class TestObject:
        def __init__(self, value):

            self.value = value

        def get_value(self):


            return self.value

        def add(self, n):


            return self.value + n

    context = EvaluationContext(
        variables={"obj": TestObject(42)}
    )
    evaluator = ExpressionEvaluator(context)

    # Method call without arguments
    method_expr = PBMethodCall(
        object=PBVariable(name="obj"),
        function_name="get_value",
        arguments=[]
    )
    assert evaluator.evaluate(method_expr) == 42

    # Method call with arguments
    add_expr = PBMethodCall(
        object=PBVariable(name="obj"),
        function_name="add",
        arguments=[PBNumberLiteral(value=8)]
    )
    assert evaluator.evaluate(add_expr) == 50

    print("✓ Method calls working correctly")


def test_constructor_calls():






    """Test constructor call expressions."""
    class TestClass:
        def __init__(self, name, value=0):
            self.name = name
            self.value = value

    context = EvaluationContext(
        functions={"TestClass": TestClass}
    )
    evaluator = ExpressionEvaluator(context)

    # Constructor call with arguments
    ctor_expr = PBConstructorCall(
        class_name="TestClass",
        arguments=[
            PBStringLiteral(value="test"),
            PBNumberLiteral(value=100)
        ]
    )
    obj = evaluator.evaluate(ctor_expr)
    assert isinstance(obj, TestClass)
    assert obj.name == "test"
    assert obj.value == 100

    print("✓ Constructor calls working correctly")


def test_type_casting():






    """Test type cast expressions."""
    evaluator = ExpressionEvaluator()

    # Cast to string
    str_cast = PBCastExpression(
        expression=PBNumberLiteral(value=42),
        target_type="string"
    )
    assert evaluator.evaluate(str_cast) == "42"

    # Cast to integer
    int_cast = PBCastExpression(
        expression=PBStringLiteral(value="100"),
        target_type="integer"
    )
    assert evaluator.evaluate(int_cast) == 100

    # Cast to boolean
    bool_cast = PBCastExpression(
        expression=PBNumberLiteral(value=1),
        target_type="boolean"
    )
    assert evaluator.evaluate(bool_cast) is True

    print("✓ Type casting working correctly")


def test_ternary_expressions():






    """Test ternary conditional expressions."""
    evaluator = ExpressionEvaluator()

    # True condition
    ternary_true = PBTernaryExpression(
        condition=PBBooleanLiteral(value=True),
        true_expr=PBStringLiteral(value="Yes"),
        false_expr=PBStringLiteral(value="No")
    )
    assert evaluator.evaluate(ternary_true) == "Yes"

    # False condition
    ternary_false = PBTernaryExpression(
        condition=PBBooleanLiteral(value=False),
        true_expr=PBNumberLiteral(value=1),
        false_expr=PBNumberLiteral(value=0)
    )
    assert evaluator.evaluate(ternary_false) == 0

    print("✓ Ternary expressions working correctly")


def test_special_references():






    """Test special reference expressions (this, parent, super)."""
    class TestWindow:
        def __init__(self):

            self.name = "TestWindow"

    class ParentWindow:
        def __init__(self):

            self.name = "ParentWindow"

    context = EvaluationContext(
        variables={
            "this": TestWindow(),
            "parent": ParentWindow(),
            "super": ParentWindow  # Class reference
        }
    )
    evaluator = ExpressionEvaluator(context)

    # This reference
    this_expr = PBThisExpression()
    this_obj = evaluator.evaluate(this_expr)
    assert this_obj.name == "TestWindow"

    # Parent reference
    parent_expr = PBParentExpression()
    parent_obj = evaluator.evaluate(parent_expr)
    assert parent_obj.name == "ParentWindow"

    # Super reference
    super_expr = PBSuperExpression()
    super_ref = evaluator.evaluate(super_expr)
    assert super_ref == ParentWindow

    print("✓ Special references working correctly")


def test_powerbuilder_specific_operators():






    """Test PowerBuilder-specific operators."""
    evaluator = ExpressionEvaluator()

    # String concatenation operator (multiple operands)
    concat_expr = PBConcatenationOperator(
        operands=[
            PBStringLiteral(value="Hello"),
            PBStringLiteral(value=" "),
            PBStringLiteral(value="World"),
            PBStringLiteral(value="!")
        ]
    )
    assert evaluator.evaluate(concat_expr) == "Hello World!"

    # Power operator (^)
    power_expr = PBPowerOperator(
        base=PBNumberLiteral(value=2),
        exponent=PBNumberLiteral(value=3)
    )
    assert evaluator.evaluate(power_expr) == 8

    print("✓ PowerBuilder-specific operators working correctly")


def test_sql_expressions():






    """Test SQL-related expressions."""
    context = EvaluationContext(
        variables={"customer_id": 123}
    )
    evaluator = ExpressionEvaluator(context)

    # SQL variable expression (bound)
    sql_var_bound = PBSqlVariableExpression(variable_name="customer_id")
    assert evaluator.evaluate(sql_var_bound) == 123

    # SQL variable expression (unbound - returns placeholder)
    sql_var_unbound = PBSqlVariableExpression(variable_name="order_id")
    assert evaluator.evaluate(sql_var_unbound) == ":order_id"

    # Dynamic SQL expression
    dynamic_sql = PBDynamicSqlExpression(
        sql_parts=[
            "SELECT * FROM customers WHERE id = ",
            PBSqlVariableExpression(variable_name="customer_id"),
            " AND active = ",
            PBBooleanLiteral(value=True)
        ]
    )
    assert evaluator.evaluate(dynamic_sql) == "SELECT * FROM customers WHERE id = 123 AND active = True"

    print("✓ SQL expressions working correctly")


def test_error_handling():






    """Test error handling in expression evaluation."""
    evaluator = ExpressionEvaluator()

    # Undefined variable
    with pytest.raises(ModelError, match="Undefined variable"):
        evaluator.evaluate(PBVariable(name="undefined"))

    # Undefined function
    with pytest.raises(ModelError, match="Undefined function"):
        evaluator.evaluate(PBFunctionCall(function_name="undefined", arguments=[]))

    # Division by zero
    with pytest.raises(ModelError, match="Division by zero"):
        evaluator.evaluate(PBBinaryOperator(
            left=PBNumberLiteral(value=10),
            right=PBNumberLiteral(value=0),
            operator="/"
        ))

    # Invalid cast
    with pytest.raises(ModelError, match="Error casting"):
        evaluator.evaluate(PBCastExpression(
            expression=PBStringLiteral(value="not a number"),
            target_type="integer"
        ))

    print("✓ Error handling working correctly")


def test_complex_expressions():






    """Test complex nested expressions."""
    context = EvaluationContext(
        variables={
            "items": [{"price": 10.0}, {"price": 20.0}, {"price": 30.0}],
            "tax_rate": 0.08
        },
        functions={
            "round": round
        }
    )
    evaluator = ExpressionEvaluator(context)

    # Complex nested expression: round((items[2].price * (1 + tax_rate)), 2)
    complex_expr = PBFunctionCall(
        function_name="round",
        arguments=[
            PBBinaryOperator(
                left=PBFieldReference(
                    object=PBArrayAccess(
                        array=PBVariable(name="items"),
                        indices=[PBNumberLiteral(value=2)]  # Second item (1-based)
                    ),
                    field_name="price"
                ),
                right=PBBinaryOperator(
                    left=PBNumberLiteral(value=1),
                    right=PBVariable(name="tax_rate"),
                    operator="+"
                ),
                operator="*"
            ),
            PBNumberLiteral(value=2)
        ]
    )
    # items[2].price = 20.0, (1 + 0.08) = 1.08, 20.0 * 1.08 = 21.6
    assert evaluator.evaluate(complex_expr) == 21.6

    print("✓ Complex nested expressions working correctly")


def test_expression_completeness():






    """Test that all major expression types are evaluable."""
    expressions_tested = [
        # Literals
        PBNumberLiteral, PBStringLiteral, PBBooleanLiteral, PBNullLiteral,
        # Variables and references
        PBVariable, PBFieldReference,
        # Operators
        PBBinaryOperator, PBUnaryOperator,
        # Complex expressions
        PBArrayAccess, PBFunctionCall, PBMethodCall, PBConstructorCall,
        PBCastExpression, PBTernaryExpression,
        # Special references
        PBThisExpression, PBParentExpression, PBSuperExpression,
        # PowerBuilder-specific
        PBConcatenationOperator, PBPowerOperator,
        # SQL-related
        PBSqlVariableExpression, PBDynamicSqlExpression
    ]

    print(f"\n✅ Expression evaluator is complete!")
    print(f"   Tested {len(expressions_tested)} expression types")
    print(f"   All expressions are evaluable without NotImplementedError")


if __name__ == "__main__":
    test_literal_expressions()
    test_variable_and_field_access()
    test_binary_operations()
    test_unary_operations()
    test_array_access()
    test_function_calls()
    test_method_calls()
    test_constructor_calls()
    test_type_casting()
    test_ternary_expressions()
    test_special_references()
    test_powerbuilder_specific_operators()
    test_sql_expressions()
    test_error_handling()
    test_complex_expressions()
    test_expression_completeness()

    print("\n✅ All expression evaluator tests passed!")