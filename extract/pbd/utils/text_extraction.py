"""Text extraction utilities for PowerBuilder binary files.

This module provides functionality to extract readable text from binary
PowerBuilder files using various pattern matching strategies.
"""

import logging
import re
from pathlib import Path


def _extract_ascii_strings(data: bytes) -> str:
    """Extract printable ASCII strings from binary data."""
    printable_pattern = re.compile(b"[ -~]{4,}")  # 4+ printable ASCII chars
    text_chunks = printable_pattern.findall(data)
    return "\n".join([chunk.decode("latin1", errors="replace") for chunk in text_chunks])

def _extract_pb_export_section(data: bytes) -> str | None:
    """Extract PowerBuilder export section if present."""
    if b"$PBExport" not in data:
        return None
    
    logging.info("PowerBuilder export marker detected")
    export_start = data.find(b"$PBExport")
    
    if export_start >= 0:
        export_data = data[export_start:]
        try:
            return export_data.decode("latin1", errors="replace")
        except Exception as e:
            logging.warning(f"Failed to decode export section: {e}")
    
    return None

def _extract_utf16_strings(data: bytes) -> str:
    """Extract UTF-16 strings from binary data."""
    utf16_pattern = re.compile(b"(?:[\x20-\x7e]\x00){4,}")
    utf16_chunks = utf16_pattern.findall(data)
    
    if not utf16_chunks:
        return ""
    
    logging.info(f"Found {len(utf16_chunks)} potential UTF-16 strings")
    utf16_text = []
    
    for chunk in utf16_chunks:
        try:
            decoded = chunk.decode("utf-16-le", errors="replace")
            utf16_text.append(decoded)
        except:
            pass
    
    return "\n\n--- UTF-16 Strings ---\n" + "\n".join(utf16_text) if utf16_text else ""

def _extract_pb_patterns(data: bytes) -> str:
    """Extract PowerBuilder-specific patterns from binary data."""
    pb_patterns = [
        b"DataWindow", b"CREATE", b"DESTROY", b"global type", b"end type",
        b"from ", b"within ", b"event ", b"function ",
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
    
    return "\n\n--- PowerBuilder Pattern Matches ---\n" + "\n".join(pattern_matches) if pattern_matches else ""

def _write_output_file(output_path: Path, extracted_text: str, file_path: Path, data_size: int) -> None:
    """Write extracted text and metadata to output file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
        f.write("\n\n--- File Info ---\n")
        f.write(f"Original file: {file_path}\n")
        f.write(f"File size: {data_size} bytes\n")
        f.write(f"Extracted text length: {len(extracted_text)} characters\n")

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

        # Try multiple extraction strategies
        extracted_text = _extract_ascii_strings(data)
        
        # Check for PowerBuilder export section
        export_text = _extract_pb_export_section(data)
        if export_text:
            extracted_text = export_text
        
        # Extract UTF-16 strings
        extracted_text += _extract_utf16_strings(data)
        
        # Extract PowerBuilder patterns
        extracted_text += _extract_pb_patterns(data)

        # Write to output file if specified
        if output_path and extracted_text:
            _write_output_file(output_path, extracted_text, file_path, len(data))

        return extracted_text

    except Exception as e:
        logging.exception(f"Error processing file {file_path}: {e}")
        return None
