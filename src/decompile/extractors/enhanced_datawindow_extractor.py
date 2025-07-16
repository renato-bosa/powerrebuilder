"""Enhanced DataWindow extractor for comprehensive DataWindow parsing."""

from enum import Enum
from typing import Any, Callable, Dict, List, Tuple


class DataWindowType(Enum):
    """Types of DataWindow objects."""
    GRID = "grid"
    TABULAR = "tabular"
    FREEFORM = "freeform"
    LABEL = "label"
    NUPTIAL = "n_up"
    GROUP = "group"
    COMPOSITE = "composite"
    CROSSTAB = "crosstab"
    GRAPH = "graph"
    OLE = "ole"
    RICHTEXT = "richtext"
    UNKNOWN = "unknown"


class MagicNumbers:
    """Magic numbers used in DataWindow extraction."""
    DW_HEADER_SIGNATURE = b"datawindow("
    RELEASE_SIGNATURE = b"release"
    BINARY_MARKER = 0x90
    TEXT_MARKER = 0x00

    # Common DataWindow binary markers
    GRID_MARKER = b"\x01\x02\x03"
    TABULAR_MARKER = b"\x02\x03\x04"

    # Size limits
    MIN_DW_SIZE = 100
    MAX_DW_SIZE = 10_000_000


class EnhancedDataWindowExtractor:
    """Enhanced extractor for DataWindow objects with multiple strategies."""

    def __init__(self):
        """Initialize the enhanced DataWindow extractor."""
        self.extraction_strategies: List[Callable] = [
            self._extract_text_based,
            self._extract_binary_based,
            self._extract_with_header_search,
            self._extract_with_pattern_matching,
            self._extract_with_recovery,
            self._extract_with_heuristics,
        ]

    def extract(self, data: bytes, filename: str = "") -> Tuple[str, bool]:
        """Extract DataWindow syntax from raw data.

        Args:
            data: Raw DataWindow data
            filename: Optional filename for type hints

        Returns:
            Tuple of (syntax_string, success_bool)
        """
        # Try to detect type from filename
        dw_type = self._detect_datawindow_type_from_filename(filename)

        # Try each extraction strategy
        for strategy in self.extraction_strategies:
            try:
                result, success = strategy(data, dw_type)
                if success and result:
                    return result, True
            except Exception:
                continue

        return "", False

    def _detect_datawindow_type_from_filename(self, filename: str) -> DataWindowType:
        """Detect DataWindow type from filename patterns."""
        filename_lower = filename.lower()

        if "grid" in filename_lower:
            return DataWindowType.GRID
        elif "tab" in filename_lower:
            return DataWindowType.TABULAR
        elif "free" in filename_lower:
            return DataWindowType.FREEFORM
        elif "label" in filename_lower:
            return DataWindowType.LABEL
        elif "cross" in filename_lower:
            return DataWindowType.CROSSTAB
        elif "graph" in filename_lower:
            return DataWindowType.GRAPH
        else:
            return DataWindowType.UNKNOWN

    def _extract_text_based(self, data: bytes, dw_type: DataWindowType) -> Tuple[str, bool]:
        """Extract text-based DataWindow syntax."""
        if not data:
            return "", False

        # Check for text markers
        if MagicNumbers.DW_HEADER_SIGNATURE in data[:200]:
            try:
                # Find the start of DataWindow syntax
                start = data.find(MagicNumbers.DW_HEADER_SIGNATURE)
                if start >= 0:
                    # Try to decode as text
                    text = data[start:].decode('utf-8', errors='ignore')
                    if self._validate_datawindow_syntax(text):
                        return text, True
            except Exception:
                pass

        return "", False

    def _extract_binary_based(self, data: bytes, dw_type: DataWindowType) -> Tuple[str, bool]:
        """Extract binary-encoded DataWindow."""
        # Placeholder for binary extraction logic
        # Would need reverse engineering of PB binary format
        return "", False

    def _extract_with_header_search(self, data: bytes, dw_type: DataWindowType) -> Tuple[str, bool]:
        """Search for DataWindow headers in data."""
        # Look for release markers
        if MagicNumbers.RELEASE_SIGNATURE in data[:1000]:
            try:
                start = data.find(MagicNumbers.RELEASE_SIGNATURE)
                # Extract from release marker onwards
                text = data[start:].decode('utf-8', errors='ignore')
                if "datawindow(" in text:
                    return text, True
            except Exception:
                pass

        return "", False

    def _extract_with_pattern_matching(self, data: bytes, dw_type: DataWindowType) -> Tuple[str, bool]:
        """Use pattern matching to find DataWindow structures."""
        patterns = [
            b"table\\(column=",
            b"column\\(band=",
            b"compute\\(band=",
            b"text\\(band=",
            b"processing=",
        ]

        for pattern in patterns:
            if pattern in data:
                # Found DataWindow pattern, try to extract
                try:
                    # Find a reasonable boundary
                    text = data.decode('utf-8', errors='ignore')
                    if self._validate_datawindow_syntax(text):
                        return text, True
                except Exception:
                    pass

        return "", False

    def _extract_with_recovery(self, data: bytes, dw_type: DataWindowType) -> Tuple[str, bool]:
        """Attempt recovery extraction for corrupted DataWindows."""
        # Simple recovery: try to extract readable portions
        try:
            # Filter out non-printable characters
            filtered = bytearray()
            for byte in data:
                if 32 <= byte <= 126 or byte in (9, 10, 13):  # Printable ASCII + tabs/newlines
                    filtered.append(byte)

            text = filtered.decode('utf-8', errors='ignore')
            if "datawindow(" in text or "processing=" in text:
                return text, True
        except Exception:
            pass

        return "", False

    def _extract_with_heuristics(self, data: bytes, dw_type: DataWindowType) -> Tuple[str, bool]:
        """Use heuristics to extract DataWindow."""
        # Last resort: look for any DataWindow-like content
        try:
            text = data.decode('utf-8', errors='replace')

            # Check for minimum DataWindow keywords
            dw_keywords = ["datawindow", "column", "table", "processing", "band"]
            keyword_count = sum(1 for kw in dw_keywords if kw in text.lower())

            if keyword_count >= 3:
                return text, True
        except Exception:
            pass

        return "", False

    def _validate_datawindow_syntax(self, text: str) -> bool:
        """Validate if text contains valid DataWindow syntax."""
        if not text:
            return False

        # Basic validation
        required_elements = ["datawindow(", "processing="]
        return all(elem in text.lower() for elem in required_elements)

    def get_datawindow_metadata(self, syntax: str) -> Dict[str, Any]:
        """Extract metadata from DataWindow syntax."""
        metadata = {
            "type": DataWindowType.UNKNOWN,
            "columns": [],
            "tables": [],
            "processing_type": None,
        }

        # Extract processing type
        if "processing=" in syntax:
            try:
                start = syntax.find("processing=") + 11
                end = syntax.find(" ", start)
                if end == -1:
                    end = syntax.find(")", start)
                processing = syntax[start:end].strip('"').strip("'")
                metadata["processing_type"] = processing

                # Map to DataWindow type
                type_map = {
                    "0": DataWindowType.GRID,
                    "1": DataWindowType.TABULAR,
                    "2": DataWindowType.FREEFORM,
                    "3": DataWindowType.LABEL,
                    "4": DataWindowType.NUPTIAL,
                    "5": DataWindowType.GROUP,
                }
                metadata["type"] = type_map.get(processing, DataWindowType.UNKNOWN)
            except Exception:
                pass

        return metadata