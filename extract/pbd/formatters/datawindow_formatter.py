"""DataWindow-specific formatting and extraction utilities.

This module provides specialized handling for PowerBuilder DataWindow objects,
which contain SQL queries, column definitions, and display formatting rather
than executable P-code.
"""


import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class DataWindowFormatter:
    """Formatter for DataWindow objects extracted from PBD files."""

    # Common DataWindow markers
    DW_MARKERS = {
        "release": re.compile(r"release\s+\d+"), "datawindow": re.compile(r"datawindow\s*\("), "table": re.compile(r"table\s*\("), "column": re.compile(r"column\s*="), "retrieve": re.compile(r"retrieve\s*="), "pbselect": re.compile(r"PBSELECT"), "processing": re.compile(r"processing\s*="), "header": re.compile(r"header\s*\("), "detail": re.compile(r"detail\s*\("), "footer": re.compile(r"footer\s*\("), "summary": re.compile(r"summary\s*\("), }

    @classmethod
    def format_datawindow_syntax(cls, raw_syntax: str, object_name: str) -> str:


        """Format extracted DataWindow syntax for readability.

        Args:
            raw_syntax: Raw extracted DataWindow syntax
            object_name: Name of the DataWindow object

        Returns:
            Formatted DataWindow syntax
        """
        if not raw_syntax:
            return ""

        # Add header comment
        formatted = f"// DataWindow: {object_name}\n"
        formatted += "// Extracted DataWindow definition\n\n"

        # Clean up the syntax
        cleaned = cls._clean_syntax(raw_syntax)

        # Add proper indentation
        indented = cls._indent_syntax(cleaned)

        formatted += indented

        return formatted

    @classmethod
    def _clean_syntax(cls, syntax: str) -> str:


        """Clean up DataWindow syntax.

        Args:
            syntax: Raw syntax to clean

        Returns:
            Cleaned syntax
        """
        # Remove null bytes and control characters
        cleaned = re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "", syntax)

        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Fix common formatting issues
        cleaned = cleaned.replace("( ", "(")
        cleaned = cleaned.replace(" )", ")")
        cleaned = cleaned.replace(", ", ", ")

        # Add line breaks after major sections
        for marker in [
            "datawindow(",
            "table(",
            "retrieve=",
            "column(",
            "header(",
            "detail(",
            "footer(",
            "summary(",
        ]:
            cleaned = cleaned.replace(marker, "\n" + marker)

        # Add line breaks before closing parentheses for major sections
        cleaned = re.sub(r"\)\s*(?=\w)", ")\n", cleaned)

        return cleaned.strip()

    @classmethod
    def _indent_syntax(cls, syntax: str) -> str:


        """Add proper indentation to DataWindow syntax.

        Args:
            syntax: Syntax to indent

        Returns:
            Indented syntax
        """
        lines = syntax.split("\n")
        indented_lines = []
        indent_level = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Decrease indent for closing parentheses
            if line.startswith(")"):
                indent_level = max(0, indent_level - 1)

            # Add indented line
            indented_lines.append("    " * indent_level + line)

            # Increase indent after opening parentheses
            if line.endswith("("):
                indent_level += 1
            # Handle lines with both opening and closing parentheses
            elif "(" in line and ")" in line:
                # Count net parentheses
                open_count = line.count("(")
                close_count = line.count(")")
                indent_level += open_count - close_count
                indent_level = max(0, indent_level)

        return "\n".join(indented_lines)

    @classmethod
    def extract_sql_from_datawindow(cls, syntax: str) -> str | None:


        """Extract SQL statement from DataWindow syntax.

        Args:
            syntax: DataWindow syntax

        Returns:
            Extracted SQL or None if not found
        """
        if not syntax:
            return None

        sql = None
        
        # Look for retrieve section
        retrieve_match = re.search(
            r'retrieve\s*=\s*"([^"]+)"', syntax, re.IGNORECASE | re.DOTALL,
        )
        if retrieve_match:
            sql = retrieve_match.group(1)
            # Clean up the SQL
            sql = sql.replace("~n", "\n")
            sql = sql.replace("~t", "\t")
            sql = sql.replace("~~", "~")
            sql = sql.replace('~"', '"')
            sql = sql.strip()

        # Look for PBSELECT section with balanced parentheses
        if not sql:
            pbselect_start = syntax.find("PBSELECT(")
            if pbselect_start != -1:
                # Extract PBSELECT with balanced parentheses
                pos = pbselect_start + 9  # Start after "PBSELECT("
                paren_count = 1

                while pos < len(syntax) and paren_count > 0:
                    if syntax[pos] == "(":
                        paren_count += 1
                    elif syntax[pos] == ")":
                        paren_count -= 1
                    pos += 1

                if paren_count == 0:
                    sql = syntax[pbselect_start:pos]

        # Fallback to regex for malformed PBSELECT
        if not sql:
            pbselect_match = re.search(
                r"PBSELECT\s*\(.*", syntax, re.IGNORECASE | re.DOTALL,
            )
            if pbselect_match:
                sql = pbselect_match.group(0).strip()
        
        # Apply PowerBuilder decoder SQL parameter fixes if SQL was found
        if sql:
            from extract.pbd.utils.powerbuilder_decoder_v4 import get_decoder
            decoder = get_decoder()
            sql = decoder._fix_sql_parameters(sql)
            
        return sql

    @classmethod
    def save_formatted_datawindow(
        cls, object_name: str, syntax: str, output_path: Path, save_sql: bool = True,
    ) -> tuple[Path, Path | None]:


        """Save formatted DataWindow to file(s).

        Args:
            object_name: Name of the DataWindow object
            syntax: DataWindow syntax to save
            output_path: Output directory
            save_sql: Whether to save SQL separately

        Returns:
            Tuple of (main_file_path, sql_file_path or None)
        """
        # Fix any corruption in the syntax first
        from extract.pbd.structures.data_corruption_fix import fix_extracted_datawindow
        fixed_syntax = fix_extracted_datawindow(syntax, object_name)
        
        # Apply PowerBuilder decoder to fix SQL parameter placeholders
        from extract.pbd.utils.powerbuilder_decoder_v4 import get_decoder
        decoder = get_decoder()
        fixed_syntax = decoder._fix_sql_parameters(fixed_syntax)

        # Format the syntax
        formatted_syntax = cls.format_datawindow_syntax(fixed_syntax, object_name)

        # Save main DataWindow file
        main_file = output_path / f"{object_name}.srd"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(formatted_syntax)

        logger.info("Saved formatted DataWindow to: %s", main_file)

        sql_file = None
        if save_sql:
            # Try to extract and save SQL separately
            sql = cls.extract_sql_from_datawindow(fixed_syntax)
            if sql:
                sql_file = output_path / f"{object_name}.sql"
                with open(sql_file, "w", encoding="utf-8") as f:
                    f.write(f"-- SQL from DataWindow: {object_name}\n\n")
                    f.write(sql)
                    f.write("\n")
                logger.info("Saved DataWindow SQL to: %s", sql_file)

        return main_file, sql_file

    @classmethod
    def is_valid_datawindow_syntax(cls, syntax: str) -> bool:


        """Check if the extracted syntax appears to be valid DataWindow syntax.

        Args:
            syntax: Syntax to validate

        Returns:
            True if syntax appears valid
        """
        if not syntax or len(syntax) < 10:
            return False

        # Check for at least one DataWindow marker
        for marker_name, marker_regex in cls.DW_MARKERS.items():
            if marker_regex.search(syntax):
                return True

        return False

    @classmethod
    def pretty_print_datawindow(cls, syntax: str, object_name: str) -> str:
        """Create a human-readable pretty-printed version of DataWindow syntax.

        Args:
            syntax: DataWindow syntax to pretty print
            object_name: Name of the DataWindow object

        Returns:
            Pretty-printed DataWindow with enhanced formatting
        """
        if not syntax:
            return ""

        # Start with formatted syntax
        formatted = cls.format_datawindow_syntax(syntax, object_name)
        
        # Extract and highlight SQL if present
        sql = cls.extract_sql_from_datawindow(syntax)
        if sql:
            formatted += "\n\n/* ===== EXTRACTED SQL ===== */\n"
            formatted += sql
            formatted += "\n/* ========================= */\n"
        
        # Add metadata summary
        formatted += "\n\n/* ===== DATAWINDOW SUMMARY ===== */\n"
        
        # Count columns
        column_count = syntax.count("column=(")
        formatted += f"// Columns: {column_count}\n"
        
        # Check for common features
        features = []
        if "retrieve=" in syntax:
            features.append("SQL Retrieval")
        if "header(" in syntax:
            features.append("Header Band")
        if "detail(" in syntax:
            features.append("Detail Band")
        if "footer(" in syntax:
            features.append("Footer Band")
        if "summary(" in syntax:
            features.append("Summary Band")
        if "processing=" in syntax:
            features.append("Processing")
        
        if features:
            formatted += f"// Features: {', '.join(features)}\n"
        
        formatted += "/* =============================== */\n"
        
        return formatted
