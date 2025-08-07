"""Fix for DataWindow extraction corruption where asterisks are inserted into content.

This module provides functions to detect and clean corrupted DataWindow extractions
where DAT block signatures leak into the extracted content.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
                cleaned_parts: Any = []
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
