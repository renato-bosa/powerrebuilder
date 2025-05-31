#!/usr/bin/env python3
"""PowerBuilder Binary to Text Converter.

This script attempts to convert PowerBuilder binary files (.win, .srw, etc.)
to a readable text format using multiple approaches.
"""

import argparse
import logging
import re
import sys
from pathlib import Path


def setup_logging(verbose=False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def binary_to_readable_format(file_path, output_path=None):
    """Attempts to convert a binary PowerBuilder file to readable text.

    Args:
        file_path: Path to the binary file
        output_path: Optional path to write the output text file

    Returns:
        The extracted text if successful, None otherwise
    """
    try:
        # Read the entire binary file
        with open(file_path, 'rb') as f:
            data = f.read()

        # Try multiple approaches to extract text

        # 1. Try a simple approach - extract ASCII strings
        printable_pattern = re.compile(b'[ -~]{4,}')  # 4+ printable ASCII chars
        text_chunks = printable_pattern.findall(data)
        extracted_text = '\n'.join([chunk.decode('latin1', errors='replace') for chunk in text_chunks])

        # 2. Check for PowerBuilder export markers
        if b'$PBExport' in data:
            logging.info("PowerBuilder export marker detected")

        # If we have an output path, write the extracted text to a file
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Extracted from: {file_path}\n\n")
                f.write(extracted_text)
            logging.info(f"Extracted text saved to {output_path}")

        return extracted_text

    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return None


def find_strings_in_binary(data, min_length=4):
    """Extract strings from binary data.

    Args:
        data: Binary data
        min_length: Minimum string length

    Returns:
        List of extracted strings
    """
    result = []
    current_string = b''

    for byte in data:
        # Check if byte is printable ASCII
        if 32 <= byte <= 126:
            current_string += bytes([byte])
        else:
            # End of string
            if len(current_string) >= min_length:
                result.append(current_string.decode('latin1', errors='replace'))
            current_string = b''

    # Add the last string if it's valid
    if len(current_string) >= min_length:
        result.append(current_string.decode('latin1', errors='replace'))

    return result


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Convert PowerBuilder binary files to text')
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', help='Output file or directory (default: <input>.txt)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    setup_logging(args.verbose)

    input_path = Path(args.input)

    if not input_path.exists():
        logging.error(f"Input path does not exist: {input_path}")
        return 1

    if input_path.is_file():
        # Process a single file
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_suffix('.txt')

        binary_to_readable_format(input_path, output_path)
    else:
        # Process a directory
        output_dir = Path(args.output) if args.output else input_path.with_name(f"{input_path.name}_text")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all potential PowerBuilder files
        pb_files = []
        for ext in ['.win', '.srd', '.sru', '.srw', '.sra', '.srm', '.srs', '.men', '.pbd', '.pbl']:
            pb_files.extend(input_path.glob(f"**/*{ext}"))

        if not pb_files:
            logging.warning(f"No PowerBuilder files found in {input_path}")
            return 1

        logging.info(f"Found {len(pb_files)} PowerBuilder files to process")

        for file_path in pb_files:
            # Create output path with same relative structure
            rel_path = file_path.relative_to(input_path)
            output_file = output_dir / rel_path.with_suffix('.txt')
            output_file.parent.mkdir(parents=True, exist_ok=True)

            binary_to_readable_format(file_path, output_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
