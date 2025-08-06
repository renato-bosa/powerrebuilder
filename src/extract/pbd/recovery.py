"""Recovery module for corrupted PowerBuilder files.

This module consolidates functionality from:
- corruption.py: DataWindow corruption detection and fixing
- entry_recovery.py: Entry parsing with recovery strategies
- checkpoint.py: Enhanced error recovery for corrupted PBL/PBD files
"""

import logging
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.circuit_breaker import circuit_breaker
from src.core.constants import BUFFER_SIZE
from src.core.resource_limits import with_memory_limit, with_timeout
from src.core.security import safe_write_file, sanitize_filename
from src.extract.pbd.constants import BLOCK_SIZE, SIGNATURES, UNICODE_SIGNATURES
from src.extract.pbd.structures import (
    HeaderClass,
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_ascii_sig_unicode_data,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Data Corruption Fixing (from corruption.py)
# ============================================================================


class DataCorruptionFixer:
    """Fixes corruption in extracted DataWindow content."""

    # Common corruption patterns found in extracted files
    CORRUPTION_PATTERNS = [
        # Pattern: word split by " * "
        (r"(\w+)\s+\*\s+(\w+)", r"\1\2"),  # "add * ess_id" -> "address_id"
        # Pattern: SQL keywords split - FIXED
        (r"COL\s*\*\s*L\s*MN", "COLUMN"),  # "COL *L MN" -> "COLUMN"
        (r"COL\*LMN", "COLUMN"),  # "COL*LMN" -> "COLUMN"
        (r"TAB\s+\*\s*E", "TABLE"),  # "TAB * E" -> "TABLE"
        (r"TAB\s+\*\s*L\s*E", "TABLE"),  # "TAB *L E" -> "TABLE"
        (r"LOG\s+\*\s+C", "LOGIC"),  # "LOG * C" -> "LOGIC"
        (r"\*OLUMN", "COLUMN"),  # "*OLUMN" -> "COLUMN"
        (r"\s+\*OLUMN", " COLUMN"),  # " *OLUMN" -> " COLUMN"
        # Pattern: column names with asterisks
        # "add * ess_id" -> "address_id"
        (r'"\s*(\w+)\s*\*\s*(\w+)\s*"', r'"\1\2"'),
        # Pattern: dot notation split
        # "table.*column" -> "table.column"
        (r"(\w+)\s*\.\s*\*(\w+)", r"\1.\2"),
        (
            r"(\w+)\.\s*(\w+)\s*\*\s*(\w+)",
            r"\1.\2\3",
        ),  # "table.col * umn" -> "table.column"
        # Pattern: Fix .*Jate -> .date (and similar patterns)
        (
            r"\.(\*[A-Z])(\w+)",
            lambda m: f".{m.group(1)[1].lower()}{m.group(2)}",
        ),  # ".*Jate" -> ".date"
        # Pattern: Remove asterisk after closing quote
        (r'"\*', '"'),  # '"address.address_id"*' -> '"address.address_id"'
        # Pattern: Fix asterisk between dot and space
        (r"\.\*\s+", ". "),  # 'address.* id' -> 'address. id' (generic)
        # Additional patterns found in real extractions
        (r'"\*\s+(\w+)', r'" \1'),  # '"* COLUMN(' -> '" COLUMN('
        (r'"\)\*\s+', '") '),  # '")* ' -> '") '
        (r'"\s*\*IGHT', '" RIGHT'),  # '"*IGHT' -> '" RIGHT'
        (r"b\s*\*\s*lling", "billing"),  # "b *lling" -> "billing"
        (r"bi\s*\*\s*ling", "billing"),  # "bi *ling" -> "billing"
        (r"NA\s*\*\s*E=", "NAME="),  # "NA *E=" -> "NAME="
        (r"NAM\s*\*\s*=", "NAME="),  # "NAM *=" -> "NAME="
        (r"EX\s*\*2", "EXP2"),  # "EX *2" -> "EXP2"
        (r'OP\s*\*"=', 'OP "='),  # 'OP *"=' -> 'OP "='
        (
            r"tblclinica\s*\*\s*tribs",
            "tblclinicattribs",
        ),  # "tblclinica *tribs" -> "tblclinicattribs"
        (
            r"tblclini\s*\*attribs",
            "tblclinicattribs",
        ),  # "tblclini *attribs" -> "tblclinicattribs"
        (
            r"locations\s*\*location",
            "locations.location",
        ),  # "locations *location" -> "locations.location"
        # "*linic_address" -> "clinic_address"
        (r"\*linic_address", "clinic_address"),
        (r'incremen\s*\*"', 'increment"'),  # 'incremen *"' -> 'increment"'
        (
            r"(\w+)\.\*\s*ddress",
            r"\1.address",
        ),  # "person_address.* ddress_id" -> "person_address.address_id"
        (r'"\s*\*\s*"\)', '"")'),  # '" *")' -> '"")'
        (r"'\s*A\s*\*", "'A'"),  # "'A *" -> "'A'"
        # 'amount_paid *)' -> 'amount_paid"'
        (r"amount_paid\s*\*\)", 'amount_paid"'),
        (r'NAM\s*\*="', 'NAME="'),  # 'NAM *="' -> 'NAME="'
        (
            r"TAB\s*\*\s*E\(NAME\s*\*=",
            "TABLE(NAME=",
        ),  # 'TAB * E(NAME *=' -> 'TABLE(NAME='
        (r"COL\s*\*\s*MN", "COLUMN"),  # 'COL * MN' -> 'COLUMN'
        (r"WHERE\s*\(\s*\*\s+", "WHERE(    "),  # 'WHERE( * ' -> 'WHERE(    '
    ]

    # Signatures that might leak into content
    DAT_SIGNATURES = [b"DAT*", b"DAT ", b"D\0A\0T\0"]

    @classmethod
    def detect_corruption(cls, content: str) -> bool:
        """Detect if content contains known corruption patterns.

        Args:
            content: Extracted text content

        Returns:
            True if corruption is detected
        """
        # Check for asterisk patterns that indicate corruption
        corruption_indicators = [
            r"\s+\*\s+",  # Spaces around asterisk
            r"[A-Z]{3}\s+\*[A-Z]",  # Like "COL *L"
            r"\w+\s+\*\s+\w+",  # Words split by asterisk
        ]

        return any(re.search(pattern, content) for pattern in corruption_indicators)

    @classmethod
    def fix_corrupted_content(cls, content: str) -> tuple[str, int]:
        """Fix known corruption patterns in content.

        Args:
            content: Corrupted content

        Returns:
            Tuple of (fixed_content, number_of_fixes_applied)
        """
        fixed_content = content
        total_fixes = 0

        # Apply each corruption pattern fix
        for pattern, replacement in cls.CORRUPTION_PATTERNS:
            fixed_content, count = re.subn(pattern, replacement, fixed_content)
            if count > 0:
                logger.debug(
                    "Applied fix for pattern '%s': %s occurrences", pattern, count
                )
                total_fixes += count

        # Additional cleanup for standalone asterisks
        fixed_content = re.sub(r"(\w)\s*\*\s*(\w)", r"\1\2", fixed_content)

        if total_fixes > 0:
            logger.info("Fixed %s corruption patterns in content", total_fixes)

        return fixed_content, total_fixes

    @classmethod
    def validate_sql_syntax(cls, content: str) -> list[str]:
        """Validate SQL syntax after fixing corruption.

        Args:
            content: Fixed SQL content

        Returns:
            List of validation issues found
        """
        issues = []

        # Check for incomplete keywords
        incomplete_keywords = [
            "COL MN",
            "TAB E",
            "SEL ECT",
            "FR OM",
            "WH ERE",
        ]

        for keyword in incomplete_keywords:
            if keyword in content:
                issues.append(f"Incomplete keyword found: {keyword}")

        # Check for valid SQL structure
        if "PBSELECT" in content:
            # PBSELECT uses TABLE() syntax instead of FROM
            if "TABLE(" not in content.upper():
                issues.append("PBSELECT missing TABLE() specification")
        elif "SELECT" in content:
            # Standard SQL should have FROM clause
            if "FROM" not in content.upper():
                issues.append("Missing required SQL keyword: FROM")

        return issues

    @classmethod
    def clean_dat_artifacts(cls, data: bytes) -> bytes:
        """Remove DAT block artifacts from binary data.

        Args:
            data: Raw binary data

        Returns:
            Cleaned binary data
        """
        # Remove DAT signatures that might have leaked into content
        cleaned = data

        for signature in cls.DAT_SIGNATURES:
            # Only remove if it appears in unexpected places (not at block boundaries)
            # This is a more careful approach to avoid removing legitimate
            # content
            parts = cleaned.split(signature)
            if len(parts) > 1:
                # Check if the signature appears to be misplaced
                cleaned_parts = []
                for i, part in enumerate(parts):
                    if i > 0 and len(part) > 0 and part[0:1] not in b"\x00\r\n":
                        # Signature appears in middle of content
                        logger.debug(
                            "Removed misplaced DAT signature at position %s",
                            len(b"".join(cleaned_parts)),
                        )
                        # Merge with previous part
                        cleaned_parts[-1] += part
                    else:
                        cleaned_parts.append(part)
                        if i < len(parts) - 1:
                            cleaned_parts.append(signature)

                cleaned = b"".join(cleaned_parts)

        return cleaned


def fix_extracted_datawindow(content: str, filename: str = "") -> str:
    """Fix a corrupted DataWindow extraction.

    Args:
        content: Extracted DataWindow content
        filename: Optional filename for logging

    Returns:
        Fixed content
    """
    fixer = DataCorruptionFixer()

    # Check if content needs fixing
    if not fixer.detect_corruption(content):
        return content

    logger.info("Detected corruption in %s", filename if filename else "content")

    # Fix the corruption
    fixed_content, fix_count = fixer.fix_corrupted_content(content)

    # Validate the result
    issues = fixer.validate_sql_syntax(fixed_content)
    if issues:
        logger.warning("Validation issues after fixing %s: %s", filename, issues)

    return fixed_content


def process_extracted_file(filepath: Path) -> bool:
    """Process an extracted file and fix corruption if needed.

    Args:
        filepath: Path to the extracted file

    Returns:
        True if file was fixed, False otherwise
    """
    try:
        with filepath.open(encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Check and fix corruption
        fixed_content = fix_extracted_datawindow(content, str(filepath))

        if fixed_content != content:
            # Write fixed content back
            with filepath.open("w", encoding="utf-8") as f:
                f.write(fixed_content)
            logger.info("Fixed corruption in %s", filepath)
            return True

    except Exception as e:
        logger.error("Error processing %s: %s", filepath, e)

    return False


# ============================================================================
# Entry Recovery (from entry_recovery.py)
# ============================================================================

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
        return ParseResult()

        # Try various recovery strategies
        # For now, just return empty result


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
    arr: bytes,
    is_unicode: bool = False,
    entry_context: str | None = None,
    pb_version=None,
) -> PbEntryDefinition | None:
    """Extract entry definition with enhanced recovery on failure.

    This function tries standard parsing first, then falls back to enhanced
    parsing with recovery strategies if standard parsing fails.

    Args:
        arr: Raw entry data
        is_unicode: Whether to try Unicode parsing first
        entry_context: Context string for logging (e.g., "entry 37 in dcm_detailobjects.pbd")
        pb_version: PowerBuilder version for version-specific parsing

    Returns:
        PbEntryDefinition if successful, None otherwise
    """
    # Try version-specific parsing first if we have a version
    result = None

    try:
        # First, try version-specific parsing with the new extract_entry_def function
        result = extract_entry_def(arr, pb_version)
        if result:
            logger.debug(
                f"Successfully parsed entry with version-specific parser: {result.object_name}"
            )
            return result

        # Fall back to original parsing methods
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


# ============================================================================
# Enhanced Recovery Engine (from checkpoint.py)
# ============================================================================


@dataclass
class RecoveredBlock:
    """Represents a recovered block from the file."""

    offset: int
    size: int
    block_type: str  # HDR, NOD, ENT, DAT, FRE
    is_unicode: bool
    data: bytes
    metadata: dict = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class EnhancedRecoveryEngine:
    """Advanced recovery engine for corrupted PowerBuilder files."""

    # Common block sizes in PowerBuilder files
    BLOCK_SIZES = [512, 1024, 2048, BUFFER_SIZE]

    # Encoding detection
    ENCODINGS = ["utf-8", "utf-16-le", "utf-16-be", "latin1", "cp1252", "ascii"]

    # Corruption patterns
    CORRUPTION_PATTERNS = {
        "asterisk_insertion": (b"*\x00*\x00*\x00*\x00", b""),  # Common corruption
        "null_insertion": (b"\x00\x00\x00\x00\x00\x00\x00\x00", b""),
        "ff_corruption": (b"\xff\xff\xff\xff", b"\x00\x00\x00\x00"),
        "repeated_pattern": (b"\xab\xcd\xab\xcd\xab\xcd", b"\x00\x00\x00\x00\x00\x00"),
        # Duplicate BOM
        "unicode_bom_corruption": (b"\xff\xfe\xff\xfe", b"\xff\xfe"),
        "control_char_spam": (
            b"\x01\x02\x03\x04\x05\x06\x07\x08",
            b"",
        ),  # Control characters
    }

    def __init__(
        self, file_bytes: bytes, output_dir: Path, progress_callback=None
    ) -> None:
        """Initialize the recovery engine.

        Args:
            file_bytes: The corrupted file data
            output_dir: Directory for recovered files
            progress_callback: Optional callback function(message, percent)
        """
        # Convert to bytearray so we can modify it
        self.file_bytes = bytearray(file_bytes)
        self.file_size = len(file_bytes)
        self.output_dir = output_dir
        self.recovery_dir = output_dir / "recovery"
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        self.block_size = BLOCK_SIZE  # Default block size
        self.progress_callback = progress_callback

        # Recovery state
        self.recovered_blocks: list[RecoveredBlock] = []
        self.block_map: dict[str, list[RecoveredBlock]] = {
            "HDR": [],
            "NOD": [],
            "ENT": [],
            "DAT": [],
            "FRE": [],
        }
        # object_name -> metadata
        self.recovered_objects: dict[str, dict] = {}
        # For fragment reconstruction
        self.fragments: dict[str, list[bytes]] = {}
        # Recovery confidence
        self.confidence_scores: dict[str, float] = {}

        # Statistics
        self.stats = {
            "blocks_found": 0,
            "blocks_recovered": 0,
            "objects_recovered": 0,
            "corruption_repairs": 0,
            "validation_failures": 0,
        }

    @with_memory_limit(1024 * 1024 * 1024)  # 1GB memory limit
    def recover_all(self) -> bool:
        """Perform comprehensive recovery of the corrupted file.

        Returns:
            True if any data was recovered
        """
        logger.info("Starting enhanced recovery engine")

        # Step 1: Apply corruption fixes
        self._update_progress("Applying corruption pattern fixes", 0)
        self._apply_corruption_fixes()

        # Step 2: Scan for all block signatures
        self._update_progress("Scanning for block signatures", 12.5)
        self._scan_all_blocks()

        # Step 3: Reconstruct header if missing
        self._update_progress("Reconstructing header", 25)
        self._reconstruct_header()

        # Step 4: Recover NOD blocks for structure
        self._update_progress("Recovering NOD blocks", 37.5)
        self._recover_nod_blocks()

        # Step 5: Match ENT and DAT blocks
        self._update_progress("Matching ENT and DAT blocks", 50)
        self._match_ent_dat_blocks()

        # Step 6: Validate and extract objects
        self._update_progress("Extracting validated objects", 62.5)
        self._extract_validated_objects()

        # Step 7: Recover orphaned blocks
        self._update_progress("Recovering orphaned blocks", 75)
        self._recover_orphaned_blocks()

        # Step 8: Generate recovery report
        self._update_progress("Generating recovery report", 87.5)
        self._generate_recovery_report()

        self._update_progress("Recovery complete", 100)

        return self.stats["objects_recovered"] > 0

    def _apply_corruption_fixes(self) -> None:
        """Apply known corruption pattern fixes."""
        logger.info("Applying corruption pattern fixes")

        for pattern_name, (pattern, replacement) in self.CORRUPTION_PATTERNS.items():
            count = 0
            pos = 0
            while True:
                pos = self.file_bytes.find(pattern, pos)
                if pos == -1:
                    break

                # Skip if this would corrupt a block signature
                skip = False
                for sig in [b"HDR*", b"NOD*", b"ENT*", b"DAT*", b"FRE*"]:
                    if pos >= 4 and self.file_bytes[pos - 4 : pos] == sig:
                        skip = True
                        break
                    if pos + len(pattern) >= 4 and self.file_bytes[pos : pos + 4] in [
                        sig[: len(pattern)],
                        sig,
                    ]:
                        skip = True
                        break

                if skip:
                    pos += 1
                    continue

                # Apply fix using proper bytearray slicing
                self.file_bytes[pos : pos + len(pattern)] = replacement
                count += 1
                pos += len(replacement)

            if count > 0:
                logger.info("Fixed %s instances of %s corruption", count, pattern_name)
                self.stats["corruption_repairs"] += count

    @circuit_breaker(
        failure_threshold=3,
        timeout=30.0,
        expected_exceptions=(struct.error, UnicodeDecodeError, ValueError),
    )
    # 2 minute timeout for scanning
    @with_timeout(120.0)
    def _scan_all_blocks(self) -> None:
        """Scan file for all block signatures."""
        logger.info("Scanning for block signatures")
        logger.debug("File size: %s bytes", self.file_size)

        # First check what signatures exist in the file
        basic_sigs = [b"HDR*", b"NOD*", b"ENT*", b"DAT*", b"FRE*"]
        for sig in basic_sigs:
            pos = self.file_bytes.find(sig)
            if pos != -1:
                logger.debug("Found %s at offset %s", sig, pos)

        # Combine ASCII and Unicode signatures
        all_sigs = {}
        for block_type, sig in SIGNATURES.items():
            all_sigs[f"{block_type}_ASCII"] = (sig, False)
        for block_type, sig in UNICODE_SIGNATURES.items():
            all_sigs[f"{block_type}_UNICODE"] = (sig, True)

        logger.debug("Looking for signatures: %s", list(all_sigs.keys()))
        logger.debug("SIGNATURES dict: %s", SIGNATURES)
        logger.debug("UNICODE_SIGNATURES dict: %s", UNICODE_SIGNATURES)

        # Scan file
        for sig_name, (signature, is_unicode) in all_sigs.items():
            block_type = sig_name.split("_")[0]

            pos = 0
            while pos < self.file_size - len(signature):
                pos = self.file_bytes.find(signature, pos)
                if pos == -1:
                    break

                logger.debug("Found %s at offset %s", sig_name, pos)

                # Try to determine block size
                block_size = self._detect_block_size(pos)

                # Create recovered block
                block = RecoveredBlock(
                    offset=pos,
                    size=block_size,
                    block_type=block_type,
                    is_unicode=is_unicode,
                    data=self.file_bytes[pos : pos + block_size],
                )

                self.recovered_blocks.append(block)
                self.block_map[block_type].append(block)
                self.stats["blocks_found"] += 1

                # Move past this block
                pos += max(len(signature), 4)

        logger.info("Found %s blocks", self.stats["blocks_found"])

    def _detect_block_size(self, offset: int) -> int:
        """Detect the likely block size at given offset.

        Args:
            offset: Starting offset of block

        Returns:
            Detected or default block size
        """
        # Look for next block signature
        min_next_offset = self.file_size

        for sig in list(SIGNATURES.values()) + list(UNICODE_SIGNATURES.values()):
            next_pos = self.file_bytes.find(sig, offset + len(sig))
            if next_pos != -1 and next_pos < min_next_offset:
                min_next_offset = next_pos

        if min_next_offset < self.file_size:
            # Found next block
            detected_size = min_next_offset - offset

            # Align to common block sizes
            for block_size in self.BLOCK_SIZES:
                if detected_size <= block_size:
                    return block_size

            return detected_size

        # Default to standard block size
        return BLOCK_SIZE

    def _reconstruct_header(self) -> HeaderClass | None:
        """Reconstruct or repair the file header.

        Returns:
            Reconstructed header or None
        """
        logger.info("Attempting header reconstruction")

        # Look for HDR blocks
        hdr_blocks = self.block_map["HDR"]

        if hdr_blocks:
            # Try to parse existing header
            for block in hdr_blocks:
                try:
                    header = self._parse_header_block(block)
                    if header:
                        logger.info("Successfully parsed existing header")
                        return header
                except Exception as e:
                    logger.debug("Failed to parse header at %s: %s", block.offset, e)

        # Reconstruct header from file analysis
        logger.info("Reconstructing header from file analysis")

        # Detect unicode from blocks
        is_unicode = self._detect_unicode_encoding()

        # Find first NOD block
        first_nod_offset = 0
        if self.block_map["NOD"]:
            first_nod_offset = min(block.offset for block in self.block_map["NOD"])

        # Create synthetic header with required parameters
        header = HeaderClass(
            hdr_str="HDR*",
            pbl_name_str="recovered.pbl",
            build_datetime_str="",
            create_timestamp_dt=None,
            dep_lower_offset_int=0,
            dep_upper_offset_int=0,
            scc_data_offset_int=0,
            reserved_int=0,
            is_unicode=is_unicode,
            first_nod_offset=first_nod_offset or 1024,  # Default
            file_signature_bytes=b"",
        )
        header.file_size = self.file_size

        # Store block size separately
        self.block_size = self._detect_common_block_size()

        logger.info(
            "Reconstructed header: unicode=%s, first_nod=%s, block_size=%s",
            is_unicode,
            first_nod_offset,
            self.block_size,
        )

        return header

    def _detect_unicode_encoding(self) -> bool:
        """Detect if file uses Unicode encoding.

        Returns:
            True if Unicode, False if ASCII
        """
        unicode_blocks = sum(1 for block in self.recovered_blocks if block.is_unicode)
        ascii_blocks = sum(1 for block in self.recovered_blocks if not block.is_unicode)

        return unicode_blocks > ascii_blocks

    def _detect_common_block_size(self) -> int:
        """Detect the most common block size.

        Returns:
            Most common block size
        """
        if not self.recovered_blocks:
            return BLOCK_SIZE

        # Count block size frequencies
        size_counts = {}
        for block in self.recovered_blocks:
            size = block.size
            # Round to nearest standard size
            for std_size in self.BLOCK_SIZES:
                if abs(size - std_size) < 100:
                    size = std_size
                    break
            size_counts[size] = size_counts.get(size, 0) + 1

        # Return most common
        return max(size_counts.items(), key=lambda x: x[1])[0]

    def _parse_header_block(self, block: RecoveredBlock) -> HeaderClass | None:
        """Parse a header block.

        Args:
            block: Header block to parse

        Returns:
            Parsed header or None
        """
        # This would use actual header parsing logic
        # Simplified for now - create header with required parameters
        header = HeaderClass(
            hdr_str="HDR*",
            pbl_name_str="recovered.pbl",
            build_datetime_str="",
            create_timestamp_dt=None,
            dep_lower_offset_int=0,
            dep_upper_offset_int=0,
            scc_data_offset_int=0,
            reserved_int=0,
            is_unicode=block.is_unicode,
            first_nod_offset=1024,  # Default, will be updated below
            file_signature_bytes=b"",
        )

        # Extract key offsets from header data
        if len(block.data) >= 16:
            # Simplified parsing - actual implementation would decode properly
            header.first_nod_offset = struct.unpack("<I", block.data[8:12])[0]

        header.file_size = self.file_size

        return header

    def _recover_nod_blocks(self) -> None:
        """Recover and parse NOD (node) blocks."""
        logger.info("Recovering %s NOD blocks", len(self.block_map["NOD"]))

        for nod_block in self.block_map["NOD"]:
            try:
                # Parse NOD structure
                node_entries = self._parse_nod_block(nod_block)

                # Store entries
                nod_block.metadata["entries"] = node_entries
                nod_block.metadata["entry_count"] = len(node_entries)

                self.stats["blocks_recovered"] += 1

                logger.debug(
                    "Recovered NOD at %s with %s entries",
                    nod_block.offset,
                    len(node_entries),
                )

            except Exception as e:
                logger.warning("Failed to parse NOD at %s: %s", nod_block.offset, e)

    def _parse_nod_block(self, block: RecoveredBlock) -> list[dict]:
        """Parse a NOD block to extract entry information.

        Args:
            block: NOD block to parse

        Returns:
            List of entry metadata
        """
        entries = []

        # Skip signature
        offset = 4

        # Read entry count (simplified)
        if len(block.data) >= offset + 4:
            entry_count = struct.unpack("<I", block.data[offset : offset + 4])[0]
            offset += 4

            # Sanity check
            if 0 < entry_count < 1000:
                # Parse each entry reference
                for i in range(min(entry_count, 100)):  # Limit for safety
                    if offset + 8 > len(block.data):
                        break

                    entry_info = {
                        "index": i,
                        "offset": struct.unpack("<I", block.data[offset : offset + 4])[
                            0
                        ],
                        "size": struct.unpack(
                            "<I", block.data[offset + 4 : offset + 8]
                        )[0],
                    }
                    entries.append(entry_info)
                    offset += 8

        return entries

    def _match_ent_dat_blocks(self) -> None:
        """Match ENT entries with their corresponding DAT blocks."""
        logger.info("Matching ENT and DAT blocks")

        for ent_block in self.block_map["ENT"]:
            try:
                # Parse ENT block
                entry_info = self._parse_ent_block(ent_block)
                if not entry_info:
                    continue

                # Find corresponding DAT block
                dat_offset = entry_info.get("data_offset")
                if dat_offset:
                    # Look for DAT block at or near this offset
                    dat_block = self._find_dat_block_near(dat_offset)
                    if dat_block:
                        # Link them
                        ent_block.metadata["dat_block"] = dat_block
                        dat_block.metadata["ent_block"] = ent_block
                        dat_block.metadata["object_name"] = entry_info.get(
                            "name", "unknown"
                        )

                        logger.debug(
                            "Matched ENT '%s' with DAT at %s",
                            entry_info.get("name"),
                            dat_block.offset,
                        )

            except Exception as e:
                logger.warning("Failed to match ENT at %s: %s", ent_block.offset, e)

    def _parse_ent_block(self, block: RecoveredBlock) -> dict | None:
        """Parse an ENT block to extract entry metadata.

        Args:
            block: ENT block to parse

        Returns:
            Entry metadata or None
        """
        try:
            # Skip signature
            offset = 4

            # Read entry info (simplified parsing)
            info = {}

            # Read object name with improved PowerBuilder decoding
            if block.is_unicode:
                # Unicode name
                name_end = block.data.find(b"\x00\x00", offset)
                if name_end > offset and name_end % 2 == 0:
                    from src.extract.utils.binary import decode_powerbuilder_name

                    info["name"] = decode_powerbuilder_name(
                        block.data[offset:name_end], is_unicode_context=True
                    )
                    offset = name_end + 2
            else:
                # ASCII name
                name_end = block.data.find(b"\x00", offset)
                if name_end > offset:
                    from src.extract.utils.binary import decode_powerbuilder_name

                    info["name"] = decode_powerbuilder_name(
                        block.data[offset:name_end], is_unicode_context=False
                    )
                    offset = name_end + 1

            # Read offsets (simplified)
            if offset + 8 <= len(block.data):
                info["data_offset"] = struct.unpack(
                    "<I", block.data[offset : offset + 4]
                )[0]
                info["data_size"] = struct.unpack(
                    "<I", block.data[offset + 4 : offset + 8]
                )[0]

            return info

        except Exception:
            return None

    def _find_dat_block_near(
        self, target_offset: int, tolerance: int = 1024
    ) -> RecoveredBlock | None:
        """Find a DAT block near the target offset.

        Args:
            target_offset: Target offset to search near
            tolerance: Search tolerance in bytes

        Returns:
            Matching DAT block or None
        """
        for dat_block in self.block_map["DAT"]:
            if abs(dat_block.offset - target_offset) <= tolerance:
                return dat_block
        return None

    def _extract_validated_objects(self) -> None:
        """Extract and validate recovered objects."""
        logger.info("Extracting validated objects")

        # Process matched ENT-DAT pairs
        for dat_block in self.block_map["DAT"]:
            if "ent_block" in dat_block.metadata:
                self._extract_object_from_blocks(
                    dat_block.metadata["ent_block"], dat_block
                )

        # Process standalone DAT blocks with content
        for dat_block in self.block_map["DAT"]:
            if "ent_block" not in dat_block.metadata:
                self._extract_standalone_dat(dat_block)

    def _extract_object_from_blocks(
        self, ent_block: RecoveredBlock, dat_block: RecoveredBlock
    ) -> None:
        """Extract an object from matched ENT-DAT blocks.

        Args:
            ent_block: Entry block
            dat_block: Data block
        """
        try:
            object_name = dat_block.metadata.get(
                "object_name", f"recovered_{dat_block.offset:08x}"
            )

            # Extract content
            content = self._extract_dat_content(dat_block)
            if not content:
                return

            # Validate content
            if self._validate_object_content(content):
                # Save object securely
                sanitized_name = sanitize_filename(f"{object_name}.txt")
                output_file = self.recovery_dir / sanitized_name
                safe_write_file(output_file, content, self.recovery_dir)

                self.recovered_objects[object_name] = {
                    "ent_offset": ent_block.offset,
                    "dat_offset": dat_block.offset,
                    "size": len(content),
                    "type": self._detect_object_type(content),
                }

                self.stats["objects_recovered"] += 1
                logger.info("Recovered object '%s'", object_name)

        except Exception as e:
            logger.warning("Failed to extract object from blocks: %s", e)

    def _extract_standalone_dat(self, dat_block: RecoveredBlock) -> None:
        """Extract content from a standalone DAT block.

        Args:
            dat_block: DAT block without matching ENT
        """
        try:
            content = self._extract_dat_content(dat_block)
            if content and self._validate_object_content(content):
                # Determine object type from content
                obj_type = self._detect_object_type(content)

                # Generate name
                object_name = f"orphaned_{obj_type}_{dat_block.offset:08x}"

                # Save securely
                sanitized_name = sanitize_filename(f"{object_name}.txt")
                output_file = self.recovery_dir / sanitized_name
                safe_write_file(output_file, content, self.recovery_dir)

                self.recovered_objects[object_name] = {
                    "dat_offset": dat_block.offset,
                    "size": len(content),
                    "type": obj_type,
                    "orphaned": True,
                }

                self.stats["objects_recovered"] += 1
                logger.info("Recovered orphaned object '%s'", object_name)

        except Exception as e:
            logger.debug("Failed to extract standalone DAT: %s", e)

    def _extract_dat_content(self, dat_block: RecoveredBlock) -> str | None:
        """Extract text content from a DAT block.

        Args:
            dat_block: DAT block to extract from

        Returns:
            Extracted text or None
        """
        # Skip signature and header
        data = dat_block.data[8:] if len(dat_block.data) > 8 else dat_block.data

        # Try various encodings
        for encoding in self.ENCODINGS:
            try:
                text = data.decode(encoding, errors="ignore")

                # Clean up
                text = text.replace("\x00", "")
                text = text.strip()

                # Validate
                if len(text) > 50 and text.count("\n") > 2:
                    return text

            except Exception:
                continue

        return None

    def _validate_object_content(self, content: str) -> bool:
        """Validate that content looks like valid PowerBuilder code.

        Args:
            content: Content to validate

        Returns:
            True if valid
        """
        if not content or len(content) < 50:
            logger.debug(
                "Content validation failed: too short (%s chars)",
                len(content) if content else 0,
            )
            return False

        # Check for PowerBuilder keywords
        pb_keywords = [
            "global",
            "type",
            "forward",
            "end",
            "function",
            "event",
            "variable",
            "constant",
            "return",
            "if",
            "then",
            "else",
        ]

        keyword_count = sum(1 for keyword in pb_keywords if keyword in content.lower())

        # Check for reasonable structure
        line_count = content.count("\n")
        null_count = content.count("\x00")
        has_structure = (
            line_count >= 2  # At least a few lines (reduced from 5)
            and keyword_count >= 1  # Has at least one PB keyword (reduced from 2)
            and null_count < len(content) // 100  # Not too much binary
        )

        if not has_structure:
            logger.debug(
                "Content validation failed: lines=%s, keywords=%s, nulls=%s, length=%s",
                line_count,
                keyword_count,
                null_count,
                len(content),
            )
            self.stats["validation_failures"] += 1
        else:
            logger.debug(
                "Content validation passed: lines=%s, keywords=%s",
                line_count,
                keyword_count,
            )

        return has_structure

    def _detect_object_type(self, content: str) -> str:
        """Detect the type of PowerBuilder object from content.

        Args:
            content: Object content

        Returns:
            Object type string
        """
        content_lower = content.lower()

        if "datawindow" in content_lower:
            return "datawindow"
        if "window" in content_lower and "type" in content_lower:
            return "window"
        if "global function" in content_lower:
            return "function"
        if "menu" in content_lower:
            return "menu"
        if "userobject" in content_lower:
            return "userobject"
        if "structure" in content_lower:
            return "structure"
        return "unknown"

    def _recover_orphaned_blocks(self) -> None:
        """Attempt to recover data from orphaned blocks."""
        logger.info("Recovering orphaned blocks")
        logger.info("Found %s FRE blocks to check", len(self.block_map["FRE"]))

        # Check FRE blocks - they might contain deleted but recoverable data
        for fre_block in self.block_map["FRE"]:
            self._check_fre_block_for_data(fre_block)

    def _check_fre_block_for_data(self, fre_block: RecoveredBlock) -> None:
        """Check if a FRE (free) block contains recoverable data.

        Args:
            fre_block: Free block to check
        """
        logger.debug(
            "Checking FRE block at offset %s, size %s", fre_block.offset, fre_block.size
        )

        # Free blocks might contain previously deleted objects
        # Look for PowerBuilder signatures within

        signatures = [
            b"$PBExportHeader$",
            b"global type",
            b"forward",
            b"type variables",
        ]

        for sig in signatures:
            pos = fre_block.data.find(sig)
            if pos != -1:
                # Found potential object in free block
                logger.info(
                    "Found potential object with signature '%s' in FRE block at %s + %s",
                    sig,
                    fre_block.offset,
                    pos,
                )

                # Create a pseudo-DAT block for extraction
                pseudo_dat = RecoveredBlock(
                    offset=fre_block.offset + pos,
                    size=len(fre_block.data) - pos,
                    block_type="DAT",
                    is_unicode=fre_block.is_unicode,
                    data=fre_block.data[pos:],
                )
                pseudo_dat.metadata["from_fre"] = True

                self._extract_standalone_dat(pseudo_dat)
                break
        else:
            logger.debug(
                "No PowerBuilder signatures found in FRE block at %s", fre_block.offset
            )

    def _generate_recovery_report(self) -> None:
        """Generate a detailed recovery report."""
        report_path = self.recovery_dir / "recovery_report.txt"

        # Build report content
        report_lines = []
        report_lines.append("Enhanced Recovery Report\n")
        report_lines.append("=" * 80 + "\n\n")

        report_lines.append("Recovery Statistics:\n")
        report_lines.append(f"  Blocks found: {self.stats['blocks_found']}\n")
        report_lines.append(f"  Blocks recovered: {self.stats['blocks_recovered']}\n")
        report_lines.append(f"  Objects recovered: {self.stats['objects_recovered']}\n")
        report_lines.append(
            f"  Corruption repairs: {self.stats['corruption_repairs']}\n"
        )
        report_lines.append(
            f"  Validation failures: {self.stats['validation_failures']}\n\n"
        )

        report_lines.append("Block Summary:\n")
        for block_type, blocks in self.block_map.items():
            report_lines.append(f"  {block_type}: {len(blocks)} blocks\n")
        report_lines.append("\n")

        report_lines.append("Recovered Objects:\n")
        for obj_name, obj_info in sorted(self.recovered_objects.items()):
            report_lines.append(f"  {obj_name}:\n")
            report_lines.append(f"    Type: {obj_info['type']}\n")
            report_lines.append(f"    Size: {obj_info['size']} bytes\n")
            if obj_info.get("orphaned"):
                report_lines.append("    Status: Orphaned (no ENT block)\n")
            report_lines.append("\n")

        report_lines.append("Recovery Methods Used:\n")
        report_lines.append("  - Corruption pattern fixing\n")
        report_lines.append("  - Block signature scanning\n")
        report_lines.append("  - Header reconstruction\n")
        report_lines.append("  - NOD block recovery\n")
        report_lines.append("  - ENT-DAT matching\n")
        report_lines.append("  - Orphaned block recovery\n")
        report_lines.append("  - FRE block analysis\n")

        # Write report securely
        report_content = "".join(report_lines)
        safe_write_file(report_path, report_content, self.recovery_dir)

        logger.info("Recovery report saved to %s", report_path)

    def _update_progress(self, message: str, percent: float) -> None:
        """Update progress callback if available.

        Args:
            message: Progress message
            percent: Progress percentage (0-100)
        """
        if self.progress_callback:
            try:
                self.progress_callback(message, percent)
            except Exception as e:
                logger.debug("Progress callback error: %s", e)

    def _reconstruct_from_fragments(self, object_name: str) -> bytes | None:
        """Attempt to reconstruct an object from fragments.

        Args:
            object_name: Name of object to reconstruct

        Returns:
            Reconstructed data or None
        """
        logger.info("Attempting fragment reconstruction for %s", object_name)

        fragments = self.fragments.get(object_name, [])
        if not fragments:
            return None

        # Sort fragments by size (larger fragments first)
        fragments.sort(key=len, reverse=True)

        # Try to piece together fragments
        reconstructed = bytearray()
        used_fragments = set()

        for i, fragment in enumerate(fragments):
            if i in used_fragments:
                continue

            # Check if fragment overlaps with existing data
            overlap_found = False
            for offset in range(
                max(0, len(reconstructed) - len(fragment) + 1), len(reconstructed)
            ):
                if reconstructed[offset:].startswith(
                    fragment[: len(reconstructed) - offset]
                ):
                    # Found overlap, merge
                    reconstructed.extend(fragment[len(reconstructed) - offset :])
                    used_fragments.add(i)
                    overlap_found = True
                    break

            if not overlap_found and len(reconstructed) == 0:
                # First fragment
                reconstructed.extend(fragment)
                used_fragments.add(i)

        # Calculate confidence score
        coverage = len(used_fragments) / len(fragments) if fragments else 0
        self.confidence_scores[object_name] = coverage

        logger.info(
            "Reconstructed %s bytes from %s/%s fragments (confidence: %.1f%%)",
            len(reconstructed),
            len(used_fragments),
            len(fragments),
            coverage * 100,
        )

        return bytes(reconstructed) if reconstructed else None

    def _calculate_integrity_score(self, data: bytes, block_type: str) -> float:
        """Calculate integrity score for recovered data.

        Args:
            data: Data to check
            block_type: Type of block

        Returns:
            Integrity score (0.0 to 1.0)
        """
        score = 1.0

        # Check for null bytes (shouldn't be too many)
        null_ratio = data.count(b"\x00") / len(data) if data else 0
        if null_ratio > 0.5:
            score *= 1.0 - null_ratio

        # Check for printable ASCII ratio
        printable_count = sum(1 for b in data if 32 <= b <= 126)
        printable_ratio = printable_count / len(data) if data else 0

        if block_type in ["ENT", "NOD"] and printable_ratio < 0.3:
            score *= printable_ratio * 3  # These should have more text

        # Check for repeated patterns (indicates corruption)
        if len(data) >= 8:
            pattern_length = 4
            repeated_patterns = 0
            for i in range(0, len(data) - pattern_length * 2, pattern_length):
                if (
                    data[i : i + pattern_length]
                    == data[i + pattern_length : i + pattern_length * 2]
                ):
                    repeated_patterns += 1

            repeat_ratio = repeated_patterns / (len(data) // pattern_length)
            if repeat_ratio > 0.3:
                score *= 1.0 - repeat_ratio

        return max(0.0, min(1.0, score))

    def _collect_fragments(self, object_name: str) -> None:
        """Collect fragments that might belong to an object.

        Args:
            object_name: Object name to search for
        """
        logger.debug("Collecting fragments for %s", object_name)

        # Search for object name in file
        name_bytes = object_name.encode("latin1", errors="ignore")
        name_unicode = object_name.encode("utf-16-le", errors="ignore")

        search_patterns = [name_bytes, name_unicode]

        for pattern in search_patterns:
            pos = 0
            while pos < self.file_size:
                pos = self.file_bytes.find(pattern, pos)
                if pos == -1:
                    break

                # Extract fragment around the name
                start = max(0, pos - 1024)
                end = min(self.file_size, pos + len(pattern) + BUFFER_SIZE)
                fragment = bytes(self.file_bytes[start:end])

                if object_name not in self.fragments:
                    self.fragments[object_name] = []
                self.fragments[object_name].append(fragment)

                pos += 1

        if object_name in self.fragments:
            logger.debug(
                "Found %s fragments for %s",
                len(self.fragments[object_name]),
                object_name,
            )

    def recover_specific_object(self, object_name: str) -> bool:
        """Attempt to recover a specific object by name.

        Args:
            object_name: Name of object to recover

        Returns:
            True if recovered
        """
        logger.info("Attempting targeted recovery of %s", object_name)

        # First, collect fragments
        self._collect_fragments(object_name)

        # Try fragment reconstruction
        reconstructed = self._reconstruct_from_fragments(object_name)

        if reconstructed:
            # Validate and save
            integrity = self._calculate_integrity_score(reconstructed, "DAT")
            logger.info("Integrity score for %s: %.2f", object_name, integrity)

            if integrity > 0.3:  # Lower threshold for desperate recovery
                output_path = self.recovery_dir / f"{object_name}_reconstructed"
                output_path.write_bytes(reconstructed)

                self.recovered_objects[object_name] = {
                    "type": "reconstructed",
                    "size": len(reconstructed),
                    "integrity": integrity,
                    "confidence": self.confidence_scores.get(object_name, 0),
                }

                logger.info(
                    "Successfully recovered %s (integrity: %.2f)",
                    object_name,
                    integrity,
                )
                return True

        logger.warning("Failed to recover %s", object_name)
        return False
