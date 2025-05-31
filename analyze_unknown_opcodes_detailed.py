#!/usr/bin/env python3
"""Detailed analysis of unknown opcodes to determine their function."""

import re
from collections import Counter, defaultdict
from pathlib import Path


class DetailedOpcodeAnalyzer:
    """Analyze unknown opcodes in detail to determine their function."""

    def __init__(self) -> None:
        self.unknown_log = Path('unknown_opcodes.log')
        self.opcodes_yaml = Path('extract/pbd_core/opcodes.yaml')

    def analyze(self) -> None:
        """Perform detailed analysis of unknown opcodes."""
        if not self.unknown_log.exists():
            return

        # Parse unknown opcodes
        unknowns = self._parse_unknowns()

        # Analyze each unknown opcode
        for opcode, instances in unknowns.items():

            self._analyze_opcode(opcode, instances)

    def _parse_unknowns(self) -> dict[str, list[dict]]:
        """Parse unknown opcodes from log."""
        unknowns = defaultdict(list)

        with open(self.unknown_log) as f:
            for line in f:
                match = re.search(
                    r'Opcode: (0x[A-F0-9]+).*Pos: (\d+).*Obj: (\S+).*Context: ([a-f0-9 ]+)',
                    line,
                )
                if match:
                    opcode = match.group(1)
                    position = int(match.group(2))
                    obj_file = match.group(3)
                    context = match.group(4).split()

                    unknowns[opcode].append({
                        'position': position,
                        'file': obj_file,
                        'context': context,
                        'line': line.strip(),
                    })

        return dict(unknowns)

    def _analyze_opcode(self, opcode: str, instances: list[dict]) -> None:
        """Analyze a specific unknown opcode."""
        # 1. Context analysis
        self._analyze_contexts(opcode, instances)

        # 2. Pattern analysis
        self._analyze_patterns(opcode, instances)

        # 3. File type analysis
        file_types = Counter(inst['file'].split('.')[-1] for inst in instances)
        for _ftype, _count in file_types.items():
            pass

        # 4. Hypothesis generation
        self._generate_hypothesis(opcode, instances)

    def _analyze_contexts(self, opcode: str, instances: list[dict]) -> None:
        """Analyze the context bytes around the opcode."""
        # Look at bytes before and after
        before_bytes = []
        after_bytes = []

        opcode_hex = opcode.lower()[2:]

        for inst in instances:
            context = inst['context']
            # Find opcode position
            for i, byte in enumerate(context):
                if byte == opcode_hex:
                    # Get surrounding bytes
                    if i > 0:
                        before_bytes.append(context[i-1])
                    if i < len(context) - 1:
                        after_bytes.append(context[i+1])

                    # Show full context for this instance
                    start = max(0, i-3)
                    end = min(len(context), i+4)
                    context_str = ' '.join(context[start:end])
                    # Highlight the opcode
                    context_str = context_str.replace(opcode_hex, f'[{opcode_hex.upper()}]')
                    break

        # Analyze patterns
        if before_bytes:
            pass
        if after_bytes:
            pass

    def _analyze_patterns(self, opcode: str, instances: list[dict]) -> None:
        """Look for patterns in how the opcode is used."""
        int(opcode, 16)

        # Check if it's part of a multi-byte sequence
        for inst in instances:
            context = inst['context']
            opcode_hex = opcode.lower()[2:]

            for i, byte in enumerate(context):
                if byte == opcode_hex:
                    # Check for common patterns
                    if i > 0 and i < len(context) - 1:
                        prev_byte = int(context[i-1], 16)
                        next_byte = int(context[i+1], 16)

                        # Check if it's a variant pattern (base + variant)
                        if prev_byte >= 0x80:
                            pass

                        # Check if next byte is a variant indicator
                        if next_byte >= 0x80:
                            pass
                    break

    def _generate_hypothesis(self, opcode: str, instances: list[dict]) -> None:
        """Generate hypothesis about what the opcode does."""
        opcode_int = int(opcode, 16)

        # Based on byte range
        if 0x00 <= opcode_int <= 0x1F or 0x80 <= opcode_int <= 0x9F or 0xA0 <= opcode_int <= 0xBF or 0xC0 <= opcode_int <= 0xCF:
            pass

        # Specific hypotheses based on opcode
        if opcode in {"0x0E", "0x90"} or opcode in {"0x99", "0xA7"} or opcode == "0xBD":
            pass

    def find_in_source_files(self, opcode: str) -> None:
        """Look for the opcode in actual P-code files to get more examples."""
        opcode_byte = bytes([int(opcode, 16)])
        search_dirs = [
            "output/test_bytes_fix",
            "output/test_final",
            "output/test_corrected",
        ]

        found_count = 0
        for search_dir in search_dirs:
            dir_path = Path(search_dir)
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*.fun"):
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()

                    # Search for opcode
                    offset = 0
                    while True:
                        pos = data.find(opcode_byte, offset)
                        if pos == -1:
                            break

                        # Get context
                        start = max(0, pos - 10)
                        end = min(len(data), pos + 10)
                        context = data[start:end]

                        # Format as hex
                        hex_context = ' '.join(f'{b:02x}' for b in context)
                        rel_pos = pos - start

                        # Highlight the opcode
                        hex_parts = hex_context.split()
                        if rel_pos < len(hex_parts):
                            hex_parts[rel_pos] = f'[{hex_parts[rel_pos].upper()}]'
                        hex_context = ' '.join(hex_parts)

                        found_count += 1

                        offset = pos + 1

                        if found_count >= 10:  # Limit output
                            return

                except Exception:
                    continue


def main() -> None:
    analyzer = DetailedOpcodeAnalyzer()
    analyzer.analyze()

    # Also search for more examples

    # Search for each unique unknown opcode
    unknowns = analyzer._parse_unknowns()
    for opcode in unknowns:
        analyzer.find_in_source_files(opcode)


if __name__ == "__main__":
    main()
