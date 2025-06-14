"""Core decompilation components."""

from .expression_reconstructor import (
    Expression,
    ExpressionLifter,
    ExpressionReconstructor,
    ExpressionType,
    # Backwards compatibility
    StackEmulator,
    StackValue,
)
from .output_formatter import OutputFormatter
from .pcode_decoder import DecodedObject, PCodeDecoderV2, PCodeInstruction

__all__ = [
    "DecodedObject",
    "Expression",
    "ExpressionLifter",  # Backwards compatibility
    "ExpressionReconstructor",
    "ExpressionType",
    "OutputFormatter",
    "PCodeDecoderV2",
    "PCodeInstruction",
    "StackEmulator",  # Backwards compatibility
    "StackValue",
]
