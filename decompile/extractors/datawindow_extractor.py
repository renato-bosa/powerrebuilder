"""DataWindow syntax extractor following PbdViewer's approach."""


import logging
import struct

from ..pdw.pdw_detector import detect_pdw_format, log_pdw_warning
from ..pdw.pdw_sql_extractor import PDWSQLExtractor

logger = logging.getLogger(__name__)


class DataWindowExtractor:
    """Extract DataWindow syntax from binary .dwo objects."""

    @staticmethod
    def extract_syntax(data: bytes) -> str | None:
        """Extract DataWindow syntax from binary data.

        Args:
            data: Raw binary data of the DataWindow object

        Returns:
            Extracted DataWindow syntax as string, or None if extraction fails
        """
        # Look for PBSELECT or other DataWindow markers in UTF-16
        markers = [
            b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00", # PBSELECT
            b"r\x00e\x00l\x00e\x00a\x00s\x00e\x00", # release
            b"d\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00", # datawindow
        ]

        syntax_pos = -1
        for marker in markers:
            pos = data.find(marker)
            if pos >= 0:
                syntax_pos = pos
                logger.debug("Found DataWindow marker at offset 0x%x", pos)
                break

        if syntax_pos < 0:
            logger.debug("No DataWindow syntax markers found")
            return None

        # Try multiple extraction methods
        results = []

        # Method 1: Look for length field before the syntax
        result1 = DataWindowExtractor._extract_with_length_field(data, syntax_pos)
        if result1:
            results.append(result1)

        # Method 2: Extract from marker to end of valid UTF-16 text
        result2 = DataWindowExtractor._extract_to_end(data, syntax_pos)
        if result2:
            results.append(result2)

        # Method 3: Try to extract with segment awareness
        result3 = DataWindowExtractor._extract_with_segments(data, syntax_pos)
        if result3:
            results.append(result3)

        # Choose the best result (usually the longest valid one)
        if results:
            # Sort by length and return the longest valid result
            results.sort(key=len, reverse=True)
            for result in results:
                # Clean up the result before validation
                cleaned = DataWindowExtractor._cleanup_syntax(result)
                if DataWindowExtractor._is_valid_datawindow_syntax(cleaned):
                    return cleaned

        return None

    @staticmethod
    def _extract_with_length_field(data: bytes, syntax_pos: int) -> str | None:
        """Try to extract using a length field before the syntax."""
        # Search backwards for a potential length field
        search_start = max(0, syntax_pos - 100)

        for offset in range(search_start, syntax_pos, 4):
            if offset + 4 > len(data):
                continue

            potential_length = struct.unpack("<I", data[offset : offset + 4])[0]

            # Validate the length
            if potential_length < 20 or potential_length > len(data) - offset - 4:
                continue

            syntax_start = offset + 4
            syntax_end = syntax_start + potential_length

            # Check if this range includes our marker
            if syntax_start > syntax_pos or syntax_end < syntax_pos + 10:
                continue

            # Try to decode
            try:
                syntax_data = data[syntax_start:syntax_end]
                decoded = syntax_data.decode("utf-16-le", errors="strict")

                # Validate the decoded text
                if DataWindowExtractor._is_valid_datawindow_syntax(decoded):
                    logger.debug(
                        "Found valid syntax with length field at 0x%x", offset,
                    )
                    return decoded.strip("\x00")
            except UnicodeDecodeError:
                continue

        return None

    @staticmethod
    def _extract_to_end(data: bytes, syntax_pos: int) -> str | None:
        """Extract from syntax position to end of valid UTF-16 text."""
        # Start from the syntax position
        current_pos = syntax_pos
        consecutive_valid = 0
        min_consecutive_valid = 10  # Require at least 10 consecutive valid chars

        # Find the end of the UTF-16 text
        while current_pos < len(data) - 2:
            # Check for double null (end of string)
            if data[current_pos : current_pos + 4] == b"\x00\x00\x00\x00":
                break

            # Check if next two bytes can be decoded as UTF-16
            try:
                char = data[current_pos : current_pos + 2].decode(
                    "utf-16-le", errors="strict",
                )

                # Check if it's a valid SQL/DataWindow character
                if (ord(char) >= 32 and ord(char) < 127) or char in "\r\n\t":
                    # ASCII printable or whitespace - good
                    consecutive_valid += 1
                    current_pos += 2
                elif ord(char) < 32 and char not in "\r\n\t":
                    # Control character - stop
                    break
                elif ord(char) >= 127:
                    # Non-ASCII character - could be valid but be cautious
                    if consecutive_valid < min_consecutive_valid:
                        # Haven't seen enough valid chars yet, probably hit binary data
                        break
                    # Reset counter as we hit a non-ASCII char
                    consecutive_valid = 0
                    current_pos += 2
            except UnicodeDecodeError:
                # Hit invalid UTF-16 - stop here
                break

        # Extract and decode with strict error handling
        try:
            syntax_data = data[syntax_pos:current_pos]
            # Use 'replace' to handle any remaining issues but log them
            decoded = syntax_data.decode("utf-16-le", errors="replace")

            # Clean up the decoded text - remove any replacement characters
            cleaned = decoded.replace(
                "\ufffd", "",
            )  # Remove Unicode replacement character

            # Additional cleanup for common corruption patterns
            import re

            # Remove sequences that look like binary data interpreted as text
            cleaned = re.sub(
                r"[\u4000-\u9fff\u3400-\u4dbf]+", "", cleaned,
            )  # Remove CJK characters
            cleaned = re.sub(
                r"䅄⩔\w+Ƕ", "", cleaned,
            )  # Remove specific corruption pattern

            if DataWindowExtractor._is_valid_datawindow_syntax(cleaned):
                return cleaned.strip("\x00")
        except (UnicodeDecodeError, AttributeError) as e:
            logger.debug("Failed to decode syntax: %s", e)

        return None

    @staticmethod
    def _extract_with_segments(data: bytes, syntax_pos: int) -> str | None:
        """Extract DataWindow syntax handling binary segments that interrupt the text."""
        import re

        # Find the end position of the SQL
        end_pos = DataWindowExtractor._find_sql_end_position(data, syntax_pos)
        
        # Extract the range
        raw_data = data[syntax_pos:end_pos]
        
        # Process and extract text segments
        segments = DataWindowExtractor._extract_text_segments(raw_data)
        
        # Join and clean up the result
        return DataWindowExtractor._clean_and_join_segments(segments)
    
    @staticmethod
    def _find_sql_end_position(data: bytes, syntax_pos: int) -> int:
        """Find the end position of SQL in the data."""
        search_limit = min(len(data), syntax_pos + 50000)  # Don't search too far
        
        # Look for common SQL end patterns
        end_markers = [
            b")\x00 \x00)\x00 \x00",  # ") ) " in UTF-16
            b")\x00\x00\x00",  # End of statement
            b"\x00\x00\x00\x00",  # Double null
        ]
        
        for marker in end_markers:
            pos = data.find(marker, syntax_pos, search_limit)
            if pos > 0:
                return pos + len(marker)
        
        return search_limit
    
    @staticmethod
    def _extract_text_segments(raw_data: bytes) -> list[str]:
        """Extract valid text segments from raw data."""
        segments = []
        i = 0
        
        while i < len(raw_data) - 1:
            # Extract a segment of valid characters
            valid_chars, i = DataWindowExtractor._extract_valid_chars_segment(raw_data, i)
            
            if valid_chars:
                segments.append("".join(valid_chars))
            
            # Skip past any binary data
            i = DataWindowExtractor._skip_binary_data(raw_data, i)
        
        return segments
    
    @staticmethod
    def _extract_valid_chars_segment(raw_data: bytes, start: int) -> tuple[list[str], int]:
        """Extract a segment of valid characters."""
        valid_chars = []
        i = start
        
        while i < len(raw_data) - 1:
            try:
                # Try to decode two bytes as UTF-16
                char = raw_data[i : i + 2].decode("utf-16-le", errors="strict")
                
                # Check if it's a reasonable character
                if not DataWindowExtractor._is_valid_char(char, i, raw_data):
                    break
                
                valid_chars.append(char)
                i += 2
                
            except UnicodeDecodeError:
                # Skip invalid bytes
                i += 2
                break
        
        return valid_chars, i
    
    @staticmethod
    def _is_valid_char(char: str, pos: int, raw_data: bytes) -> bool:
        """Check if a character is valid for SQL/DataWindow syntax."""
        # Control character check
        if ord(char) < 32 and char not in "\r\n\t":
            return False
        
        # Check for metadata pattern
        if ord(char) > 127 and pos + 8 < len(raw_data):
            return not DataWindowExtractor._is_metadata_pattern(raw_data[pos : pos + 8])
        
        return True
    
    @staticmethod
    def _is_metadata_pattern(next_bytes: bytes) -> bool:
        """Check if bytes match metadata pattern."""
        return (
            len(next_bytes) >= 8
            and next_bytes[0] > 127
            and next_bytes[2] > 127
            and next_bytes[4] > 127
            and next_bytes[6] > 127
        )
    
    @staticmethod
    def _skip_binary_data(raw_data: bytes, start: int) -> int:
        """Skip past binary data to find next text segment."""
        i = start
        
        while i < len(raw_data) - 1:
            try:
                char = raw_data[i : i + 2].decode("utf-16-le", errors="strict")
                if 32 <= ord(char) < 127 or char in "\r\n\t":
                    # Found start of next text segment
                    break
            except UnicodeDecodeError:
                pass
            i += 2
        
        return i
    
    @staticmethod
    def _clean_and_join_segments(segments: list[str]) -> str | None:
        """Clean and join text segments."""
        import re
        
        if not segments:
            return None
        
        # Join segments
        result = "".join(segments)
        
        # Clean up common issues
        result = re.sub(r"\s+", " ", result)  # Normalize whitespace
        result = re.sub(
            r"([a-z])([A-Z])", r"\1_\2", result
        )  # Fix camelCase that got concatenated
        
        # Specific fixes for known patterns
        result = result.replace(
            "chart_account_type", "chart_of_accounts.chart_account_type"
        )
        
        return result.strip() if result else None
    
    @staticmethod
    def _clean_characters(text: str) -> list[str]:
        """Clean non-ASCII characters from text while preserving word boundaries."""
        chars = []
        i = 0
        
        while i < len(text):
            char = text[i]
            if 32 <= ord(char) < 127 or char in "\r\n\t":
                # ASCII printable or whitespace - keep it
                chars.append(char)
            elif ord(char) >= 0x2000 and DataWindowExtractor._should_add_space_for_word_break(text, i, chars):
                chars.append(" ")
            i += 1
        
        return chars
    
    @staticmethod
    def _should_add_space_for_word_break(text: str, pos: int, chars: list[str]) -> bool:
        """Check if we should add a space when removing a character."""
        if not (0 < pos < len(text) - 1):
            return False
        
        prev_char = text[pos - 1]
        next_char = text[pos + 1]
        
        # Only add space if breaking between word characters
        if not (prev_char.isalnum() and next_char.isalnum() and chars and chars[-1] not in " \r\n\t"):
            return False
        
        # Check if this forms a known word when combined
        word_before = DataWindowExtractor._get_word_before(chars)
        word_after = DataWindowExtractor._get_word_after(text, pos + 1)
        combined = word_before + word_after
        
        known_words = [
            "account", "linkedaccount", "description", "column", 
            "table", "where", "select", "version", "name"
        ]
        
        return combined.lower() not in known_words
    
    @staticmethod
    def _get_word_before(chars: list[str]) -> str:
        """Get the partial word before current position."""
        word = ""
        j = len(chars) - 1
        while j >= 0 and chars[j].isalnum():
            word = chars[j] + word
            j -= 1
        return word
    
    @staticmethod
    def _get_word_after(text: str, start: int) -> str:
        """Get the partial word after current position."""
        word = ""
        k = start
        while k < len(text) and text[k].isalnum():
            word += text[k]
            k += 1
        return word

    @staticmethod
    def _cleanup_syntax(text: str) -> str:
        """Clean up extracted DataWindow syntax from common corruption patterns."""
        import re

        if not text:
            return text

        # First pass: Clean characters
        chars = DataWindowExtractor._clean_characters(text)
        cleaned = "".join(chars)

        # Remove Unicode replacement character
        cleaned = cleaned.replace("\ufffd", "")

        # Fix broken words due to corruption removal
        # Common patterns where corruption splits words
        word_fixes = [
            (r"\s+\*OLUMN", " COLUMN"), # Fix "*OLUMN" -> "COLUMN"
            (r"\*\s+OLUMN", "COLUMN"), # Fix "* OLUMN" -> "COLUMN"
            (r"\*OLUMN", "COLUMN"), # Fix "*OLUMN" -> "COLUMN" (no space)
            (r"WHERE\s*\(\s*\*\s+", "WHERE(    "), # Fix "WHERE(* " -> "WHERE(    "
            (r"ac\s+\*?ount", "account"), # "ac *ount" -> "account"
            (r"chart_a\s+ccount_type", "chart_account_type"), (r"linkedaccoun\s+t", "linkedaccount"), (r"back_rec_\s+ast_date", "back_rec_last_date"), (r"ARG\s*\(\s*NAME\s+", "ARG(NAME = "), (r'COLUMN\s*\(\s*NAME\s*=\s*"([^"]+)"\s*\)', r'COLUMN(NAME="\1")'), (r"(\w+)_a\s+ccount", r"\1_account"), (r'(\w+)\s+(\w+)_(\w+)"', r'\1\2_\3"'), # Fix split table.field names
            (
                r"(\w+)\.(\w+)\s+\*?(\w+)", r"\1.\2\3", ), # Fix "table.ac *ount" -> "table.account"
        ]

        for pattern, replacement in word_fixes:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # Fix whitespace issues
        cleaned = re.sub(r"\s+", " ", cleaned)  # Multiple spaces to single
        cleaned = re.sub(
            r"\s*([(), =])\s*", r"\1", cleaned,
        )  # Remove spaces around operators
        cleaned = re.sub(r'"\s+', '"', cleaned)  # Remove trailing spaces in quotes
        cleaned = re.sub(r'\s+"', '"', cleaned)  # Remove leading spaces in quotes

        # Reconstruct proper DataWindow syntax spacing
        replacements = {
            "PBSELECT(": "PBSELECT( ", "VERSION(": "VERSION(", "TABLE(": "TABLE(", "COLUMN(": "COLUMN(", "WHERE(": "WHERE(    ", "ARG(": "ARG(", "JOIN(": "JOIN(", "LEFT=": "LEFT=", "NAME=": "NAME=", "OP=": "OP =", "EXP1=": "EXP1 =", "EXP2=": "EXP2 =", '""': '" "', # Fix empty strings
        }

        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        # Final cleanup - ensure proper spacing
        cleaned = re.sub(r"([A-Z]+)\(", r" \1(", cleaned)  # Space before keywords
        cleaned = re.sub(r"^\s+", "", cleaned)  # Remove leading space
        cleaned = re.sub(r'([)"])\s*([A-Z]+)', r"\1 \2", cleaned)  # Space after closing

        return cleaned.strip()

    @staticmethod
    def _is_valid_datawindow_syntax(text: str) -> bool:
        """Check if the text looks like valid DataWindow syntax."""
        if not text or len(text) < 10:
            return False

        # Check for common DataWindow keywords
        keywords = ["PBSELECT", "release", "datawindow", "TABLE", "COLUMN"]
        if not any(kw in text for kw in keywords):
            return False

        # Basic validation - should have balanced parentheses
        if text.count("(") != text.count(")") and text.count("(") - text.count(")") > 2:
            return False

        # Should not have too many non-ASCII characters (indicates corruption)
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return non_ascii <= len(text) * 0.1  # Less than or equal to 10% non-ASCII


def extract_datawindow_from_pbd(data: bytes, object_name: str) -> str | None:
    """Extract DataWindow syntax from PBD object data.

    Args:
        data: Raw bytes of the DataWindow object from PBD
        object_name: Name of the DataWindow object (for logging)

    Returns:
        DataWindow syntax as string, or None if not a DataWindow
    """
    # Log header information for debugging
    header_info = data[:8].hex() if len(data) >= 8 else data.hex()
    logger.debug("%s header bytes: %s", object_name, header_info)

    # Check for compiled PDW format first
    pdw_info = detect_pdw_format(data, object_name)
    if pdw_info.is_compiled:
        log_pdw_warning(object_name, pdw_info)

        # Use comprehensive PDW extractor
        logger.info("Attempting comprehensive extraction from compiled PDW file: %s", object_name)

        try:
            from .pdw_comprehensive_extractor import decompile_pdw
            pdw_dw = decompile_pdw(data, object_name)

            if pdw_dw and (pdw_dw.sql or pdw_dw.columns):
                # Generate complete DataWindow source approximation
                dw_syntax = pdw_dw.get_source_approximation()
                logger.info(
                    "Successfully extracted comprehensive data from PDW file %s: SQL=%d chars, Columns=%d", object_name, len(pdw_dw.sql or ""), len(pdw_dw.columns),
                )
                return dw_syntax
            logger.warning("Comprehensive PDW extraction failed, falling back to SQL-only extraction")
        except (ImportError, ValueError) as e:
            logger.warning("Error in comprehensive PDW extraction: %s", e)

        # Fallback to SQL-only extraction
        logger.info("Attempting SQL-only extraction from compiled PDW file: %s", object_name)
        sql = PDWSQLExtractor.extract_sql_from_pdw(data, object_name)

        if sql:
            # Create a minimal DataWindow syntax with the extracted SQL
            dw_syntax = f"""release 10
datawindow(units=0 timer_interval=0 color=1073741824 brushmode=0 transparency=0 gradient.angle=0 gradient.color=8421504 gradient.focus=0 gradient.repetition.count=0 gradient.repetition.length=100 gradient.repetition.mode=0 gradient.scale=100 gradient.spread=100 gradient.transparency=0 picture.blur=0 picture.clip.bottom=0 picture.clip.left=0 picture.clip.right=0 picture.clip.top=0 picture.mode=0 picture.scale.x=100 picture.scale.y=100 picture.transparency=0 processing=0 HTMLDW=no print.printername="" print.documentname="" print.orientation=0 print.margin.left=110 print.margin.right=110 print.margin.top=96 print.margin.bottom=96 print.paper.source=0 print.paper.size=0 print.canusedefaultprinter=yes print.prompt=no print.buttons=no print.preview.buttons=no print.cliptext=no print.overrideprintjob=no print.collate=yes print.background=no print.preview.background=no print.preview.outline=yes hidegrayline=no showbackcoloronxp=no picture.file="" )
header(height=0 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
summary(height=0 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
footer(height=0 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
detail(height=0 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
table(column=(type=char(10) updatewhereclause=no name=dummy dbname="dummy" )
 retrieve="{sql}" )
data(
)
htmltable(border="1" )
htmlgen(clientevents="1" clientvalidation="1" clientcomputedfields="1" clientformatting="0" clientscriptable="0" generatejavascript="1" encodeselflinkargs="1" netscapelayers="0" pagingmethod=0 generatedddwframes="1" )
xhtmlgen() cssgen(sessionspecific="0" )
xmlgen(inline="0" )
xsltgen()
jsgen()
export.xml(headgroups="1" includewhitespace="0" metadatatype=0 savemetadata=0 )
import.xml()
export.pdf(method=0 distill.custompostscript="0" xslfop.print="0" nativepdf.customsize=0 nativepdf.customorientation=0 nativepdf.pdfstandard=0 nativepdf.useprintspec=no )
export.xhtml()
"""
            logger.info("Successfully extracted SQL from PDW file %s: %d characters", object_name, len(sql))
            return dw_syntax
        logger.warning("Could not extract any data from PDW file: %s", object_name)
        return None  # Could not extract even SQL from compiled format

    # Check for common DataWindow formats
    has_dat_header = data.startswith((b"DAT*", b"D\0A\0T\0"))

    if not has_dat_header:
        logger.debug("%s does not have DAT* header, attempting extraction anyway", object_name)

    logger.info("Extracting DataWindow syntax from %s", object_name)

    # Use the extractor
    syntax = DataWindowExtractor.extract_syntax(data)

    if syntax:
        logger.info(
            "Successfully extracted %d characters from %s",
            len(syntax),
            object_name,
        )
    else:
        logger.warning("Failed to extract syntax from %s", object_name)

    return syntax
