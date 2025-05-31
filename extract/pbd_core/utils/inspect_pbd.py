#!/usr/bin/env python3
"""Inspect the header of a PowerBuilder PBD file to diagnose extraction issues."""

import argparse
import binascii
from pathlib import Path

# Default values
DEFAULT_OFFSET = 0
DEFAULT_LENGTH = 128
DEFAULT_BLOCK_SIZE = 512


def print_hex_dump(data, length=64) -> None:
    """Print a hexdump of the first bytes of data."""
    hex_dump = binascii.hexlify(data[:length]).decode('ascii')
    for i in range(0, len(hex_dump), 32):
        line = hex_dump[i:i + 32]
        ' '.join(line[j:j + 2] for j in range(0, len(line), 2))
        i // 2

    ascii_chars = []
    for i in range(min(length, len(data))):
        if 32 <= data[i] <= 126:  # Printable ASCII
            ascii_chars.append(chr(data[i]))
        else:
            ascii_chars.append('.')
    for i in range(0, len(ascii_chars), 16):
        pass


def check_file_signature(filepath) -> None:
    """Check the file signature to identify the format."""
    known_signatures = {
        b'HDR\0': "PowerBuilder Header",
        b'NOD\0': "PowerBuilder Node",
        b'FRE\0': "PowerBuilder Free Block",
        b'DAT\0': "PowerBuilder Data",
        b'PBD\0': "PowerBuilder PBD",
        b'PBL\0': "PowerBuilder PBL",
        b'PK\x03\x04': "ZIP Archive",
        b'\x4d\x5a': "Executable (MZ)",
        b'\x7f\x45\x4c\x46': "ELF Binary",
    }

    with open(filepath, 'rb') as f:
        header = f.read(16)  # Read first 16 bytes

        print_hex_dump(header, 16)

        # Check for known signatures
        for sig, _desc in known_signatures.items():
            if header.startswith(sig):
                return

        # Try to detect encoding
        try:
            # Try to interpret as ASCII/UTF-8
            decoded = header.decode('utf-8', errors='ignore')
            if any(c.isalpha() for c in decoded):
                pass
        except:
            pass

        try:
            # Try to interpret as UTF-16
            decoded = header.decode('utf-16-le', errors='ignore')
            if any(c.isalpha() for c in decoded):
                pass
        except:
            pass


def hexdump_bytes(data: bytes, offset_display_start: int = 0) -> None:
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in range(0, len(data), 16):
        chars = data[c:c + 16]
        hex_str = ' '.join([f"{x:02x}" for x in chars])
        if len(hex_str) > 24:  # Insert a space in the middle for readability if more than 8 bytes
            hex_str = hex_str[:24] + ' ' + hex_str[24:]
        printable = ''.join(["%s" % ((x < 127 and FILTER[x]) or '.') for x in chars])
        lines.append("0x%08x:  %-*s  |%s|" % (offset_display_start + c, 16 * 3, hex_str, printable))


def read_and_hexdump(file_path_str: str, offset: int, length: int, block_size: int) -> None:
    file_path = Path(file_path_str)
    if not file_path.exists() or not file_path.is_file():
        return

    try:
        with open(file_path, 'rb') as f:
            file_size = f.seek(0, 2)  # Get file size

            if offset >= file_size:
                return

            f.seek(offset)
            bytes_to_read = min(length, file_size - offset)  # Don't read past EOF

            data = f.read(bytes_to_read)
            hexdump_bytes(data, offset_display_start=offset)

            if bytes_to_read < length:
                pass

            # Optional: Display block boundaries if relevant
            offset // block_size
            end_block_offset_of_data = offset + bytes_to_read - 1  # last byte of data read
            end_block_offset_of_data // block_size

            if offset % block_size != 0:
                pass

            if (offset + bytes_to_read) % block_size != 0 and bytes_to_read == length:  # only if not eof
                 block_size - ((offset + bytes_to_read) % block_size)

    except OSError:
        pass
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Hexdump utility for inspecting PBD/PBL files.")
    parser.add_argument("file_path", help="Path to the PBD/PBL file.")
    parser.add_argument(
        "--offset",
        type=lambda x: int(x, 0),  # Allows hex (0x) or decimal input
        default=DEFAULT_OFFSET,
        help=f"Starting offset (decimal or hex with 0x prefix). Default: {DEFAULT_OFFSET}",
    )
    parser.add_argument(
        "--length",
        type=lambda x: int(x, 0),
        default=DEFAULT_LENGTH,
        help=f"Number of bytes to read (decimal or hex). Default: {DEFAULT_LENGTH}",
    )
    parser.add_argument(
        "--block-size",
        type=lambda x: int(x, 0),
        default=DEFAULT_BLOCK_SIZE,
        help=f"Block size for informational display. Default: {DEFAULT_BLOCK_SIZE}",
    )

    args = parser.parse_args()

    read_and_hexdump(args.file_path, args.offset, args.length, args.block_size)


if __name__ == "__main__":
    main()
