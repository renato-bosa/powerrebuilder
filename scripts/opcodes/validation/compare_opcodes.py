#!/usr/bin/env python3
"""Compare our guessed opcodes with verified opcodes from reference implementations."""

from collections import Counter
from pathlib import Path

import yaml


def load_opcodes(filepath):
    """Load opcodes from YAML file."""
    opcodes = {}
    if Path(filepath).exists():
        with open(filepath) as f:
            data = yaml.safe_load(f)

            # Handle different YAML formats
            if data:
                if "opcodes" in data:
                    # Verified format: has 'opcodes' key
                    for opcode_hex, info in data["opcodes"].items():
                        if isinstance(info, dict):
                            opcodes[opcode_hex.upper()] = info
                else:
                    # Guessed format: direct numeric keys
                    for key, info in data.items():
                        if isinstance(key, int):
                            # Convert numeric key to hex
                            opcode_hex = f"0x{key:X}"
                            if isinstance(info, dict):
                                # Transform guessed format to match verified format
                                opcodes[opcode_hex] = {
                                    "name": info.get("mnemonic", "UNKNOWN"),
                                    "category": info.get("category", "unknown"),
                                    "description": info.get("description", ""),
                                    "operands": info.get("operands", []),
                                    "stack_effect": info.get("stack_effect", "0 -> 0"),
                                }
    return opcodes


def compare_opcodes() -> None:
    """Compare guessed and verified opcodes."""
    # Load both sets of opcodes
    guessed = load_opcodes("extract/pbd_core/opcodes_guessed.yaml")
    verified = load_opcodes("extract/pbd_core/opcodes_verified.yaml")

    # Find common opcodes
    common_opcodes = set(guessed.keys()) & set(verified.keys())
    set(guessed.keys()) - set(verified.keys())
    set(verified.keys()) - set(guessed.keys())

    # Compare names for common opcodes
    name_matches = 0
    name_partial_matches = 0
    name_mismatches = []

    for opcode in sorted(common_opcodes, key=lambda x: int(x, 16)):
        guessed_name = guessed[opcode].get("name", "UNKNOWN")
        verified_name = verified[opcode].get("name", "UNKNOWN")

        if guessed_name == verified_name:
            name_matches += 1
        elif (
            guessed_name.lower() in verified_name.lower()
            or verified_name.lower() in guessed_name.lower()
        ):
            name_partial_matches += 1
        else:
            name_mismatches.append((opcode, guessed_name, verified_name))

    # Show some examples of mismatches
    if name_mismatches:
        for _i, (opcode, guessed_name, verified_name) in enumerate(
            name_mismatches[:20]
        ):
            pass

    # Analyze guessed opcode patterns
    guessed_prefixes = Counter()
    for opcode, info in guessed.items():
        name = info.get("name", "UNKNOWN")
        prefix = name.split("_")[0] if "_" in name else name
        guessed_prefixes[prefix] += 1

    for prefix, _count in guessed_prefixes.most_common(10):
        pass

    # Analyze verified opcode patterns
    verified_prefixes = Counter()
    for opcode, info in verified.items():
        name = info.get("name", "UNKNOWN")
        prefix = name.split("_")[0] if "_" in name else name
        verified_prefixes[prefix] += 1

    for prefix, _count in verified_prefixes.most_common(10):
        pass

    # Check specific opcodes we thought we knew
    key_opcodes = {
        "0xE4": "LOAD",  # We thought this was LOAD
        "0xE8": "STORE",  # We thought this was STORE
        "0xC4": "CONST_0",  # We thought this was a constant
        "0xD4": "JUMP",  # We thought this was JUMP
        "0xE0": "CONDITIONAL_JUMP",  # We thought this was conditional jump
        "0xE1": "CALL",  # We thought this was CALL
    }

    for opcode, our_guess in key_opcodes.items():
        if opcode in verified:
            verified_name = verified[opcode].get("name", "UNKNOWN")
            guessed_name = guessed.get(opcode, {}).get("name", "NOT FOUND")
            "✓" if our_guess.lower() in verified_name.lower() else "✗"

    # Summary statistics
    if common_opcodes:
        (name_matches + name_partial_matches) / len(common_opcodes) * 100
    else:
        pass


if __name__ == "__main__":
    compare_opcodes()
