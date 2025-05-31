#!/usr/bin/env python3
"""Generate YAML entries for missing opcodes from unknown_opcodes.log analysis."""

import re
import yaml
from collections import Counter
from pathlib import Path

def load_existing_opcodes():
    """Load existing opcodes from opcodes.yaml."""
    opcodes_file = Path('extract/pbd_core/opcodes.yaml')
    with open(opcodes_file, 'r') as f:
        try:
            opcodes = yaml.safe_load(f)
            return opcodes or {}
        except yaml.YAMLError as e:
            print(f"Error loading opcodes.yaml: {e}")
            return {}

def analyze_and_generate_yaml():
    """Analyze unknown_opcodes.log and generate YAML entries for missing opcodes."""
    
    # Load existing opcodes
    existing_opcodes = load_existing_opcodes()
    
    with open('unknown_opcodes.log', 'r') as f:
        lines = f.readlines()

    # Extract opcode and next byte pairs
    pairs = []
    single_opcodes = []
    
    for line in lines:
        match = re.search(r'Opcode: (0x[A-F0-9]+).*Context: ([a-f0-9 ]+)', line)
        if match:
            opcode = match.group(1)
            context = match.group(2).split()
            
            # Find opcode position in context
            opcode_hex = opcode.lower()[2:]  # Remove 0x prefix
            
            for i, byte in enumerate(context):
                if byte == opcode_hex:
                    # Record single opcode
                    single_opcodes.append(opcode)
                    
                    # If there's a next byte, record the pair
                    if i + 1 < len(context):
                        next_byte = context[i+1].upper()
                        pairs.append((opcode, f'0x{next_byte}'))
                    break

    # Count occurrences
    pair_counts = Counter(pairs)
    single_counts = Counter(single_opcodes)
    
    # Group by base opcode
    opcode_variants = {}
    for (opcode, variant), count in pair_counts.items():
        if opcode not in opcode_variants:
            opcode_variants[opcode] = []
        opcode_variants[opcode].append((variant, count))
    
    # Generate YAML for opcodes with more than 5 occurrences
    yaml_entries = []
    
    # First, handle single opcodes without variants (threshold: 50 occurrences)
    for opcode, count in single_counts.most_common():
        if count < 50:
            break
        # Convert hex string to int for checking in existing opcodes
        opcode_int = int(opcode, 16)
        if opcode_int not in existing_opcodes and (opcode not in opcode_variants or len(opcode_variants[opcode]) == 0):
            # Single opcode without variants
            yaml_entries.append(f"""
{opcode}:
  mnemonic: "OP_{opcode[2:]}"
  category: "unknown"
  operands: []
  stack_effect: "varies"
  description: "Unknown operation {opcode[2:]}"
""")
    
    # Handle opcodes with variants (threshold: 5 occurrences per variant)
    for opcode in sorted(opcode_variants.keys()):
        opcode_int = int(opcode, 16)
        
        # Check if opcode exists
        if opcode_int in existing_opcodes:
            # Check if it has variants section
            existing_def = existing_opcodes[opcode_int]
            if isinstance(existing_def, dict) and 'variants' in existing_def:
                # Only add new variants
                existing_variants = existing_def['variants']
                new_variants = []
                
                for variant, count in opcode_variants[opcode]:
                    if count >= 5:
                        variant_int = int(variant, 16)
                        if variant_int not in existing_variants:
                            new_variants.append((variant, count))
                
                if new_variants:
                    # Generate update for existing opcode with new variants
                    yaml_entries.append(f"\n# New variants for existing opcode {opcode}")
                    yaml_entries.append(f"# Add these variants to {opcode} in opcodes.yaml:")
                    for variant, count in new_variants:
                        variant_hex = variant[2:]
                        yaml_entries.append(f"#    {variant}:")
                        yaml_entries.append(f'#      mnemonic: "OP_{opcode[2:]}_{variant_hex}"')
                        yaml_entries.append(f'#      operands: ["value"]')
                        yaml_entries.append(f'#      stack_effect: "varies"')
                        yaml_entries.append(f'#      description: "Unknown operation {opcode[2:]} variant {variant_hex}"')
            else:
                # Opcode exists but doesn't have variants - skip
                continue
        else:
            # New opcode
            variants = opcode_variants[opcode]
            # Sort variants by count
            variants.sort(key=lambda x: x[1], reverse=True)
            
            # Only include variants with significant occurrences
            significant_variants = [(v, c) for v, c in variants if c >= 5]
            
            if significant_variants:
                yaml_entries.append(f"\n{opcode}:")
                yaml_entries.append(f'  category: "unknown"')
                yaml_entries.append(f'  description: "Unknown operation {opcode[2:]} with variants"')
                yaml_entries.append(f'  variants:')
                
                for variant, count in significant_variants:
                    variant_hex = variant[2:]
                    yaml_entries.append(f"    {variant}:")
                    yaml_entries.append(f'      mnemonic: "OP_{opcode[2:]}_{variant_hex}"')
                    yaml_entries.append(f'      operands: ["value"]')
                    yaml_entries.append(f'      stack_effect: "varies"')
                    yaml_entries.append(f'      description: "Unknown operation {opcode[2:]} variant {variant_hex}"')
    
    return '\n'.join(yaml_entries)

if __name__ == "__main__":
    yaml_output = analyze_and_generate_yaml()
    
    if yaml_output.strip():
        # Append to opcodes.yaml
        opcodes_file = Path('extract/pbd_core/opcodes.yaml')
        
        # Save backup
        backup_file = opcodes_file.with_suffix('.yaml.bak')
        backup_file.write_bytes(opcodes_file.read_bytes())
        print(f"Created backup: {backup_file}")
        
        # Append new opcodes
        with open(opcodes_file, 'a') as f:
            f.write("\n\n# Automatically added missing opcodes\n")
            f.write(yaml_output)
        
        print(f"Added missing opcodes to {opcodes_file}")
        
        # Count how many were added
        new_opcodes = yaml_output.count('\n0x')
        print(f"Added {new_opcodes} new opcode definitions")
    else:
        print("No new opcodes to add - all unknowns are already defined!") 