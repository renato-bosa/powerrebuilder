"""Tests for advanced expression optimizer."""


from model.entities.expressions import (
    PBBinaryOperator,
    PBNumberLiteral,
    PBVariable,
    PBFunctionCall,
)
from model.optimization.advanced_expression_optimizer import (
    AdvancedExpressionOptimizer,
    ExpressionHash,
    optimize_expression_advanced,
)


class TestStrengthReduction:
    """Test strength reduction optimizations."""
    
    def test_multiply_by_two_to_addition(self):

    
        
    
        """Test x * 2 -> x + x optimization."""
        optimizer = AdvancedExpressionOptimizer()
        var = PBVariable(name="x")
        
        # x * 2 -> x + x
        expr = PBBinaryOperator(
            left=var,
            operator="*",
            right=PBNumberLiteral(value=2)
        )
        
        result = optimizer.optimize(expr)
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "+"
        assert isinstance(result.left, PBVariable)
        assert isinstance(result.right, PBVariable)
        assert result.left.name == "x"
        assert result.right.name == "x"
        assert optimizer.optimizations_applied >= 1
    
    def test_nested_strength_reduction(self):

    
        
    
        """Test strength reduction in nested expressions."""
        optimizer = AdvancedExpressionOptimizer()
        var = PBVariable(name="y")
        
        # (y * 2) + 5 -> (y + y) + 5
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=var,
                operator="*",
                right=PBNumberLiteral(value=2)
            ),
            operator="+",
            right=PBNumberLiteral(value=5)
        )
        
        result = optimizer.optimize(expr)
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "+"
        assert isinstance(result.left, PBBinaryOperator)
        assert result.left.operator == "+"
    
    def test_function_argument_optimization(self):

    
        
    
        """Test optimization of function arguments."""
        optimizer = AdvancedExpressionOptimizer()
        
        # f(x * 2, 3 + 4) -> f(x + x, 7)
        expr = PBFunctionCall(
            function_name="f",
            arguments=[
                PBBinaryOperator(
                    left=PBVariable(name="x"),
                    operator="*",
                    right=PBNumberLiteral(value=2)
                ),
                PBBinaryOperator(
                    left=PBNumberLiteral(value=3),
                    operator="+",
                    right=PBNumberLiteral(value=4)
                )
            ]
        )
        
        result = optimizer.optimize(expr)
        assert isinstance(result, PBFunctionCall)
        assert len(result.arguments) == 2
        # First argument should be x + x
        assert isinstance(result.arguments[0], PBBinaryOperator)
        assert result.arguments[0].operator == "+"
        # Second argument should be folded to 7
        assert isinstance(result.arguments[1], PBNumberLiteral)
        assert result.arguments[1].value == 7


class TestDistributiveLaw:
    """Test distributive law optimizations."""
    
    def test_distribute_multiplication_over_addition(self):

    
        
    
        """Test a * (b + c) distribution when beneficial."""
        optimizer = AdvancedExpressionOptimizer()
        
        # 2 * (x + 3) -> 2 * x + 2 * 3 -> 2 * x + 6
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=2),
            operator="*",
            right=PBBinaryOperator(
                left=PBVariable(name="x"),
                operator="+",
                right=PBNumberLiteral(value=3)
            )
        )
        
        result = optimizer.optimize(expr)
        # Should distribute and then fold constants
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "+"
    
    def test_no_distribute_when_not_beneficial(self):

    
        
    
        """Test that distribution doesn't happen when not beneficial."""
        optimizer = AdvancedExpressionOptimizer()
        
        # x * (y + z) should not distribute (no simplification possible)
        expr = PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="*",
            right=PBBinaryOperator(
                left=PBVariable(name="y"),
                operator="+",
                right=PBVariable(name="z")
            )
        )
        
        result = optimizer.optimize(expr)
        # Should remain as is
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "*"
        assert isinstance(result.right, PBBinaryOperator)
        assert result.right.operator == "+"


class TestAssociativeLaw:
    """Test associative law optimizations."""
    
    def test_reassociate_addition_with_constants(self):

    
        
    
        """Test (a + 2) + 3 -> a + 5."""
        optimizer = AdvancedExpressionOptimizer()
        
        # (x + 2) + 3 -> x + 5
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBVariable(name="x"),
                operator="+",
                right=PBNumberLiteral(value=2)
            ),
            operator="+",
            right=PBNumberLiteral(value=3)
        )
        
        result = optimizer.optimize(expr)
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "+"
        assert isinstance(result.left, PBVariable)
        assert result.left.name == "x"
        assert isinstance(result.right, PBNumberLiteral)
        assert result.right.value == 5
    
    def test_reassociate_multiplication_with_constants(self):

    
        
    
        """Test (a * 2) * 3 -> a * 6."""
        optimizer = AdvancedExpressionOptimizer()
        
        # (y * 2) * 3 -> y * 6
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBVariable(name="y"),
                operator="*",
                right=PBNumberLiteral(value=2)
            ),
            operator="*",
            right=PBNumberLiteral(value=3)
        )
        
        result = optimizer.optimize(expr)
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "*"
        assert isinstance(result.left, PBVariable)
        assert result.left.name == "y"
        assert isinstance(result.right, PBNumberLiteral)
        assert result.right.value == 6
    
    def test_complex_reassociation(self):

    
        
    
        """Test complex reassociation scenarios."""
        optimizer = AdvancedExpressionOptimizer()
        
        # ((x + 1) + 2) + 3 -> x + 6
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBBinaryOperator(
                    left=PBVariable(name="x"),
                    operator="+",
                    right=PBNumberLiteral(value=1)
                ),
                operator="+",
                right=PBNumberLiteral(value=2)
            ),
            operator="+",
            right=PBNumberLiteral(value=3)
        )
        
        result = optimizer.optimize(expr)
        # Should eventually simplify to x + 6
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "+"


class TestCommonSubexpressionElimination:
    """Test common subexpression elimination."""
    
    def test_detect_common_subexpressions(self):

    
        
    
        """Test detection of common subexpressions."""
        optimizer = AdvancedExpressionOptimizer()
        
        # (x + y) * (x + y) has common subexpression x + y
        subexpr = PBBinaryOperator(
            left=PBVariable(name="x"),
            operator="+",
            right=PBVariable(name="y")
        )
        
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBVariable(name="x"),
                operator="+",
                right=PBVariable(name="y")
            ),
            operator="*",
            right=PBBinaryOperator(
                left=PBVariable(name="x"),
                operator="+",
                right=PBVariable(name="y")
            )
        )
        
        # Collect subexpressions
        optimizer._collect_subexpressions(expr)
        
        # Check that x + y was detected as common
        assert len(optimizer.expression_counts) > 0
        # Find the x + y hash
        found_common = False
        for hash_expr, count in optimizer.expression_counts.items():
            if hash_expr.type_ == "binary" and hash_expr.value == "+" and count > 1:
                found_common = True
                break
        assert found_common
    
    def test_expression_hash_equality(self):

    
        
    
        """Test that expression hashes work correctly."""
        # Same expressions should have same hash
        hash1 = ExpressionHash("binary", "+", 
                              (ExpressionHash("variable", "x"),
                               ExpressionHash("number", 5)))
        hash2 = ExpressionHash("binary", "+", 
                              (ExpressionHash("variable", "x"),
                               ExpressionHash("number", 5)))
        
        assert hash1 == hash2
        assert hash(hash1) == hash(hash2)
        
        # Different expressions should have different hashes
        hash3 = ExpressionHash("binary", "*", 
                              (ExpressionHash("variable", "x"),
                               ExpressionHash("number", 5)))
        
        assert hash1 != hash3
        assert hash(hash1) != hash(hash3)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_is_power_of_two(self):

    
        
    
        """Test power of two detection."""
        optimizer = AdvancedExpressionOptimizer()
        
        assert optimizer._is_power_of_two(1) is True
        assert optimizer._is_power_of_two(2) is True
        assert optimizer._is_power_of_two(4) is True
        assert optimizer._is_power_of_two(8) is True
        assert optimizer._is_power_of_two(16) is True
        assert optimizer._is_power_of_two(32) is True
        
        assert optimizer._is_power_of_two(0) is False
        assert optimizer._is_power_of_two(3) is False
        assert optimizer._is_power_of_two(5) is False
        assert optimizer._is_power_of_two(6) is False
        assert optimizer._is_power_of_two(7) is False
        assert optimizer._is_power_of_two(-2) is False
        assert optimizer._is_power_of_two(2.5) is False
    
    def test_convenience_function(self):

    
        
    
        """Test the convenience optimization function."""
        # 5 + 0 -> 5
        expr = PBBinaryOperator(
            left=PBNumberLiteral(value=5),
            operator="+",
            right=PBNumberLiteral(value=0)
        )
        
        result = optimize_expression_advanced(expr)
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 5


class TestComplexOptimizationScenarios:
    """Test complex optimization scenarios combining multiple techniques."""
    
    def test_combined_optimizations(self):

    
        
    
        """Test expressions requiring multiple optimization types."""
        optimizer = AdvancedExpressionOptimizer()
        
        # ((x * 2) + 0) * 1 -> (x + x) + 0 -> x + x
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBBinaryOperator(
                    left=PBVariable(name="x"),
                    operator="*",
                    right=PBNumberLiteral(value=2)
                ),
                operator="+",
                right=PBNumberLiteral(value=0)
            ),
            operator="*",
            right=PBNumberLiteral(value=1)
        )
        
        result = optimizer.optimize(expr)
        # Should apply strength reduction, algebraic identity, and more
        assert isinstance(result, PBBinaryOperator)
        assert result.operator == "+"
        assert optimizer.optimizations_applied >= 2
    
    def test_deeply_nested_optimization(self):

    
        
    
        """Test optimization of deeply nested expressions."""
        optimizer = AdvancedExpressionOptimizer()
        
        # Build a complex nested expression
        # (((2 + 3) * 2) + ((4 - 4) * x)) / 1
        # Should simplify to: 10 + 0 -> 10
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBBinaryOperator(
                    left=PBBinaryOperator(
                        left=PBNumberLiteral(value=2),
                        operator="+",
                        right=PBNumberLiteral(value=3)
                    ),
                    operator="*",
                    right=PBNumberLiteral(value=2)
                ),
                operator="+",
                right=PBBinaryOperator(
                    left=PBBinaryOperator(
                        left=PBNumberLiteral(value=4),
                        operator="-",
                        right=PBNumberLiteral(value=4)
                    ),
                    operator="*",
                    right=PBVariable(name="x")
                )
            ),
            operator="/",
            right=PBNumberLiteral(value=1)
        )
        
        result = optimizer.optimize(expr)
        # Should eventually simplify significantly
        assert isinstance(result, PBNumberLiteral)
        assert result.value == 10