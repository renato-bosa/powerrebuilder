#!/usr/bin/env python3
"""Validate opcode interpretations by checking logical patterns in decoded output."""

import re
from collections import Counter, defaultdict
from pathlib import Path


class OpcodeValidator:
    """Validate opcode interpretations through pattern analysis."""

    def __init__(self) -> None:
        self.stack_depth = 0
        self.warnings = []
        self.patterns = defaultdict(list)

    def validate_file(self, pcode_file: Path) -> None:
        """Validate a decoded P-code file."""
        with open(pcode_file) as f:
            lines = f.readlines()

        instructions = self._parse_instructions(lines)

        # Run various validation checks
        self._check_stack_balance(instructions)

        self._check_pattern_consistency(instructions)

        self._check_opcode_sequences(instructions)

        self._analyze_constant_usage(instructions)

        self._validate_control_flow(instructions)

        # Summary
        for _warning in self.warnings[:10]:  # Show first 10
            pass
        if len(self.warnings) > 10:
            pass

    def _parse_instructions(self, lines: list[str]) -> list[dict]:
        """Parse instruction lines into structured format."""
        instructions = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse format: "0036: FUNCTION_START"
            match = re.match(r"([0-9A-F]+):\s+(\S+)(?:\s+(.*))?", line)
            if match:
                addr = match.group(1)
                opcode = match.group(2)
                operands = match.group(3) or ""

                instructions.append(
                    {
                        "address": addr,
                        "opcode": opcode,
                        "operands": operands,
                        "line": line,
                    },
                )

        return instructions

    def _check_stack_balance(self, instructions: list[dict]) -> None:
        """Check if stack operations are balanced."""
        stack_depth = 0
        max_depth = 0
        min_depth = 0

        # Define stack effects for our opcodes
        stack_effects = {
            # Constants push 1
            "CONST_": (0, 1),
            "STRING": (0, 1),
            "LOAD_": (0, 1),
            # Stores pop 1
            "STORE_": (1, 0),
            # Binary ops pop 2, push 1
            "COMPARE": (2, 1),
            "ARITHMETIC_OP": (2, 1),
            "LOGICAL_OP": (2, 1),
            # Jumps pop 1
            "JUMP_COND_": (1, 0),
            "JUMP_IF_": (1, 0),
            # Function calls vary
            "CALL_": ("varies", 1),
        }

        for inst in instructions:
            opcode = inst["opcode"]

            # Find matching stack effect
            for pattern, (pop, push) in stack_effects.items():
                if opcode.startswith(pattern):
                    if pop != "varies":
                        stack_depth -= pop
                        stack_depth += push
                    break

            max_depth = max(max_depth, stack_depth)
            min_depth = min(min_depth, stack_depth)

            if stack_depth < 0:
                self.warnings.append(
                    f"Stack underflow at {inst['address']}: {inst['line']}",
                )

        if stack_depth != 0:
            self.warnings.append(f"Stack not balanced! Final depth: {stack_depth}")

    def _check_pattern_consistency(self, instructions: list[dict]) -> None:
        """Check if similar opcodes appear in similar contexts."""
        # Look for patterns like LOAD followed by STORE
        patterns = []

        for i in range(len(instructions) - 1):
            curr = instructions[i]
            next = instructions[i + 1]

            pattern = f"{curr['opcode']} -> {next['opcode']}"
            patterns.append(pattern)

        # Count common patterns
        pattern_counts = Counter(patterns)
        for pattern, _count in pattern_counts.most_common(10):
            pass

    def _check_opcode_sequences(self, instructions: list[dict]) -> None:
        """Validate that opcode sequences make logical sense."""
        for i in range(len(instructions) - 2):
            seq = [instructions[i], instructions[i + 1], instructions[i + 2]]

            # Check for illogical sequences
            # E.g., two stores in a row without a load
            if all("STORE" in inst["opcode"] for inst in seq[:2]):
                self.warnings.append(
                    f"Suspicious: Two STOREs in a row at {seq[0]['address']}",
                )

            # Jump to next instruction (pointless)
            if (
                "JUMP" in seq[0]["opcode"]
                and seq[0]["operands"].strip() == seq[1]["address"]
            ):
                self.warnings.append(
                    f"Pointless jump to next instruction at {seq[0]['address']}",
                )

    def _analyze_constant_usage(self, instructions: list[dict]) -> None:
        """Analyze how constants are used."""
        const_instructions = [
            inst for inst in instructions if "CONST" in inst["opcode"]
        ]

        # Group by constant type
        const_types = Counter(
            inst["opcode"].split("_")[1] if "_" in inst["opcode"] else "UNKNOWN"
            for inst in const_instructions
        )

        for _ctype, _count in const_types.most_common():
            pass

        # Check if constants are followed by operations
        for i, inst in enumerate(instructions):
            if "CONST" in inst["opcode"] and i < len(instructions) - 1:
                next_inst = instructions[i + 1]
                if "CONST" in next_inst["opcode"]:
                    # Two constants in a row - likely for binary operation
                    if i < len(instructions) - 2:
                        third = instructions[i + 2]
                        if (
                            "COMPARE" not in third["opcode"]
                            and "ARITHMETIC" not in third["opcode"]
                        ):
                            self.warnings.append(
                                f"Two constants not followed by operation at {inst['address']}",
                            )

    def _validate_control_flow(self, instructions: list[dict]) -> None:
        """Validate control flow instructions."""
        # Collect all addresses
        addresses = {inst["address"] for inst in instructions}

        # Check jump targets
        jumps = [inst for inst in instructions if "JUMP" in inst["opcode"]]

        for jump in jumps:
            # Extract target from operands
            target_match = re.search(r"([0-9A-F]+)", jump["operands"])
            if target_match:
                target = target_match.group(1)
                if target not in addresses:
                    self.warnings.append(
                        f"Jump to non-existent address {target} at {jump['address']}",
                    )


def compare_with_source(pcode_file: Path, source_file: Path | None = None) -> None:
    """Compare decoded P-code with known source code patterns."""
    # If we had source code, we could verify:
    # - Variable declarations match LOAD/STORE patterns
    # - Function calls match CALL opcodes
    # - Control structures match JUMP patterns

    if source_file and source_file.exists():

        # Read source code
        with open(source_file) as f:
            source_content = f.read()

        # Read P-code
        with open(pcode_file) as f:
            pcode_lines = f.readlines()

        # Parse instructions
        validator = OpcodeValidator()
        instructions = validator._parse_instructions(pcode_lines)

        # Extract patterns from source
        source_patterns = extract_source_patterns(source_content)

        # Compare patterns
        compare_patterns(instructions, source_patterns)
    else:
        pass


def extract_source_patterns(source_content: str) -> dict:
    """Extract patterns from PowerBuilder source code."""
    patterns = {
        "variables": [],
        "functions": [],
        "control_structures": [],
        "assignments": [],
        "comparisons": [],
    }

    lines = source_content.split("\n")

    for line in lines:
        line = line.strip()

        # Variable declarations
        if any(
            keyword in line
            for keyword in ["integer", "string", "long", "boolean", "decimal"]
        ):
            # Extract variable name
            var_match = re.search(
                r"(integer|string|long|boolean|decimal)\s+(\w+)", line
            )
            if var_match:
                patterns["variables"].append(
                    {
                        "type": var_match.group(1),
                        "name": var_match.group(2),
                    }
                )

        # Function calls
        func_match = re.search(r"(\w+)\s*\((.*?)\)", line)
        if func_match and not any(kw in line for kw in ["if", "while", "for"]):
            patterns["functions"].append(
                {
                    "name": func_match.group(1),
                    "args": func_match.group(2),
                }
            )

        # Control structures
        if line.startswith("if "):
            patterns["control_structures"].append({"type": "if", "line": line})
        elif line.startswith("for "):
            patterns["control_structures"].append({"type": "for", "line": line})
        elif line.startswith("while "):
            patterns["control_structures"].append({"type": "while", "line": line})

        # Assignments
        if "=" in line and not any(op in line for op in ["==", "!=", "<=", ">="]):
            assign_match = re.search(r"(\w+)\s*=\s*(.+)", line)
            if assign_match:
                patterns["assignments"].append(
                    {
                        "target": assign_match.group(1),
                        "value": assign_match.group(2),
                    }
                )

        # Comparisons
        if any(op in line for op in ["==", "!=", "<", ">", "<=", ">="]):
            patterns["comparisons"].append(line)

    return patterns


def compare_patterns(instructions: list[dict], source_patterns: dict) -> None:
    """Compare P-code instructions with source patterns."""
    # Count instruction types
    inst_counts = Counter(inst["opcode"].split("_")[0] for inst in instructions)

    # Check variables
    sum(
        count for opcode, count in inst_counts.items() if opcode in ["LOAD", "STORE"]
    )
    len(source_patterns["variables"])

    # Check function calls
    inst_counts.get("CALL", 0)
    len(source_patterns["functions"])

    # Check control structures
    sum(count for opcode, count in inst_counts.items() if "JUMP" in opcode)
    len(source_patterns["control_structures"])

    # Check comparisons
    inst_counts.get("COMPARE", 0)
    len(source_patterns["comparisons"])

    # Detailed analysis

    # Map variable names to potential LOAD/STORE operations
    if source_patterns["variables"]:
        for _var in source_patterns["variables"][:5]:  # Show first 5
            pass

    # Map function calls
    if source_patterns["functions"]:
        for _func in source_patterns["functions"][:5]:  # Show first 5
            pass

    # Validate control flow
    if source_patterns["control_structures"]:
        for _ctrl in source_patterns["control_structures"][:5]:  # Show first 5
            pass


def main() -> None:
    """Run validation on decoded P-code files."""
    import sys

    pcode_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test.pcode")
    source_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not pcode_file.exists():
        return

    validator = OpcodeValidator()
    validator.validate_file(pcode_file)

    # Additional validation approaches
    if source_file:
        compare_with_source(pcode_file, source_file)
    else:
        pass


if __name__ == "__main__":
    main()
