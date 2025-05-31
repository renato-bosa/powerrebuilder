#!/usr/bin/env python3
"""Binary file hex dump utility.

This script displays the contents of a binary file in a hexadecimal
format with ASCII representation.
"""

import argparse
import os
import sys
from pathlib import Path


def hex_dump(file_path, bytes_per_line=16, offset=0, length=None, output_format='full'):
    """Generate a hex dump of a binary file.

    Args:
        file_path: Path to the binary file
        bytes_per_line: Number of bytes to display per line
        offset: Starting offset in the file
        length: Number of bytes to read (None for entire file)
        output_format: 'full' for hex+ASCII, 'hex' for hex only, 'text' for best-effort text

    Returns:
        String containing the formatted hex dump
    """
    try:
        file_size = os.path.getsize(file_path)

        offset = max(offset, 0)

        if length is None:
            length = file_size - offset
        else:
            # Make sure we don't read past the end of file
            length = min(length, file_size - offset)

        if length <= 0:
            return "No data to display (invalid offset or length)"

        result = []

        with open(file_path, 'rb') as f:
            f.seek(offset)
            bytes_read = 0

            if output_format == 'text':
                # Try to read as text with error handling
                try:
                    f.seek(offset)
                    return f.read(length).decode('utf-8', errors='replace')
                except Exception as e:
                    return f"Error reading as text: {e}"

            while bytes_read < length:
                chunk_size = min(bytes_per_line, length - bytes_read)
                chunk = f.read(chunk_size)

                if not chunk:
                    break

                # Current position in file
                pos = offset + bytes_read

                # Hex representation
                hex_values = ' '.join(f'{b:02x}' for b in chunk)

                # Padding for incomplete lines
                padding = '   ' * (bytes_per_line - len(chunk))

                # ASCII representation
                ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)

                if output_format == 'full':
                    result.append(f'{pos:08x}:  {hex_values}{padding}  |{ascii_values}|')
                elif output_format == 'hex':
                    result.append(f'{pos:08x}:  {hex_values}')

                bytes_read += len(chunk)

        return '\n'.join(result)

    except Exception as e:
        return f"Error reading file: {e}"


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Display binary file as hex dump')
    parser.add_argument('file', help='Binary file to view')
    parser.add_argument('-o', '--offset', type=int, default=0,
                        help='Starting offset (default: 0)')
    parser.add_argument('-l', '--length', type=int, default=None,
                        help='Number of bytes to read (default: entire file)')
    parser.add_argument('-b', '--bytes-per-line', type=int, default=16,
                        help='Number of bytes per line (default: 16)')
    parser.add_argument('-f', '--format', choices=['full', 'hex', 'text'], default='full',
                        help='Output format: full (hex+ASCII), hex (hex only), or text (best-effort text) (default: full)')
    parser.add_argument('-s', '--save', type=str, default=None,
                        help='Save output to file instead of displaying')

    args = parser.parse_args()

    file_path = Path(args.file)

    if not file_path.exists():
        return 1

    if not file_path.is_file():
        return 1

    output = hex_dump(
        file_path,
        bytes_per_line=args.bytes_per_line,
        offset=args.offset,
        length=args.length,
        output_format=args.format,
    )

    if args.save:
        with open(args.save, 'w', encoding='utf-8') as f:
            f.write(output)
    else:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
