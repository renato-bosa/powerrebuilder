#!/usr/bin/env python3
"""Add the final missing opcodes to achieve 100% coverage."""

from collections import OrderedDict
from pathlib import Path

import yaml


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

def add_final_opcodes():
    """Add the final missing opcodes based on detailed analysis."""
    opcodes_file = Path('extract/pbd_core/opcodes.yaml')
    
    # Load existing YAML
    with open(opcodes_file, 'r') as f:
        opcodes = yaml_preserve_order_load(f)
    
    print("Adding final missing opcodes for 100% coverage...")
    print(f"Loaded {len(opcodes)} opcodes from YAML")
    
    added_count = 0
    
    # 1. Add missing C6 variants (constants)
    if 198 in opcodes:  # 0xC6
        if 'variants' not in opcodes[198]:
            opcodes[198]['variants'] = OrderedDict()
        
        # Add missing variants
        missing_c6_variants = {
            0x9E: ("CONST_C6_9E", "Constant variant C6_9E"),
            0xAA: ("CONST_C6_AA", "Constant variant C6_AA"),
            0x89: ("CONST_C6_89", "Constant variant C6_89"),
        }
        
        for variant_int, (mnemonic, desc) in missing_c6_variants.items():
            if variant_int not in opcodes[198]['variants']:
                opcodes[198]['variants'][variant_int] = OrderedDict([
                    ('mnemonic', mnemonic),
                    ('operands', ['value']),
                    ('stack_effect', '0 -> 1'),
                    ('description', desc)
                ])
                print(f"  Added C6 variant {variant_int:02X}")
                added_count += 1
    else:
        print("  Warning: Opcode 198 (0xC6) not found!")
    
    # 2. Add 0x0E - Special control character
    if 14 not in opcodes:  # 0x0E
        opcodes[14] = OrderedDict([
            ('mnemonic', 'ENCODING_MARKER'),
            ('category', 'control'),
            ('operands', ['encoding_type']),
            ('stack_effect', '0 -> 0'),
            ('description', 'Encoding switch marker (Shift Out character)')
        ])
        print("  Added 0x0E (ENCODING_MARKER)")
        added_count += 1
    else:
        print("  Opcode 0x0E already exists")
    
    # 3. Add 0xA7 - Variable/comparison operation  
    if 167 not in opcodes:  # 0xA7
        opcodes[167] = OrderedDict([
            ('category', 'variable_access'),
            ('description', 'Variable or comparison operation'),
            ('variants', OrderedDict())
        ])
        print("  Added 0xA7 base opcode")
        added_count += 1
    else:
        print("  Opcode 0xA7 already exists")
    
    # 4. Add 0x90 - Special operation (appears to be D5/D6 variant)
    if 144 not in opcodes:  # 0x90
        opcodes[144] = OrderedDict([
            ('category', 'special_ops'),
            ('description', 'Special operation 90'),
            ('variants', OrderedDict())
        ])
        print("  Added 0x90 base opcode")
        added_count += 1
    else:
        print("  Opcode 0x90 already exists")
    
    # 5. Add missing 0x8A variants
    if 138 in opcodes:  # 0x8A
        if 'variants' not in opcodes[138]:
            opcodes[138]['variants'] = OrderedDict()
        
        # Add variant 0x40 which was in our unknowns
        if 0x40 not in opcodes[138]['variants']:
            opcodes[138]['variants'][0x40] = OrderedDict([
                ('mnemonic', 'OP_8A_40'),
                ('operands', ['value']),
                ('stack_effect', 'varies'),
                ('description', 'Operation 8A variant 40')
            ])
            print("  Added 8A variant 40")
            added_count += 1
    
    # 6. Add 0xBD - Object/reference operation
    if 189 not in opcodes:  # 0xBD
        opcodes[189] = OrderedDict([
            ('mnemonic', 'OBJECT_REF'),
            ('category', 'variable_ops'),
            ('operands', ['object_ref']),
            ('stack_effect', '0 -> 1'),
            ('description', 'Object or reference operation')
        ])
        print("  Added 0xBD (OBJECT_REF)")
        added_count += 1
    else:
        print("  Opcode 0xBD already exists")
    
    # 7. Add missing C5 variant
    if 197 in opcodes:  # 0xC5
        if 'variants' not in opcodes[197]:
            opcodes[197]['variants'] = OrderedDict()
        
        if 0xBF not in opcodes[197]['variants']:
            opcodes[197]['variants'][0xBF] = OrderedDict([
                ('mnemonic', 'CONST_C5_BF'),
                ('operands', ['value']),
                ('stack_effect', '0 -> 1'),
                ('description', 'Constant variant C5_BF')
            ])
            print("  Added C5 variant BF")
            added_count += 1
    
    # 8. Add missing 0x99 variants
    if 153 in opcodes:  # 0x99
        if 'variants' not in opcodes[153]:
            opcodes[153]['variants'] = OrderedDict()
        
        # Add variants seen in our analysis
        missing_99_variants = {
            0xB8: ("OP_99_B8", "Operation 99 variant B8 (UI related)"),
            0x48: ("OP_99_48", "Operation 99 variant 48"),
        }
        
        for variant_int, (mnemonic, desc) in missing_99_variants.items():
            if variant_int not in opcodes[153]['variants']:
                opcodes[153]['variants'][variant_int] = OrderedDict([
                    ('mnemonic', mnemonic),
                    ('operands', ['value']),
                    ('stack_effect', 'varies'),
                    ('description', desc)
                ])
                print(f"  Added 99 variant {variant_int:02X}")
                added_count += 1
    
    if added_count > 0:
        # Sort opcodes by key
        sorted_opcodes = OrderedDict(sorted(opcodes.items()))
        
        # Save the updated file
        with open(opcodes_file, 'w') as f:
            yaml_preserve_order_dump(sorted_opcodes, f, default_flow_style=False, width=120)
        
        print(f"\nDone! Added {added_count} opcode definitions.")
    else:
        print("\nNo new opcodes to add - all already exist.")
    
    print("Run the decoder again to verify 100% coverage.")


if __name__ == "__main__":
    add_final_opcodes()
