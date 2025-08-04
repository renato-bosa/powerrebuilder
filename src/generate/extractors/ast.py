"""AST extraction service for generation module."""

import logging
import re
from typing import Any

from src.contracts.interfaces import IASTExtractor
from src.generate.converters.data.relationships import RelationshipExtractor
from src.parse.parser.sql import SQLParser

logger = logging.getLogger(__name__)


class ASTExtractor(IASTExtractor):
    """Extracts information from AST for code generation."""

    def __init__(self) -> None:
        """Initialize the AST extractor."""
        self.sql_parser = SQLParser()
        self.relationship_extractor = RelationshipExtractor()

    def extract_datawindow_from_ast(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract DataWindow information from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            DataWindow structure with columns, relationships, and SQL
        """
        if not isinstance(ast, dict):
            return {}

        # Look for DataWindow node in the AST
        if ast.get("node_type") == "DataWindow" or ast.get("type") == "datawindow":
            columns = []
            relationships = []
            sql_info = {}
            primary_keys = []

            # Extract columns with foreign key information
            if "columns" in ast:
                columns = self._extract_columns(
                    ast["columns"], relationships, primary_keys
                )

            # Extract SQL statements
            for sql_type in [
                "retrieve_sql",
                "update_sql",
                "insert_sql",
                "delete_sql",
            ]:
                if ast.get(sql_type):
                    sql_info[sql_type] = ast[sql_type]

            # Extract table information
            table_name = self._extract_table_info(ast, sql_info, primary_keys)

            # Extract relationships from SQL
            if sql_info.get("retrieve_sql"):
                self._extract_sql_relationships(
                    sql_info["retrieve_sql"], relationships, table_name
                )

            # Extract nested DataWindow relationships
            if ast.get("datawindow_type") == "nested" or "nested_datawindow" in ast:
                self._extract_nested_relationships(ast, relationships)

            # Extract explicit relationships
            if "relationships" in ast:
                self._extract_explicit_relationships(
                    ast["relationships"], relationships, table_name
                )

            # Cross-table column analysis
            if sql_info.get("retrieve_sql") and columns:
                self._analyze_cross_table_columns(
                    sql_info["retrieve_sql"], columns, relationships, table_name
                )

            return {
                "columns": columns,
                "relationships": relationships,
                "sql": sql_info,
                "table_name": table_name,
                "primary_keys": list(set(primary_keys)),
            }

        # Recursively search for DataWindow nodes
        for value in ast.values():
            if isinstance(value, dict):
                result = self.extract_datawindow_from_ast(value)
                if result:
                    return result
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result = self.extract_datawindow_from_ast(item)
                        if result:
                            return result

        return {}

    def extract_methods_from_ast(self, ast: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract methods from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            List of methods with name, return_type, parameters, etc.
        """
        methods = []

        if not isinstance(ast, dict):
            return methods

        # Look for function/event nodes
        node_type = ast.get("node_type") or ast.get("type")

        # Check for methods within functions/events lists
        if "functions" in ast:
            for func in ast["functions"]:
                if isinstance(func, dict):
                    sub_methods = self.extract_methods_from_ast(func)
                    methods.extend(sub_methods)

        if "events" in ast:
            for event in ast["events"]:
                if isinstance(event, dict):
                    sub_methods = self.extract_methods_from_ast(event)
                    methods.extend(sub_methods)

        # Process method nodes
        if node_type in [
            "Function",
            "Event",
            "Method",
            "function",
            "event",
            "method",
            "PBFunction",
            "PBEvent",
        ]:
            method_name = ast.get("name", "unnamed_method")

            method_info = {
                "name": method_name,
                "return_type": ast.get("return_type", "void"),
                "visibility": ast.get("visibility", "public"),
                "parameters": [],
                "body": ast.get("body", []),
            }

            # Extract parameters
            self._extract_method_parameters(ast, method_info)

            # Validate and add method
            if method_info["name"] and method_info["name"] != "unnamed_method":
                methods.append(method_info)

        # Recursively search for method nodes
        skip_keys = {"functions", "events", "body", "statements"}
        for key, value in ast.items():
            if key in skip_keys:
                continue
            if isinstance(value, dict):
                sub_methods = self.extract_methods_from_ast(value)
                methods.extend(sub_methods)
            elif isinstance(value, list) and key not in ["parameters", "arguments"]:
                for item in value:
                    if isinstance(item, dict):
                        sub_methods = self.extract_methods_from_ast(item)
                        methods.extend(sub_methods)

        return methods

    def extract_window_from_ast(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract window information from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            Window structure with params, controllers, services
        """
        window_info = {"params": {}, "controllers": [], "services": []}

        if not isinstance(ast, dict):
            return window_info

        # Look for window node
        if ast.get("node_type") == "Window" or ast.get("type") == "window":
            # Extract window parameters (instance variables)
            if "variables" in ast:
                for var in ast["variables"]:
                    if var.get("visibility") == "public":
                        window_info["params"][var.get("name", "")] = {
                            "type": var.get("type", "any"),
                            "default": var.get("initial_value"),
                        }

            # Extract events that act as controllers
            if "events" in ast:
                for event in ast["events"]:
                    window_info["controllers"].append(
                        {"name": event.get("name", ""), "type": "event"}
                    )

            # Extract referenced services (functions)
            methods = self.extract_methods_from_ast(ast)
            for method in methods:
                if method.get("visibility") == "public":
                    window_info["services"].append(method["name"])

        # Recursively search
        for value in ast.values():
            if isinstance(value, dict):
                result = self.extract_window_from_ast(value)
                self._merge_window_info(window_info, result)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result = self.extract_window_from_ast(item)
                        self._merge_window_info(window_info, result)

        # Remove duplicates
        window_info["controllers"] = list(
            {c["name"]: c for c in window_info["controllers"]}.values()
        )
        window_info["services"] = list(set(window_info["services"]))

        return window_info

    # Private helper methods

    def _extract_columns(
        self,
        columns_data: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        primary_keys: list[str],
    ) -> list[dict[str, Any]]:
        """Extract column information."""
        columns = []

        for col in columns_data:
            col_name = col.get("name", col.get("column_name", ""))
            col_type = col.get("column_type", col.get("type", "string"))

            column_info = {
                "name": col_name,
                "type": col_type,
                "nullable": col.get("is_nullable", True),
                "length": col.get("length"),
                "precision": col.get("precision"),
                "scale": col.get("scale"),
            }

            # Extract foreign key information
            if col.get("foreign_key"):
                column_info["foreign_key"] = col["foreign_key"]
                relationships.append(
                    {
                        "type": "foreign_key",
                        "source_column": column_info["name"],
                        "target_table": col.get("foreign_table"),
                        "target_column": col.get("foreign_column", "id"),
                    }
                )
            else:
                # Infer foreign key from column name
                fk_info = self._infer_foreign_key_from_column_name(col_name)
                if fk_info:
                    column_info["foreign_key"] = True
                    relationships.append(
                        {
                            "type": "foreign_key",
                            "source_column": col_name,
                            "target_table": fk_info["target_table"],
                            "target_column": fk_info["target_column"],
                            "inferred_from_name": True,
                        }
                    )

            # Check if primary key
            if col.get("is_primary_key") or col.get("primary_key"):
                primary_keys.append(column_info["name"])
                column_info["primary_key"] = True

            # Add blob metadata if this is a blob column
            if col_type.lower() == "blob":
                blob_usage = self._determine_blob_usage(col_name)
                column_info["blob_metadata"] = {
                    "usage": blob_usage,
                    "display_widget": f"{self._to_pascal_case(col_name)}BlobDisplay",
                    "mime_type": self._guess_mime_type(blob_usage, col_name),
                    "expected_size": col.get("blob_size", "medium"),
                }

            columns.append(column_info)

        return columns

    def _infer_foreign_key_from_column_name(
        self, column_name: str
    ) -> dict[str, str] | None:
        """Infer foreign key from column name patterns."""
        patterns = [
            (
                r"(\w+)_id$",
                lambda m: {"target_table": m.group(1), "target_column": "id"},
            ),
            (
                r"(\w+)_code$",
                lambda m: {"target_table": m.group(1), "target_column": "code"},
            ),
            (
                r"(\w+)_key$",
                lambda m: {"target_table": m.group(1), "target_column": "id"},
            ),
            (
                r"fk_(\w+)$",
                lambda m: {"target_table": m.group(1), "target_column": "id"},
            ),
        ]

        for pattern, extractor in patterns:
            match = re.match(pattern, column_name.lower())
            if match:
                return extractor(match)

        return None

    def _determine_blob_usage(self, column_name: str) -> str:
        """Determine blob usage based on column name."""
        name_lower = column_name.lower()

        # Image-related keywords
        image_keywords = [
            "image",
            "img",
            "photo",
            "picture",
            "pic",
            "thumbnail",
            "avatar",
            "icon",
            "logo",
            "banner",
        ]
        if any(keyword in name_lower for keyword in image_keywords):
            return "image"

        # Document-related keywords
        doc_keywords = [
            "document",
            "doc",
            "pdf",
            "file",
            "attachment",
            "report",
            "excel",
            "word",
            "spreadsheet",
            "presentation",
        ]
        if any(keyword in name_lower for keyword in doc_keywords):
            return "document"

        return "data"

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        # Remove common prefixes
        name = name.removeprefix("d_")
        name = name.removeprefix("dw_")

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def _guess_mime_type(self, usage: str, column_name: str) -> str:
        """Guess MIME type based on usage and column name."""
        name_lower = column_name.lower()

        if usage == "image":
            if "jpg" in name_lower or "jpeg" in name_lower:
                return "image/jpeg"
            if "png" in name_lower:
                return "image/png"
            if "gif" in name_lower:
                return "image/gif"
            if "bmp" in name_lower:
                return "image/bmp"
            return "image/jpeg"
        if usage == "document":
            if "pdf" in name_lower:
                return "application/pdf"
            if "excel" in name_lower or "xls" in name_lower:
                return "application/vnd.ms-excel"
            if "word" in name_lower or "doc" in name_lower:
                return "application/msword"
            return "application/octet-stream"
        return "application/octet-stream"

    def _extract_table_info(
        self, ast: dict[str, Any], sql_info: dict[str, str], primary_keys: list[str]
    ) -> str:
        """Extract table information from AST."""
        table_info = ast.get("table", {})

        if isinstance(table_info, dict):
            table_name = table_info.get("name", "")

            # Extract primary keys from table definition
            if "primary_key" in table_info:
                pk = table_info["primary_key"]
                if isinstance(pk, list):
                    primary_keys.extend(pk)
                elif isinstance(pk, str):
                    primary_keys.append(pk)
        else:
            # Try to parse from SQL
            table_name = self._extract_table_from_sql(sql_info.get("retrieve_sql", ""))

        return table_name

    def _extract_table_from_sql(self, sql: str) -> str:
        """Extract table name from SQL statement."""
        if not sql:
            return ""

        # Simple extraction - look for FROM clause
        sql_upper = sql.upper()
        from_idx = sql_upper.find("FROM")
        if from_idx != -1:
            # Extract text after FROM
            after_from = sql[from_idx + 4 :].strip()
            # Get first word (table name)
            parts = after_from.split()
            if parts:
                return parts[0].strip('"').strip("'").strip("`")

        return ""

    def _extract_sql_relationships(
        self, sql: str, relationships: list[dict[str, Any]], _table_name: Any
    ) -> None:
        """Extract relationships from SQL."""
        try:
            # Parse the SQL to get AST
            parsed_sql = self.sql_parser.parse(sql)

            if parsed_sql and isinstance(parsed_sql, list) and len(parsed_sql) > 0:
                sql_stmt = parsed_sql[0]

                # Use RelationshipExtractor to find relationships
                sql_relationships = self.relationship_extractor.extract_from_select(
                    sql_stmt
                )

                # Convert relationships to our format
                for rel in sql_relationships:
                    for mapping in rel.column_mappings:
                        # Check if we already have this relationship
                        existing = any(
                            r.get("source_column") == mapping.source_column
                            and r.get("target_table") == mapping.target_table
                            for r in relationships
                        )

                        if not existing:
                            relationships.append(
                                {
                                    "type": "foreign_key",
                                    "source_table": mapping.source_table,
                                    "source_column": mapping.source_column,
                                    "target_table": mapping.target_table,
                                    "target_column": mapping.target_column,
                                    "join_type": rel.join_type.value,
                                    "inferred_from_sql": True,
                                }
                            )

        except (ValueError, KeyError) as e:
            logger.warning("Invalid SQL structure for relationship extraction: %s", e)
        except Exception as e:
            logger.warning("Failed to extract relationships from SQL: %s", e)

    def _extract_nested_relationships(
        self, ast: dict[str, Any], relationships: list[dict[str, Any]]
    ) -> None:
        """Extract nested DataWindow relationships."""
        nested_info = ast.get("nested_datawindow", {})
        if nested_info:
            relationships.append(
                {
                    "type": "nested",
                    "parent_columns": nested_info.get("parent_columns", []),
                    "child_datawindow": nested_info.get("child_datawindow"),
                    "linkage_columns": nested_info.get("linkage_columns", []),
                }
            )

    def _extract_explicit_relationships(
        self,
        explicit_rels: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        table_name: str,
    ) -> None:
        """Extract explicit relationships from AST."""
        for rel in explicit_rels:
            relationships.append(
                {
                    "type": rel.get("type", "unknown"),
                    "source_table": rel.get("source_table", table_name),
                    "source_column": rel.get("source_column"),
                    "target_table": rel.get("target_table"),
                    "target_column": rel.get("target_column"),
                    "join_type": rel.get("join_type", "inner"),
                }
            )

    def _analyze_cross_table_columns(
        self,
        sql: str,
        columns: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        table_name: str,
    ) -> None:
        """Analyze columns for cross-table relationships."""
        try:
            # Extract all tables from SQL
            tables_in_sql = self._extract_tables_from_sql(sql)

            # For each column, check if it references another table
            for col in columns:
                col_name = col["name"]

                # Skip if already has a foreign key
                if col.get("foreign_key"):
                    continue

                # Check against each table name
                for table in tables_in_sql:
                    # Skip self-references unless it's a parent_id pattern
                    if table == table_name and not col_name.lower().startswith(
                        "parent"
                    ):
                        continue

                    # Check if column name matches table pattern
                    if self._column_matches_table(col_name, table) and not any(
                        r["source_column"] == col_name for r in relationships
                    ):
                        relationships.append(
                            {
                                "type": "foreign_key",
                                "source_table": table_name,
                                "source_column": col_name,
                                "target_table": table,
                                "target_column": "id",
                                "inferred_from_column_pattern": True,
                            }
                        )

        except re.error as e:
            logger.debug("Regex error in cross-table analysis: %s", e)
        except (ValueError, KeyError) as e:
            logger.debug("Invalid data in cross-table analysis: %s", e)
        except Exception as e:
            logger.debug("Cross-table analysis failed: %s", e)

    def _extract_tables_from_sql(self, sql: str) -> list[str]:
        """Extract all table names from SQL statement."""
        if not sql:
            return []

        tables = []
        sql_upper = sql.upper()

        # Extract from FROM clause
        from_match = re.search(
            r"\bFROM\s+([^WHERE|JOIN|GROUP|ORDER|HAVING]+)", sql_upper
        )
        if from_match:
            from_text = from_match.group(1)
            # Extract table names and aliases
            table_parts = from_text.split(", ")
            for part in table_parts:
                words = part.strip().split()
                if words:
                    # Get original case table name
                    start = from_match.start(1)
                    end = from_match.end(1)
                    original_text = sql[start:end]
                    table_name = (
                        original_text.split(", ")[table_parts.index(part)]
                        .strip()
                        .split()[0]
                    )
                    tables.append(table_name.strip('"').strip("'").strip("`").lower())

        # Extract from JOIN clauses
        join_pattern = r"\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(\w+)"
        join_matches = re.finditer(join_pattern, sql, re.IGNORECASE)
        for match in join_matches:
            table_name = match.group(1)
            tables.append(table_name.strip('"').strip("'").strip("`").lower())

        return list(set(tables))

    def _column_matches_table(self, column_name: str, table_name: str) -> bool:
        """Check if a column name suggests a foreign key to the given table."""
        col_lower = column_name.lower()
        table_lower = table_name.lower()

        # Direct patterns
        patterns = [
            f"{table_lower}_id",
            f"{table_lower}_code",
            f"{table_lower}_key",
            f"{table_lower}id",
            f"fk_{table_lower}",
            f"{table_lower}_fk",
        ]

        return any(col_lower == pattern for pattern in patterns)

    def _extract_method_parameters(
        self, ast: dict[str, Any], method_info: dict[str, Any]
    ) -> None:
        """Extract method parameters from AST."""
        # Check arguments format
        if "arguments" in ast:
            args = ast["arguments"]
            if isinstance(args, dict) and "arguments" in args:
                args = args["arguments"]

            for arg in args if isinstance(args, list) else []:
                param = {
                    "name": arg.get("name", ""),
                    "type": arg.get("type", "any"),
                    "is_reference": arg.get("is_reference", False),
                    "is_readonly": arg.get("is_readonly", False),
                    "default_value": arg.get("default_value"),
                }
                method_info["parameters"].append(param)

        # Also check for parameters in different formats
        if "parameters" in ast:
            params = ast["parameters"]
            if isinstance(params, list):
                method_info["parameters"] = []
                for param in params:
                    if isinstance(param, dict):
                        method_info["parameters"].append(
                            {
                                "name": param.get("name", ""),
                                "type": param.get("type", "any"),
                                "is_reference": param.get("is_reference", False),
                                "is_readonly": param.get("is_readonly", False),
                                "default_value": param.get("default_value"),
                            }
                        )

    def _merge_window_info(
        self, target: dict[str, Any], source: dict[str, Any]
    ) -> None:
        """Merge window info from source into target."""
        target["params"].update(source["params"])
        target["controllers"].extend(source["controllers"])
        target["services"].extend(source["services"])
