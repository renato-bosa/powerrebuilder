"""Advanced expression optimizer for PowerBuilder AST expressions.

This module extends the basic expression optimizer with more sophisticated
optimization techniques including:
- Common subexpression elimination
- Strength reduction
- Advanced algebraic transformations
- Expression pattern matching
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from model.entities.expressions import (
    PBBinaryOperator,
    PBBooleanLiteral,
    PBExpression,
    PBNumberLiteral,
    PBStringLiteral,
    PBVariable,
    PBFunctionCall,
    PBArrayAccess,
    PBFieldReference,
)
from model.optimization.expression_optimizer import ExpressionOptimizer

logger = logging.getLogger(__name__)


@dataclass
class ExpressionHash:
    """Represents a hashable form of an expression for CSE."""
    type_: str
    value: Any
    children: Tuple['ExpressionHash', ...] = field(default_factory=tuple)
    
    def __hash__(self):
        return hash((self.type_, self.value, self.children))
    
    def __eq__(self, other):
        return (isinstance(other, ExpressionHash) and 
                self.type_ == other.type_ and 
                self.value == other.value and 
                self.children == other.children)


class AdvancedExpressionOptimizer(ExpressionOptimizer):
    """Advanced expression optimizer with sophisticated optimization techniques."""
    
    def __init__(self):
        """Initialize the advanced optimizer."""
        super().__init__()
        
        # Common subexpression tracking
        self.common_subexpressions: Dict[ExpressionHash, PBExpression] = {}
        self.expression_counts: Dict[ExpressionHash, int] = {}
        
        # Pattern matching rules
        self.patterns = self._init_patterns()
        
    def optimize(self, expression: PBExpression) -> PBExpression:
        """Apply all optimization passes including advanced techniques.
        
        Args:
            expression: The expression to optimize
            
        Returns:
            The optimized expression
        """
        if not isinstance(expression, PBExpression):
            return expression
            
        # Reset state
        self.optimizations_applied = 0
        self.common_subexpressions.clear()
        self.expression_counts.clear()
        
        # First pass: collect common subexpressions
        self._collect_subexpressions(expression)
        
        # Apply basic optimizations first
        result = super().optimize(expression)
        
        # Apply advanced optimizations
        result = self._optimize_strength_reduction(result)
        result = self._optimize_distributive(result)
        result = self._optimize_associative(result)
        result = self._apply_pattern_matching(result)
        
        # Apply common subexpression elimination
        result = self._eliminate_common_subexpressions(result)
        
        if self.optimizations_applied > 0:
            logger.debug("Applied %s advanced optimizations", self.optimizations_applied)
            
        return result
    
    def _optimize_strength_reduction(self, expr: PBExpression) -> PBExpression:
        """Apply strength reduction optimizations.
        
        Converts expensive operations to cheaper equivalents.
        
        Args:
            expr: Expression to optimize
            
        Returns:
            Optimized expression
        """
        if isinstance(expr, PBBinaryOperator):
            # Recursively optimize operands
            left = self._optimize_strength_reduction(expr.left)
            right = self._optimize_strength_reduction(expr.right)
            
            # Multiplication by power of 2 -> shift left
            if expr.operator == "*" and isinstance(right, PBNumberLiteral):
                if self._is_power_of_two(right.value) and right.value > 0:
                    # In PowerBuilder, we can't use bit shifts directly,
                    # but we can note this for code generation
                    logger.debug("Could optimize %s * %s to shift", left, right.value)
            
            # Division by power of 2 -> shift right
            elif expr.operator == "/" and isinstance(right, PBNumberLiteral):
                if self._is_power_of_two(right.value) and right.value > 0:
                    logger.debug("Could optimize %s / %s to shift", left, right.value)
            
            # x * 2 -> x + x (addition is often faster)
            elif expr.operator == "*" and isinstance(right, PBNumberLiteral) and right.value == 2:
                self.optimizations_applied += 1
                return PBBinaryOperator(left=left, operator="+", right=left)
            
            # Return expression with optimized operands
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)
                
        elif isinstance(expr, PBFunctionCall):
            # Optimize function arguments
            args = [self._optimize_strength_reduction(arg) for arg in expr.arguments]
            if args != expr.arguments:
                return PBFunctionCall(
                    function_name=expr.function_name,
                    arguments=args,
                    object=expr.object
                )
                
        return expr
    
    def _optimize_distributive(self, expr: PBExpression) -> PBExpression:
        """Apply distributive law optimizations.
        
        Args:
            expr: Expression to optimize
            
        Returns:
            Optimized expression
        """
        if isinstance(expr, PBBinaryOperator):
            # Recursively optimize operands
            left = self._optimize_distributive(expr.left)
            right = self._optimize_distributive(expr.right)
            
            # a * (b + c) -> a * b + a * c (only if it simplifies)
            if expr.operator == "*":
                if isinstance(right, PBBinaryOperator) and right.operator == "+":
                    # Check if distributing would allow further optimization
                    if isinstance(left, PBNumberLiteral):
                        # Distribute the multiplication
                        self.optimizations_applied += 1
                        return PBBinaryOperator(
                            left=PBBinaryOperator(left=left, operator="*", right=right.left),
                            operator="+",
                            right=PBBinaryOperator(left=left, operator="*", right=right.right)
                        )
            
            # Return expression with optimized operands
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)
                
        return expr
    
    def _optimize_associative(self, expr: PBExpression) -> PBExpression:
        """Apply associative law optimizations.
        
        Rearranges expressions to enable more optimizations.
        
        Args:
            expr: Expression to optimize
            
        Returns:
            Optimized expression
        """
        if isinstance(expr, PBBinaryOperator):
            # Recursively optimize operands
            left = self._optimize_associative(expr.left)
            right = self._optimize_associative(expr.right)
            
            # For associative operators (+ and *), rearrange to group constants
            if expr.operator in ["+", "*"]:
                # (a + 2) + 3 -> a + (2 + 3) -> a + 5
                if (isinstance(left, PBBinaryOperator) and 
                    left.operator == expr.operator and
                    isinstance(left.right, PBNumberLiteral) and
                    isinstance(right, PBNumberLiteral)):
                    
                    # Fold the constants
                    if expr.operator == "+":
                        const_value = left.right.value + right.value
                    else:  # "*"
                        const_value = left.right.value * right.value
                    
                    self.optimizations_applied += 1
                    return PBBinaryOperator(
                        left=left.left,
                        operator=expr.operator,
                        right=PBNumberLiteral(value=const_value)
                    )
            
            # Return expression with optimized operands
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)
                
        return expr
    
    def _apply_pattern_matching(self, expr: PBExpression) -> PBExpression:
        """Apply pattern-based optimizations.
        
        Args:
            expr: Expression to optimize
            
        Returns:
            Optimized expression
        """
        # Try each pattern
        for pattern, replacement in self.patterns:
            result = self._match_and_replace(expr, pattern, replacement)
            if result is not expr:
                self.optimizations_applied += 1
                return result
                
        # Recursively apply to subexpressions
        if isinstance(expr, PBBinaryOperator):
            left = self._apply_pattern_matching(expr.left)
            right = self._apply_pattern_matching(expr.right)
            if left is not expr.left or right is not expr.right:
                return PBBinaryOperator(left=left, operator=expr.operator, right=right)
                
        return expr
    
    def _collect_subexpressions(self, expr: PBExpression) -> ExpressionHash:
        """Collect common subexpressions for CSE.
        
        Args:
            expr: Expression to analyze
            
        Returns:
            Hash representation of the expression
        """
        if isinstance(expr, PBNumberLiteral):
            hash_expr = ExpressionHash("number", expr.value)
        elif isinstance(expr, PBStringLiteral):
            hash_expr = ExpressionHash("string", expr.value)
        elif isinstance(expr, PBBooleanLiteral):
            hash_expr = ExpressionHash("boolean", expr.value)
        elif isinstance(expr, PBVariable):
            hash_expr = ExpressionHash("variable", expr.name)
        elif isinstance(expr, PBBinaryOperator):
            left_hash = self._collect_subexpressions(expr.left)
            right_hash = self._collect_subexpressions(expr.right)
            hash_expr = ExpressionHash("binary", expr.operator, (left_hash, right_hash))
        else:
            # For other types, create a simple hash
            hash_expr = ExpressionHash("other", str(type(expr).__name__))
        
        # Count occurrences
        self.expression_counts[hash_expr] = self.expression_counts.get(hash_expr, 0) + 1
        
        # Store mapping for expressions that appear multiple times
        if self.expression_counts[hash_expr] > 1:
            self.common_subexpressions[hash_expr] = expr
            
        return hash_expr
    
    def _eliminate_common_subexpressions(self, expr: PBExpression) -> PBExpression:
        """Eliminate common subexpressions.
        
        Note: This is a simplified version. Full CSE would require
        creating temporary variables and ensuring proper scoping.
        
        Args:
            expr: Expression to optimize
            
        Returns:
            Optimized expression
        """
        # For now, just log potential CSE opportunities
        expr_hash = self._create_hash(expr)
        if expr_hash in self.common_subexpressions and self.expression_counts.get(expr_hash, 0) > 2:
            logger.debug("Common subexpression detected: %s", expr)
            
        return expr
    
    def _create_hash(self, expr: PBExpression) -> ExpressionHash:
        """Create hash representation of an expression."""
        if isinstance(expr, PBNumberLiteral):
            return ExpressionHash("number", expr.value)
        elif isinstance(expr, PBStringLiteral):
            return ExpressionHash("string", expr.value)
        elif isinstance(expr, PBBooleanLiteral):
            return ExpressionHash("boolean", expr.value)
        elif isinstance(expr, PBVariable):
            return ExpressionHash("variable", expr.name)
        elif isinstance(expr, PBBinaryOperator):
            left_hash = self._create_hash(expr.left)
            right_hash = self._create_hash(expr.right)
            return ExpressionHash("binary", expr.operator, (left_hash, right_hash))
        else:
            return ExpressionHash("other", str(type(expr).__name__))
    
    def _is_power_of_two(self, n: float) -> bool:
        """Check if a number is a power of two."""
        if n <= 0 or n != int(n):
            return False
        n = int(n)
        return (n & (n - 1)) == 0
    
    def _init_patterns(self) -> List[Tuple[Any, Any]]:
        """Initialize pattern matching rules.
        
        Returns:
            List of (pattern, replacement) tuples
        """
        patterns = []
        
        # Pattern: -(-x) -> x (double negation)
        # Pattern: x + x -> 2 * x
        # Pattern: x - (-y) -> x + y
        # These would be implemented with proper pattern matching logic
        
        return patterns
    
    def _match_and_replace(self, expr: PBExpression, pattern: Any, 
                          replacement: Any) -> PBExpression:
        """Match expression against pattern and apply replacement.
        
        Args:
            expr: Expression to match
            pattern: Pattern to match against
            replacement: Replacement to apply
            
        Returns:
            Replaced expression or original if no match
        """
        # This would implement actual pattern matching logic
        # For now, return the original expression
        return expr


def optimize_expression_advanced(expr: PBExpression) -> PBExpression:
    """Convenience function to apply advanced optimizations.
    
    Args:
        expr: Expression to optimize
        
    Returns:
        Optimized expression
    """
    optimizer = AdvancedExpressionOptimizer()
    return optimizer.optimize(expr)