#!/usr/bin/env python3
"""Add the final missing variants to opcodes.yaml based on unknown_opcodes.log analysis."""

import re
from collections import Counter, OrderedDict
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

def get_all_missing_variants():
    """Extract ALL missing variants from unknown_opcodes.log."""
    with open('logs/unknown_opcodes.log') as f:
        lines = f.readlines()

    # Extract opcode and next byte pairs
    pairs = []
    for line in lines:
        match = re.search(r'Opcode: (0x[A-F0-9]+).*Context: ([a-f0-9 ]+)', line)
        if match:
            opcode = match.group(1)
            context = match.group(2).split()

            # Find opcode position in context
            opcode_hex = opcode.lower()[2:]  # Remove 0x prefix

            for i, byte in enumerate(context):
                if byte == opcode_hex:
                    # If there's a next byte, record the pair
                    if i + 1 < len(context):
                        next_byte = context[i+1].upper()
                        pairs.append((opcode, f'0x{next_byte}'))
                    break

    # Count occurrences
    pair_counts = Counter(pairs)

    # Group by base opcode
    missing_variants = {}
    for (opcode, variant), count in pair_counts.items():
        if opcode not in missing_variants:
            missing_variants[opcode] = []
        missing_variants[opcode].append((variant, count))

    return missing_variants

def add_all_missing_variants():
    """Add ALL missing variants to opcodes.yaml."""
    opcodes_file = Path('extract/pbd_core/opcodes.yaml')

    # Load existing YAML
    with open(opcodes_file) as f:
        opcodes = yaml_preserve_order_load(f)

    missing_variants = get_all_missing_variants()

    added_count = 0

    # Add ALL missing variants, regardless of count
    for opcode_hex, variants in missing_variants.items():
        opcode_int = int(opcode_hex, 16)

        if opcode_int in opcodes:
            opcode_def = opcodes[opcode_int]

            # Make sure it has a variants section
            if isinstance(opcode_def, dict):
                if 'variants' not in opcode_def:
                    opcode_def['variants'] = OrderedDict()

                existing_variants = opcode_def['variants']

                # Add all missing variants
                for variant_hex, count in variants:
                    variant_int = int(variant_hex, 16)

                    if variant_int not in existing_variants:
                        # Determine the type based on the opcode
                        if opcode_int in [0xC4, 0xC5, 0xC6, 0xC7]:
                            mnemonic = f"CONST_{opcode_hex[2:]}_{variant_hex[2:]}"
                            description = f"Constant variant {opcode_hex[2:]}_{variant_hex[2:]}"
                            stack_effect = '0 -> 1'
                        elif opcode_int in [0xD4, 0xDC, 0xDE, 0xDF]:
                            mnemonic = f"CTRL_{opcode_hex[2:]}_{variant_hex[2:]}"
                            description = f"Control flow variant {opcode_hex[2:]}_{variant_hex[2:]}"
                            stack_effect = 'varies'
                        elif opcode_int in [0xE4, 0xE5, 0xE6, 0xE7]:
                            mnemonic = f"VAR_{opcode_hex[2:]}_{variant_hex[2:]}"
                            description = f"Variable operation {opcode_hex[2:]}_{variant_hex[2:]}"
                            stack_effect = '1 -> 1'
                        elif opcode_int in [0xE8, 0xE9, 0xEA, 0xEB]:
                            mnemonic = f"STORE_{opcode_hex[2:]}_{variant_hex[2:]}"
                            description = f"Store operation {opcode_hex[2:]}_{variant_hex[2:]}"
                            stack_effect = '2 -> 0'
                        elif opcode_int in [0xEC, 0xED, 0xEE, 0xEF]:
                            mnemonic = f"TEST_{opcode_hex[2:]}_{variant_hex[2:]}"
                            description = f"Test operation {opcode_hex[2:]}_{variant_hex[2:]}"
                            stack_effect = '1 -> 1'
                        else:
                            mnemonic = f"OP_{opcode_hex[2:]}_{variant_hex[2:]}"
                            description = f"Operation {opcode_hex[2:]}_{variant_hex[2:]}"
                            stack_effect = 'varies'

                        existing_variants[variant_int] = OrderedDict([
                            ('mnemonic', mnemonic),
                            ('operands', ['value']),
                            ('stack_effect', stack_effect),
                            ('description', description),
                        ])
                        added_count += 1
                        print(f"Added {opcode_hex} variant {variant_hex} ({count} occurrences)")

    # Save the updated file
    with open(opcodes_file, 'w') as f:
        yaml_preserve_order_dump(opcodes, f, default_flow_style=False, width=120)

    print(f"\nTotal variants added: {added_count}")


if __name__ == "__main__":
    add_all_missing_variants()
