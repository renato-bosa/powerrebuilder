"""Unified PowerBuilder decompiler that properly integrates all components.

This module consolidates the best features from the three separate implementations
(IntegratedDecompiler, PCodeToSource, StructuredDecompiler) into a single,
comprehensive decompiler that matches the approach used in decompile_coordinator.py.
"""

import logging
from pathlib import Path
from typing import Optional

from ..analysis.control_flow_analyzer import BlockType, ControlBlock, ControlFlowAnalyzer
from ..analysis.pcode_detector import EnhancedPCodeDetector  
from ..core.expression_reconstructor import ExpressionReconstructor
from ..core.output_formatter import OutputFormatter
from ..core.pcode_decoder import DecodedObject, PCodeDecoderV2

logger = logging.getLogger(__name__)


class UnifiedDecompiler:
    """Unified PowerBuilder decompiler combining all best practices."""

    def __init__(self, version: str = "pb80_0"):
        """Initialize the unified decompiler.
        
        Args:
            version: PowerBuilder version for opcode tables
        """
        self.version = version
        self.decoder = PCodeDecoderV2(version)
        self.cf_analyzer = ControlFlowAnalyzer()
        self.expression_reconstructor = ExpressionReconstructor()
        self.formatter = OutputFormatter()
        self.detector = EnhancedPCodeDetector()
        
        # Symbol tables from StructuredDecompiler
        self.locals: dict[int, str] = {}
        self.globals: dict[int, str] = {}
        self.methods: dict[int, str] = {}
        self.fields: dict[int, str] = {}
        self.strings: dict[int, str] = {}
        self.classes: dict[int, str] = {}

    def decompile_object(self, pbd_file, offset: int, size: int,
                        object_name: str) -> Optional[DecodedObject]:
        """Decompile a single object from PBD using the proven approach.
        
        This matches the implementation in decompile_coordinator.py.
        
        Args:
            pbd_file: Open PBD file handle
            offset: Object offset in PBD
            size: Object size
            object_name: Name of the object
            
        Returns:
            DecodedObject with decompiled code or None
        """
        logger.debug(f"Decompiling {object_name}")

        # Skip non-P-code objects
        if not EnhancedPCodeDetector.is_pcode_object(object_name):
            logger.debug(f"Skipping {object_name} - no P-code expected")
            return None

        # Decode P-code instructions
        decoded_obj = self.decoder.decode_pbd_object(
            pbd_file, offset, size, object_name
        )

        if not decoded_obj or not decoded_obj.instructions:
            logger.warning(f"No P-code found in {object_name}")
            return None

        # Analyze control flow
        control_blocks = self.cf_analyzer.analyze(decoded_obj.instructions)

        # Reconstruct expressions using stack emulation
        for block in control_blocks:
            self.expression_reconstructor.emulate_block(block)

        # Store the analyzed blocks in the decoded object
        decoded_obj.control_blocks = control_blocks
        
        # Generate formatted output
        output_lines = self.formatter.format_object(
            decoded_obj, control_blocks, self.version
        )
        decoded_obj.source_lines = output_lines

        return decoded_obj

    def decompile_file(self, file_path: Path) -> str:
        """Decompile a standalone PowerBuilder file.
        
        This is useful for testing individual files outside of PBD context.
        
        Args:
            file_path: Path to the binary file
            
        Returns:
            Decompiled PowerBuilder source code
        """
        logger.info(f"Decompiling standalone file {file_path}")

        # Read the file
        with open(file_path, 'rb') as f:
            data = f.read()

        # Determine object type from extension
        file_ext = file_path.suffix.lower()
        object_name = file_path.name
        
        # Map extensions to object types
        ext_to_type = {
            '.fun': 'function',
            '.win': 'window', 
            '.dwo': 'datawindow',
            '.udo': 'userobject',
            '.sru': 'userobject',
            '.srw': 'window',
            '.srf': 'function',
            '.srm': 'menu',
            '.srd': 'datawindow',
        }
        object_type = ext_to_type.get(file_ext, 'unknown')

        # Find P-code section
        pcode_start, pcode_end = self.detector.find_pcode_section(data, object_type)
        
        if pcode_start < 0:
            # Try fallback method from PCodeToSource
            header = b'$PBExportComments$'
            pos = data.find(header)
            if pos >= 0:
                pcode_start = pos + len(header) + 2  # Skip header and CRLF
            else:
                return f"// Failed to find P-code in {file_path}"

        # Extract P-code
        pcode = data[pcode_start:pcode_end] if pcode_end > 0 else data[pcode_start:]

        # Create a temporary file-like object for decoder
        class FakeFile:
            def __init__(self, data):
                self.data = data
                self.pos = 0
            def seek(self, offset):
                self.pos = offset
            def read(self, size):
                result = self.data[self.pos:self.pos + size]
                self.pos += size
                return result

        fake_file = FakeFile(pcode)
        
        # Use the main decompilation path
        decoded_obj = self.decompile_object(
            fake_file, 0, len(pcode), object_name
        )

        if decoded_obj and decoded_obj.source_lines:
            return '\n'.join(decoded_obj.source_lines)
        else:
            return f"// Failed to decompile {file_path}"

    def reset_symbol_tables(self):
        """Reset all symbol tables for a fresh decompilation."""
        self.locals.clear()
        self.globals.clear()
        self.methods.clear()
        self.fields.clear()
        self.strings.clear()
        self.classes.clear()