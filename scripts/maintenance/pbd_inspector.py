#!/usr/bin/env python3
"""PowerBuilder PBD/PBL file inspector with hexdump functionality.

This utility combines hexdump functionality with PowerBuilder-specific
file format analysis for debugging and inspection purposes.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from extract.pbd_io.utils import retrieve_bytes_from_file

# Known PowerBuilder signatures
KNOWN_SIGNATURES = {
    b"HDR\x00": "PowerBuilder Header",
    b"NOD\x00": "PowerBuilder Node",
    b"FRE\x00": "PowerBuilder Free Block",
    b"DAT\x00": "PowerBuilder Data",
    b"ENT\x00": "PowerBuilder Entry",
    b"PBD\x00": "PowerBuilder PBD",
    b"PBL\x00": "PowerBuilder PBL",
    b"PK\x03\x04": "ZIP Archive",
    b"\x4d\x5a": "Executable (MZ)",
    b"\x7f\x45\x4c\x46": "ELF Binary",
}

# Default values
DEFAULT_BYTES_PER_LINE = 16
DEFAULT_LENGTH = 256
DEFAULT_BLOCK_SIZE = 512


def hex_dump(
    data: bytes, offset: int = 0, bytes_per_line: int = 16, output_format: str = "full"
) -> str:
    """Generate a hex dump of binary data.

    Args:
        data: Binary data to dump
        offset: Starting offset for display
        bytes_per_line: Number of bytes to display per line
        output_format: 'full' for hex+ASCII, 'hex' for hex only, 'text' for text

    Returns:
        String containing the formatted hex dump
    """
    if not data:
        return "No data to display"

    result = []

    if output_format == "text":
        # Try to decode as text with error handling
        try:
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error reading as text: {e}"

    for i in range(0, len(data), bytes_per_line):
        chunk = data[i : i + bytes_per_line]

        # Current position
        pos = offset + i

        # Hex representation
        hex_values = " ".join(f"{b:02x}" for b in chunk)

        # Insert space in the middle for readability if more than 8 bytes
        if len(chunk) > 8:
            hex_left = " ".join(f"{b:02x}" for b in chunk[:8])
            hex_right = " ".join(f"{b:02x}" for b in chunk[8:])
            hex_values = f"{hex_left}  {hex_right}"

        # Padding for incomplete lines
        if len(chunk) < bytes_per_line:
            # Calculate padding considering the extra space in the middle
            missing = bytes_per_line - len(chunk)
            if len(chunk) <= 8:
                padding = (
                    "   " * missing + "  "
                )  # Extra spaces for missing middle separator
            else:
                padding = "   " * missing
            hex_values += padding

        # ASCII representation
        ascii_values = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

        if output_format == "full":
            result.append(f"{pos:08x}:  {hex_values}  |{ascii_values}|")
        elif output_format == "hex":
            result.append(f"{pos:08x}:  {hex_values}")

    return "\n".join(result)


def check_file_signature(file_path: Path) -> tuple[str | None, bytes]:
    """Check the file signature to identify the format.

    Args:
        file_path: Path to the file to check

    Returns:
        Tuple of (signature description, header bytes)
    """
    try:
        # Use the efficient file reading utility
        header = retrieve_bytes_from_file(file_path, 0, 16)

        # Check for known signatures
        for sig, desc in KNOWN_SIGNATURES.items():
            if header.startswith(sig):
                return desc, header

        # Check if it might be text
        try:
            decoded = header.decode("utf-8", errors="strict")
            if all(c.isprintable() or c.isspace() for c in decoded):
                return "Text file (UTF-8)", header
        except:
            pass

        try:
            decoded = header.decode("utf-16-le", errors="strict")
            if any(c.isalpha() for c in decoded):
                return "Text file (UTF-16LE)", header
        except:
            pass

        return "Unknown format", header

    except Exception as e:
        return f"Error reading file: {e}", b""


def inspect_pbd_structure(
    file_path: Path, block_size: int = DEFAULT_BLOCK_SIZE
) -> None:
    """Inspect the structure of a PBD/PBL file.

    Args:
        file_path: Path to the PBD/PBL file
        block_size: Expected block size for the file
    """
    # Check file signature
    sig_desc, header = check_file_signature(file_path)

    if sig_desc.startswith("PowerBuilder"):
        # Check for common PBD/PBL blocks
        try:
            # Read first few blocks
            for block_num in range(4):
                offset = block_num * block_size
                data = retrieve_bytes_from_file(file_path, offset, min(block_size, 64))

                if not data:
                    break

                # Check block signature
                block_sig = data[:4] if len(data) >= 4 else data
                sig_desc = KNOWN_SIGNATURES.get(block_sig, "Unknown")

        except Exception:
            pass


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PowerBuilder PBD/PBL file inspector with hexdump functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic hexdump of a file
  %(prog)s file.pbd

  # Inspect PBD structure
  %(prog)s --inspect file.pbd

  # Hexdump with custom offset and length
  %(prog)s file.pbd --offset 0x1000 --length 256

  # Save output to file
  %(prog)s file.pbd --output dump.txt

  # Hex-only format
  %(prog)s file.pbd --format hex
""",
    )

    parser.add_argument("file", nargs="?", help="File to inspect")
    parser.add_argument(
        "-o",
        "--offset",
        type=lambda x: int(x, 0),
        default=0,
        help="Starting offset (supports hex with 0x prefix)",
    )
    parser.add_argument(
        "-l",
        "--length",
        type=lambda x: int(x, 0),
        default=DEFAULT_LENGTH,
        help="Number of bytes to display (default: %(default)s)",
    )
    parser.add_argument(
        "-b",
        "--bytes-per-line",
        type=int,
        default=DEFAULT_BYTES_PER_LINE,
        help="Bytes per line (default: %(default)s)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["full", "hex", "text"],
        default="full",
        help="Output format (default: %(default)s)",
    )
    parser.add_argument("--output", type=str, help="Save output to file")
    parser.add_argument(
        "--inspect", action="store_true", help="Perform PowerBuilder structure analysis"
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=DEFAULT_BLOCK_SIZE,
        help="Block size for PBD analysis (default: %(default)s)",
    )
    parser.add_argument(
        "--list-files",
        nargs="*",
        dest="files",
        help="List of files to process (alternative to single file)",
    )

    args = parser.parse_args()

    # Determine files to process
    files_to_process = []
    if args.file:
        files_to_process.append(args.file)
    if args.files:
        files_to_process.extend(args.files)

    if not files_to_process:
        parser.print_help()
        return 1

    # Process each file
    for file_path_str in files_to_process:
        file_path = Path(file_path_str)

        if not file_path.exists():
            continue

        if not file_path.is_file():
            continue

        if len(files_to_process) > 1:
            pass

        try:
            if args.inspect:
                # Perform PowerBuilder structure analysis
                inspect_pbd_structure(file_path, args.block_size)
            else:
                # Regular hexdump
                file_size = file_path.stat().st_size

                # Validate offset
                if args.offset >= file_size:
                    continue

                # Calculate actual length to read
                length = (
                    min(args.length, file_size - args.offset)
                    if args.length
                    else file_size - args.offset
                )

                # Read data using efficient utility
                data = retrieve_bytes_from_file(file_path, args.offset, length)

                # Generate hexdump
                output = hex_dump(data, args.offset, args.bytes_per_line, args.format)

                # Output
                if args.output:
                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output)
                else:
                    pass

        except Exception:
            continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
