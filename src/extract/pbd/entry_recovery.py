"""Entry parsing with recovery wrapper functions."""

import logging
from typing import Any

from src.extract.pbd.entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_ascii_sig_unicode_data,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
)

logger = logging.getLogger(__name__)

# Global instance for enhanced parser (lazy initialization)
_enhanced_parser = None


class EnhancedEntryParser:
    """Enhanced entry parser with recovery capabilities."""

    def __init__(self, enable_recovery: bool = True) -> None:
        self.enable_recovery = enable_recovery

    def parse_entry_with_recovery(
        self, arr: bytes, context: str | None = None
    ) -> "ParseResult":
        """Parse entry with recovery strategies.

        Args:
            arr: Raw entry data
            context: Context string for logging

        Returns:
            ParseResult with entry or partial data
        """
        # This is a placeholder implementation
        # The actual implementation would include recovery logic
        result = ParseResult()

        # Try various recovery strategies
        # For now, just return empty result
        return result


class ParseResult:
    """Result of parsing attempt."""

    def __init__(self) -> None:
        self.entry: PbEntryDefinition | None = None
        self.partial_data: dict[str, Any] | None = None


def get_enhanced_parser() -> EnhancedEntryParser:
    """Get or create the global enhanced parser instance."""
    global _enhanced_parser
    if _enhanced_parser is None:
        _enhanced_parser = EnhancedEntryParser(enable_recovery=True)
    return _enhanced_parser


def extract_entry_with_recovery(
    arr: bytes, is_unicode: bool = False, entry_context: str | None = None
) -> PbEntryDefinition | None:
    """Extract entry definition with enhanced recovery on failure.

    This function tries standard parsing first, then falls back to enhanced
    parsing with recovery strategies if standard parsing fails.

    Args:
        arr: Raw entry data
        is_unicode: Whether to try Unicode parsing first
        entry_context: Context string for logging (e.g., "entry 37 in dcm_detailobjects.pbd")

    Returns:
        PbEntryDefinition if successful, None otherwise
    """
    # Try standard parsing first
    result = None

    try:
        if is_unicode:
            result = extract_entry_def_unicode(arr)
            if not result:
                # Try mixed mode
                result = extract_entry_def_mixed_mode(arr)
        # For ASCII signature, check if it has Unicode data first
        elif len(arr) >= 12 and arr[0:4] == b"ENT*":
            # Check if the name portion has Unicode data (look further in the structure)
            # After the fixed header (28 bytes), check for Unicode patterns
            has_unicode_name = False
            if len(arr) > 40:
                # Look for null bytes in what should be the name area
                name_area = arr[28 : min(len(arr), 100)]
                if (
                    b"\x00" in name_area
                    and name_area.count(b"\x00") > len(name_area) // 4
                ):
                    has_unicode_name = True

            if has_unicode_name or b"\x00" in arr[4:12]:
                # This appears to be ASCII ENT* with Unicode data
                logger.debug(
                    "extract_entry_with_recovery: Detected ASCII ENT* with Unicode data, trying extract_entry_def_ascii_sig_unicode_data"
                )
                result = extract_entry_def_ascii_sig_unicode_data(arr)
                if not result:
                    # Fall back to pure ASCII
                    logger.debug(
                        "extract_entry_with_recovery: ascii_sig_unicode_data failed, trying pure ASCII"
                    )
                    result = extract_entry_def(arr)
            else:
                # Pure ASCII
                logger.debug(
                    "extract_entry_with_recovery: Detected pure ASCII ENT*, trying extract_entry_def"
                )
                result = extract_entry_def(arr)
        else:
            # Try pure ASCII first
            result = extract_entry_def(arr)
            if not result:
                # Try ascii sig with unicode data
                result = extract_entry_def_ascii_sig_unicode_data(arr)

        if result:
            return result

    except Exception as e:
        logger.warning("Standard parsing failed with exception: %s", e)

    # Standard parsing failed, try enhanced parser
    logger.info(
        f"Standard parsing failed{f' for {entry_context}' if entry_context else ''}, trying enhanced parser"
    )

    parser = get_enhanced_parser()
    parse_result = parser.parse_entry_with_recovery(arr, context=entry_context)

    if parse_result.entry:
        logger.info(
            f"Enhanced parser succeeded{f' for {entry_context}' if entry_context else ''}"
        )
        return parse_result.entry

    if parse_result.partial_data:
        logger.warning(
            f"Only partial data could be extracted{f' for {entry_context}' if entry_context else ''}: "
            f"{parse_result.partial_data}",
        )

    return None
