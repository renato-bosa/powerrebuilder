"""Main PowerBuilder decompiler orchestrator.

This module orchestrates the complete decompilation process following the
"best of both worlds" approach, combining accuracy from PbdViewer with
the portability of PowerBuilder-decompile.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from extract.pbd_core.header import extract_pbl_header
from extract.pbd_core.node import extract_nods
from extract.pbd_core.version_detector import VersionDetector, PowerBuilderVersion
from extract.pbd_io.utils import BLOCK_SIZE as DEFAULT_BLOCK_SIZE

from .pcode_decoder_v2 import PCodeDecoderV2, DecodedObject
from .stack_emulator import StackEmulator
from .control_flow_analyzer import ControlFlowAnalyzer
from .output_formatter import OutputFormatter
from .pcode_detector import PCodeDetector

logger = logging.getLogger(__name__)


class PowerBuilderDecompiler:
    """Main orchestrator for PowerBuilder decompilation."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the decompiler.
        
        Args:
            output_dir: Directory to write decompiled files (None for stdout only)
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
    
    def decompile_pbd(self, pbd_path: Path) -> bool:
        """Decompile a complete PBD file.
        
        Args:
            pbd_path: Path to the PBD file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting decompilation of {pbd_path}")
        
        try:
            with open(pbd_path, 'rb') as pbd_file:
                # Step 1: Parse header and detect version
                logger.info("Parsing PBD header...")
                header = extract_pbl_header(
                    pbd_file, 
                    block_size=DEFAULT_BLOCK_SIZE,
                    file_path_for_error_log=str(pbd_path)
                )
                
                # Detect PowerBuilder version
                version = VersionDetector.detect_from_file(pbd_file)
                if version is None:
                    version = VersionDetector.get_default_version(header.is_unicode)
                    logger.warning(f"Could not detect version, using default: {version}")
                else:
                    logger.info(f"Detected PowerBuilder version: {version}")
                
                # Step 2: Parse object directory
                logger.info("Parsing object directory...")
                nodes = extract_nods(
                    pbd_file,
                    header.is_unicode,
                    header.first_nod_offset,
                    DEFAULT_BLOCK_SIZE
                )
                
                # Count total objects
                total_objects = sum(
                    len(node.entry_defs) if node and hasattr(node, 'entry_defs') else 0
                    for node in nodes
                )
                logger.info(f"Found {total_objects} objects in PBD")
                
                # Step 3: Process each object
                decompiled_count = 0
                for node in nodes:
                    if node and hasattr(node, 'entry_defs') and node.entry_defs:
                        for entry in node.entry_defs:
                            if entry:
                                success = self._decompile_object(
                                    pbd_file, entry, version, pbd_path.name
                                )
                                if success:
                                    decompiled_count += 1
                
                logger.info(f"Successfully decompiled {decompiled_count}/{total_objects} objects")
                return decompiled_count > 0
                
        except Exception as e:
            logger.error(f"Failed to decompile {pbd_path}: {e}", exc_info=True)
            return False
    
    def _decompile_object(self, pbd_file, entry, version: PowerBuilderVersion, 
                         pbd_name: str) -> bool:
        """Decompile a single object from the PBD.
        
        Args:
            pbd_file: Open PBD file handle
            entry: Entry definition for the object
            version: PowerBuilder version
            pbd_name: Name of the PBD file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            object_name = entry.objectname
            logger.debug(f"Decompiling {object_name}")
            
            # Check if it's a DataWindow (special handling)
            if object_name.lower().endswith('.dwo'):
                return self._extract_datawindow(pbd_file, entry, pbd_name)
            
            # Skip objects that typically don't contain P-code
            if not PCodeDetector.is_pcode_object(object_name):
                logger.debug(f"Skipping {object_name} - no P-code expected")
                return False
            
            # Step 4: Extract and decode P-code
            decoder = PCodeDecoderV2(version)
            decoded_obj = decoder.decode_pbd_object(
                pbd_file, 
                entry.offset, 
                entry.objectsize,
                object_name
            )
            
            if not decoded_obj.instructions:
                logger.warning(f"No P-code found in {object_name}")
                return False
            
            # Step 5: Analyze control flow
            cf_analyzer = ControlFlowAnalyzer()
            control_blocks = cf_analyzer.analyze(decoded_obj.instructions)
            
            # Step 6: Reconstruct expressions using stack emulation
            emulator = StackEmulator()
            for block in control_blocks:
                emulator.emulate_block(block)
            
            # Step 7: Generate output
            formatter = OutputFormatter()
            output_lines = formatter.format_object(
                decoded_obj, control_blocks, pbd_name
            )
            
            # Write or print output
            if self.output_dir:
                output_path = self.output_dir / f"{object_name}.pb"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(output_lines))
                logger.debug(f"Wrote {output_path}")
            else:
                # Print to stdout
                print(f"\n{'='*60}")
                print(f"// Object: {object_name}")
                print(f"// From: {pbd_name}")
                print(f"// Version: {version}")
                print(f"{'='*60}")
                print('\n'.join(output_lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to decompile {entry.objectname}: {e}")
            return False
    
    def _extract_datawindow(self, pbd_file, entry, pbd_name: str) -> bool:
        """Extract DataWindow syntax directly.
        
        Args:
            pbd_file: Open PBD file handle
            entry: Entry definition for the DataWindow
            pbd_name: Name of the PBD file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Seek to DataWindow data
            pbd_file.seek(entry.offset)
            dw_data = pbd_file.read(entry.objectsize)
            
            # Look for DataWindow syntax markers
            syntax_start = dw_data.find(b'release ')
            if syntax_start < 0:
                syntax_start = dw_data.find(b'datawindow(')
            
            if syntax_start >= 0:
                # Extract syntax (often UTF-16 encoded)
                syntax_data = dw_data[syntax_start:]
                
                # Try to decode as UTF-16 first, then UTF-8
                syntax_text = None
                for encoding in ['utf-16le', 'utf-16be', 'utf-8', 'latin-1']:
                    try:
                        syntax_text = syntax_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if syntax_text:
                    # Clean up the syntax
                    syntax_text = syntax_text.split('\x00')[0]  # Remove null padding
                    
                    # Output the DataWindow syntax
                    if self.output_dir:
                        output_path = self.output_dir / f"{entry.objectname}"
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(syntax_text)
                        logger.debug(f"Wrote DataWindow {output_path}")
                    else:
                        print(f"\n{'='*60}")
                        print(f"// DataWindow: {entry.objectname}")
                        print(f"// From: {pbd_name}")
                        print(f"{'='*60}")
                        print(syntax_text)
                    
                    return True
            
            logger.warning(f"Could not extract DataWindow syntax from {entry.objectname}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to extract DataWindow {entry.objectname}: {e}")
            return False


def main():
    """Command-line interface for the decompiler."""
    parser = argparse.ArgumentParser(
        description="PowerBuilder PBD Decompiler - Best of Both Worlds Edition"
    )
    parser.add_argument(
        'pbd_file',
        type=Path,
        help='Path to the PBD file to decompile'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        help='Directory to write decompiled files (default: stdout)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # Check input file
    if not args.pbd_file.exists():
        print(f"Error: File not found: {args.pbd_file}", file=sys.stderr)
        sys.exit(1)
    
    if not args.pbd_file.suffix.lower() in ['.pbd', '.pbl']:
        print(f"Warning: File may not be a PBD/PBL file: {args.pbd_file}")
    
    # Run decompiler
    decompiler = PowerBuilderDecompiler(args.output_dir)
    success = decompiler.decompile_pbd(args.pbd_file)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()