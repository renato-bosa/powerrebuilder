"""Schema documentation generator for database analysis.

This module generates comprehensive schema documentation from analyzed PowerBuilder
code. It supports multiple output formats including JSON, Markdown, SQL DDL, and
PlantUML diagrams for visualization.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from src.core.exceptions import SchemaGenerationError

logger = logging.getLogger(__name__)

OutputFormat = Literal["json", "markdown", "sql", "plantuml", "html"]


class SchemaDocumentationGenerator:
    """Generate schema documentation from analyzed database schema."""

    def __init__(self) -> None:
        """Initialize the schema documentation generator."""
        self.schema_data: dict[str, Any] = {}
        self.project_name: str = "PowerBuilder Database Schema"
        self.generation_timestamp: str = datetime.now().isoformat()

    def generate_documentation(
        self,
        schema_data: dict[str, Any],
        output_format: OutputFormat = "markdown",
        output_path: Path | None = None,
        project_name: str | None = None,
    ) -> str:
        """Generate schema documentation in the specified format.

        Args:
            schema_data: Dictionary containing extracted schema information
            output_format: Output format (json, markdown, sql, plantuml, html)
            output_path: Optional path to save the documentation
            project_name: Optional project name for documentation

        Returns:
            Generated documentation as string

        Raises:
            SchemaGenerationError: If generation fails
        """
        self.schema_data = schema_data
        if project_name:
            self.project_name = project_name

        try:
            # Generate documentation based on format
            if output_format == "json":
                content = self._generate_json()
            elif output_format == "markdown":
                content = self._generate_markdown()
            elif output_format == "sql":
                content = self._generate_sql_ddl()
            elif output_format == "plantuml":
                content = self._generate_plantuml()
            elif output_format == "html":
                content = self._generate_html()
            else:
                raise SchemaGenerationError(
                    f"Unsupported output format: {output_format}"
                )

            # Save to file if path provided
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content, encoding="utf-8")
                logger.info("Schema documentation saved to %s", output_path)

            return content

        except Exception as e:
            raise SchemaGenerationError(
                f"Failed to generate schema documentation: {e}"
            ) from e

    def _generate_json(self) -> str:
        """Generate JSON format documentation."""
        # Add metadata
        doc_data = {
            "project": self.project_name,
            "generated": self.generation_timestamp,
            "schema": self.schema_data,
        }
        return json.dumps(doc_data, indent=2, default=str)

    def _generate_markdown(self) -> str:
        """Generate Markdown format documentation."""
        lines = []

        # Header
        lines.append(f"# {self.project_name}")
        lines.append("")
        lines.append(f"*Generated: {self.generation_timestamp}*")
        lines.append("")

        # Summary statistics
        stats = self.schema_data.get("statistics", {})
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Tables**: {stats.get('total_tables', 0)}")
        lines.append(f"- **Total Columns**: {stats.get('total_columns', 0)}")
        lines.append(
            f"- **Total Relationships**: {stats.get('total_relationships', 0)}"
        )
        lines.append(f"- **Total Operations**: {stats.get('total_operations', 0)}")
        lines.append("")

        # Operation counts
        if op_counts := stats.get("operation_counts", {}):
            lines.append("### Operations by Type")
            lines.append("")
            for op_type, count in sorted(op_counts.items()):
                lines.append(f"- **{op_type}**: {count}")
            lines.append("")

        # Tables
        lines.append("## Tables")
        lines.append("")

        tables = self.schema_data.get("tables", {})
        for table_name in sorted(tables.keys()):
            table_info = tables[table_name]
            lines.append(f"### {table_name}")
            lines.append("")

            # Columns
            if columns := table_info.get("columns", []):
                lines.append("**Columns:**")
                for col in sorted(columns):
                    fk_info = table_info.get("foreign_keys", {}).get(col)
                    if fk_info:
                        lines.append(f"- `{col}` → {fk_info}")
                    elif col in table_info.get("primary_keys", []):
                        lines.append(f"- `{col}` (PK)")
                    else:
                        lines.append(f"- `{col}`")
                lines.append("")

            # Used in objects
            if objects := table_info.get("used_in_objects", []):
                lines.append("**Used in:**")
                for obj in sorted(objects):
                    lines.append(f"- {obj}")
                lines.append("")

            # Operations
            if operations := table_info.get("operations", {}):
                lines.append("**Operations:**")
                for op, count in sorted(operations.items()):
                    lines.append(f"- {op}: {count}")
                lines.append("")

        # Relationships
        if relationships := self.schema_data.get("relationships", []):
            lines.append("## Relationships")
            lines.append("")
            for rel in relationships:
                lines.append(
                    f"- `{rel['from_table']}.{rel['from_column']}` → "
                    f"`{rel['to_table']}.{rel['to_column']}` "
                    f"({rel['type']})"
                )
            lines.append("")

        # Connection strings
        if conn_strings := self.schema_data.get("connection_strings", {}):
            lines.append("## Connection Strings")
            lines.append("")
            for obj, conn in sorted(conn_strings.items()):
                lines.append(f"- **{obj}**: `{conn}`")
            lines.append("")

        # Transaction objects
        if trans_objects := self.schema_data.get("transaction_objects", {}):
            lines.append("## Transaction Objects")
            lines.append("")
            for trans_name, trans_info in sorted(trans_objects.items()):
                lines.append(f"### {trans_name}")
                if props := trans_info.get("properties", {}):
                    lines.append("**Properties:**")
                    for prop, value in sorted(props.items()):
                        lines.append(f"- {prop}: {value}")
                if used_in := trans_info.get("used_in", []):
                    lines.append("**Used in:**")
                    for obj in sorted(used_in):
                        lines.append(f"- {obj}")
                lines.append("")

        return "\n".join(lines)

    def _generate_sql_ddl(self) -> str:
        """Generate SQL DDL statements from schema."""
        lines = []

        # Header comment
        lines.append(f"-- {self.project_name}")
        lines.append(f"-- Generated: {self.generation_timestamp}")
        lines.append(
            "-- Note: This is a reverse-engineered schema and may need adjustments"
        )
        lines.append("")

        tables = self.schema_data.get("tables", {})
        relationships = self.schema_data.get("relationships", [])

        # Create tables
        for table_name in sorted(tables.keys()):
            table_info = tables[table_name]
            lines.append(f"CREATE TABLE {table_name} (")

            columns = []
            for col in sorted(table_info.get("columns", [])):
                col_def = f"    {col}"

                # Try to guess column type based on name
                if col.lower() == "id" or col.lower().endswith("_id"):
                    col_def += " INTEGER"
                elif "date" in col.lower() or "time" in col.lower():
                    col_def += " TIMESTAMP"
                elif "amount" in col.lower() or "price" in col.lower():
                    col_def += " DECIMAL(10,2)"
                elif "flag" in col.lower() or "is_" in col.lower():
                    col_def += " BOOLEAN"
                else:
                    col_def += " VARCHAR(255)"

                # Add primary key constraint
                if col in table_info.get("primary_keys", []):
                    col_def += " PRIMARY KEY"

                columns.append(col_def)

            lines.append(",\n".join(columns))
            lines.append(");")
            lines.append("")

        # Add foreign key constraints
        for rel in relationships:
            lines.append(
                f"ALTER TABLE {rel['from_table']} "
                f"ADD CONSTRAINT fk_{rel['from_table']}_{rel['from_column']} "
                f"FOREIGN KEY ({rel['from_column']}) "
                f"REFERENCES {rel['to_table']}({rel['to_column']});"
            )

        if relationships:
            lines.append("")

        return "\n".join(lines)

    def _generate_plantuml(self) -> str:
        """Generate PlantUML diagram for schema visualization."""
        lines = []

        # PlantUML header
        lines.append("@startuml")
        lines.append(f"title {self.project_name}")
        lines.append("!define Table(name,desc) class name as desc << (T,#FFAAAA) >>")
        lines.append("!define PK(x) <u>x</u>")
        lines.append("!define FK(x) <i>x</i>")
        lines.append("")

        tables = self.schema_data.get("tables", {})
        relationships = self.schema_data.get("relationships", [])

        # Define tables
        for table_name in sorted(tables.keys()):
            table_info = tables[table_name]
            lines.append(f'Table({table_name}, "{table_name}") {{')

            # Primary keys first
            for col in sorted(table_info.get("primary_keys", [])):
                lines.append(f"  PK({col})")

            # Foreign keys
            for col, _ref in sorted(table_info.get("foreign_keys", {}).items()):
                lines.append(f"  FK({col})")

            # Other columns
            other_cols = (
                set(table_info.get("columns", []))
                - set(table_info.get("primary_keys", []))
                - set(table_info.get("foreign_keys", {}).keys())
            )
            for col in sorted(other_cols):
                lines.append(f"  {col}")

            lines.append("}")
            lines.append("")

        # Define relationships
        for rel in relationships:
            rel_type = rel.get("type", "many-to-one")
            if rel_type == "many-to-one":
                arrow = "-->"
            elif rel_type == "one-to-many":
                arrow = "<--"
            else:  # many-to-many
                arrow = "<-->"

            lines.append(
                f"{rel['from_table']} {arrow} {rel['to_table']} : "
                f"{rel['from_column']} -> {rel['to_column']}"
            )

        lines.append("")
        lines.append("@enduml")

        return "\n".join(lines)

    def _generate_html(self) -> str:
        """Generate HTML format documentation."""
        # Convert markdown to HTML (simple version)
        markdown_content = self._generate_markdown()

        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.project_name}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #555; margin-top: 30px; }",
            "h3 { color: #777; margin-top: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            "code { background-color: #f5f5f5; padding: 2px 4px; }",
            ".statistics { background-color: #f9f9f9; padding: 20px; border-radius: 5px; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Simple markdown to HTML conversion
        lines = markdown_content.split("\n")
        in_list = False

        for line in lines:
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                # Convert markdown code blocks
                content = line[2:]
                content = content.replace("`", "<code>").replace("`", "</code>")
                html_lines.append(f"<li>{content}</li>")
            elif line.startswith("*") and line.endswith("*"):
                html_lines.append(f"<em>{line[1:-1]}</em>")
            elif line.strip() == "":
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append("<br>")
            else:
                html_lines.append(f"<p>{line}</p>")

        if in_list:
            html_lines.append("</ul>")

        html_lines.extend(
            [
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_lines)

    def generate_summary_report(self) -> dict[str, Any]:
        """Generate a summary report of the schema analysis.

        Returns:
            Dictionary containing summary statistics and insights
        """
        tables = self.schema_data.get("tables", {})
        relationships = self.schema_data.get("relationships", [])
        operations = self.schema_data.get("operations", [])

        # Analyze table complexity
        table_complexity = {}
        for table_name, table_info in tables.items():
            complexity_score = (
                len(table_info.get("columns", [])) * 1
                + len(table_info.get("foreign_keys", {})) * 2
                + len(table_info.get("used_in_objects", [])) * 0.5
            )
            table_complexity[table_name] = complexity_score

        # Find most used tables
        table_usage = {}
        for op in operations:
            for table in op.get("tables", []):
                table_usage[table] = table_usage.get(table, 0) + 1

        # Find objects with most database interactions
        object_db_usage = {}
        for op in operations:
            obj = op.get("object", "")
            object_db_usage[obj] = object_db_usage.get(obj, 0) + 1

        # Generate insights
        insights = []

        # Most complex tables
        complex_tables = sorted(
            table_complexity.items(), key=lambda x: x[1], reverse=True
        )[:5]
        if complex_tables:
            insights.append(
                {
                    "type": "complex_tables",
                    "description": "Most complex tables (by columns and relationships)",
                    "data": [
                        {"table": t[0], "complexity_score": t[1]}
                        for t in complex_tables
                    ],
                }
            )

        # Most used tables
        used_tables = sorted(table_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        if used_tables:
            insights.append(
                {
                    "type": "most_used_tables",
                    "description": "Most frequently accessed tables",
                    "data": [
                        {"table": t[0], "operation_count": t[1]} for t in used_tables
                    ],
                }
            )

        # Database-heavy objects
        db_heavy_objects = sorted(
            object_db_usage.items(), key=lambda x: x[1], reverse=True
        )[:5]
        if db_heavy_objects:
            insights.append(
                {
                    "type": "database_heavy_objects",
                    "description": "Objects with most database operations",
                    "data": [
                        {"object": obj[0], "operation_count": obj[1]}
                        for obj in db_heavy_objects
                    ],
                }
            )

        # Potential issues
        issues = []

        # Tables without relationships
        isolated_tables = [
            table
            for table, info in tables.items()
            if not info.get("foreign_keys")
            and not any(rel["to_table"] == table for rel in relationships)
        ]
        if isolated_tables:
            issues.append(
                {
                    "type": "isolated_tables",
                    "severity": "warning",
                    "description": "Tables without any relationships",
                    "tables": isolated_tables,
                }
            )

        # Tables with many foreign keys (potential over-normalization)
        over_normalized = [
            table
            for table, info in tables.items()
            if len(info.get("foreign_keys", {})) > 5
        ]
        if over_normalized:
            issues.append(
                {
                    "type": "over_normalized",
                    "severity": "info",
                    "description": "Tables with many foreign keys",
                    "tables": over_normalized,
                }
            )

        return {
            "summary": {
                "project": self.project_name,
                "generated": self.generation_timestamp,
                "statistics": self.schema_data.get("statistics", {}),
            },
            "insights": insights,
            "potential_issues": issues,
            "recommendations": self._generate_recommendations(insights, issues),
        }

    def _generate_recommendations(
        self, insights: list[dict[str, Any]], issues: list[dict[str, Any]]
    ) -> list[str]:
        """Generate recommendations based on insights and issues."""
        recommendations = []

        # Check for isolated tables
        isolated = [issue for issue in issues if issue.get("type") == "isolated_tables"]
        if isolated:
            recommendations.append(
                "Consider reviewing isolated tables to ensure they are "
                "properly integrated into the data model."
            )

        # Check for complex tables
        complex_tables = [
            insight for insight in insights if insight.get("type") == "complex_tables"
        ]
        if complex_tables and complex_tables[0]["data"][0]["complexity_score"] > 50:
            recommendations.append(
                "Some tables appear very complex. Consider reviewing them "
                "for potential normalization or refactoring opportunities."
            )

        # Check for database-heavy objects
        db_heavy = [
            insight
            for insight in insights
            if insight.get("type") == "database_heavy_objects"
        ]
        if db_heavy and db_heavy[0]["data"][0]["operation_count"] > 20:
            recommendations.append(
                "Some objects have many database operations. Consider "
                "implementing a data access layer or repository pattern."
            )

        # General recommendations
        if not self.schema_data.get("connection_strings"):
            recommendations.append(
                "No connection strings were found. Ensure database "
                "connections are properly configured."
            )

        return recommendations
