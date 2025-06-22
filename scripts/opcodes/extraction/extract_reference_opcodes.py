#!/usr/bin/env python3
"""Extract and compare opcode definitions from reference PowerBuilder decompilers."""

import re
from collections import OrderedDict
from pathlib import Path

import yaml


def extract_csharp_opcodes() -> None:



    


    """Extract opcode definitions from C# PbdViewer."""
    opcodes = {}

    # Read the PCodeParser90.cs file for opcode mappings
    parser_path = Path("reference/decompilers/pbdviewer/Uitils/PCode/PCodeParser90.cs")
    if parser_path.exists():
        with open(parser_path) as f:
            content = f.read()

        # Extract case statements
        case_pattern = r"case\s+(\d+):\s*\n\s*(\w+)\((.*?)\);"
        matches = re.findall(case_pattern, content, re.MULTILINE)

        for match in matches:
            opcode = int(match[0])
            function = match[1]
            params = match[2]

            # Map C# function names to opcode names
            opcode_name = None
            if function == "Return":
                opcode_name = "RETURN" if "0" in params else "RETURN_VALUE"
            elif function == "Jump":
                if "JmpType.JmpIfTrue" in params:
                    opcode_name = "JUMP_IF_TRUE"
                elif "JmpType.JmpIfFalse" in params:
                    opcode_name = "JUMP_IF_FALSE"
                elif "JmpType.Jmp" in params:
                    opcode_name = "JUMP"
            elif function.startswith("Push"):
                if "LocalVariable" in function:
                    opcode_name = "PUSH_LOCAL_VAR"
                elif "SharedVariable" in function:
                    opcode_name = "PUSH_SHARED_VAR"
                elif "GlobalVariable" in function:
                    opcode_name = "PUSH_GLOBAL_VAR"
                elif "Constant" in function:
                    opcode_name = "PUSH_CONSTANT"
                elif "This" in function:
                    opcode_name = "PUSH_THIS"
                elif "Parent" in function:
                    opcode_name = "PUSH_PARENT"
            elif function == "OperateStack":
                if '"and"' in params:
                    opcode_name = "AND"
                elif '"or"' in params:
                    opcode_name = "OR"
                elif '"+"' in params:
                    opcode_name = "ADD"
                elif '"-"' in params:
                    opcode_name = "SUB"
                elif '"*"' in params:
                    opcode_name = "MUL"
                elif '"/"' in params:
                    opcode_name = "DIV"
                elif '"^"' in params:
                    opcode_name = "POWER"
                elif '"="' in params:
                    opcode_name = "EQ"
                elif '"<>"' in params:
                    opcode_name = "NE"
                elif '">"' in params:
                    opcode_name = "GT"
                elif '"<"' in params:
                    opcode_name = "LT"
                elif '">="' in params:
                    opcode_name = "GE"
                elif '"<="' in params:
                    opcode_name = "LE"
            elif function == "OperateStackSingle":
                if '"not"' in params:
                    opcode_name = "NOT"
                elif '"-"' in params:
                    opcode_name = "NEGATE"
            elif function.startswith("BeginAssign"):
                opcode_name = "BEGIN_ASSIGN"
            elif function == "EndAssign":
                opcode_name = "ASSIGN"
            elif function == "CallFunction":
                opcode_name = "CALL_FUNCTION"
            elif function == "CreateObject":
                opcode_name = "CREATE_OBJECT"
            elif function == "DestroyObject":
                opcode_name = "DESTROY_OBJECT"
            elif function == "Halt":
                opcode_name = "HALT"

            if opcode_name:
                opcodes[hex(opcode)] = opcode_name

    # For PowerBuilder 10.5, adjust opcode values (offset by 1)
    parser105_path = Path(
        "reference/decompilers/pbdviewer/Uitils/PCode/PCodeParser105.cs"
    )
    if parser105_path.exists():
        # PB 10.5 shifts opcodes by 1
        adjusted_opcodes = {}
        for opcode_hex, name in opcodes.items():
            opcode_val = int(opcode_hex, 16)
            if opcode_val >= 2:
                adjusted_opcodes[hex(opcode_val + 1)] = name
        # Special cases for 0 and 1
        adjusted_opcodes["0x0"] = "RETURN"
        adjusted_opcodes["0x1"] = "RETURN_VALUE"
        return adjusted_opcodes

    return opcodes


def extract_python_opcodes() -> list:



    


    """Extract opcode definitions from Python powerbuilder-decompile."""
    opcodes = {}

    pcode_path = Path("reference/decompilers/powerbuilder-decompile/pbd/pcode.py")
    if pcode_path.exists():
        with open(pcode_path) as f:
            content = f.read()

        # Extract g_codes dictionary
        g_codes_start = content.find("g_codes = [")
        if g_codes_start != -1:
            g_codes_end = content.find("]", g_codes_start) + 1
            g_codes_text = content[g_codes_start:g_codes_end]

            # Parse each opcode entry
            entry_pattern = r"'index':\s*0x([0-9a-fA-F]+),\s*'name':\s*'([^']+)'"
            matches = re.findall(entry_pattern, g_codes_text)

            for match in matches:
                opcode_hex = f"0x{match[0].upper()}"
                opcode_name = match[1].replace("SM_", "")  # Remove SM_ prefix
                opcodes[opcode_hex] = opcode_name

    return opcodes


def load_guessed_opcodes() -> None:



    


    """Load our guessed opcodes."""
    opcodes = {}

    guessed_path = Path("extract/pbd_core/opcodes_guessed.yaml")
    if guessed_path.exists():
        with open(guessed_path) as f:
            data = yaml.safe_load(f)
            if data and "opcodes" in data:
                for opcode_hex, info in data["opcodes"].items():
                    if isinstance(info, dict) and "name" in info:
                        opcodes[opcode_hex.upper()] = info["name"]

    return opcodes


def create_verified_opcodes(csharp_opcodes, python_opcodes, guessed_opcodes) -> None:



    


    """Create verified opcodes by comparing references."""
    verified = OrderedDict()

    # Get all unique opcode values
    all_opcodes = set()
    all_opcodes.update(csharp_opcodes.keys())
    all_opcodes.update(python_opcodes.keys())
    all_opcodes.update(guessed_opcodes.keys())

    # Sort opcodes numerically
    sorted_opcodes = sorted(all_opcodes, key=lambda x: int(x, 16))

    for opcode_hex in sorted_opcodes:
        csharp_name = csharp_opcodes.get(opcode_hex, "")
        python_name = python_opcodes.get(opcode_hex, "")
        guessed_name = guessed_opcodes.get(opcode_hex, "")

        # Determine the verified name
        verified_name = None
        confidence = "low"
        source = []

        if csharp_name and python_name:
            # Both references agree (normalize names for comparison)
            if csharp_name.replace("_", "") == python_name.replace("_", ""):
                verified_name = python_name  # Use Python naming convention
                confidence = "high"
                source = ["pbdviewer", "powerbuilder-decompile"]
            else:
                # References disagree, prefer Python as it seems more complete
                verified_name = python_name if python_name else csharp_name
                confidence = "medium"
                source = ["powerbuilder-decompile"] if python_name else ["pbdviewer"]
        elif python_name:
            verified_name = python_name
            confidence = "medium"
            source = ["powerbuilder-decompile"]
        elif csharp_name:
            verified_name = csharp_name
            confidence = "medium"
            source = ["pbdviewer"]

        if verified_name:
            # Determine instruction length based on opcode value
            opcode_val = int(opcode_hex, 16)

            # Default lengths based on patterns observed
            length = 1  # Default
            if 0x00 <= opcode_val <= 0x28:
                length_map = {
                    0x01: 2,
                    0x02: 2,
                    0x03: 2,
                    0x04: 2,
                    0x0A: 2,
                    0x0B: 4,
                    0x0C: 4,
                    0x0D: 2,
                    0x0E: 4,
                    0x0F: 4,
                    0x10: 5,
                    0x13: 6,
                    0x15: 4,
                    0x17: 4,
                    0x18: 4,
                    0x1A: 5,
                    0x1B: 4,
                    0x1C: 6,
                    0x1D: 5,
                    0x1E: 2,
                    0x1F: 2,
                    0x20: 3,
                    0x27: 2,
                }
                length = length_map.get(opcode_val, 1)
            elif 0x29 <= opcode_val <= 0x3D:
                length = 3 if opcode_val in [0x29, 0x2B, 0x2C, 0x2D, 0x2E] else 2
            elif opcode_val >= 0x80:
                length = 2 if opcode_val in range(0x80, 0x8D) else 1

            verified[opcode_hex] = OrderedDict(
                [
                    ("name", verified_name),
                    ("length", length),
                    ("confidence", confidence),
                    ("source", source),
                    (
                        "notes",
                        f"C#: {csharp_name}, Py: {python_name}, Guessed: {guessed_name}",
                    ),
                ]
            )

    return verified


def main() -> None:
    
    


    # Extract from both sources
    csharp_opcodes = extract_csharp_opcodes()

    python_opcodes = extract_python_opcodes()

    guessed_opcodes = load_guessed_opcodes()

    # Create verified opcodes
    verified_opcodes = create_verified_opcodes(
        csharp_opcodes, python_opcodes, guessed_opcodes
    )

    # Save verified opcodes
    output_path = Path("extract/pbd_core/opcodes_verified.yaml")

    # Convert OrderedDict to regular dict for YAML compatibility
    simple_opcodes = {}
    for opcode_hex, info in verified_opcodes.items():
        simple_opcodes[opcode_hex] = dict(info)

    with open(output_path, "w") as f:
        yaml.dump(
            {
                "format_version": "1.0",
                "description": "PowerBuilder P-code opcodes verified from reference implementations",
                "sources": [
                    "https://github.com/hucxy/pbdviewer",
                    "https://github.com/sijms/powerbuilder-decompile",
                ],
                "opcodes": simple_opcodes,
            },
            f,
            default_flow_style=False,
            sort_keys=False,
        )

    # Show summary
    sum(1 for op in verified_opcodes.values() if op["confidence"] == "high")
    sum(1 for op in verified_opcodes.values() if op["confidence"] == "medium")
    sum(1 for op in verified_opcodes.values() if op["confidence"] == "low")

    # Show sample comparisons
    for i, (opcode_hex, info) in enumerate(verified_opcodes.items()):
        if i >= 10:
            break


if __name__ == "__main__":
    main()
