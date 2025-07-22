"""PowerBuilder object formatters for extraction."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DataWindowFormatter:
    """Formatter for DataWindow objects."""

    @staticmethod
    def save_formatted_datawindow(
        object_name: str, syntax: str, output_path: Path, save_sql: bool = True
    ) -> tuple[Path, Path | None]:
        """Save DataWindow syntax to file(s).

        Args:
            object_name: Name of the DataWindow object
            syntax: DataWindow syntax text
            output_path: Directory to save files to
            save_sql: Whether to save SQL separately

        Returns:
            Tuple of (main_file_path, sql_file_path)
        """
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        # Main DataWindow file
        main_file = output_path / object_name

        # Write main file with PowerBuilder export header
        with main_file.open("w", encoding="utf-8") as f:
            f.write(f"HA$PBExportHeader${object_name}\n")
            f.write("$PBExportComments$\n")
            f.write(syntax)

        logger.debug("Saved DataWindow to %s", main_file)

        # Extract and save SQL if requested
        sql_file = None
        if save_sql:
            sql_content = _extract_sql_from_syntax(syntax)
            if sql_content:
                sql_file = output_path / f"{object_name}.sql"
                with sql_file.open("w", encoding="utf-8") as f:
                    f.write(sql_content)
                logger.debug("Saved SQL to %s", sql_file)

        return main_file, sql_file


def _extract_sql_from_syntax(syntax: str) -> str | None:
    """Extract SQL from DataWindow syntax.

    Args:
        syntax: DataWindow syntax text

    Returns:
        SQL content or None if not found
    """
    # Look for PBSELECT section
    if "PBSELECT" not in syntax:
        return None

    # Simple extraction - find PBSELECT section
    lines = syntax.split("\n")
    sql_lines = []
    in_sql = False

    for line in lines:
        if "PBSELECT" in line:
            in_sql = True
            sql_lines.append(line)
        elif in_sql:
            # SQL typically ends at the next major section
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                break
            sql_lines.append(line)

    if sql_lines:
        return "\n".join(sql_lines)

    return None
