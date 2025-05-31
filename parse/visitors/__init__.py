"""PowerBuilder visitors package.

This package provides visitor and transformer classes for PowerBuilder ASTs.
"""

from __future__ import annotations

from .abstract_visitor import PowerBuilderASTVisitor

# Function exports for common use cases
from .pb_function import (
    visit_function_definition,
    visit_param,
    visit_param_list,
    visit_statement_list,
    visit_type_spec,
)
from .pb_transformer import PowerBuilderTransformer
from .position_tracker import PositionMixin, SourceContext, get_text_span
from .transformer import PBTransformer

__all__ = [
    # Base classes
    'PowerBuilderASTVisitor',
    'PBTransformer',
    'PowerBuilderTransformer',
    'PositionMixin',
    'SourceContext',
    # Helper functions
    'get_text_span',
    'visit_function_definition',
    'visit_param_list',
    'visit_param',
    'visit_type_spec',
    'visit_statement_list',
]
