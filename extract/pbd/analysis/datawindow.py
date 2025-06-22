import logging
import re  # Added re
from typing import Any  # Added List, Any

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

# Tentatively adding decode from utils, as it's often needed for blob inspection
from extract.pbd.io.binary_utils import binary_to_int  # MODIFIED

logger = logging.getLogger(__name__)

DW_SIGNATURES = [
    b"DWHD", # Common DataWindow header signature
    b"\x01\x00\x00\x00\x01\x00\x00\x00", # Example: seen in some binary DWs
    b"HA$PBExportHeader$", # Sometimes DW source is stored directly
]

DW_EXPORT_HEADER_REGEX = re.compile(r"HA\$PBExportHeader\$(?P<name>[^\.]+)\.dw\s*")


def detect_datawindow_blob(data: bytes) -> bool:








    """Detect if binary data is likely a DataWindow blob."""
    if not data or len(data) < 8:  # Minimum length for some signatures
        return False
    for sig in DW_SIGNATURES:
        if data.startswith(sig):
            logger.debug("DataWindow signature '%s' found.", sig.decode(errors="ignore"))
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
                "DataWindow-like text content ('release 6.0', 'table(') found.",
            )
            return True
    except UnicodeDecodeError:
        pass  # Ignore decoding errors for this detection step, binary checks will follow
    except Exception as e_dec:
        logger.debug("Unexpected error during text-based DW detection: %s", e_dec)
        # Still treat as non-match for text, binary checks will follow
    return False


def _try_decode_text(data: bytes) -> tuple[str | None , str]:








    """Try to decode bytes as text with fallback encodings.

    Returns:
        Tuple of (decoded_text, encoding_used)
        If decoding fails, returns (None, 'binary')
    """
    encodings = ["utf-8", "latin1"]

    for encoding in encodings:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.warning("Error during %s decoding for DW metadata: %s", encoding, e)
            continue

    return None, "binary"


def _determine_format(text_content: str | None, data: bytes) -> tuple[str, str | None]:








    """Determine DataWindow format from content.

    Returns:
        Tuple of (format, estimated_name)
    """
    if text_content:
        # Check for export header
        if "HA$PBExportHeader$" in text_content:
            match = DW_EXPORT_HEADER_REGEX.search(text_content)
            estimated_name = match.group("name") + ".dw" if match else None
            return "export_text", estimated_name

        # Check for source syntax
        elif "create syntax" in text_content.lower() or (
            "table(" in text_content.lower() and "column=(" in text_content.lower()
        ):
            return "source_syntax", None

    # Check for binary DWHD format
    if data.startswith(b"DWHD"):
        return "binary_dwhd", None

    # Default cases
    if text_content:
        return "binary_or_unknown_text", None
    else:
        return "binary", None


def _extract_text_metadata(text_content: str, metadata: dict[str, Any]) -> None:








    """Extract metadata from text-based DataWindow content.

    Updates metadata dict in-place.
    """
    metadata["summary_preview"] = text_content[:500]

    # Extract objects and column count
    objects, column_count = _extract_objects_and_columns(text_content[:500])
    metadata["objects"] = objects
    metadata["column_count"] = column_count


def _extract_binary_metadata(data: bytes, metadata: dict[str, Any]) -> None:








    """Extract metadata from binary DataWindow content.

    Updates metadata dict in-place.
    """
    if metadata["format"] == "binary_dwhd":
        # Try to extract column count from known offset
        try:
            if len(data) > 0x2A + 2:
                num_cols_bytes = data[0x2A : 0x2A + 2]
                num_cols = binary_to_int(num_cols_bytes)
                if 0 < num_cols < 500:  # Reasonable range
                    metadata["column_count"] = num_cols
        except Exception as e:
            logger.debug("Binary DW parsing attempt failed: %s", e)

    # Set binary preview
    metadata["summary_preview"] = data[:100].hex() + "... (binary content)"


def _extract_objects_and_columns(text: str) -> tuple[list[str], int]:








    """Extract object types and column count from DataWindow text.

    Returns:
        Tuple of (objects_list, column_count)
    """
    if not isinstance(text, str):
        return [], 0

    text_lower = text.lower()

    # Find all object types
    objects = re.findall(
        r"\b(text|line|rectangle|roundrectangle|oval|group|button|bitmap|compute|graph|report|ole|table|column|datawindow)\b", text_lower, )

    # Count columns
    column_count = text_lower.count("column=(")

    return objects, column_count


def extract_datawindow_metadata(data: bytes) -> dict[str, Any]:








    """Rudimentary extraction of metadata from a DataWindow blob (text or binary).
    This is a placeholder for more sophisticated parsing.
    """
    metadata: dict[str, Any] = {
        "is_datawindow": False, "format": "unknown", "estimated_name": None, "objects": [], "column_count": 0, "summary_preview": "", }

    if not detect_datawindow_blob(data):
        return metadata

    metadata["is_datawindow"] = True

    # Try to decode as text
    text_content, encoding = _try_decode_text(data)

    # Determine format
    format_type, estimated_name = _determine_format(text_content, data)
    metadata["format"] = format_type
    if estimated_name:
        metadata["estimated_name"] = estimated_name

    # Extract metadata based on format
    if text_content and format_type in {"export_text", "source_syntax"}:
        _extract_text_metadata(text_content, metadata)
    else:
        _extract_binary_metadata(data, metadata)

    return metadata
