#!/usr/bin/env python3
"""Update opcodes.yaml with verified opcodes from opcodes_verified.yaml.

This script merges verified opcode definitions into the main opcodes.yaml file,
fixing the issue where many opcodes are incorrectly defined or missing.
"""

import yaml
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_yaml_file(path: Path) -> dict:
    """Load a YAML file and return its contents."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml_file(path: Path, data: dict) -> None:
    """Save data to a YAML file."""
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, width=120)

def merge_opcode_definitions(main_opcodes: dict, verified_opcodes: dict) -> tuple[dict, list]:
    """Merge verified opcodes into main opcodes dictionary.
    
    Returns:
        Tuple of (updated opcodes dict, list of updated opcode numbers)
    """
    updated_opcodes = []
    
    # Process verified opcodes
    for hex_key, verified_info in verified_opcodes.get('opcodes', {}).items():
        # Convert hex string to decimal int
        try:
            if hex_key.startswith('0x'):
                opcode_num = int(hex_key, 16)
            else:
                opcode_num = int(hex_key)
        except ValueError:
            logger.warning(f"Skipping invalid opcode key: {hex_key}")
            continue
        
        # Get the verified opcode info
        name = verified_info.get('name', '')
        length = verified_info.get('length', 1)
        confidence = verified_info.get('confidence', 'medium')
        
        # Create new opcode definition
        new_definition = {
            'mnemonic': name,
            'category': 'verified',  # Mark as verified
            'description': f"Verified opcode: {name}",
            'operands': [],
            'stack_effect': '? -> ?',  # To be determined
            'verified_from': hex_key,
            'confidence': confidence,
            'updated': datetime.now().isoformat()
        }
        
        # Handle operand length
        if length > 1:
            # Add operand info based on length
            operand_count = length - 1
            if operand_count == 1:
                new_definition['operands'] = ['byte']
            elif operand_count == 2:
                new_definition['operands'] = ['int16']
            elif operand_count == 4:
                new_definition['operands'] = ['int32']
            else:
                new_definition['operands'] = [f'{operand_count}_bytes']
        
        # Check if opcode exists in main file
        if opcode_num in main_opcodes:
            current = main_opcodes[opcode_num]
            # Force update with verified definition
            if True:  # Always update with verified opcodes
                logger.info(f"Updating opcode {opcode_num} (0x{opcode_num:02X}): "
                          f"{current.get('mnemonic', 'EMPTY')} -> {name}")
                main_opcodes[opcode_num] = new_definition
                updated_opcodes.append(opcode_num)
            else:
                # Check if names match
                if current.get('mnemonic') != name:
                    logger.warning(f"Opcode {opcode_num} (0x{opcode_num:02X}) has conflicting definitions: "
                                 f"current={current.get('mnemonic')}, verified={name}")
        else:
            # Add new opcode
            logger.info(f"Adding new opcode {opcode_num} (0x{opcode_num:02X}): {name}")
            main_opcodes[opcode_num] = new_definition
            updated_opcodes.append(opcode_num)
    
    return main_opcodes, updated_opcodes

def main():
    """Main function to update opcodes."""
    # Paths
    project_root = Path(__file__).parent.parent
    main_opcodes_path = project_root / "extract" / "pbd_core" / "opcodes.yaml"
    verified_opcodes_path = project_root / "extract" / "pbd_core" / "opcodes_verified.yaml"
    
    # Check files exist
    if not main_opcodes_path.exists():
        logger.error(f"Main opcodes file not found: {main_opcodes_path}")
        return 1
    
    if not verified_opcodes_path.exists():
        logger.error(f"Verified opcodes file not found: {verified_opcodes_path}")
        return 1
    
    # Backup main opcodes file
    backup_path = main_opcodes_path.with_suffix('.yaml.backup')
    logger.info(f"Creating backup: {backup_path}")
    backup_path.write_text(main_opcodes_path.read_text())
    
    # Load files
    logger.info("Loading opcode files...")
    main_opcodes = load_yaml_file(main_opcodes_path)
    verified_opcodes = load_yaml_file(verified_opcodes_path)
    
    # Merge opcodes
    logger.info("Merging verified opcodes...")
    updated_opcodes, updated_list = merge_opcode_definitions(main_opcodes, verified_opcodes)
    
    # Save updated opcodes
    logger.info(f"Saving updated opcodes to {main_opcodes_path}...")
    save_yaml_file(main_opcodes_path, updated_opcodes)
    
    # Report results
    logger.info(f"\nUpdate complete! Updated {len(updated_list)} opcodes:")
    for opcode in sorted(updated_list):
        info = updated_opcodes[opcode]
        logger.info(f"  0x{opcode:02X} ({opcode:3d}): {info['mnemonic']}")
    
    # Check specific opcodes that were causing issues
    important_opcodes = [0x80, 0xC4, 0xC6, 0xC7]
    logger.info("\nChecking important opcodes:")
    for opcode in important_opcodes:
        if opcode in updated_opcodes:
            info = updated_opcodes[opcode]
            logger.info(f"  0x{opcode:02X}: {info['mnemonic']} ✓")
        else:
            logger.warning(f"  0x{opcode:02X}: NOT FOUND")
    
    return 0

if __name__ == "__main__":
    exit(main())