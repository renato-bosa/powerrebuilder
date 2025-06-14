"""PowerBuilder decompilation module.

This module provides functionality for decompiling PowerBuilder P-code
into human-readable source code.

Organization:
- core/: Core decompilation logic (decoder, control flow, expression lifting)
- analysis/: Analysis tools (P-code detection, control flow analysis)
- generators/: Different decompilation approaches
- opcodes/: PowerBuilder version-specific opcode definitions
- templates/: Jinja2 templates for code generation
"""

# Core components
from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer
from decompile.analysis.datawindow_extractor import DataWindowExtractor

# Analysis components
from decompile.analysis.pcode_detector_enhanced import (
    EnhancedPCodeDetectorV2 as EnhancedPCodeDetector,
)
from decompile.core.expression_reconstructor import (
    ExpressionLifter,
    ExpressionReconstructor,
    StackEmulator,
)
from decompile.core.output_formatter import OutputFormatter
from decompile.core.pcode_decoder import PCodeDecoderV2, PCodeInstruction

# Generators
# from decompile.generators.unified_decompiler import UnifiedDecompiler
# Main coordinator
from decompile.decompile_coordinator import PowerBuilderDecompiler
from decompile.types import BlockType, ControlBlock

__all__ = [
    "BlockType",
    "ControlBlock",
    "ControlFlowAnalyzer",
    "DataWindowExtractor",
    # Analysis
    "EnhancedPCodeDetector",
    "ExpressionLifter",  # Backwards compatibility
    "ExpressionReconstructor",
    "OutputFormatter",
    # Core
    "PCodeDecoderV2",
    "PCodeInstruction",
    # Generators
    # 'UnifiedDecompiler',
    # Main
    "PowerBuilderDecompiler",
    "StackEmulator",  # Backwards compatibility
]
