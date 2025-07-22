#!/usr/bin/env python3
"""Deep analysis of the specific f_get_username.fun file to determine
if it actually contains executable P-code or is just data.
"""

import math
import sys


def analyze_file_deeply(file_path: str) -> None:
    """Perform deep analysis of the file."""
    with open(file_path, "rb") as f:
        data = f.read()


    # Find the P-code section
    first_newline = data.find(b"\n")
    second_newline = data.find(b"\n", first_newline + 1)
    pcode_start = second_newline + 1
    pcode_data = data[pcode_start:]


    # Detailed analysis of P-code section
    analyze_pcode_section(pcode_data)

    # Check if this looks like a DataWindow
    check_datawindow_characteristics(data)


def analyze_pcode_section(pcode_data: bytes) -> None:
    """Analyze the supposed P-code section in detail."""
    # Basic statistics
    null_count = pcode_data.count(0x00)
    (null_count / len(pcode_data)) * 100


    # Entropy calculation
    byte_counts = {}
    for byte in pcode_data:
        byte_counts[byte] = byte_counts.get(byte, 0) + 1

    entropy = 0.0
    for count in byte_counts.values():
        probability = count / len(pcode_data)
        if probability > 0:
            entropy -= probability * math.log2(probability)


    # Most common bytes
    sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (byte, count) in enumerate(sorted_bytes[:10]):
        (count / len(pcode_data)) * 100
        chr(byte) if 32 <= byte < 127 else "."

    # Look for text patterns that suggest this is data, not code

    # Look for Unicode text patterns (Windows uses UTF-16LE)
    unicode_patterns = 0
    for i in range(0, len(pcode_data) - 1, 2):
        if pcode_data[i] != 0 and pcode_data[i + 1] == 0:
            unicode_patterns += 1

    (unicode_patterns * 2 / len(pcode_data)) * 100

    # Extract some potential text
    potential_text = []
    for i in range(0, min(1000, len(pcode_data) - 1), 2):
        if pcode_data[i] != 0 and pcode_data[i + 1] == 0:
            char = chr(pcode_data[i])
            if 32 <= ord(char) < 127:  # Printable ASCII
                potential_text.append(char)
        else:
            if potential_text and len(potential_text) >= 3:
                text = "".join(potential_text)
                if len(text) >= 3:
                    pass
            potential_text = []

    # Show hex dump of interesting sections

    # Show beginning of P-code section
    hex_dump(pcode_data[:64])

    # Find and show sections with higher diversity
    chunk_size = 256
    interesting_chunks = []

    for i in range(0, len(pcode_data), chunk_size):
        chunk = pcode_data[i : i + chunk_size]
        if len(chunk) < chunk_size // 2:
            continue

        unique_bytes = len(set(chunk))
        null_pct = (chunk.count(0x00) / len(chunk)) * 100

        if unique_bytes > 30 and null_pct < 50:
            interesting_chunks.append((i, unique_bytes, null_pct, chunk))

    interesting_chunks.sort(key=lambda x: (x[1], -x[2]), reverse=True)

    for i, (offset, _unique, null_pct, chunk) in enumerate(interesting_chunks[:3]):
        hex_dump(chunk[:64], offset)


def hex_dump(data: bytes, start_offset: int = 0) -> None:
    """Create a hex dump of the data."""
    for i in range(0, len(data), 16):
        " ".join(f"{b:02x}" for b in data[i : i + 16])
        "".join(chr(b) if 32 <= b < 127 else "." for b in data[i : i + 16])


def check_datawindow_characteristics(data: bytes) -> None:
    """Check if this file has DataWindow characteristics."""
    # Look for DataWindow-specific keywords
    dw_keywords = [
        b"column",
        b"table",
        b"retrieve",
        b"header",
        b"detail",
        b"summary",
        b"datawindow",
        b"processing",
        b"control",
        b"text",
        b"expression",
        b"edit",
        b"dropdown",
        b"validation",
        b"format",
    ]

    found_keywords = []
    for keyword in dw_keywords:
        # Look for both direct and Unicode versions
        if keyword in data:
            found_keywords.append(keyword.decode("utf-8"))

        # Check Unicode version (UTF-16LE)
        unicode_keyword = keyword.decode("utf-8").encode("utf-16le")
        if unicode_keyword in data:
            found_keywords.append(f"{keyword.decode('utf-8')} (Unicode)")

    if found_keywords:
        pass
    else:
        pass

    # Check for form/control definitions
    control_patterns = [
        b"id=",
        b"name=",
        b"x=",
        b"y=",
        b"width=",
        b"height=",
        b"type=",
        b"color=",
        b"font=",
    ]

    control_count = 0
    for pattern in control_patterns:
        if pattern in data:
            control_count += 1

    if control_count > 3:
        pass


def final_assessment(file_path: str) -> None:
    """Provide final assessment."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Get P-code section
    first_newline = data.find(b"\n")
    second_newline = data.find(b"\n", first_newline + 1)
    pcode_data = data[second_newline + 1 :]

    null_percentage = (pcode_data.count(0x00) / len(pcode_data)) * 100

    # Count Unicode text patterns
    unicode_patterns = 0
    for i in range(0, len(pcode_data) - 1, 2):
        if pcode_data[i] != 0 and pcode_data[i + 1] == 0:
            unicode_patterns += 1
    unicode_percentage = (unicode_patterns * 2 / len(pcode_data)) * 100


    if null_percentage > 60 or unicode_percentage > 30:
        pass
    else:
        pass



def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        sys.exit(1)

    file_path = sys.argv[1]
    analyze_file_deeply(file_path)
    final_assessment(file_path)


if __name__ == "__main__":
    main()
