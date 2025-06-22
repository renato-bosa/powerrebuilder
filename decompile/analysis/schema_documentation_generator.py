"""Schema documentation generator for PowerBuilder applications.

This module generates comprehensive, human-readable documentation of the database
schema, business logic mappings, and data flows extracted from PowerBuilder code.
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SchemaDocumentationGenerator:
    """Generates human-readable documentation from extracted schema and mappings."""

    def __init__(self) -> None:




        """Initialize the documentation generator."""
        self.sections = []

    def generate_documentation(self, mapping_data: dict[str, Any], output_format: str = "markdown", output_path: Path | None = None) -> str:




        """Generate comprehensive documentation.

        Args:
            mapping_data: Data from BusinessLogicMapper
            output_format: Format for output ('markdown', 'html', 'json')
            output_path: Optional path to save the documentation

        Returns:
            Generated documentation as string
        """
        logger.info(f"Generating {output_format} documentation")

        if output_format == "markdown":
            doc = self._generate_markdown_documentation(mapping_data)
        elif output_format == "html":
            doc = self._generate_html_documentation(mapping_data)
        elif output_format == "json":
            doc = self._generate_json_documentation(mapping_data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(doc)
            logger.info(f"Documentation saved to {output_path}")

        return doc

    def _generate_markdown_documentation(self, data: dict[str, Any]) -> str:




        """Generate Markdown documentation."""
        lines = []

        # Header
        lines.append("# PowerBuilder Application Database Schema and Business Logic Documentation")
        lines.append("")
        lines.append(f"Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
        lines.append("")

        # Table of Contents
        lines.append("## Table of Contents")
        lines.append("")
        lines.append("1. [Executive Summary](#executive-summary)")
        lines.append("2. [Database Schema](#database-schema)")
        lines.append("3. [Business Logic Functions](#business-logic-functions)")
        lines.append("4. [User Interface Elements](#user-interface-elements)")
        lines.append("5. [Data Flow Analysis](#data-flow-analysis)")
        lines.append("6. [Table Relationships](#table-relationships)")
        lines.append("7. [Connection Information](#connection-information)")
        lines.append("")

        # Executive Summary
        lines.extend(self._generate_executive_summary(data))

        # Database Schema
        lines.extend(self._generate_database_schema_section(data.get("database_schema", {})))

        # Business Logic Functions
        lines.extend(self._generate_business_logic_section(data.get("business_functions", {})))

        # User Interface Elements
        lines.extend(self._generate_ui_elements_section(data.get("ui_elements", {})))

        # Data Flow Analysis
        lines.extend(self._generate_data_flow_section(data.get("data_flows", [])))

        # Table Relationships
        lines.extend(self._generate_relationships_section(data.get("database_schema", {}).get("relationships", [])))

        # Connection Information
        lines.extend(self._generate_connection_section(data.get("database_schema", {})))

        return "\n".join(lines)

    def _generate_executive_summary(self, data: dict[str, Any]) -> list[str]:




        """Generate executive summary section."""
        lines = []
        lines.append("## Executive Summary")
        lines.append("")

        # Extract statistics
        db_stats = data.get("database_schema", {}).get("statistics", {})
        logic_stats = data.get("statistics", {})

        lines.append("### Key Metrics")
        lines.append("")
        lines.append(f"- **Total Database Tables**: {db_stats.get("total_tables", 0)}")
        lines.append(f"- **Total Columns**: {db_stats.get("total_columns", 0)}")
        lines.append(f"- **Total Relationships**: {db_stats.get("total_relationships", 0)}")
        lines.append(f"- **Total Business Functions**: {logic_stats.get("total_functions", 0)}")
        lines.append(f"- **Total UI Elements**: {logic_stats.get("total_ui_elements", 0)}")
        lines.append(f"- **Total Data Flows**: {logic_stats.get("total_data_flows", 0)}")
        lines.append("")

        # Operation breakdown
        op_counts = db_stats.get("operation_counts", {})
        if op_counts:
            lines.append("### Database Operation Summary")
            lines.append("")
            for op, count in sorted(op_counts.items()):
                lines.append(f"- **{op}**: {count} operations")
            lines.append("")

        return lines

    def _generate_database_schema_section(self, schema_data: dict[str, Any]) -> list[str]:




        """Generate database schema section."""
        lines = []
        lines.append("## Database Schema")
        lines.append("")

        tables = schema_data.get("tables", {})

        if not tables:
            lines.append("*No tables found in the schema.*")
            lines.append("")
            return lines

        # Sort tables by name
        for table_name in sorted(tables.keys()):
            table_info = tables[table_name]

            lines.append(f"### Table: `{table_name}`")
            lines.append("")

            # Columns
            columns = table_info.get("columns", [])
            if columns:
                lines.append("#### Columns")
                lines.append("")
                lines.append("| Column Name | Type | Key |")
                lines.append("|-------------|------|-----|")

                primary_keys = set(table_info.get("primary_keys", []))
                foreign_keys = table_info.get("foreign_keys", {})

                for column in sorted(columns):
                    key_type = []
                    if column in primary_keys:
                        key_type.append("PK")
                    if column in foreign_keys:
                        key_type.append(f"FK → {foreign_keys[column]}")

                    key_str = ", ".join(key_type) if key_type else "-"
                    lines.append(f"| {column} | - | {key_str} |")

                lines.append("")

            # Operations
            operations = table_info.get("operations", {})
            if operations:
                lines.append("#### Operations")
                lines.append("")
                for op, count in sorted(operations.items()):
                    lines.append(f"- **{op}**: {count} occurrences")
                lines.append("")

            # Used in objects
            used_in = table_info.get("used_in_objects", [])
            if used_in:
                lines.append("#### Used In")
                lines.append("")
                for obj in sorted(used_in):
                    lines.append(f"- {obj}")
                lines.append("")

        return lines

    def _generate_business_logic_section(self, functions: dict[str, Any]) -> list[str]:




        """Generate business logic functions section."""
        lines = []
        lines.append("## Business Logic Functions")
        lines.append("")

        if not functions:
            lines.append("*No business logic functions found.*")
            lines.append("")
            return lines

        # Group functions by object
        functions_by_object = defaultdict(list)
        for func_key, func_info in functions.items():
            obj_name = func_info.get("object", "Unknown")
            functions_by_object[obj_name].append((func_key, func_info))

        # Generate documentation for each object
        for obj_name in sorted(functions_by_object.keys()):
            lines.append(f"### Object: `{obj_name}`")
            lines.append("")

            for func_key, func_info in sorted(functions_by_object[obj_name], key=lambda x:
                x[1]["name"],):
                func_name = func_info.get("name", "Unknown")
                func_type = func_info.get("type", "Unknown")

                lines.append(f"#### Function: `{func_name}`")
                lines.append("")

                # Function signature
                params = func_info.get("parameters", [])
                return_type = func_info.get("return_type", "void")
                param_str = ", ".join(params) if params else ""

                lines.append(f"**Signature**: `{return_type} {func_name}({param_str})`")
                lines.append("")

                # Description
                if func_info.get("description"):
                    lines.append(f"**Description**: {func_info["description"]}")
                    lines.append("")

                # Accessed tables
                tables = func_info.get("accessed_tables", [])
                if tables:
                    lines.append("**Database Access**:")
                    lines.append("")
                    for table in sorted(tables):
                        operations = [op["type"] for op in func_info.get("operations", []) 
                                    if table in op.get("tables", [])]
                        if operations:
                            lines.append(f"- `{table}`: {", ".join(set(operations))}")
                        else:
                            lines.append(f"- `{table}`")
                    lines.append("")

                # UI elements
                ui_elements = func_info.get("ui_elements", [])
                if ui_elements:
                    lines.append("**UI Elements**:")
                    lines.append("")
                    for ui in sorted(ui_elements):
                        lines.append(f"- {ui}")
                    lines.append("")

                # Called functions
                called = func_info.get("called_functions", [])
                if called:
                    lines.append("**Calls**:")
                    lines.append("")
                    for func in sorted(called):
                        lines.append(f"- {func}")
                    lines.append("")

        return lines

    def _generate_ui_elements_section(self, ui_elements: dict[str, Any]) -> list[str]:




        """Generate UI elements section."""
        lines = []
        lines.append("## User Interface Elements")
        lines.append("")

        if not ui_elements:
            lines.append("*No UI elements found.*")
            lines.append("")
            return lines

        # Group by type
        elements_by_type = defaultdict(list)
        for ui_key, ui_info in ui_elements.items():
            ui_type = ui_info.get("type", "Unknown")
            elements_by_type[ui_type].append((ui_key, ui_info))

        # Generate documentation for each type
        for ui_type in sorted(elements_by_type.keys()):
            lines.append(f"### {ui_type} Elements")
            lines.append("")

            for ui_key, ui_info in sorted(elements_by_type[ui_type], key=lambda x:
                x[1]["name"],):
                name = ui_info.get("name", "Unknown")
                parent = ui_info.get("parent", "Unknown")

                lines.append(f"#### `{name}`")
                lines.append("")
                lines.append(f"**Parent**: {parent}")
                lines.append("")

                # Data source (for DataWindows)
                if ui_info.get("data_source"):
                    lines.append(f"**Data Source**: {ui_info["data_source"]}")
                    lines.append("")

                # Accessed tables
                tables = ui_info.get("accessed_tables", [])
                if tables:
                    lines.append("**Database Tables**:")
                    lines.append("")
                    for table in sorted(tables):
                        lines.append(f"- {table}")
                    lines.append("")

                # Bound columns
                columns = ui_info.get("bound_columns", [])
                if columns:
                    lines.append("**Bound Columns**:")
                    lines.append("")
                    for col in columns:
                        lines.append(f"- {col}")
                    lines.append("")

                # Event handlers
                events = ui_info.get("event_handlers", {})
                if events:
                    lines.append("**Event Handlers**:")
                    lines.append("")
                    for event, handler in sorted(events.items()):
                        lines.append(f"- {event} → {handler}")
                    lines.append("")

        return lines

    def _generate_data_flow_section(self, data_flows: list[dict[str, Any]]) -> list[str]:




        """Generate data flow analysis section."""
        lines = []
        lines.append("## Data Flow Analysis")
        lines.append("")

        if not data_flows:
            lines.append("*No data flows found.*")
            lines.append("")
            return lines

        # Group flows by operation type
        flows_by_operation = defaultdict(list)
        for flow in data_flows:
            op = flow.get("operation", "Unknown")
            flows_by_operation[op].append(flow)

        # Generate flow tables for each operation
        for op in sorted(flows_by_operation.keys()):
            lines.append(f"### {op} Operations")
            lines.append("")

            lines.append("| Source | Source Type | Target | Target Type | Data Items |")
            lines.append("|--------|-------------|--------|-------------|------------|")

            for flow in sorted(flows_by_operation[op], key=lambda x: (x["source"], x["target"])):
                source = flow.get("source", "-")
                source_type = flow.get("source_type", "-")
                target = flow.get("target", "-")
                target_type = flow.get("target_type", "-")
                data_items = ", ".join(flow.get("data_items", [])) or "-"

                lines.append(f"| {source} | {source_type} | {target} | {target_type} | {data_items} |")

            lines.append("")

        return lines

    def _generate_relationships_section(self, relationships: list[dict[str, Any]]) -> list[str]:




        """Generate table relationships section."""
        lines = []
        lines.append("## Table Relationships")
        lines.append("")

        if not relationships:
            lines.append("*No explicit relationships found. Relationships may be inferred from foreign key naming conventions.*")
            lines.append("")
            return lines

        lines.append("| From Table | From Column | To Table | To Column | Type | Join Type |")
        lines.append("|------------|-------------|----------|-----------|------|-----------|")

        for rel in sorted(relationships, key=lambda x: (x["from_table"], x["to_table"])):
            from_table = rel.get("from_table", "-")
            from_column = rel.get("from_column", "-")
            to_table = rel.get("to_table", "-")
            to_column = rel.get("to_column", "-")
            rel_type = rel.get("type", "-")
            join_type = rel.get("join_type", "-")

            lines.append(f"| {from_table} | {from_column} | {to_table} | {to_column} | {rel_type} | {join_type} |")

        lines.append("")

        # Add relationship diagram if possible
        lines.append("### Relationship Diagram")
        lines.append("")
        lines.append("```mermaid")
        lines.append("erDiagram")

        # Generate mermaid diagram
        processed_tables = set()
        for rel in relationships:
            from_table = rel.get("from_table", "")
            to_table = rel.get("to_table", "")
            rel_type = rel.get("type", "many-to-one")

            if from_table and to_table:
                if rel_type == "one-to-many":
                    lines.append(f"    {from_table} ||--o{{ {to_table} : has")
                elif rel_type == "many-to-one":
                    lines.append(f"    {from_table} }}o--|| {to_table} : references")
                elif rel_type == "many-to-many":
                    lines.append(f"    {from_table} }}o--o{{ {to_table} : relates")
                else:
                    lines.append(f"    {from_table} ||--|| {to_table} : links")

                processed_tables.add(from_table)
                processed_tables.add(to_table)

        lines.append("```")
        lines.append("")

        return lines

    def _generate_connection_section(self, schema_data: dict[str, Any]) -> list[str]:




        """Generate connection information section."""
        lines = []
        lines.append("## Connection Information")
        lines.append("")

        # Connection strings
        conn_strings = schema_data.get("connection_strings", {})
        if conn_strings:
            lines.append("### Connection Strings")
            lines.append("")
            for obj, conn_str in sorted(conn_strings.items()):
                lines.append(f"#### Object: `{obj}`")
                lines.append("")
                lines.append(f"```")
                lines.append(conn_str)
                lines.append(f"```")
                lines.append("")

        # Transaction objects
        trans_objects = schema_data.get("transaction_objects", {})
        if trans_objects:
            lines.append("### Transaction Objects")
            lines.append("")

            for trans_name, trans_info in sorted(trans_objects.items()):
                lines.append(f"#### `{trans_name}`")
                lines.append("")

                # Properties
                props = trans_info.get("properties", {})
                if props:
                    lines.append("**Properties**:")
                    lines.append("")
                    for prop, value in sorted(props.items()):
                        lines.append(f"- {prop}: {value}")
                    lines.append("")

                # Used in
                used_in = trans_info.get("used_in", [])
                if used_in:
                    lines.append("**Used In**:")
                    lines.append("")
                    for obj in sorted(used_in):
                        lines.append(f"- {obj}")
                    lines.append("")

        return lines

    def _generate_html_documentation(self, data: dict[str, Any]) -> str:




        """Generate HTML documentation."""
        # Convert markdown to HTML with some styling
        markdown_doc = self._generate_markdown_documentation(data)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PowerBuilder Database Schema Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 8px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 16px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        ul {{
            padding-left: 20px;
        }}
        .toc {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .toc a {{
            color: #3498db;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="content">
        {self._markdown_to_basic_html(markdown_doc)}
    </div>
</body>
</html>
"""
        return html

    def _markdown_to_basic_html(self, markdown: str) -> str:




        """Convert markdown to basic HTML (simplified)."""
        html = markdown

        # Convert headers
        html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # Convert code blocks
        html = re.sub(r"```(.+?)```", r"<pre><code>\1</code></pre>", html, flags=re.DOTALL)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

        # Convert bold
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # Convert lists
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*</li>\n)+", r"<ul>\g<0></ul>", html, flags=re.MULTILINE)

        # Convert links
        html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

        # Convert tables (simplified)
        lines = html.split("\n")
        in_table = False
        new_lines = []

        for line in lines:
            if "|" in line and not in_table:
                in_table = True
                new_lines.append("<table>")

            if in_table:
                if "|---" in line:
                    continue  # Skip separator
                elif "|" in line:
                    cells = [cell.strip() for cell in line.split("|")[1:-1]]
                    if any("---" in cell for cell in cells):
                        continue
                    row = "<tr>"
                    for cell in cells:
                        row += f"<td>{cell}</td>"
                    row += "</tr>"
                    new_lines.append(row)
                else:
                    new_lines.append("</table>")
                    new_lines.append(line)
                    in_table = False
            else:
                new_lines.append(line)

        if in_table:
            new_lines.append("</table>")

        html = "\n".join(new_lines)

        # Convert paragraphs
        html = re.sub(r"\n\n", r"</p><p>", html)
        html = f"<p>{html}</p>"

        return html

    def _generate_json_documentation(self, data: dict[str, Any]) -> str:




        """Generate JSON documentation."""
        # Add metadata
        doc_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "PowerBuilder Schema Documentation Generator",
                "version": "1.0.0",
            },
            "data": data,
        }

        return json.dumps(doc_data, indent=2, sort_keys=True)


# Convenience function
def generate_schema_documentation(mapping_data: dict[str, Any], 
                                output_format: str = "markdown",
                                output_path: Path | None = None) -> str:




    """Generate schema documentation.

    Args:
        mapping_data: Data from BusinessLogicMapper
        output_format: Format for output ('markdown', 'html', 'json')
        output_path: Optional path to save the documentation

    Returns:
        Generated documentation as string
    """
    generator = SchemaDocumentationGenerator()
    return generator.generate_documentation(mapping_data, output_format, output_path)
