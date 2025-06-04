"""PowerBuilder decompilation module.

This module provides functionality for decompiling PowerBuilder P-code
into human-readable source code.

Organization:
- core/: Core decompilation logic (decoder, control flow, expression lifting)
- analysis/: Analysis tools (P-code detection, control flow analysis)
- generators/: Different decompilation approaches
- legacy/: Older implementations kept for reference
- opcode_tables/: PowerBuilder version-specific opcode definitions
- scripts/: Utility scripts for opcode discovery and management
- templates/: Jinja2 templates for code generation
- violations/: Code violation detection
"""

# Core components
from decompile.core.pcode_decoder import PCodeDecoderV2, PCodeInstruction
from decompile.core.control_flow import EnhancedControlFlowAnalyzer
from decompile.core.expression_lifter import ExpressionLifter
from decompile.core.stack_emulator import StackEmulator
from decompile.core.output_formatter import OutputFormatter

# Analysis components
from decompile.analysis.pcode_detector import EnhancedPCodeDetector
from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer, ControlBlock, BlockType
from decompile.analysis.datawindow_extractor import DataWindowExtractor

# Generators
from decompile.generators.structured_decompiler import StructuredDecompiler
from decompile.generators.integrated_decompiler import IntegratedDecompiler
from decompile.generators.pcode_to_source import PowerBuilderDecompiler

# Main coordinator
from decompile.decompile_coordinator import PowerBuilderDecompiler as MainDecompiler

__all__ = [
    # Core
    'PCodeDecoderV2',
    'PCodeInstruction',
    'EnhancedControlFlowAnalyzer',
    'ExpressionLifter',
    'StackEmulator',
    'OutputFormatter',
    # Analysis
    'EnhancedPCodeDetector',
    'ControlFlowAnalyzer',
    'ControlBlock',
    'BlockType',
    'DataWindowExtractor',
    # Generators
    'StructuredDecompiler',
    'IntegratedDecompiler',
    'PowerBuilderDecompiler',
    # Main
    'MainDecompiler',
]