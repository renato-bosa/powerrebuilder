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
from decompile.core.pcode_decoder import PCodeDecoderV2, PCodeInstruction
from decompile.core.expression_reconstructor import ExpressionReconstructor, ExpressionLifter, StackEmulator
from decompile.core.output_formatter import OutputFormatter

# Analysis components
from decompile.analysis.pcode_detector import EnhancedPCodeDetector
from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer, ControlBlock, BlockType
from decompile.analysis.datawindow_extractor import DataWindowExtractor

# Generators
from decompile.generators.unified_decompiler import UnifiedDecompiler

# Main coordinator
from decompile.decompile_coordinator import PowerBuilderDecompiler

__all__ = [
    # Core
    'PCodeDecoderV2',
    'PCodeInstruction',
    'ExpressionReconstructor',
    'ExpressionLifter',  # Backwards compatibility
    'StackEmulator',  # Backwards compatibility
    'OutputFormatter',
    # Analysis
    'EnhancedPCodeDetector',
    'ControlFlowAnalyzer',
    'ControlBlock',
    'BlockType',
    'DataWindowExtractor',
    # Generators
    'UnifiedDecompiler',
    # Main
    'PowerBuilderDecompiler',
]