"""Core decompilation components."""

from .expression_reconstructor import (
    Expression,
    ExpressionReconstructor,
    ExpressionType,
    StackValue,
    # Backwards compatibility
    StackEmulator,
    ExpressionLifter,
)
from .output_formatter import OutputFormatter
from .pcode_decoder import DecodedObject, PCodeDecoderV2, PCodeInstruction

__all__ = [
    'Expression',
    'ExpressionReconstructor',
    'ExpressionType',
    'StackValue',
    'StackEmulator',  # Backwards compatibility
    'ExpressionLifter',  # Backwards compatibility
    'OutputFormatter',
    'DecodedObject',
    'PCodeDecoderV2',
    'PCodeInstruction',
]