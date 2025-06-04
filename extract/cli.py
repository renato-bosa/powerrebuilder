#!/usr/bin/env python3
"""Unified command-line interface for PowerBuilder extraction utilities.

This module consolidates all CLI utilities into a single entry point with subcommands.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.extract_coordinator import extract_pbls
from extract.pbd_core.core import extract_pbl
from extract.pbd_core.text_extraction import binary_to_readable_format


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def cmd_extract(args) -> int:
    """Extract PowerBuilder binary files to text format."""
    setup_logging(args.verbose)
    
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


def cmd_text(args) -> int:
    """Convert PowerBuilder binary files to readable text format."""
    setup_logging(args.verbose)
    
    input_path = Path(args.input)

    if not input_path.exists():
        logging.error(f"Input file does not exist: {input_path}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default: same name with .txt extension
        output_path = input_path.with_suffix('.txt')

    logging.info(f"Converting {input_path} to text format...")
    result = binary_to_readable_format(input_path, output_path)

    if result:
        logging.info(f"Successfully converted. Output saved to {output_path}")
        
        # Also print to stdout if requested
        if args.stdout:
            print("\n--- Extracted Text ---")
            print(result)
        return 0
    else:
        logging.error("Conversion failed")
        return 1


def cmd_inspect(args) -> int:
    """Run the PBD inspection utility."""
    # Path to the consolidated pbd_inspector.py script
    script_path = Path(__file__).parent / "pbd_core" / "utils" / "pbd_inspector.py"
    
    if not script_path.exists():
        logging.error(f"Inspector utility not found at: {script_path}")
        return 1
    
    # Build command with arguments - add --inspect flag for structure analysis
    cmd = [sys.executable, str(script_path), "--inspect"]
    if args.file:
        cmd.extend(args.file)
    
    # Run the script
    try:
        return subprocess.call(cmd)
    except Exception as e:
        logging.error(f"Failed to run inspector utility: {e}")
        return 1


def cmd_hexdump(args) -> int:
    """Run the hexdump viewer utility."""
    # Path to the consolidated pbd_inspector.py script
    script_path = Path(__file__).parent / "pbd_core" / "utils" / "pbd_inspector.py"
    
    if not script_path.exists():
        logging.error(f"Inspector utility not found at: {script_path}")
        return 1
    
    # Build command with arguments - no special flags for hexdump mode
    cmd = [sys.executable, str(script_path)]
    if args.file:
        cmd.extend(args.file)
    
    # Run the script
    try:
        return subprocess.call(cmd)
    except Exception as e:
        logging.error(f"Failed to run inspector utility: {e}")
        return 1


def main() -> int:
    """Main entry point for the unified CLI."""
    parser = argparse.ArgumentParser(
        description="PowerBuilder extraction utilities",
        prog="pb-extract"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract PBD/PBL files to text')
    extract_parser.add_argument('input', help='Input file or directory path')
    extract_parser.add_argument('-o', '--output', default='output/extracted',
                               help='Output directory (default: output/extracted)')
    extract_parser.add_argument('-u', '--unicode', action='store_true',
                               help='Use unicode mode for extraction')
    extract_parser.add_argument('-v', '--verbose', action='store_true',
                               help='Enable verbose logging')
    extract_parser.set_defaults(func=cmd_extract)
    
    # Text conversion command
    text_parser = subparsers.add_parser('text', help='Convert binary PB files to text')
    text_parser.add_argument('input', help='Input binary file path')
    text_parser.add_argument('-o', '--output', help='Output text file path')
    text_parser.add_argument('-s', '--stdout', action='store_true',
                            help='Also print to stdout')
    text_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Enable verbose logging')
    text_parser.set_defaults(func=cmd_text)
    
    # Inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect PBD file structure')
    inspect_parser.add_argument('file', nargs='*', help='Files to inspect')
    inspect_parser.set_defaults(func=cmd_inspect)
    
    # Hexdump command
    hexdump_parser = subparsers.add_parser('hexdump', help='View hexdump of PB files')
    hexdump_parser.add_argument('file', nargs='*', help='Files to view')
    hexdump_parser.set_defaults(func=cmd_hexdump)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute the appropriate command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())