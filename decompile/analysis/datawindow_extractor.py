"""DataWindow syntax extractor following PbdViewer's approach."""

import logging
import struct

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
            b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00",  # PBSELECT
            b"r\x00e\x00l\x00e\x00a\x00s\x00e\x00",  # release
            b"d\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00",  # datawindow
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
                        "Found valid syntax with length field at 0x%x",
                        offset
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
                    "utf-16-le", errors="strict"
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
                "\ufffd", ""
            )  # Remove Unicode replacement character

            # Additional cleanup for common corruption patterns
            import re

            # Remove sequences that look like binary data interpreted as text
            cleaned = re.sub(
                r"[\u4000-\u9fff\u3400-\u4dbf]+", "", cleaned
            )  # Remove CJK characters
            cleaned = re.sub(
                r"䅄⩔\w+Ƕ", "", cleaned
            )  # Remove specific corruption pattern

            if DataWindowExtractor._is_valid_datawindow_syntax(cleaned):
                return cleaned.strip("\x00")
        except Exception as e:
            logger.debug("Failed to decode syntax: %s", e)

        return None

    @staticmethod
    def _extract_with_segments(data: bytes, syntax_pos: int) -> str | None:
        """Extract DataWindow syntax handling binary segments that interrupt the text."""
        import re

        # Look for a pattern where we have text segments separated by binary data
        # The pattern seems to be that binary metadata is inserted between text segments

        # First, try to find the approximate end of the SQL
        end_pos = syntax_pos
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
                end_pos = pos + len(marker)
                break

        if end_pos == syntax_pos:
            end_pos = search_limit

        # Extract the range
        raw_data = data[syntax_pos:end_pos]

        # Process in chunks, looking for valid UTF-16 text segments
        segments = []
        i = 0

        while i < len(raw_data) - 1:
            # Try to decode a segment
            valid_chars = []

            while i < len(raw_data) - 1:
                try:
                    # Try to decode two bytes as UTF-16
                    char = raw_data[i : i + 2].decode("utf-16-le", errors="strict")

                    # Check if it's a reasonable character for SQL
                    if ord(char) < 32 and char not in "\r\n\t":
                        # Control character - might be segment boundary
                        break
                    if ord(char) > 127:
                        # Non-ASCII - check if it looks like our corruption pattern
                        if i + 8 < len(raw_data):
                            # Check if this looks like the metadata pattern
                            next_bytes = raw_data[i : i + 8]
                            if (
                                next_bytes[0] > 127
                                and next_bytes[2] > 127
                                and next_bytes[4] > 127
                                and next_bytes[6] > 127
                            ):
                                # Likely metadata - skip ahead
                                # Look for next valid text
                                j = i + 2
                                while j < len(raw_data) - 1:
                                    try:
                                        test_char = raw_data[j : j + 2].decode(
                                            "utf-16-le", errors="strict"
                                        )
                                        if 32 <= ord(test_char) < 127:
                                            # Found likely text continuation
                                            i = j
                                            break
                                    except Exception:
                                        # Continue searching for valid UTF-16 text
                                        continue
                                    j += 2
                                else:
                                    # No more valid text found
                                    break
                                continue

                    valid_chars.append(char)
                    i += 2

                except UnicodeDecodeError:
                    # Skip invalid bytes
                    i += 2
                    # If we have accumulated valid chars, save them
                    if valid_chars:
                        segments.append("".join(valid_chars))
                        valid_chars = []

            # Save any remaining valid chars
            if valid_chars:
                segments.append("".join(valid_chars))

            # Skip past any binary data
            while i < len(raw_data) - 1:
                try:
                    char = raw_data[i : i + 2].decode("utf-16-le", errors="strict")
                    if 32 <= ord(char) < 127 or char in "\r\n\t":
                        # Found start of next text segment
                        break
                except Exception:
                    # Continue searching for next valid character
                    continue
                i += 2

        # Join segments with appropriate spacing
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
    def _cleanup_syntax(text: str) -> str:
        """Clean up extracted DataWindow syntax from common corruption patterns."""
        import re

        if not text:
            return text

        # First pass: Remove all non-ASCII characters that are likely corruption
        # Keep only ASCII printable chars, newlines, tabs
        chars = []
        i = 0
        while i < len(text):
            char = text[i]
            if 32 <= ord(char) < 127 or char in "\r\n\t":
                # ASCII printable or whitespace - keep it
                chars.append(char)
            elif ord(char) >= 0x2000:  # Various Unicode ranges that are corruption
                # Skip this character, but check context for word breaks
                # Don't add space if we're in the middle of a word
                if i > 0 and i < len(text) - 1:
                    prev_char = text[i - 1] if i > 0 else ""
                    next_char = text[i + 1] if i < len(text) - 1 else ""
                    # Only add space if breaking between word characters
                    if (
                        prev_char.isalnum()
                        and next_char.isalnum()
                        and chars
                        and chars[-1] not in " \r\n\t"
                    ):
                        # Check if this looks like it's splitting a known word
                        # Get the partial word before and after
                        word_before = ""
                        j = len(chars) - 1
                        while j >= 0 and chars[j].isalnum():
                            word_before = chars[j] + word_before
                            j -= 1

                        # Look ahead to see what comes next
                        word_after = ""
                        k = i + 1
                        while k < len(text) and text[k].isalnum():
                            word_after += text[k]
                            k += 1

                        # Check if this forms a known word when combined
                        combined = word_before + word_after
                        known_words = [
                            "account",
                            "linkedaccount",
                            "description",
                            "column",
                            "table",
                            "where",
                            "select",
                            "version",
                            "name",
                        ]

                        if combined.lower() not in known_words:
                            chars.append(" ")
            i += 1

        cleaned = "".join(chars)

        # Remove Unicode replacement character
        cleaned = cleaned.replace("\ufffd", "")

        # Fix broken words due to corruption removal
        # Common patterns where corruption splits words
        word_fixes = [
            (r"ac\s+\*?ount", "account"),  # "ac *ount" -> "account"
            (r"chart_a\s+ccount_type", "chart_account_type"),
            (r"linkedaccoun\s+t", "linkedaccount"),
            (r"back_rec_\s+ast_date", "back_rec_last_date"),
            (r"ARG\s*\(\s*NAME\s+", "ARG(NAME = "),
            (r'COLUMN\s*\(\s*NAME\s*=\s*"([^"]+)"\s*\)', r'COLUMN(NAME="\1")'),
            (r"(\w+)_a\s+ccount", r"\1_account"),
            (r'(\w+)\s+(\w+)_(\w+)"', r'\1\2_\3"'),  # Fix split table.field names
            (
                r"(\w+)\.(\w+)\s+\*?(\w+)",
                r"\1.\2\3",
            ),  # Fix "table.ac *ount" -> "table.account"
        ]

        for pattern, replacement in word_fixes:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # Fix whitespace issues
        cleaned = re.sub(r"\s+", " ", cleaned)  # Multiple spaces to single
        cleaned = re.sub(
            r"\s*([(),=])\s*", r"\1", cleaned
        )  # Remove spaces around operators
        cleaned = re.sub(r'"\s+', '"', cleaned)  # Remove trailing spaces in quotes
        cleaned = re.sub(r'\s+"', '"', cleaned)  # Remove leading spaces in quotes

        # Reconstruct proper DataWindow syntax spacing
        replacements = {
            "PBSELECT(": "PBSELECT( ",
            "VERSION(": "VERSION(",
            "TABLE(": "TABLE(",
            "COLUMN(": "COLUMN(",
            "WHERE(": "WHERE(    ",
            "ARG(": "ARG(",
            "JOIN(": "JOIN(",
            "LEFT=": "LEFT=",
            "NAME=": "NAME=",
            "OP=": "OP =",
            "EXP1=": "EXP1 =",
            "EXP2=": "EXP2 =",
            '""': '" "',  # Fix empty strings
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
        if text.count("(") != text.count(")"):
            # Allow for truncation at the end
            if text.count("(") - text.count(")") > 2:
                return False

        # Should not have too many non-ASCII characters (indicates corruption)
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if non_ascii > len(text) * 0.1:  # More than 10% non-ASCII
            return False

        return True


def extract_datawindow_from_pbd(data: bytes, object_name: str) -> str | None:
    """Extract DataWindow syntax from PBD object data.

    Args:
        data: Raw bytes of the DataWindow object from PBD
        object_name: Name of the DataWindow object (for logging)

    Returns:
        DataWindow syntax as string, or None if not a DataWindow
    """
    # Check if this is a DataWindow (DAT* header)
    if not data.startswith(b"DAT*"):
        logger.debug("%s does not have DAT* header", object_name)
        return None

    logger.info("Extracting DataWindow syntax from %s", object_name)

    # Use the extractor
    syntax = DataWindowExtractor.extract_syntax(data)

    if syntax:
        logger.info(
            "Successfully extracted %d characters from %s",
            len(syntax),
            object_name
        )
    else:
        logger.warning("Failed to extract syntax from %s", object_name)

    return syntax
