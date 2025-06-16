"""Expression optimization module for PowerBuilder models.

This module provides optimization passes for PowerBuilder expressions,
including constant folding, algebraic simplification, and boolean optimization.
"""

from .expression_optimizer import ExpressionOptimizer

__all__ = ["ExpressionOptimizer"]