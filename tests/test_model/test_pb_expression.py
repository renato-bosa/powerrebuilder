"""Tests for PowerBuilder expression model."""

from model.entities.pb_expression import (
    PBAdditionExpression,
    PBAndExpression,
    PBArrayAccessExpression,
    PBAssignmentExpression,
    PBBooleanLiteral,
    PBCastExpression,
    PBCreateExpression,
    PBDivisionExpression,
    PBEqualityExpression,
    PBExpressionNode,
    PBFunctionCallExpression,
    PBGreaterThanExpression,
    PBIdentifierExpression,
    PBInequalityExpression,
    PBLessThanExpression,
    PBMemberAccessExpression,
    PBMethodCallExpression,
    PBMultiplicationExpression,
    PBNegationExpression,
    PBNotExpression,
    PBNullLiteral,
    PBNumberLiteral,
    PBOrExpression,
    PBPowerExpression,
    PBStringLiteral,
    PBSubtractionExpression,
    PBTernaryExpression,
)


class TestPBExpressionNode:
    """Test PBExpressionNode base class."""

    def test_expression_node_creation(self):


        

        """Test creating an expression node."""
        node = PBExpressionNode(expression_type="literal")
        assert node.expression_type == "literal"


class TestPBLiteralExpressions:
    """Test literal expression classes."""

    def test_number_literal(self):


        

        """Test creating a number literal."""
        num = PBNumberLiteral(value=42)
        assert num.value == 42

    def test_string_literal(self):


        

        """Test creating a string literal."""
        str_lit = PBStringLiteral(value="Hello World")
        assert str_lit.value == "Hello World"

    def test_boolean_literal(self):


        

        """Test creating a boolean literal."""
        bool_lit = PBBooleanLiteral(value=True)
        assert bool_lit.value is True

    def test_null_literal(self):


        

        """Test creating a null literal."""
        null = PBNullLiteral()
        assert hasattr(null, "value")


class TestPBBinaryExpressions:
    """Test binary expression classes."""

    def test_addition_expression(self):


        

        """Test creating an addition expression."""
        left = PBNumberLiteral(value=10)
        right = PBNumberLiteral(value=20)
        add = PBAdditionExpression(left=left, right=right)
        assert add.left.value == 10
        assert add.right.value == 20

    def test_subtraction_expression(self):


        

        """Test creating a subtraction expression."""
        left = PBNumberLiteral(value=30)
        right = PBNumberLiteral(value=10)
        sub = PBSubtractionExpression(left=left, right=right)
        assert sub.left.value == 30
        assert sub.right.value == 10

    def test_multiplication_expression(self):


        

        """Test creating a multiplication expression."""
        left = PBNumberLiteral(value=5)
        right = PBNumberLiteral(value=6)
        mult = PBMultiplicationExpression(left=left, right=right)
        assert mult.left.value == 5
        assert mult.right.value == 6

    def test_division_expression(self):


        

        """Test creating a division expression."""
        left = PBNumberLiteral(value=100)
        right = PBNumberLiteral(value=4)
        div = PBDivisionExpression(left=left, right=right)
        assert div.left.value == 100
        assert div.right.value == 4

    def test_power_expression(self):


        

        """Test creating a power expression."""
        base = PBNumberLiteral(value=2)
        exponent = PBNumberLiteral(value=8)
        power = PBPowerExpression(left=base, right=exponent)
        assert power.left.value == 2
        assert power.right.value == 8


class TestPBComparisonExpressions:
    """Test comparison expression classes."""

    def test_greater_than_expression(self):


        

        """Test creating a greater than expression."""
        left = PBNumberLiteral(value=10)
        right = PBNumberLiteral(value=5)
        gt = PBGreaterThanExpression(left=left, right=right)
        assert gt.left.value == 10
        assert gt.right.value == 5

    def test_less_than_expression(self):


        

        """Test creating a less than expression."""
        left = PBNumberLiteral(value=3)
        right = PBNumberLiteral(value=7)
        lt = PBLessThanExpression(left=left, right=right)
        assert lt.left.value == 3
        assert lt.right.value == 7

    def test_equality_expression(self):


        

        """Test creating an equality expression."""
        left = PBStringLiteral(value="test")
        right = PBStringLiteral(value="test")
        eq = PBEqualityExpression(left=left, right=right)
        assert eq.left.value == "test"
        assert eq.right.value == "test"

    def test_inequality_expression(self):


        

        """Test creating an inequality expression."""
        left = PBNumberLiteral(value=1)
        right = PBNumberLiteral(value=2)
        ne = PBInequalityExpression(left=left, right=right)
        assert ne.left.value == 1
        assert ne.right.value == 2


class TestPBLogicalExpressions:
    """Test logical expression classes."""

    def test_and_expression(self):


        

        """Test creating an AND expression."""
        left = PBBooleanLiteral(value=True)
        right = PBBooleanLiteral(value=False)
        and_expr = PBAndExpression(left=left, right=right)
        assert and_expr.left.value is True
        assert and_expr.right.value is False

    def test_or_expression(self):


        

        """Test creating an OR expression."""
        left = PBBooleanLiteral(value=True)
        right = PBBooleanLiteral(value=False)
        or_expr = PBOrExpression(left=left, right=right)
        assert or_expr.left.value is True
        assert or_expr.right.value is False

    def test_not_expression(self):


        

        """Test creating a NOT expression."""
        operand = PBBooleanLiteral(value=True)
        not_expr = PBNotExpression(operand=operand)
        assert not_expr.operand.value is True


class TestPBUnaryExpressions:
    """Test unary expression classes."""

    def test_negation_expression(self):


        

        """Test creating a negation expression."""
        operand = PBNumberLiteral(value=42)
        neg = PBNegationExpression(operand=operand)
        assert neg.operand.value == 42


class TestPBComplexExpressions:
    """Test complex expression classes."""

    def test_function_call_expression(self):


        

        """Test creating a function call expression."""
        call = PBFunctionCallExpression(
            function_name="MessageBox",
            arguments=[
                PBStringLiteral(value="Title"),
                PBStringLiteral(value="Message"),
            ],
        )
        assert call.function_name == "MessageBox"
        assert len(call.arguments) == 2

    def test_method_call_expression(self):


        

        """Test creating a method call expression."""
        obj = PBIdentifierExpression(name="window")
        method_call = PBMethodCallExpression(
            object=obj,
            method_name="Show",
            arguments=[],
        )
        assert method_call.object.name == "window"
        assert method_call.method_name == "Show"

    def test_member_access_expression(self):


        

        """Test creating a member access expression."""
        obj = PBIdentifierExpression(name="customer")
        member = PBMemberAccessExpression(
            object=obj,
            member_name="name",
        )
        assert member.object.name == "customer"
        assert member.member_name == "name"

    def test_array_access_expression(self):


        

        """Test creating an array access expression."""
        array = PBIdentifierExpression(name="items")
        index = PBNumberLiteral(value=0)
        access = PBArrayAccessExpression(
            array=array,
            index=index,
        )
        assert access.array.name == "items"
        assert access.index.value == 0

    def test_ternary_expression(self):


        

        """Test creating a ternary expression."""
        condition = PBBooleanLiteral(value=True)
        true_expr = PBStringLiteral(value="Yes")
        false_expr = PBStringLiteral(value="No")
        ternary = PBTernaryExpression(
            condition=condition,
            true_expression=true_expr,
            false_expression=false_expr,
        )
        assert ternary.condition.value is True
        assert ternary.true_expression.value == "Yes"
        assert ternary.false_expression.value == "No"

    def test_cast_expression(self):


        

        """Test creating a cast expression."""
        expr = PBNumberLiteral(value=42)
        cast = PBCastExpression(
            expression=expr,
            target_type="string",
        )
        assert cast.expression.value == 42
        assert cast.target_type == "string"

    def test_create_expression(self):


        

        """Test creating a create expression."""
        create = PBCreateExpression(
            type_name="n_customer",
            arguments=[],
        )
        assert create.type_name == "n_customer"

    def test_assignment_expression(self):


        

        """Test creating an assignment expression."""
        target = PBIdentifierExpression(name="total")
        value = PBNumberLiteral(value=100)
        assign = PBAssignmentExpression(
            target=target,
            value=value,
        )
        assert assign.target.name == "total"
        assert assign.value.value == 100
