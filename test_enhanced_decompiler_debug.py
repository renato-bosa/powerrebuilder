#!/usr/bin/env python3
"""Debug test for the enhanced decompiler components."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from decompile.structured_decompiler import StructuredDecompiler
from extract.pbd_core.library import Library

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_decompile_debug():
    """Test decompiling with debug output."""
    
    pbd_path = Path("input/pbd_files/dcm_accounting.pbd")
    object_name = "of_get_linked_acc.fun"
    
    logger.info(f"Testing decompilation of {object_name}")
    
    try:
        # Open the PBD file
        with Library(str(pbd_path)) as library:
            if object_name not in library.entries_map:
                logger.error(f"Object {object_name} not found")
                return
            
            entry = library.entries_map[object_name]
            logger.info(f"Found {entry.objectname} at offset {entry.offset:#x}, size {entry.objectsize}")
            
            # Create decompiler
            decompiler = StructuredDecompiler()
            
            # Open the PBD file for reading
            with open(pbd_path, 'rb') as f:
                # Decompile the object
                decoded_obj = decompiler.decompile_object(
                    f, entry.offset, entry.objectsize, entry.objectname
                )
                
                if decoded_obj:
                    logger.info(f"Successfully decoded {len(decoded_obj.instructions)} instructions")
                    
                    # Print first 30 instructions to see pattern
                    print("\n=== First 30 P-code instructions ===")
                    for i, inst in enumerate(decoded_obj.instructions[:30]):
                        print(f"{inst.text_format} [opcode: 0x{inst.opcode.hex()}]")
                    
                    # Check control blocks
                    control_blocks = decoded_obj.metadata.get('control_blocks', [])
                    print(f"\n=== Control blocks: {len(control_blocks)} ===")
                    
                    # Check what's causing so many blocks
                    print("\n=== Block terminators ===")
                    terminator_count = {}
                    for block in control_blocks[:50]:
                        if block.instructions:
                            last_inst = block.instructions[-1]
                            terminator_count[last_inst.opcode_name] = terminator_count.get(last_inst.opcode_name, 0) + 1
                    
                    for opcode, count in sorted(terminator_count.items(), key=lambda x: x[1], reverse=True)[:10]:
                        print(f"  {opcode}: {count}")
                    print()
                    for i, block in enumerate(control_blocks[:5]):
                        print(f"Block {i}: {block.type.name} [{block.start_addr:04X}-{block.end_addr:04X}]")
                        print(f"  Instructions: {len(block.instructions)}")
                        print(f"  Statements: {len(block.statements)}")
                        if block.statements:
                            for stmt in block.statements[:3]:
                                print(f"    {stmt}")
                    
                    # Check symbols
                    print(f"\n=== Symbol tables ===")
                    print(f"Locals: {list(decompiler.locals.items())[:5]}...")
                    print(f"Methods: {list(decompiler.methods.items())[:5]}...")
                    print(f"Strings: {list(decompiler.strings.items())[:5]}...")
                    
                else:
                    logger.error(f"Failed to decompile {entry.objectname}")
                    
    except Exception as e:
        logger.error(f"Error testing decompiler: {e}", exc_info=True)


if __name__ == "__main__":
    test_decompile_debug()