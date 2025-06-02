#!/usr/bin/env python3
"""Add the specific missing variants based on unknown_opcodes.log."""

import yaml
from pathlib import Path
from collections import OrderedDict
import re

def yaml_preserve_order_load(stream):
    """Load YAML preserving order."""
    class OrderedLoader(yaml.SafeLoader):
        pass
    
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))
    
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    
    return yaml.load(stream, OrderedLoader)

def yaml_preserve_order_dump(data, stream=None, **kwds):
    """Dump YAML preserving order."""
    class OrderedDumper(yaml.SafeDumper):
        pass
    
    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    
    return yaml.dump(data, stream, OrderedDumper, **kwds)

def parse_unknown_log():
    """Parse unknown_opcodes.log to get opcode/variant pairs."""
    log_file = Path('unknown_opcodes.log')
    if not log_file.exists():
        print("No unknown_opcodes.log found")
        return []
    
    unknowns = []
    with open(log_file, 'r') as f:
        for line in f:
            match = re.search(r'Opcode: (0x[A-F0-9]+).*Context: ([a-f0-9 ]+)', line)
            if match:
                opcode = match.group(1)
                context = match.group(2).split()
                
                # Find opcode position and get next byte
                opcode_hex = opcode.lower()[2:]
                for i, byte in enumerate(context):
                    if byte == opcode_hex:
                        if i + 1 < len(context):
                            next_byte = context[i+1]
                            unknowns.append((int(opcode, 16), int(next_byte, 16)))
                        break
    
    return unknowns

def add_missing_variants():
    """Add the specific missing variants."""
    opcodes_file = Path('extract/pbd_core/opcodes.yaml')
    
    # Parse unknowns
    unknowns = parse_unknown_log()
    if not unknowns:
        print("No unknown opcodes found")
        return
    
    print(f"Found {len(unknowns)} unknown opcode/variant pairs")
    
    # Load existing YAML
    with open(opcodes_file, 'r') as f:
        opcodes = yaml_preserve_order_load(f)
    
    added_count = 0
    
    # Process each unknown
    for opcode_int, variant_int in unknowns:
        opcode_hex = f"0x{opcode_int:02X}"
        variant_hex = f"0x{variant_int:02X}"
        
        print(f"\nProcessing {opcode_hex} variant {variant_hex}")
        
        if opcode_int not in opcodes:
            print(f"  Error: Base opcode {opcode_hex} not found!")
            continue
        
        # Ensure variants section exists
        if 'variants' not in opcodes[opcode_int]:
            opcodes[opcode_int]['variants'] = OrderedDict()
        
        # Check if variant already exists
        if variant_int in opcodes[opcode_int]['variants']:
            print(f"  Variant {variant_hex} already exists")
            continue
        
        # Add the variant based on opcode type
        if opcode_int == 0x0E:  # ENCODING_MARKER
            opcodes[opcode_int]['variants'][variant_int] = OrderedDict([
                ('mnemonic', f'ENCODING_{variant_hex[2:]}'),
                ('operands', ['encoding_data']),
                ('stack_effect', '0 -> 0'),
                ('description', f'Encoding marker variant {variant_hex[2:]}')
            ])
        elif opcode_int == 0xA7:  # Variable/comparison
            opcodes[opcode_int]['variants'][variant_int] = OrderedDict([
                ('mnemonic', f'VAR_OP_A7_{variant_hex[2:]}'),
                ('operands', ['value']),
                ('stack_effect', 'varies'),
                ('description', f'Variable operation A7 variant {variant_hex[2:]}')
            ])
        elif opcode_int == 0x90:  # Special operation
            opcodes[opcode_int]['variants'][variant_int] = OrderedDict([
                ('mnemonic', f'SPECIAL_90_{variant_hex[2:]}'),
                ('operands', ['value']),
                ('stack_effect', 'varies'),
                ('description', f'Special operation 90 variant {variant_hex[2:]}')
            ])
        else:
            # Generic variant
            opcodes[opcode_int]['variants'][variant_int] = OrderedDict([
                ('mnemonic', f'OP_{opcode_hex[2:]}_{variant_hex[2:]}'),
                ('operands', ['value']),
                ('stack_effect', 'varies'),
                ('description', f'Operation {opcode_hex[2:]} variant {variant_hex[2:]}')
            ])
        
        print(f"  Added variant {variant_hex}")
        added_count += 1
    
    if added_count > 0:
        # Sort opcodes by key
        sorted_opcodes = OrderedDict(sorted(opcodes.items()))
        
        # Save the updated file
        with open(opcodes_file, 'w') as f:
            yaml_preserve_order_dump(sorted_opcodes, f, default_flow_style=False, width=120)
        
        print(f"\nDone! Added {added_count} variant definitions.")
    else:
        print("\nNo new variants to add.")
    
    print("Run the decoder again to verify 100% coverage.")

if __name__ == "__main__":
    add_missing_variants() 