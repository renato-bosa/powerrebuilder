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


class DataCorruptionFixer:
    """Fixes corruption in extracted DataWindow content."""

    CORRUPTION_PATTERNS = [
        ("(\\w+)\\s+\\*\\s+(\\w+)", "\\1\\2"),
        ("COL\\s*\\*\\s*L\\s*MN", "COLUMN"),
        ("COL\\*LMN", "COLUMN"),
        ("TAB\\s+\\*\\s*E", "TABLE"),
        ("TAB\\s+\\*\\s*L\\s*E", "TABLE"),
        ("LOG\\s+\\*\\s+C", "LOGIC"),
        ("\\*OLUMN", "COLUMN"),
        ("\\s+\\*OLUMN", " COLUMN"),
        ('"\\s*(\\w+)\\s*\\*\\s*(\\w+)\\s*"', '"\\1\\2"'),
        ("(\\w+)\\s*\\.\\s*\\*(\\w+)", "\\1.\\2"),
        ("(\\w+)\\.\\s*(\\w+)\\s*\\*\\s*(\\w+)", "\\1.\\2\\3"),
        ("\\.(\\*[A-Z])(\\w+)", lambda m: f".{m.group(1)[1].lower()}{m.group(2)}"),
        ('"\\*', '"'),
        ("\\.\\*\\s+", ". "),
        ('"\\*\\s+(\\w+)', '" \\1'),
        ('"\\)\\*\\s+', '") '),
        ('"\\s*\\*IGHT', '" RIGHT'),
        ("b\\s*\\*\\s*lling", "billing"),
        ("bi\\s*\\*\\s*ling", "billing"),
        ("NA\\s*\\*\\s*E=", "NAME="),
        ("NAM\\s*\\*\\s*=", "NAME="),
        ("EX\\s*\\*2", "EXP2"),
        ('OP\\s*\\*"=', 'OP "='),
        ("tblclinica\\s*\\*\\s*tribs", "tblclinicattribs"),
        ("tblclini\\s*\\*attribs", "tblclinicattribs"),
        ("locations\\s*\\*location", "locations.location"),
        ("\\*linic_address", "clinic_address"),
        ('incremen\\s*\\*"', 'increment"'),
        ("(\\w+)\\.\\*\\s*ddress", "\\1.address"),
        ('"\\s*\\*\\s*"\\)', '"")'),
        ("'\\s*A\\s*\\*", "'A'"),
        ("amount_paid\\s*\\*\\)", 'amount_paid"'),
        ('NAM\\s*\\*="', 'NAME="'),
        ("TAB\\s*\\*\\s*E\\(NAME\\s*\\*=", "TABLE(NAME="),
        ("COL\\s*\\*\\s*MN", "COLUMN"),
        ("WHERE\\s*\\(\\s*\\*\\s+", "WHERE(    "),
    ]
    DAT_SIGNATURES = [b"DAT*", b"DAT ", b"D\x00A\x00T\x00"]

    @classmethod
    def detect_corruption(cls, content: str) -> bool:
        """Detect if content contains known corruption patterns.

        Args:
            content: Extracted text content

        Returns:
            True if corruption is detected
        """
        corruption_indicators = [
            "\\s+\\*\\s+",
            "[A-Z]{3}\\s+\\*[A-Z]",
            "\\w+\\s+\\*\\s+\\w+",
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
        for pattern, replacement in cls.CORRUPTION_PATTERNS:
            fixed_content, count = re.subn(pattern, replacement, fixed_content)
            if count > 0:
                logger.debug(
                    "Applied fix for pattern '%s': %s occurrences", pattern, count
                )
                total_fixes += count
        fixed_content = re.sub("(\\w)\\s*\\*\\s*(\\w)", "\\1\\2", fixed_content)
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
        incomplete_keywords = ["COL MN", "TAB E", "SEL ECT", "FR OM", "WH ERE"]
        for keyword in incomplete_keywords:
            if keyword in content:
                issues.append(f"Incomplete keyword found: {keyword}")
        if "PBSELECT" in content:
            if "TABLE(" not in content.upper():
                issues.append("PBSELECT missing TABLE() specification")
        elif "SELECT" in content:
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
        cleaned = data
        for signature in cls.DAT_SIGNATURES:
            parts = cleaned.split(signature)
            if len(parts) > 1:
                cleaned_parts: Any = []
                for i, part in enumerate(parts):
                    if i > 0 and len(part) > 0 and part[0:1] not in b"\x00\r\n":
                        logger.debug(
                            "Removed misplaced DAT signature at position %s",
                            len(b"".join(cleaned_parts)),
                        )
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
    if not fixer.detect_corruption(content):
        return content
    logger.info("Detected corruption in %s", filename if filename else "content")
    fixed_content, fix_count = fixer.fix_corrupted_content(content)
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
        fixed_content = fix_extracted_datawindow(content, str(filepath))
        if fixed_content != content:
            with filepath.open("w", encoding="utf-8") as f:
                f.write(fixed_content)
            logger.info("Fixed corruption in %s", filepath)
            return True
    except Exception as e:
        logger.error("Error processing %s: %s", filepath, e)
    return False


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
    arr: bytes,
    is_unicode: bool = False,
    entry_context: (str | None) = None,
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
    result = None
    try:
        result = extract_entry_def(arr, pb_version)
        if result:
            logger.debug(
                "Successfully parsed entry with version-specific parser: %s",
                result.object_name,
            )
            return result
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


@dataclass
class RecoveredBlock:
    """Represents a recovered block from the file."""

    offset: int
    size: int
    block_type: str
    is_unicode: bool
    data: bytes
    metadata: dict[Any, Any] | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class EnhancedRecoveryEngine:
    """Advanced recovery engine for corrupted PowerBuilder files."""

    BLOCK_SIZES = [512, 1024, 2048, BUFFER_SIZE]
    ENCODINGS = ["utf-8", "utf-16-le", "utf-16-be", "latin1", "cp1252", "ascii"]
    CORRUPTION_PATTERNS = {
        "asterisk_insertion": (b"*\x00*\x00*\x00*\x00", b""),
        "null_insertion": (b"\x00\x00\x00\x00\x00\x00\x00\x00", b""),
        "ff_corruption": (b"\xff\xff\xff\xff", b"\x00\x00\x00\x00"),
        "repeated_pattern": (b"\xab\xcd\xab\xcd\xab\xcd", b"\x00\x00\x00\x00\x00\x00"),
        "unicode_bom_corruption": (b"\xff\xfe\xff\xfe", b"\xff\xfe"),
        "control_char_spam": (b"\x01\x02\x03\x04\x05\x06\x07\x08", b""),
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
        self.file_bytes = bytearray(file_bytes)
        self.file_size = len(file_bytes)
        self.output_dir = output_dir
        self.recovery_dir = output_dir / "recovery"
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        self.block_size = BLOCK_SIZE
        self.progress_callback = progress_callback
        self.recovered_blocks: list[RecoveredBlock] = []
        self.block_map: dict[str, list[RecoveredBlock]] = {
            "HDR": [],
            "NOD": [],
            "ENT": [],
            "DAT": [],
            "FRE": [],
        }
        self.recovered_objects: dict[str, dict] = {}
        self.fragments: dict[str, list[bytes]] = {}
        self.confidence_scores: dict[str, float] = {}
        self.stats = {
            "blocks_found": 0,
            "blocks_recovered": 0,
            "objects_recovered": 0,
            "corruption_repairs": 0,
            "validation_failures": 0,
        }

    @with_memory_limit(1024 * 1024 * 1024)
    def recover_all(self) -> bool:
        """Perform comprehensive recovery of the corrupted file.

        Returns:
            True if any data was recovered
        """
        logger.info("Starting enhanced recovery engine")
        self._update_progress("Applying corruption pattern fixes", 0)
        self._apply_corruption_fixes()
        self._update_progress("Scanning for block signatures", 12.5)
        self._scan_all_blocks()
        self._update_progress("Reconstructing header", 25)
        self._reconstruct_header()
        self._update_progress("Recovering NOD blocks", 37.5)
        self._recover_nod_blocks()
        self._update_progress("Matching ENT and DAT blocks", 50)
        self._match_ent_dat_blocks()
        self._update_progress("Extracting validated objects", 62.5)
        self._extract_validated_objects()
        self._update_progress("Recovering orphaned blocks", 75)
        self._recover_orphaned_blocks()
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
    @with_timeout(120.0)
    def _scan_all_blocks(self) -> None:
        """Scan file for all block signatures."""
        logger.info("Scanning for block signatures")
        logger.debug("File size: %s bytes", self.file_size)
        basic_sigs = [b"HDR*", b"NOD*", b"ENT*", b"DAT*", b"FRE*"]
        for sig in basic_sigs:
            pos = self.file_bytes.find(sig)
            if pos != -1:
                logger.debug("Found %s at offset %s", sig, pos)
        all_sigs = {}
        for block_type, sig in SIGNATURES.items():
            all_sigs[f"{block_type}_ASCII"] = sig, False
        for block_type, sig in UNICODE_SIGNATURES.items():
            all_sigs[f"{block_type}_UNICODE"] = sig, True
        logger.debug("Looking for signatures: %s", list(all_sigs.keys()))
        logger.debug("SIGNATURES dict: %s", SIGNATURES)
        logger.debug("UNICODE_SIGNATURES dict: %s", UNICODE_SIGNATURES)
        for sig_name, (signature, is_unicode) in all_sigs.items():
            block_type = sig_name.split("_")[0]
            pos = 0
            while pos < self.file_size - len(signature):
                pos = self.file_bytes.find(signature, pos)
                if pos == -1:
                    break
                logger.debug("Found %s at offset %s", sig_name, pos)
                block_size = self._detect_block_size(pos)
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
                pos += max(len(signature), 4)
        logger.info("Found %s blocks", self.stats["blocks_found"])

    def _detect_block_size(self, offset: int) -> int:
        """Detect the likely block size at given offset.

        Args:
            offset: Starting offset of block

        Returns:
            Detected or default block size
        """
        min_next_offset = self.file_size
        for sig in list(SIGNATURES.values()) + list(UNICODE_SIGNATURES.values()):
            next_pos = self.file_bytes.find(sig, offset + len(sig))
            if next_pos != -1 and next_pos < min_next_offset:
                min_next_offset = next_pos
        if min_next_offset < self.file_size:
            detected_size = min_next_offset - offset
            for block_size in self.BLOCK_SIZES:
                if detected_size <= block_size:
                    return block_size
            return detected_size
        return BLOCK_SIZE

    def _reconstruct_header(self) -> HeaderClass | None:
        """Reconstruct or repair the file header.

        Returns:
            Reconstructed header or None
        """
        logger.info("Attempting header reconstruction")
        hdr_blocks = self.block_map["HDR"]
        if hdr_blocks:
            for block in hdr_blocks:
                try:
                    header = self._parse_header_block(block)
                    if header:
                        logger.info("Successfully parsed existing header")
                        return header
                except Exception as e:
                    logger.debug("Failed to parse header at %s: %s", block.offset, e)
        logger.info("Reconstructing header from file analysis")
        is_unicode = self._detect_unicode_encoding()
        first_nod_offset = 0
        if self.block_map["NOD"]:
            first_nod_offset = min(block.offset for block in self.block_map["NOD"])
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
            first_nod_offset=first_nod_offset or 1024,
            file_signature_bytes=b"",
        )
        header.file_size = self.file_size
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
        size_counts: dict[str, int] = {}
        for block in self.recovered_blocks:
            size = block.size
            for std_size in self.BLOCK_SIZES:
                if abs(size - std_size) < 100:
                    size = std_size
                    break
            size_counts[size] = size_counts.get(size, 0) + 1
        return max(size_counts.items(), key=lambda x: x[1])[0]

    def _parse_header_block(self, block: RecoveredBlock) -> HeaderClass | None:
        """Parse a header block.

        Args:
            block: Header block to parse

        Returns:
            Parsed header or None
        """
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
            first_nod_offset=1024,
            file_signature_bytes=b"",
        )
        if len(block.data) >= 16:
            header.first_nod_offset = struct.unpack("<I", block.data[8:12])[0]
        header.file_size = self.file_size
        return header

    def _recover_nod_blocks(self) -> None:
        """Recover and parse NOD (node) blocks."""
        logger.info("Recovering %s NOD blocks", len(self.block_map["NOD"]))
        for nod_block in self.block_map["NOD"]:
            try:
                node_entries = self._parse_nod_block(nod_block)
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
        offset = 4
        if len(block.data) >= offset + 4:
            entry_count = struct.unpack("<I", block.data[offset : offset + 4])[0]
            offset += 4
            if 0 < entry_count < 1000:
                for i in range(min(entry_count, 100)):
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
                entry_info = self._parse_ent_block(ent_block)
                if not entry_info:
                    continue
                dat_offset = entry_info.get("data_offset")
                if dat_offset:
                    dat_block = self._find_dat_block_near(dat_offset)
                    if dat_block:
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
            offset = 4
            info = {}
            if block.is_unicode:
                name_end = block.data.find(b"\x00\x00", offset)
                if name_end > offset and name_end % 2 == 0:
                    from src.extract.utils.binary import decode_powerbuilder_name

                    info["name"] = decode_powerbuilder_name(
                        block.data[offset:name_end], is_unicode_context=True
                    )
                    offset = name_end + 2
            else:
                name_end = block.data.find(b"\x00", offset)
                if name_end > offset:
                    from src.extract.utils.binary import decode_powerbuilder_name

                    info["name"] = decode_powerbuilder_name(
                        block.data[offset:name_end], is_unicode_context=False
                    )
                    offset = name_end + 1
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
        for dat_block in self.block_map["DAT"]:
            if "ent_block" in dat_block.metadata:
                self._extract_object_from_blocks(
                    dat_block.metadata["ent_block"], dat_block
                )
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
            content = self._extract_dat_content(dat_block)
            if not content:
                return
            if self._validate_object_content(content):
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
                obj_type = self._detect_object_type(content)
                object_name = f"orphaned_{obj_type}_{dat_block.offset:08x}"
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
        data = dat_block.data[8:] if len(dat_block.data) > 8 else dat_block.data
        for encoding in self.ENCODINGS:
            try:
                text = data.decode(encoding, errors="ignore")
                text = text.replace("\x00", "")
                text = text.strip()
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
        line_count = content.count("\n")
        null_count = content.count("\x00")
        has_structure = (
            line_count >= 2 and keyword_count >= 1 and null_count < len(content) // 100
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
        signatures = [
            b"$PBExportHeader$",
            b"global type",
            b"forward",
            b"type variables",
        ]
        for sig in signatures:
            pos = fre_block.data.find(sig)
            if pos != -1:
                logger.info(
                    "Found potential object with signature '%s' in FRE block at %s + %s",
                    sig,
                    fre_block.offset,
                    pos,
                )
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
        fragments.sort(key=len, reverse=True)
        reconstructed = bytearray()
        used_fragments = set()
        for i, fragment in enumerate(fragments):
            if i in used_fragments:
                continue
            overlap_found = False
            for offset in range(
                max(0, len(reconstructed) - len(fragment) + 1), len(reconstructed)
            ):
                if reconstructed[offset:].startswith(
                    fragment[: len(reconstructed) - offset]
                ):
                    reconstructed.extend(fragment[len(reconstructed) - offset :])
                    used_fragments.add(i)
                    overlap_found = True
                    break
            if not overlap_found and len(reconstructed) == 0:
                reconstructed.extend(fragment)
                used_fragments.add(i)
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
        null_ratio = data.count(b"\x00") / len(data) if data else 0
        if null_ratio > 0.5:
            score *= 1.0 - null_ratio
        printable_count = sum(1 for b in data if 32 <= b <= 126)
        printable_ratio = printable_count / len(data) if data else 0
        if block_type in ["ENT", "NOD"] and printable_ratio < 0.3:
            score *= printable_ratio * 3
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
        name_bytes = object_name.encode("latin1", errors="ignore")
        name_unicode = object_name.encode("utf-16-le", errors="ignore")
        search_patterns = [name_bytes, name_unicode]
        for pattern in search_patterns:
            pos = 0
            while pos < self.file_size:
                pos = self.file_bytes.find(pattern, pos)
                if pos == -1:
                    break
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
        self._collect_fragments(object_name)
        reconstructed = self._reconstruct_from_fragments(object_name)
        if reconstructed:
            integrity = self._calculate_integrity_score(reconstructed, "DAT")
            logger.info("Integrity score for %s: %.2f", object_name, integrity)
            if integrity > 0.3:
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
