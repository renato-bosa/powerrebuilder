#!/usr/bin/env python3
"""Test the full SIME Finch pipeline with opcode recognition verification."""

import logging
import sys
from pathlib import Path
from collections import defaultdict

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.pbd_core.library import Library
from decompile.generators.structured_decompiler import StructuredDecompiler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_pipeline():
    """Test the full extraction and decompilation pipeline."""
    
    # Test with multiple PBD files
    pbd_files = list(Path("input/pbd_files").glob("*.pbd"))
    
    if not pbd_files:
        logger.error("No PBD files found in input/pbd_files/")
        return
    
    logger.info(f"Found {len(pbd_files)} PBD files to process")
    
    # Track unknown opcodes across all files
    global_unknown_opcodes = defaultdict(int)
    total_instructions = 0
    successful_decompiles = 0
    
    for pbd_path in pbd_files[:3]:  # Process first 3 files for testing
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pbd_path.name}")
        logger.info(f"{'='*60}")
        
        try:
            with Library(str(pbd_path)) as library:
                # Get all P-code objects
                pcode_objects = []
                for name, entry in library.entries_map.items():
                    if name.endswith(('.fun', '.udo', '.win')):
                        pcode_objects.append((name, entry))
                
                logger.info(f"Found {len(pcode_objects)} P-code objects")
                
                # Decompile first few objects
                decompiler = StructuredDecompiler()
                
                with open(pbd_path, 'rb') as f:
                    for obj_name, entry in pcode_objects[:5]:  # First 5 objects
                        logger.info(f"\nDecompiling: {obj_name}")
                        
                        try:
                            decoded_obj = decompiler.decompile_object(
                                f, entry.offset, entry.objectsize, entry.objectname
                            )
                            
                            if decoded_obj:
                                successful_decompiles += 1
                                inst_count = len(decoded_obj.instructions)
                                total_instructions += inst_count
                                
                                # Check for unknown opcodes
                                unknown_count = decoded_obj.metadata.get('unknown_opcodes', 0)
                                
                                logger.info(f"  Instructions: {inst_count}")
                                logger.info(f"  Unknown opcodes: {unknown_count}")
                                
                                # Print first few instructions
                                logger.info("  First instructions:")
                                for inst in decoded_obj.instructions[:3]:
                                    logger.info(f"    {inst.text_format}")
                                
                                # Track unknown opcodes
                                for inst in decoded_obj.instructions:
                                    if inst.opcode_name.startswith('UNK_'):
                                        global_unknown_opcodes[inst.opcode_name] += 1
                            else:
                                logger.warning(f"  Failed to decompile")
                                
                        except Exception as e:
                            logger.error(f"  Error decompiling {obj_name}: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing {pbd_path}: {e}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total instructions decoded: {total_instructions}")
    logger.info(f"Successful decompiles: {successful_decompiles}")
    
    if global_unknown_opcodes:
        logger.info(f"\nUnknown opcodes found:")
        for opcode, count in sorted(global_unknown_opcodes.items()):
            logger.info(f"  {opcode}: {count} occurrences")
        logger.info(f"\nTotal unique unknown opcodes: {len(global_unknown_opcodes)}")
    else:
        logger.info("\nAll opcodes recognized! ✓")
    
    return len(global_unknown_opcodes) == 0


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)