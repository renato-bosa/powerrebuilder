#!/usr/bin/env python3
"""Validate opcode interpretations by checking logical patterns in decoded output."""

import re
from collections import Counter, defaultdict
from pathlib import Path


class OpcodeValidator:
    """Validate opcode interpretations through pattern analysis."""

    def __init__(self):
        self.stack_depth = 0
        self.warnings = []
        self.patterns = defaultdict(list)

    def validate_file(self, pcode_file: Path):
        """Validate a decoded P-code file."""
        print(f"Validating {pcode_file}...")

        with open(pcode_file) as f:
            lines = f.readlines()

        instructions = self._parse_instructions(lines)

        # Run various validation checks
        print("\n1. STACK BALANCE CHECK:")
        self._check_stack_balance(instructions)

        print("\n2. PATTERN CONSISTENCY CHECK:")
        self._check_pattern_consistency(instructions)

        print("\n3. OPCODE SEQUENCE VALIDATION:")
        self._check_opcode_sequences(instructions)

        print("\n4. CONSTANT USAGE ANALYSIS:")
        self._analyze_constant_usage(instructions)

        print("\n5. CONTROL FLOW VALIDATION:")
        self._validate_control_flow(instructions)

        # Summary
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY:")
        print(f"Total warnings: {len(self.warnings)}")
        for warning in self.warnings[:10]:  # Show first 10
            print(f"  ⚠️  {warning}")
        if len(self.warnings) > 10:
            print(f"  ... and {len(self.warnings) - 10} more warnings")

    def _parse_instructions(self, lines: list[str]) -> list[dict]:
        """Parse instruction lines into structured format."""
        instructions = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse format: "0036: FUNCTION_START"
            match = re.match(r'([0-9A-F]+):\s+(\S+)(?:\s+(.*))?', line)
            if match:
                addr = match.group(1)
                opcode = match.group(2)
                operands = match.group(3) or ""

                instructions.append({
                    'address': addr,
                    'opcode': opcode,
                    'operands': operands,
                    'line': line,
                })

        return instructions

    def _check_stack_balance(self, instructions: list[dict]):
        """Check if stack operations are balanced."""
        stack_depth = 0
        max_depth = 0
        min_depth = 0

        # Define stack effects for our opcodes
        stack_effects = {
            # Constants push 1
            'CONST_': (0, 1),
            'STRING': (0, 1),
            'LOAD_': (0, 1),

            # Stores pop 1
            'STORE_': (1, 0),

            # Binary ops pop 2, push 1
            'COMPARE': (2, 1),
            'ARITHMETIC_OP': (2, 1),
            'LOGICAL_OP': (2, 1),

            # Jumps pop 1
            'JUMP_COND_': (1, 0),
            'JUMP_IF_': (1, 0),

            # Function calls vary
            'CALL_': ('varies', 1),
        }

        for inst in instructions:
            opcode = inst['opcode']

            # Find matching stack effect
            for pattern, (pop, push) in stack_effects.items():
                if opcode.startswith(pattern):
                    if pop != 'varies':
                        stack_depth -= pop
                        stack_depth += push
                    break

            max_depth = max(max_depth, stack_depth)
            min_depth = min(min_depth, stack_depth)

            if stack_depth < 0:
                self.warnings.append(f"Stack underflow at {inst['address']}: {inst['line']}")

        print(f"  Final stack depth: {stack_depth}")
        print(f"  Max depth: {max_depth}, Min depth: {min_depth}")

        if stack_depth != 0:
            self.warnings.append(f"Stack not balanced! Final depth: {stack_depth}")

    def _check_pattern_consistency(self, instructions: list[dict]):
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
        print("  Most common patterns:")
        for pattern, count in pattern_counts.most_common(10):
            print(f"    {pattern}: {count} times")

    def _check_opcode_sequences(self, instructions: list[dict]):
        """Validate that opcode sequences make logical sense."""
        for i in range(len(instructions) - 2):
            seq = [instructions[i], instructions[i+1], instructions[i+2]]

            # Check for illogical sequences
            # E.g., two stores in a row without a load
            if all('STORE' in inst['opcode'] for inst in seq[:2]):
                self.warnings.append(f"Suspicious: Two STOREs in a row at {seq[0]['address']}")

            # Jump to next instruction (pointless)
            if 'JUMP' in seq[0]['opcode'] and seq[0]['operands'].strip() == seq[1]['address']:
                self.warnings.append(f"Pointless jump to next instruction at {seq[0]['address']}")

    def _analyze_constant_usage(self, instructions: list[dict]):
        """Analyze how constants are used."""
        const_instructions = [inst for inst in instructions if 'CONST' in inst['opcode']]

        print(f"  Total constants: {len(const_instructions)}")

        # Group by constant type
        const_types = Counter(inst['opcode'].split('_')[1] if '_' in inst['opcode'] else 'UNKNOWN'
                              for inst in const_instructions)

        print("  Constant types:")
        for ctype, count in const_types.most_common():
            print(f"    {ctype}: {count}")

        # Check if constants are followed by operations
        for i, inst in enumerate(instructions):
            if 'CONST' in inst['opcode'] and i < len(instructions) - 1:
                next_inst = instructions[i + 1]
                if 'CONST' in next_inst['opcode']:
                    # Two constants in a row - likely for binary operation
                    if i < len(instructions) - 2:
                        third = instructions[i + 2]
                        if 'COMPARE' not in third['opcode'] and 'ARITHMETIC' not in third['opcode']:
                            self.warnings.append(f"Two constants not followed by operation at {inst['address']}")

    def _validate_control_flow(self, instructions: list[dict]):
        """Validate control flow instructions."""
        # Collect all addresses
        addresses = {inst['address'] for inst in instructions}

        # Check jump targets
        jumps = [inst for inst in instructions if 'JUMP' in inst['opcode']]

        for jump in jumps:
            # Extract target from operands
            target_match = re.search(r'([0-9A-F]+)', jump['operands'])
            if target_match:
                target = target_match.group(1)
                if target not in addresses:
                    self.warnings.append(f"Jump to non-existent address {target} at {jump['address']}")

        print(f"  Total jumps: {len(jumps)}")
        print(f"  Jump types: {Counter(j['opcode'] for j in jumps).most_common(5)}")

def compare_with_source(pcode_file: Path, source_file: Path = None):
    """Compare decoded P-code with known source code patterns."""
    print("\n" + "="*60)
    print("SOURCE COMPARISON:")

    # If we had source code, we could verify:
    # - Variable declarations match LOAD/STORE patterns
    # - Function calls match CALL opcodes
    # - Control structures match JUMP patterns

    if source_file and source_file.exists():
        print(f"Comparing with source: {source_file}")
        # TODO: Implement source comparison
    else:
        print("No source file available for comparison")
        print("To truly validate opcodes, we need:")
        print("  1. Known PowerBuilder source code")
        print("  2. Its compiled P-code")
        print("  3. Expected behavior documentation")

def main():
    """Run validation on decoded P-code files."""
    import sys

    if len(sys.argv) > 1:
        pcode_file = Path(sys.argv[1])
    else:
        pcode_file = Path("test.pcode")

    if not pcode_file.exists():
        print(f"File not found: {pcode_file}")
        return

    validator = OpcodeValidator()
    validator.validate_file(pcode_file)

    # Additional validation approaches
    print("\n" + "="*60)
    print("ADDITIONAL VALIDATION NEEDED:")
    print("1. Cross-reference with PowerBuilder documentation")
    print("2. Test with known source->P-code pairs")
    print("3. Execute decompiled code and verify behavior")
    print("4. Compare with other PowerBuilder decompilers")
    print("5. Analyze more P-code files for pattern confirmation")

if __name__ == "__main__":
    main()
