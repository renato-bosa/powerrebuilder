"""Text extraction utilities for PowerBuilder binary files.

This module provides functionality to extract readable text from binary
PowerBuilder files using various pattern matching strategies.
"""

import logging
import re
from pathlib import Path


def binary_to_readable_format(
    file_path: Path, output_path: Path | None = None
) -> str | None:
    """Convert a PowerBuilder binary file to readable text format.

    This function attempts to extract readable text from binary PowerBuilder files
    using multiple strategies including ASCII string extraction, UTF-16 decoding,
    and PowerBuilder-specific pattern matching.

    Args:
        file_path: Path to the binary file
        output_path: Optional path to write the output text file

    Returns:
        The extracted text if successful, None otherwise
    """
    try:
        # Read the entire binary file
        with open(file_path, "rb") as f:
            data = f.read()

        # Try multiple approaches to extract text

        # 1. Try a simple approach - extract ASCII strings
        printable_pattern = re.compile(b"[ -~]{4,}")  # 4+ printable ASCII chars
        text_chunks = printable_pattern.findall(data)
        extracted_text = "\n".join(
            [chunk.decode("latin1", errors="replace") for chunk in text_chunks]
        )

        # 2. Check for PowerBuilder export markers
        if b"$PBExport" in data:
            logging.info("PowerBuilder export marker detected")
            # Find the start of the export section
            export_start = data.find(b"$PBExport")
            if export_start >= 0:
                # Extract from the export marker onwards
                export_data = data[export_start:]
                # Try to decode as ASCII/Latin1
                try:
                    export_text = export_data.decode("latin1", errors="replace")
                    extracted_text = export_text
                except Exception as e:
                    logging.warning(f"Failed to decode export section: {e}")

        # 3. Try to extract UTF-16 strings (common in newer PB versions)
        utf16_pattern = re.compile(b"(?:[\x20-\x7e]\x00){4,}")
        utf16_chunks = utf16_pattern.findall(data)
        if utf16_chunks:
            logging.info(f"Found {len(utf16_chunks)} potential UTF-16 strings")
            utf16_text = []
            for chunk in utf16_chunks:
                try:
                    decoded = chunk.decode("utf-16-le", errors="replace")
                    utf16_text.append(decoded)
                except:
                    pass
            if utf16_text:
                extracted_text += "\n\n--- UTF-16 Strings ---\n" + "\n".join(utf16_text)

        # 4. Look for specific PowerBuilder patterns
        pb_patterns = [
            b"DataWindow",
            b"CREATE",
            b"DESTROY",
            b"global type",
            b"end type",
            b"from ",
            b"within ",
            b"event ",
            b"function ",
        ]

        pattern_matches = []
        for pattern in pb_patterns:
            indices = [m.start() for m in re.finditer(pattern, data)]
            for idx in indices:
                # Extract context around the pattern
                start = max(0, idx - 50)
                end = min(len(data), idx + 200)
                context = data[start:end]
                # Try to extract a readable line
                line_match = re.search(b"[^\x00-\x1f\x7f-\xff]{10,}", context)
                if line_match:
                    pattern_matches.append(
                        line_match.group().decode("latin1", errors="replace")
                    )

        if pattern_matches:
            extracted_text += "\n\n--- PowerBuilder Pattern Matches ---\n" + "\n".join(
                pattern_matches
            )

        # Write to output file if specified
        if output_path and extracted_text:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
                f.write("\n\n--- File Info ---\n")
                f.write(f"Original file: {file_path}\n")
                f.write(f"File size: {len(data)} bytes\n")
                f.write(f"Extracted text length: {len(extracted_text)} characters\n")

        return extracted_text

    except Exception as e:
        logging.exception(f"Error processing file {file_path}: {e}")
        return None
