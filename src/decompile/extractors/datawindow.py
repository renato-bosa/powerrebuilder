"""Consolidated DataWindow extractor combining all DataWindow extraction functionality."""

import logging
import struct
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple, Callable

logger = logging.getLogger(__name__)


# Minimal PDW stub implementations to fix missing imports
def detect_pdw_format(data: bytes) -> Optional[str]:
    """Stub function to detect PDW format in data."""
    # Check for common PDW signatures
    if data[:4] == b'PDW\x00':
        return 'pdw'
    elif data[:8] == b'\x00\x00\x00\x00PDW\x00':
        return 'pdw_extended'
    return None


def log_pdw_warning(format_type: str, object_name: str) -> None:
    """Stub function to log PDW format warnings."""
    logger.warning(f"PDW format '{format_type}' detected for object '{object_name}'")


class PDWSQLExtractor:
    """Stub PDW SQL extractor for minimal functionality."""
    
    def extract_sql(self, data: bytes, pdw_format: str) -> Optional[str]:
        """Stub method to extract SQL from PDW data."""
        # Basic implementation that looks for SQL patterns
        try:
            # Try to find common SQL keywords in the data
            text = data.decode('utf-8', errors='ignore')
            sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ORDER BY']
            
            for keyword in sql_keywords:
                if keyword in text.upper():
                    # Found SQL content, try to extract it
                    start = text.upper().find('SELECT')
                    if start >= 0:
                        # Simple extraction until semicolon or end
                        end = text.find(';', start)
                        if end < 0:
                            end = len(text)
                        return text[start:end].strip()
        except Exception:
            pass
        
        return None


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


class DataWindowExtractor:
    """Unified DataWindow extractor combining standard and enhanced extraction methods."""

    # DataWindow markers in UTF-16
    MARKERS = {
        'PBSELECT': b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00",
        'release': b"r\x00e\x00l\x00e\x00a\x00s\x00e\x00",
        'datawindow': b"d\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00",
        'table': b"t\x00a\x00b\x00l\x00e\x00",
        'column': b"c\x00o\x00l\x00u\x00m\x00n\x00",
    }

    def __init__(self):
        """Initialize the DataWindow extractor."""
        self.pdw_extractor = PDWSQLExtractor()
        # Enhanced extraction strategies
        self.extraction_strategies: List[Callable] = [
            self._extract_text_based,
            self._extract_binary_based,
            self._extract_with_header_search,
            self._extract_with_pattern_matching,
            self._extract_with_recovery,
            self._extract_with_heuristics,
        ]

    def extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract DataWindow content from binary data.

        This is the main entry point that combines all extraction methods.

        Args:
            data: Raw binary data of the DataWindow object
            object_info: Optional metadata about the object

        Returns:
            Dictionary containing:
                - syntax: Extracted DataWindow syntax
                - sql: Extracted SQL if found
                - format: Detected format (pdw, binary, etc.)
                - metadata: Additional extracted metadata
        """
        result = {
            'syntax': None,
            'sql': None,
            'format': None,
            'metadata': {},
        }

        # Detect PDW format
        pdw_format = detect_pdw_format(data)
        if pdw_format:
            result['format'] = pdw_format
            log_pdw_warning(pdw_format, object_info.get('name', 'unknown') if object_info else 'unknown')

            # Try PDW extraction
            pdw_sql = self._extract_pdw_sql(data, pdw_format)
            if pdw_sql:
                result['sql'] = pdw_sql

        # Try standard DataWindow syntax extraction
        syntax = self.extract_syntax(data)
        if syntax:
            result['syntax'] = syntax
            result['format'] = result['format'] or 'datawindow'

            # Extract SQL from syntax if not already found
            if not result['sql']:
                result['sql'] = self._extract_sql_from_syntax(syntax)

        # Try enhanced extraction if standard failed
        if not result['syntax']:
            enhanced_result = self.extract_enhanced(data, object_info)
            if enhanced_result:
                result.update(enhanced_result)

        # If still no syntax, try the enhanced extraction strategies
        if not result['syntax']:
            # Try to detect type from filename if available
            filename = object_info.get('name', '') if object_info else ''
            dw_type = self._detect_datawindow_type_from_filename(filename)
            
            # Try each extraction strategy
            for strategy in self.extraction_strategies:
                try:
                    extracted, success = strategy(data, dw_type)
                    if success and extracted:
                        result['syntax'] = extracted
                        result['format'] = result['format'] or 'enhanced'
                        break
                except Exception:
                    continue

        return result

    def extract_syntax(self, data: bytes) -> Optional[str]:
        """Extract DataWindow syntax from binary data.

        Args:
            data: Raw binary data of the DataWindow object

        Returns:
            Extracted DataWindow syntax as string, or None if extraction fails
        """
        # Look for DataWindow markers
        syntax_pos = -1
        for marker_name, marker_bytes in self.MARKERS.items():
            pos = data.find(marker_bytes)
            if pos >= 0:
                syntax_pos = pos
                logger.debug(f"Found DataWindow marker '{marker_name}' at offset 0x{pos:x}")
                break

        if syntax_pos < 0:
            logger.debug("No DataWindow syntax markers found")
            return None

        # Try multiple extraction methods
        results = []

        # Method 1: Look for length field before the syntax
        result1 = self._extract_with_length_field(data, syntax_pos)
        if result1:
            results.append(result1)

        # Method 2: Extract until null terminator
        result2 = self._extract_until_null(data, syntax_pos)
        if result2:
            results.append(result2)

        # Method 3: Look for common end patterns
        result3 = self._extract_with_end_pattern(data, syntax_pos)
        if result3:
            results.append(result3)

        # Choose the best result
        if results:
            # Prefer results that look like complete DataWindow syntax
            for result in results:
                if self._validate_datawindow_syntax(result):
                    return result
            # Otherwise return the longest result
            return max(results, key=len)

        return None

    def extract_enhanced(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Enhanced DataWindow extraction with additional metadata.

        Args:
            data: Raw binary data
            object_info: Optional object metadata

        Returns:
            Dictionary with extracted content or None
        """
        # Try to find DataWindow structure
        dw_offset = self._find_datawindow_structure(data)
        if dw_offset < 0:
            return None

        result = {
            'format': 'enhanced',
            'metadata': {}
        }

        # Extract header information
        if dw_offset >= 16:
            header_data = struct.unpack('<IIII', data[dw_offset-16:dw_offset])
            result['metadata']['header'] = {
                'magic': header_data[0],
                'version': header_data[1],
                'size': header_data[2],
                'checksum': header_data[3],
            }

        # Extract DataWindow definition
        definition = self._extract_definition(data, dw_offset)
        if definition:
            result['syntax'] = definition

        # Extract additional components
        result['metadata']['controls'] = self._extract_controls(data, dw_offset)
        result['metadata']['properties'] = self._extract_properties(data, dw_offset)

        return result

    def _extract_with_length_field(self, data: bytes, start_pos: int) -> Optional[str]:
        """Extract using length field before content."""
        if start_pos < 4:
            return None

        try:
            # Try different length field positions and formats
            for offset in [4, 8, 12, 16]:
                if start_pos < offset:
                    continue

                # Try little-endian 32-bit length
                length = struct.unpack('<I', data[start_pos-offset:start_pos-offset+4])[0]
                if 100 < length < len(data) - start_pos:
                    extracted = data[start_pos:start_pos+length].decode('utf-16-le', errors='ignore')
                    if self._looks_like_datawindow(extracted):
                        return extracted.strip('\x00')

            return None
        except Exception as e:
            logger.debug(f"Length field extraction failed: {e}")
            return None

    def _extract_until_null(self, data: bytes, start_pos: int) -> Optional[str]:
        """Extract until null terminator."""
        try:
            # Find double null (UTF-16 terminator)
            end_pos = data.find(b'\x00\x00', start_pos)
            if end_pos > start_pos:
                # Make sure we're on a 2-byte boundary
                if (end_pos - start_pos) % 2 != 0:
                    end_pos += 1

                extracted = data[start_pos:end_pos].decode('utf-16-le', errors='ignore')
                if self._looks_like_datawindow(extracted):
                    return extracted.strip('\x00')

            return None
        except Exception as e:
            logger.debug(f"Null terminator extraction failed: {e}")
            return None

    def _extract_with_end_pattern(self, data: bytes, start_pos: int) -> Optional[str]:
        """Extract using common end patterns."""
        # Common end patterns for DataWindow definitions
        end_patterns = [
            b'\r\x00\n\x00\r\x00\n\x00',  # Double CRLF in UTF-16
            b')\x00\r\x00\n\x00',          # ) followed by CRLF
            b'}\x00\r\x00\n\x00',          # } followed by CRLF
        ]

        try:
            best_result = None
            for pattern in end_patterns:
                pos = data.find(pattern, start_pos)
                if pos > start_pos:
                    end_pos = pos + len(pattern)
                    extracted = data[start_pos:end_pos].decode('utf-16-le', errors='ignore')
                    if self._looks_like_datawindow(extracted):
                        if not best_result or len(extracted) > len(best_result):
                            best_result = extracted.strip('\x00')

            return best_result
        except Exception as e:
            logger.debug(f"End pattern extraction failed: {e}")
            return None

    def _looks_like_datawindow(self, text: str) -> bool:
        """Check if text looks like DataWindow syntax."""
        if not text or len(text) < 50:
            return False

        # Check for common DataWindow keywords
        keywords = ['release', 'datawindow', 'table', 'column', 'PBSELECT']
        keyword_count = sum(1 for kw in keywords if kw in text)

        # Check for structure
        has_parens = '(' in text and ')' in text
        has_equals = '=' in text

        return keyword_count >= 2 and has_parens and has_equals

    def _validate_datawindow_syntax(self, syntax: str) -> bool:
        """Validate that syntax is complete DataWindow definition."""
        if not syntax:
            return False

        # Check for balanced parentheses
        paren_count = syntax.count('(') - syntax.count(')')
        if abs(paren_count) > 2:  # Allow small imbalance
            return False

        # Check for required sections
        required = ['release', 'datawindow']
        return all(section in syntax.lower() for section in required)

    def _extract_pdw_sql(self, data: bytes, pdw_format: str) -> Optional[str]:
        """Extract SQL from PDW format."""
        try:
            return self.pdw_extractor.extract_sql(data, pdw_format)
        except Exception as e:
            logger.debug(f"PDW SQL extraction failed: {e}")
            return None

    def _extract_sql_from_syntax(self, syntax: str) -> Optional[str]:
        """Extract SQL statement from DataWindow syntax."""
        if not syntax:
            return None

        # Look for PBSELECT section
        pbselect_start = syntax.find('PBSELECT')
        if pbselect_start < 0:
            return None

        # Find the opening parenthesis
        paren_start = syntax.find('(', pbselect_start)
        if paren_start < 0:
            return None

        # Find matching closing parenthesis
        paren_count = 1
        pos = paren_start + 1
        while pos < len(syntax) and paren_count > 0:
            if syntax[pos] == '(':
                paren_count += 1
            elif syntax[pos] == ')':
                paren_count -= 1
            pos += 1

        if paren_count == 0:
            pbselect_content = syntax[paren_start+1:pos-1]
            # Extract RETRIEVE clause
            retrieve_pos = pbselect_content.find('RETRIEVE=')
            if retrieve_pos >= 0:
                sql_start = pbselect_content.find('"', retrieve_pos) + 1
                sql_end = pbselect_content.find('"', sql_start)
                if sql_start > 0 and sql_end > sql_start:
                    return pbselect_content[sql_start:sql_end]

        return None

    def _find_datawindow_structure(self, data: bytes) -> int:
        """Find the start of DataWindow structure in binary data."""
        # Look for DataWindow structure markers
        for marker_name, marker_bytes in self.MARKERS.items():
            pos = data.find(marker_bytes)
            if pos >= 0:
                return pos
        return -1

    def _extract_definition(self, data: bytes, offset: int) -> Optional[str]:
        """Extract DataWindow definition from offset."""
        # This is a simplified version - real implementation would be more complex
        return self.extract_syntax(data[offset:])

    def _extract_controls(self, data: bytes, offset: int) -> List[Dict[str, Any]]:
        """Extract control definitions."""
        controls = []
        # Simplified - would parse actual control structures
        return controls

    def _extract_properties(self, data: bytes, offset: int) -> Dict[str, Any]:
        """Extract DataWindow properties."""
        properties = {}
        # Simplified - would parse actual properties
        return properties

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
            b"table(column=",
            b"column(band=",
            b"compute(band=",
            b"text(band=",
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


# Integration helper for backward compatibility
class EnhancedDataWindowIntegration:
    """Helper class for enhanced DataWindow extraction integration."""

    def __init__(self):
        self.extractor = DataWindowExtractor()

    def extract_datawindow_info(self, data: bytes, object_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract DataWindow information with enhanced methods."""
        return self.extractor.extract(data, object_info)


class DataWindowExtractionManager:
    """Manager for enhanced DataWindow extraction."""

    def __init__(self):
        self.extractor = DataWindowExtractor()

    def extract_from_pbd_object(self, dw_data: bytes, object_name: str) -> Tuple[str, bool]:
        """Extract DataWindow syntax from PBD object data.

        Args:
            dw_data: Raw DataWindow data from PBD
            object_name: Name of the DataWindow object

        Returns:
            Tuple of (syntax, success)
        """
        if not dw_data:
            return "", False

        # Use the main extractor with object info
        result = self.extractor.extract(dw_data, {"name": object_name})
        
        if result['syntax']:
            return result['syntax'], True
        
        return "", False


# Create singleton instance for backward compatibility
extraction_manager = DataWindowExtractionManager()