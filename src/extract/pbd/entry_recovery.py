"""Entry parsing with recovery wrapper functions."""

import logging
from typing import Any
from src.extract.pbd.structures import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_ascii_sig_unicode_data,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
)

logger = logging.getLogger(__name__)
_enhanced_parser = None


class EnhancedEntryParser:
    """Enhanced entry parser with recovery capabilities."""

    def __init__(self, enable_recovery: bool = True) -> None:
        self.enable_recovery = enable_recovery

    def parse_entry_with_recovery(
        self, arr: bytes, context: (str | None) = None
    ) -> "ParseResult":
        """Parse entry with recovery strategies.

        Args:
            arr: Raw entry data
            context: Context string for logging

        Returns:
            ParseResult with entry or partial data
        """
        return ParseResult()


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
    arr: bytes, is_unicode: bool = False, entry_context: (str | None) = None
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
    result = None
    try:
        if is_unicode:
            result = extract_entry_def_unicode(arr)
            if not result:
                result = extract_entry_def_mixed_mode(arr)
        elif len(arr) >= 12 and arr[0:4] == b"ENT*":
            has_unicode_name = False
            if len(arr) > 40:
                name_area = arr[28 : min(len(arr), 100)]
                if (
                    b"\x00" in name_area
                    and name_area.count(b"\x00") > len(name_area) // 4
                ):
                    has_unicode_name = True
            if has_unicode_name or b"\x00" in arr[4:12]:
                logger.debug(
                    "extract_entry_with_recovery: Detected ASCII ENT* with Unicode data, trying extract_entry_def_ascii_sig_unicode_data"
                )
                result = extract_entry_def_ascii_sig_unicode_data(arr)
                if not result:
                    logger.debug(
                        "extract_entry_with_recovery: ascii_sig_unicode_data failed, trying pure ASCII"
                    )
                    result = extract_entry_def(arr)
            else:
                logger.debug(
                    "extract_entry_with_recovery: Detected pure ASCII ENT*, trying extract_entry_def"
                )
                result = extract_entry_def(arr)
        else:
            result = extract_entry_def(arr)
            if not result:
                result = extract_entry_def_ascii_sig_unicode_data(arr)
        if result:
            return result
    except Exception as e:
        logger.warning("Standard parsing failed with exception: %s", e)
    logger.info(
        "Standard parsing failed%s, trying enhanced parser",
        f" for {entry_context}" if entry_context else "",
    )
    parser = get_enhanced_parser()
    parse_result = parser.parse_entry_with_recovery(arr, context=entry_context)
    if parse_result.entry:
        logger.info(
            "Enhanced parser succeeded%s",
            f" for {entry_context}" if entry_context else "",
        )
        return parse_result.entry
    if parse_result.partial_data:
        logger.warning(
            "Only partial data could be extracted%s: %s",
            f" for {entry_context}" if entry_context else "",
            parse_result.partial_data,
        )
    return None
