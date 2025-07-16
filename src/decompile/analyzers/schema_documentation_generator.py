"""Schema documentation generator for database analysis."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_schema_documentation(
    mapping_data: Dict[str, Any],
    output_format: str = "markdown",
    output_path: Path = None
) -> None:
    """Generate database schema documentation.

    Args:
        mapping_data: Mapped project data including schema information
        output_format: Output format (markdown, html, json)
        output_path: Path to write documentation
    """
    if not output_path:
        output_path = Path("database_schema_documentation.md")

    if output_format == "markdown":
        _generate_markdown_doc(mapping_data, output_path)
    elif output_format == "html":
        _generate_html_doc(mapping_data, output_path)
    elif output_format == "json":
        _generate_json_doc(mapping_data, output_path)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def _generate_markdown_doc(mapping_data: Dict[str, Any], output_path: Path) -> None:
    """Generate Markdown documentation."""
    content = ["# Database Schema Documentation\n"]

    # Add schema information
    schema = mapping_data.get("database_schema", {})

    if "tables" in schema:
        content.append("## Tables\n")
        for table_name, table_info in schema["tables"].items():
            content.append(f"### {table_name}\n")
            if "columns" in table_info:
                content.append("| Column | Type | Description |")
                content.append("|--------|------|-------------|")
                for col in table_info["columns"]:
                    content.append(f"| {col.get('name', '')} | {col.get('type', '')} | {col.get('description', '')} |")
                content.append("")

    # Add statistics
    stats = mapping_data.get("statistics", {})
    if stats:
        content.append("## Statistics\n")
        for key, value in stats.items():
            content.append(f"- {key}: {value}")

    # Write to file
    output_path.write_text("\n".join(content))
    logger.info(f"Generated Markdown documentation at {output_path}")


def _generate_html_doc(mapping_data: Dict[str, Any], output_path: Path) -> None:
    """Generate HTML documentation."""
    # TODO: Implement HTML generation
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Database Schema Documentation</title>
</head>
<body>
    <h1>Database Schema Documentation</h1>
    <pre>{json.dumps(mapping_data, indent=2)}</pre>
</body>
</html>"""

    output_path.write_text(html_content)
    logger.info(f"Generated HTML documentation at {output_path}")


def _generate_json_doc(mapping_data: Dict[str, Any], output_path: Path) -> None:
    """Generate JSON documentation."""
    with open(output_path, 'w') as f:
        json.dump(mapping_data, f, indent=2)
    logger.info(f"Generated JSON documentation at {output_path}")