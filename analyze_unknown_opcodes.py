import re
from collections import Counter
from pathlib import Path


def analyze_unknown_opcodes() -> None:
    """Analyze patterns in unknown opcodes log."""
    if not Path('unknown_opcodes.log').exists():
        return

    with open('unknown_opcodes.log') as f:
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
                        pairs.append(f'{opcode} 0x{next_byte}')
                    break

    # Count occurrences
    pair_counts = Counter(pairs)
    single_counts = Counter(single_opcodes)

    for opcode, _count in single_counts.most_common(30):
        pass

    for _pair, _count in pair_counts.most_common(30):
        pass

    # Analyze specific opcodes
    e4_variants = {k: v for k, v in pair_counts.items() if k.startswith('0xE4')}
    for _pair, _count in sorted(e4_variants.items(), key=lambda x: x[1], reverse=True):
        pass

    e0_variants = {k: v for k, v in pair_counts.items() if k.startswith('0xE0')}
    for _pair, _count in sorted(e0_variants.items(), key=lambda x: x[1], reverse=True):
        pass

    e1_variants = {k: v for k, v in pair_counts.items() if k.startswith('0xE1')}
    for _pair, _count in sorted(e1_variants.items(), key=lambda x: x[1], reverse=True):
        pass

if __name__ == "__main__":
    analyze_unknown_opcodes()
