#!/usr/bin/env python3
"""Comprehensive P-code pattern analysis tool.
Analyzes binary P-code files to identify opcode patterns and structures.
"""

import struct
from collections import Counter, defaultdict
from pathlib import Path


def find_pcode_start(data: bytes) -> int:
    """Find the start of P-code after headers."""
    header2 = b'$PBExportComments$'
    pos = data.find(header2)
    if pos >= 0:
        # Find end of header line
        end = data.find(b'\n', pos)
        if end >= 0:
            return end + 1
    return -1

def extract_strings(pcode: bytes, min_length: int = 4) -> dict[int, str]:
    """Extract ASCII strings from P-code."""
    strings = {}
    current_string = []
    string_start = 0

    for i, b in enumerate(pcode):
        if 32 <= b < 127:  # Printable ASCII
            if not current_string:
                string_start = i
            current_string.append(chr(b))
        else:
            if len(current_string) >= min_length:
                string = ''.join(current_string)
                strings[string_start] = string
            current_string = []

    return strings

def extract_unicode_strings(pcode: bytes, min_length: int = 4) -> dict[int, str]:
    """Extract Unicode strings from P-code."""
    strings = {}
    i = 0

    while i < len(pcode) - 1:
        # Look for Unicode patterns (char, 0x00)
        if pcode[i+1] == 0 and 32 <= pcode[i] < 127:
            # Potential Unicode string start
            start = i
            chars = []

            while i < len(pcode) - 1 and pcode[i+1] == 0 and 32 <= pcode[i] < 127:
                chars.append(chr(pcode[i]))
                i += 2

            if len(chars) >= min_length:
                strings[start] = ''.join(chars)
        else:
            i += 1

    return strings

def analyze_opcode_patterns(pcode: bytes) -> dict[str, any]:
    """Analyze opcode patterns in P-code."""
    analysis = {
        'total_bytes': len(pcode),
        'byte_frequency': Counter(pcode),
        'two_byte_patterns': Counter(),
        'three_byte_patterns': Counter(),
        'four_byte_patterns': Counter(),
        'likely_opcodes': defaultdict(list),
        'strings': {},
        'unicode_strings': {},
        'potential_functions': [],
        'potential_jumps': [],
        'numeric_constants': [],
    }

    # Extract strings
    analysis['strings'] = extract_strings(pcode)
    analysis['unicode_strings'] = extract_unicode_strings(pcode)

    # Analyze byte patterns
    for i in range(len(pcode)):
        # Two-byte patterns
        if i < len(pcode) - 1:
            pattern = (pcode[i], pcode[i+1])
            analysis['two_byte_patterns'][pattern] += 1

        # Three-byte patterns
        if i < len(pcode) - 2:
            pattern = (pcode[i], pcode[i+1], pcode[i+2])
            analysis['three_byte_patterns'][pattern] += 1

        # Four-byte patterns
        if i < len(pcode) - 3:
            pattern = (pcode[i], pcode[i+1], pcode[i+2], pcode[i+3])
            analysis['four_byte_patterns'][pattern] += 1

    # Identify likely opcodes (bytes that appear frequently before certain patterns)
    for i in range(len(pcode) - 4):
        # Common patterns that might indicate opcodes
        if pcode[i] == 0xe4 and pcode[i+1] in [0x81, 0x82, 0x83]:
            analysis['likely_opcodes']['LOAD_VAR'].append({
                'offset': i,
                'bytes': pcode[i:i+3].hex(),
                'variant': pcode[i+1],
            })

        if pcode[i] in [0xc4, 0xc5, 0xc6, 0xc7, 0xc8]:
            analysis['likely_opcodes']['CONST'].append({
                'offset': i,
                'bytes': pcode[i:i+4].hex(),
                'following': pcode[i+1:i+4].hex(),
            })

        # Look for potential jump instructions (often have addresses)
        if pcode[i] in [0x70, 0x71, 0x72, 0x73, 0x74, 0x75]:  # Common jump opcodes
            if i + 4 < len(pcode):
                # Try to read as address
                addr = struct.unpack('<I', pcode[i+1:i+5])[0]
                if addr < len(pcode):  # Reasonable address
                    analysis['potential_jumps'].append({
                        'offset': i,
                        'opcode': pcode[i],
                        'target': addr,
                    })

        # Look for numeric constants
        if i + 3 < len(pcode):
            # Try different integer formats
            try:
                val_32 = struct.unpack('<i', pcode[i:i+4])[0]
                if -1000 <= val_32 <= 10000:  # Reasonable constant range
                    analysis['numeric_constants'].append({
                        'offset': i,
                        'value': val_32,
                        'type': 'int32',
                    })
            except:
                pass

    # Look for function markers (0x03 pattern)
    for i in range(len(pcode) - 7):
        if pcode[i] == 0x03:
            # Check if followed by specific pattern
            header = pcode[i+1:i+7]
            if any(b != 0 for b in header):  # Non-zero header
                analysis['potential_functions'].append({
                    'offset': i,
                    'header': header.hex(),
                })

    return analysis

def format_frequency_table(counter: Counter, top_n: int = 20) -> str:
    """Format a frequency counter as a readable table."""
    lines = []
    for item, count in counter.most_common(top_n):
        if isinstance(item, tuple):
            hex_str = ' '.join(f'{b:02x}' for b in item)
        else:
            hex_str = f'{item:02x}'
        lines.append(f"  {hex_str}: {count:6d} times")
    return '\n'.join(lines)

def analyze_file(file_path: Path) -> None:
    """Analyze a single P-code file."""
    with open(file_path, 'rb') as f:
        data = f.read()

    # Find P-code start
    pcode_start = find_pcode_start(data)
    if pcode_start < 0:
        return

    pcode = data[pcode_start:]

    # Print hex dump of first bytes (from analyze_pcode.py)
    max_display = 128
    for i in range(0, min(max_display, len(pcode)), 16):
        ' '.join(f'{b:02x}' for b in pcode[i:i+16])
        ''.join(chr(b) if 32 <= b < 127 else '.' for b in pcode[i:i+16])

    # Analyze patterns
    analysis = analyze_opcode_patterns(pcode)

    for _byte, _count in analysis['byte_frequency'].most_common(15):
        pass



    for _opcode_type, instances in analysis['likely_opcodes'].items():
        for _inst in instances[:5]:  # Show first 5
            pass

    for _offset, _string in list(analysis['strings'].items())[:10]:
        pass

    if analysis['unicode_strings']:
        for _offset, _string in list(analysis['unicode_strings'].items())[:10]:
            pass

    for _func in analysis['potential_functions'][:10]:
        pass

    const_values = [c['value'] for c in analysis['numeric_constants']]
    const_counter = Counter(const_values)
    for _val, _count in const_counter.most_common(10):
        pass

def compare_files() -> None:
    """Compare P-code structure across different file types."""
    base_path = Path("output/test_bytes_fix/dcm_accounting.pbd/dcm_accounting.pbd")

    files = [
        base_path / "of_get_linked_acc.fun",  # Function
        base_path / "d_accounttype_dddw.dwo",  # DataWindow
        base_path / "w_balance_sheet.win",     # Window (if exists)
        base_path / "u_linked_acc_payables_tabpg.udo",  # User object
    ]

    # Track patterns across all files
    global_patterns = {
        'opcodes': defaultdict(int),
        'two_byte_starts': defaultdict(int),
        'common_sequences': defaultdict(int),
    }

    for file_path in files:
        if file_path.exists():
            analyze_file(file_path)

            # Collect global patterns
            with open(file_path, 'rb') as f:
                data = f.read()
                pcode_start = find_pcode_start(data)
                if pcode_start >= 0:
                    pcode = data[pcode_start:]

                    # Track two-byte patterns that might be opcodes
                    for i in range(len(pcode) - 2):
                        if pcode[i] in [0xe4, 0xe8, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8]:
                            global_patterns['opcodes'][(pcode[i], pcode[i+1])] += 1

                        # Track common starting bytes
                        if i == 0 or pcode[i-1] == 0x00:
                            global_patterns['two_byte_starts'][(pcode[i], pcode[i+1] if i+1 < len(pcode) else 0)] += 1
        else:
            pass


    for _pattern, _count in sorted(global_patterns['opcodes'].items(), key=lambda x: x[1], reverse=True)[:20]:
        pass

    for _pattern, _count in sorted(global_patterns['two_byte_starts'].items(), key=lambda x: x[1], reverse=True)[:20]:
        pass

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description='Analyze P-code patterns in PowerBuilder files')
    parser.add_argument('files', nargs='*', help='Specific files to analyze')
    parser.add_argument('--compare', action='store_true', help='Compare multiple file types')

    args = parser.parse_args()

    if args.compare or not args.files:
        # Run comparison mode
        compare_files()
    else:
        # Analyze specific files
        for file_path in args.files:
            path = Path(file_path)
            if path.exists():
                analyze_file(path)
            else:
                pass


if __name__ == "__main__":
    main()
