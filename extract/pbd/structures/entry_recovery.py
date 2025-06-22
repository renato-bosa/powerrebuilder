"""Entry parsing with recovery wrapper functions."""

import logging

from extract.pbd.structures.enhanced_entry_parser import EnhancedEntryParser
from extract.pbd.structures.entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_ascii_sig_unicode_data,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
)

logger = logging.getLogger(__name__)

# Global enhanced parser instance
_enhanced_parser = None

def get_enhanced_parser() -> EnhancedEntryParser:






    """Get or create the global enhanced parser instance."""
    global _enhanced_parser
    if _enhanced_parser is None:
        _enhanced_parser = EnhancedEntryParser(enable_recovery=True)
    return _enhanced_parser


def extract_entry_with_recovery(arr: bytes, is_unicode: bool = False, entry_context: str | None = None) -> PbEntryDefinition | None:








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
        else:
            result = extract_entry_def(arr)
            if not result:
                # Try ascii sig with unicode data
                result = extract_entry_def_ascii_sig_unicode_data(arr)

        if result:
            return result

    except Exception as e:
        logger.warning(f"Standard parsing failed with exception: {e}")

    # Standard parsing failed, try enhanced parser
    logger.info(f"Standard parsing failed{f" for {entry_context}" if entry_context else ""}, trying enhanced parser")

    parser = get_enhanced_parser()
    parse_result = parser.parse_entry_with_recovery(arr, context=entry_context)

    if parse_result.entry:
        logger.info(f"Enhanced parser succeeded{f" for {entry_context}" if entry_context else ""}")
        return parse_result.entry

    if parse_result.partial_data:
        logger.warning(
            f"Only partial data could be extracted{f" for {entry_context}" if entry_context else ""}: "
            f"{parse_result.partial_data}",
        )

    return None


def extract_entries_with_recovery(entries_data: list[tuple[bytes, int]], is_unicode: bool = False, file_context: str | None = None) -> list[PbEntryDefinition]:








    """Extract multiple entries with recovery, logging statistics.

    Args:
        entries_data: List of (entry_bytes, offset) tuples
        is_unicode: Whether entries are expected to be Unicode
        file_context: File context for logging (e.g., "dcm_detailobjects.pbd")

    Returns:
        List of successfully parsed entries
    """
    results = []
    failed_entries = []

    for i, (entry_bytes, offset) in enumerate(entries_data):
        context = f"entry {i} at offset {offset}"
        if file_context:
            context = f"{context} in {file_context}"

        entry = extract_entry_with_recovery(entry_bytes, is_unicode, context)

        if entry:
            results.append(entry)
        else:
            failed_entries.append((i, offset))

    # Log statistics
    total = len(entries_data)
    success = len(results)
    failed = len(failed_entries)

    if file_context:
        logger.info(
            f"{file_context}: Parsed {success}/{total} entries ({success/total*100:.1f}% success rate)",
        )

    if failed_entries:
        logger.warning(
            f"Failed to parse {failed} entries: {[f"entry {i} at {offset}" for i, offset in failed_entries[:5]]}"
            f"{" and more..." if len(failed_entries) > 5 else ""}",
        )

    # Get parser statistics
    parser = get_enhanced_parser()
    stats = parser.get_statistics()
    if stats["recovered_entries"] > 0:
        logger.info(
            f"Enhanced parser recovered {stats["recovered_entries"]} entries "
            f"({stats["recovery_rate"]:.1f}% recovery rate)",
        )

    return results
