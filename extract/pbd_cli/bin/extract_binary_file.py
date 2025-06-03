#!/usr/bin/env python3
"""Binary file extractor for PowerBuilder PBD/PBL files.

This script extracts the contents of binary PowerBuilder files and saves them
as text files that can be viewed in a text editor.
"""

import argparse
import logging
import sys
from pathlib import Path

from extract.pbd_cli.extract_coordinator import extract_pbls
from extract.pbd_core.core import extract_pbl


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int | None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Extract PowerBuilder binary files to text format')
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', default='output/extracted',
                        help='Output directory (default: output/extracted)')
    parser.add_argument('-u', '--unicode', action='store_true',
                        help='Use unicode mode for extraction')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    # Set up logging
    setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logging.error(f"Input path does not exist: {input_path}")
        return 1

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        if input_path.is_file():
            # Single file extraction
            logging.info(f"Extracting file: {input_path}")
            extract_pbl(str(input_path), str(output_path), args.unicode)
        else:
            # Directory extraction
            logging.info(f"Extracting all files from directory: {input_path}")
            extract_pbls(str(input_path), str(output_path), args.unicode)

        logging.info(f"Extraction complete. Files saved to {output_path}")
        return 0
    except Exception as e:
        logging.error(f"Extraction failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
