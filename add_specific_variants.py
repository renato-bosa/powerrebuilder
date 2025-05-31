#!/usr/bin/env python3
"""Add specific missing variants to existing opcodes in opcodes.yaml."""

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

def get_missing_variants():
    """Extract missing variants from unknown_opcodes.log."""
    with open('unknown_opcodes.log') as f:
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
        if count >= 10:  # Only include variants with at least 10 occurrences
            if opcode not in missing_variants:
                missing_variants[opcode] = []
            missing_variants[opcode].append((variant, count))

    return missing_variants

def add_variants_manually() -> None:
    """Add missing variants to opcodes.yaml manually."""
    opcodes_file = Path('extract/pbd_core/opcodes.yaml')

    # Load existing YAML
    with open(opcodes_file) as f:
        opcodes = yaml_preserve_order_load(f)

    missing_variants = get_missing_variants()

    # Priority additions based on frequency
    priority_additions = {
        0xC4: ['0x83', '0x97', '0x93', '0x9B', '0x9F', '0xB1', '0xB5', '0xB6', '0xB9', '0xBD', '0xBE'],
        0xC5: ['0xA1', '0xA7', '0xA9', '0xAD', '0xAF', '0xB3', '0xB7', '0xBD', '0xBE'],
        0xC6: ['0xA1', '0xA2', '0xA3', '0xA5', '0xA6', '0xAA', '0xAD', '0xAE', '0xB3', '0xB5', '0xB6', '0xB7', '0xB9', '0xBA', '0xBD'],
        0xC7: ['0x8F', '0xBD', '0x81', '0x83', '0x85', '0x87', '0x89', '0x8A', '0x8B', '0x8D', '0x93', '0x95', '0x97', '0x99', '0x9B', '0x9D', '0x9F', '0xA2', '0xA3', '0xA5', '0xA6', '0xA7', '0xAB', '0xAF', '0xB1', '0xB2', '0xB3', '0xB5', '0xB7', '0xB9', '0xBE'],
        0xE5: ['0x86', '0x8E', '0x96', '0x9E', '0xA6', '0xAE', '0xB6', '0xBE'],
        0xE6: ['0xB8', '0x8C', '0x84'],  # E6 B8 is the most common remaining unknown
        0xE7: ['0x8C', '0x84', '0x9C', '0xA4', '0xAC', '0xB4', '0xBC'],
        0xE8: ['0xB0', '0x88', '0x90', '0x98', '0xA0', '0xA8', '0xB8'],
        0x90: ['0xC2', '0xC3', '0xC4', '0xC5'],
        0xDC: ['0x80'],  # DC 80 was common in earlier analysis
        0x8A: ['0x00'],  # 8A 00 pattern
        0xE4: ['0xB6', '0xBE', '0x86', '0x8E', '0x96', '0x9E', '0xA6', '0xAE'],
    }

    added_count = 0

    for opcode_int, variants_to_add in priority_additions.items():
        opcode_hex = f'0x{opcode_int:02X}'

        if opcode_int in opcodes:
            opcode_def = opcodes[opcode_int]

            # Make sure it has a variants section
            if isinstance(opcode_def, dict):
                if 'variants' not in opcode_def:
                    opcode_def['variants'] = OrderedDict()

                variants = opcode_def['variants']

                # Add missing variants
                for variant in variants_to_add:
                    variant_int = int(variant, 16)

                    # Check if this variant exists in our missing list
                    variant_in_missing = False
                    if opcode_hex in missing_variants:
                        for v, _count in missing_variants[opcode_hex]:
                            if v == variant:
                                variant_in_missing = True
                                break

                    if variant_int not in variants and variant_in_missing:
                        # Determine the type of constant based on the opcode
                        if opcode_int in [0xC4, 0xC5, 0xC6, 0xC7]:
                            mnemonic = f"CONST_{opcode_hex[2:]}_{variant[2:]}"
                            description = f"Constant variant {opcode_hex[2:]}_{variant[2:]}"
                        elif opcode_int == 0xE5:
                            mnemonic = f"OBJ_OP_{opcode_hex[2:]}_{variant[2:]}"
                            description = f"Object operation {opcode_hex[2:]}_{variant[2:]}"
                        elif opcode_int == 0xE6:
                            mnemonic = f"TYPE_OP_{opcode_hex[2:]}_{variant[2:]}"
                            description = f"Type operation {opcode_hex[2:]}_{variant[2:]}"
                        else:
                            mnemonic = f"OP_{opcode_hex[2:]}_{variant[2:]}"
                            description = f"Operation {opcode_hex[2:]}_{variant[2:]}"

                        variants[variant_int] = OrderedDict([
                            ('mnemonic', mnemonic),
                            ('operands', ['value']),
                            ('stack_effect', '0 -> 1' if opcode_int in [0xC4, 0xC5, 0xC6, 0xC7] else '1 -> 1'),
                            ('description', description),
                        ])
                        added_count += 1

    # Save the updated file
    with open(opcodes_file, 'w') as f:
        yaml_preserve_order_dump(opcodes, f, default_flow_style=False, width=120)


if __name__ == "__main__":
    add_variants_manually()
