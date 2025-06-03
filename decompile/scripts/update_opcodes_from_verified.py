#!/usr/bin/env python3
"""
Update opcodes.yaml with verified definitions from opcodes_verified.yaml

This script merges verified opcode definitions into the main opcodes.yaml file,
preserving existing information where it doesn't conflict.
"""

import yaml
from pathlib import Path
from datetime import datetime
import sys

def load_yaml(filepath):
    """Load a YAML file and return its contents."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data, filepath):
    """Save data to a YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def convert_verified_to_opcodes_format(verified_opcode):
    """Convert a verified opcode entry to the opcodes.yaml format."""
    # Map verified fields to opcodes.yaml fields
    result = {}
    
    # Set category based on the opcode name
    name = verified_opcode.get('name', '')
    if name.startswith('JUMP') or name in ['RETURN', 'CALL', 'HALT']:
        result['category'] = 'control'
    elif name.startswith('ASSIGN'):
        result['category'] = 'assignment'
    elif name.startswith('LOAD') or name.startswith('PUSH'):
        result['category'] = 'stack'
    elif name.startswith('CONST'):
        result['category'] = 'constants'
    elif any(op in name for op in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POWER', 'NEG']):
        result['category'] = 'arithmetic'
    elif any(op in name for op in ['EQ', 'NE', 'LT', 'LE', 'GT', 'GE', 'AND', 'OR', 'NOT']):
        result['category'] = 'comparison'
    elif name.startswith('ARRAY') or '_ARRAY' in name:
        result['category'] = 'array'
    elif name.startswith('OBJECT') or '_OBJ' in name or '_OBINST' in name:
        result['category'] = 'object'
    else:
        result['category'] = 'misc'
    
    # Set description based on name
    result['description'] = f"Verified opcode: {name}"
    if 'notes' in verified_opcode and verified_opcode['notes']:
        result['description'] += f" ({verified_opcode['notes']})"
    
    # Set mnemonic
    result['mnemonic'] = name
    
    # Set operands based on length
    length = verified_opcode.get('length', 1)
    if length > 1:
        result['operands'] = [f'byte{i}' for i in range(1, length)]
    else:
        result['operands'] = []
    
    # Set stack effect (default, can be refined later)
    result['stack_effect'] = '? -> ?'
    
    # Add verification metadata
    result['verified'] = True
    result['verified_source'] = verified_opcode.get('source', [])
    result['verified_confidence'] = verified_opcode.get('confidence', 'unknown')
    result['verified_date'] = datetime.now().strftime('%Y-%m-%d')
    
    return result

def main():
    # Define file paths
    opcodes_path = Path(__file__).parent.parent.parent / 'extract' / 'pbd_core' / 'opcodes.yaml'
    verified_path = Path(__file__).parent.parent.parent / 'extract' / 'pbd_core' / 'opcodes_verified.yaml'
    
    # Load both files
    print(f"Loading {opcodes_path}...")
    opcodes_data = load_yaml(opcodes_path)
    
    print(f"Loading {verified_path}...")
    verified_data = load_yaml(verified_path)
    
    # Track updates
    updates = []
    
    # Process each verified opcode
    for hex_key, verified_opcode in verified_data.get('opcodes', {}).items():
        # Convert hex key to decimal
        try:
            if hex_key.startswith('0x'):
                opcode_num = int(hex_key, 16)
            else:
                opcode_num = int(hex_key)
        except ValueError:
            print(f"Warning: Invalid opcode key: {hex_key}")
            continue
        
        # Convert verified format to opcodes format
        new_entry = convert_verified_to_opcodes_format(verified_opcode)
        
        # Check if this opcode exists in opcodes.yaml
        if opcode_num in opcodes_data:
            old_entry = opcodes_data[opcode_num]
            
            # Compare and update
            if old_entry.get('mnemonic') != new_entry['mnemonic']:
                print(f"Updating opcode {opcode_num} (0x{opcode_num:02X}):")
                print(f"  Old: {old_entry.get('mnemonic', 'UNKNOWN')}")
                print(f"  New: {new_entry['mnemonic']}")
                
                # Preserve variants if they exist
                if 'variants' in old_entry:
                    new_entry['variants'] = old_entry['variants']
                
                # Update the entry
                opcodes_data[opcode_num] = new_entry
                updates.append(opcode_num)
        else:
            # Add new opcode
            print(f"Adding new opcode {opcode_num} (0x{opcode_num:02X}): {new_entry['mnemonic']}")
            opcodes_data[opcode_num] = new_entry
            updates.append(opcode_num)
    
    # Save updated opcodes.yaml
    if updates:
        print(f"\nUpdating {len(updates)} opcodes...")
        
        # Create backup
        backup_path = opcodes_path.with_suffix('.yaml.bak')
        print(f"Creating backup at {backup_path}...")
        import shutil
        shutil.copy2(opcodes_path, backup_path)
        
        # Save updated file
        save_yaml(opcodes_data, opcodes_path)
        print(f"Updated {opcodes_path}")
        print(f"\nUpdated opcodes: {sorted(updates)}")
    else:
        print("\nNo updates needed.")
    
    # Specifically check the problematic opcodes mentioned
    problematic = [0x80, 0xC4, 0xC6, 0xC7]
    print("\nVerifying problematic opcodes:")
    for opcode in problematic:
        if opcode in opcodes_data:
            entry = opcodes_data[opcode]
            print(f"  0x{opcode:02X} ({opcode}): {entry.get('mnemonic', 'UNKNOWN')}")

if __name__ == '__main__':
    main()