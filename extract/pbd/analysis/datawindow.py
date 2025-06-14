import logging
import re  # Added re
from typing import Any  # Added List, Any

# Tentatively adding decode from utils, as it's often needed for blob inspection
from extract.pbd.io.binary_utils import binary_to_int  # MODIFIED

logger = logging.getLogger(__name__)

DW_SIGNATURES = [
    b"DWHD",  # Common DataWindow header signature
    b"\x01\x00\x00\x00\x01\x00\x00\x00",  # Example: seen in some binary DWs
    b"HA$PBExportHeader$",  # Sometimes DW source is stored directly
]

DW_EXPORT_HEADER_REGEX = re.compile(r"HA\$PBExportHeader\$(?P<name>[^\.]+)\.dw\s*")


def detect_datawindow_blob(data: bytes) -> bool:
    """Detect if binary data is likely a DataWindow blob."""
    if not data or len(data) < 8:  # Minimum length for some signatures
        return False
    for sig in DW_SIGNATURES:
        if data.startswith(sig):
            logger.debug(f"DataWindow signature '{sig.decode(errors='ignore')}' found.")
            return True
    # As a fallback, check for common text patterns if it's mostly text
    try:
        text_content = data.decode("utf-8", errors="ignore")  # Try UTF-8 first
        if not text_content:
            text_content = data.decode("latin1", errors="ignore")  # Fallback to latin1

        if DW_EXPORT_HEADER_REGEX.search(text_content):
            logger.debug("DataWindow text export header found.")
            return True
        if "release 6.0" in text_content.lower() and "table(" in text_content.lower():
            logger.debug(
                "DataWindow-like text content ('release 6.0', 'table(') found."
            )
            return True
    except UnicodeDecodeError:
        pass  # Ignore decoding errors for this detection step, binary checks will follow
    except Exception as e_dec:
        logger.debug(f"Unexpected error during text-based DW detection: {e_dec}")
        # Still treat as non-match for text, binary checks will follow
    return False


def extract_datawindow_metadata(data: bytes) -> dict[str, Any]:
    """Rudimentary extraction of metadata from a DataWindow blob (text or binary).
    This is a placeholder for more sophisticated parsing.
    """
    metadata: dict[str, Any] = {
        "is_datawindow": False,
        "format": "unknown",  # binary, export_text, source_syntax
        "estimated_name": None,
        "objects": [],
        "column_count": 0,
        "summary_preview": "",
    }

    if not detect_datawindow_blob(data):
        return metadata

    metadata["is_datawindow"] = True

    # Try to decode as text first for header/syntax based DWs
    try:
        text_content = data.decode("utf-8")
        if "HA$PBExportHeader$" in text_content:
            metadata["format"] = "export_text"
            match = DW_EXPORT_HEADER_REGEX.search(text_content)
            if match:
                metadata["estimated_name"] = match.group("name") + ".dw"
            metadata["summary_preview"] = text_content[
                :500
            ]  # First 500 chars as preview
        elif "create syntax" in text_content.lower() or (
            "table(" in text_content.lower() and "column=(" in text_content.lower()
        ):
            metadata["format"] = "source_syntax"
            metadata["summary_preview"] = text_content[:500]
    except UnicodeDecodeError:
        # If UTF-8 fails, try latin1 for older export formats
        try:
            text_content = data.decode("latin1")
            if "HA$PBExportHeader$" in text_content:
                metadata["format"] = "export_text"
                match = DW_EXPORT_HEADER_REGEX.search(text_content)
                if match:
                    metadata["estimated_name"] = match.group("name") + ".dw"
                metadata["summary_preview"] = text_content[:500]
            elif "create syntax" in text_content.lower() or (
                "table(" in text_content.lower() and "column=(" in text_content.lower()
            ):
                metadata["format"] = "source_syntax"
                metadata["summary_preview"] = text_content[:500]
            else:
                metadata["format"] = "binary_or_unknown_text"
                metadata["summary_preview"] = data[:100].hex()  # Hex preview for binary
        except UnicodeDecodeError:
            metadata["format"] = "binary"
            metadata["summary_preview"] = data[:100].hex()  # Hex preview for binary
    except Exception as e:
        logger.warning(f"Error during text decoding for DW metadata: {e}")
        metadata["format"] = "binary_undecodable_text"
        metadata["summary_preview"] = data[:100].hex()

    # Basic binary parsing attempt (very simplistic)
    if metadata["format"] == "binary" or metadata["format"].startswith(
        "binary_or_unknown"
    ):
        if data.startswith(b"DWHD"):
            metadata["format"] = "binary_dwhd"
            # Placeholder for actual binary parsing
            try:
                # Example: Try to find column count if it's at a known offset
                # This is highly speculative and format-dependent
                # For some formats, a short int at offset 0x2A might be num_cols
                if len(data) > 0x2A + 2:
                    num_cols_bytes = data[0x2A : 0x2A + 2]
                    num_cols = binary_to_int(
                        num_cols_bytes
                    )  # Assumes little-endian short
                    if 0 < num_cols < 500:  # Reasonable range for columns
                        metadata["column_count"] = num_cols
            except Exception as e_bin:
                logger.debug(f"Binary DW parsing attempt failed: {e_bin}")
        metadata["summary_preview"] = data[:100].hex() + "... (binary content)"

    # Simple object count for text-based DWs
    if (
        metadata["format"] in {"export_text", "source_syntax"}
        and metadata["summary_preview"]
    ):
        text_for_obj_scan = metadata["summary_preview"]
        if isinstance(text_for_obj_scan, str):
            metadata["objects"] = re.findall(
                r"\b(text|line|rectangle|roundrectangle|oval|group|button|bitmap|compute|graph|report|ole|table|column|datawindow)\b",
                text_for_obj_scan.lower(),
            )
            metadata["column_count"] = text_for_obj_scan.lower().count("column=(")

    return metadata
