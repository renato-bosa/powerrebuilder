"""Database schema extractor for PowerBuilder applications.

This module extracts comprehensive database schema information from PowerBuilder
source code, including tables, columns, relationships, and database operations.
It analyzes SQL statements, DataWindow definitions, and embedded SQL code.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.model.ast.nodes.sql import (
    ColumnReference,
    DeleteStatement,
    InsertStatement,
    JoinClause,
    SelectStatement,
    TableReference,
    UpdateStatement,
)
from src.parse.parser.sql import SQLParser

logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Information about a database table."""

    name: str
    columns: set[str] = field(default_factory=set)
    primary_keys: set[str] = field(default_factory=set)
    foreign_keys: dict[str, str] = field(
        default_factory=dict
    )  # column -> referenced_table.column
    indexes: set[str] = field(default_factory=set)
    used_in_objects: set[str] = field(
        default_factory=set
    )  # PowerBuilder objects using this table
    operations: dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )  # operation -> count

    def add_column(self, column: str) -> None:
        """Add a column to the table."""
        if column and column.lower() not in ["*", "count", "sum", "avg", "min", "max"]:
            self.columns.add(column)

    def add_operation(self, operation: str, pb_object: str) -> None:
        """Add an operation performed on this table."""
        self.operations[operation] += 1
        self.used_in_objects.add(pb_object)


@dataclass
class RelationshipInfo:
    """Information about a table relationship."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str  # "one-to-many", "many-to-one", "many-to-many"
    join_type: str | None = None  # "INNER", "LEFT", "RIGHT", etc.
    used_in_objects: set[str] = field(default_factory=set)


@dataclass
class DatabaseOperation:
    """Information about a database operation."""

    operation_type: str  # SELECT, INSERT, UPDATE, DELETE, etc.
    tables: list[str]
    columns: list[str]
    pb_object: str
    pb_function: str | None = None
    line_number: int | None = None
    sql_text: str | None = None


class DatabaseSchemaExtractor:
    """Extract database schema information from PowerBuilder code."""

    def __init__(self) -> None:
        """Initialize the schema extractor."""
        self.sql_parser = SQLParser()
        self.tables: dict[str, TableInfo] = {}
        self.relationships: list[RelationshipInfo] = []
        self.operations: list[DatabaseOperation] = []
        self.connection_strings: dict[str, str] = {}
        self.transaction_objects: dict[str, dict[str, Any]] = {}

    def extract_schema_from_project(self, project_path: Path) -> dict[str, Any]:
        """Extract database schema from an entire PowerBuilder project.

        Args:
            project_path: Path to the PowerBuilder project

        Returns:
            Dictionary containing comprehensive schema information
        """
        logger.info("Extracting database schema from project: %s", project_path)

        # Find all relevant files
        pb_files = list(project_path.rglob("*.srw"))  # Windows
        pb_files.extend(project_path.rglob("*.sru"))  # User objects
        pb_files.extend(project_path.rglob("*.srd"))  # DataWindows
        pb_files.extend(project_path.rglob("*.dwo"))  # DataWindow objects
        # Compiled DataWindows
        pb_files.extend(project_path.rglob("*.pdw"))
        pb_files.extend(project_path.rglob("*.fun"))  # Functions
        pb_files.extend(project_path.rglob("*.srq"))  # SQL files

        # Process each file
        for file_path in pb_files:
            try:
                self._process_file(file_path)
            except (OSError, ValueError) as e:
                logger.error("Error processing file %s: %s", file_path, e)

        # Analyze relationships
        self._analyze_relationships()

        # Build the result
        return self._build_schema_result()

    def extract_schema_from_file(self, file_path: Path) -> dict[str, Any]:
        """Extract database schema from a single file.

        Args:
            file_path: Path to the PowerBuilder file

        Returns:
            Dictionary containing schema information from the file
        """
        self._process_file(file_path)
        return self._build_schema_result()

    def _process_file(self, file_path: Path) -> None:
        """Process a single PowerBuilder file."""
        logger.debug("Processing file: %s", file_path)

        # Handle compiled DataWindow files
        if file_path.suffix.lower() == ".pdw":
            self._process_pdw_file(file_path)
            return

        # Read the file content
        try:
            with file_path.open(encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, ValueError) as e:
            logger.error("Error reading file %s: %s", file_path, e)
            return

        # Extract object name
        object_name = file_path.stem

        # Extract SQL statements
        self._extract_sql_statements(content, object_name, file_path)

        # Extract DataWindow SQL
        if file_path.suffix.lower() in [".srd", ".dwo"]:
            self._extract_datawindow_sql(content, object_name, file_path)

        # Extract transaction configurations
        self._extract_transaction_config(content, object_name)

        # Extract connection strings
        self._extract_connection_strings(content, object_name)

    def _process_pdw_file(self, file_path: Path) -> None:
        """Process a compiled PDW file."""
        try:
            # PDWSQLExtractor is no longer available - removed from imports

            with file_path.open("rb") as f:
                data = f.read()

            metadata = PDWSQLExtractor.extract_metadata_from_pdw(data, file_path.stem)

            if metadata.get("has_sql") and metadata.get("sql"):
                self._process_sql_statement(
                    metadata["sql"],
                    file_path.stem,
                    "DataWindow",
                    None,
                )

            # Add tables and columns from metadata
            for table in metadata.get("tables", []):
                if table not in self.tables:
                    self.tables[table] = TableInfo(name=table)
                self.tables[table].used_in_objects.add(file_path.stem)

            for column in metadata.get("columns", []):
                # Try to associate column with table (heuristic
                # approach)
                for table in metadata.get("tables", []):
                    self.tables[table].add_column(column)

        except (OSError, ValueError, ImportError) as e:
            logger.error("Error processing PDW file %s: %s", file_path, e)

    def _extract_sql_statements(
        self, content: str, object_name: str, _file_path: Path
    ) -> None:
        """Extract SQL statements from PowerBuilder code."""
        # Pattern for embedded SQL
        sql_patterns = [
            # SELECT INTO :var
            r"SELECT\s+(.+?)\s+INTO\s+:(.+?)\s+FROM\s+(.+?)(?:WHERE|GROUP|ORDER||\n)",
            # Regular SELECT
            r"SELECT\s+(.+?)\s+FROM\s+(.+?)(?:WHERE|GROUP|ORDER|;|\n)",
            # INSERT
            r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
            # UPDATE
            r"UPDATE\s+(\w+)\s+SET\s+(.+?)(?:WHERE|;|\n)",
            # DELETE
            r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+?))?(?:;|\n)",
            # DECLARE CURSOR
            r"DECLARE\s+(\w+)\s+CURSOR\s+FOR\s+(.+?)(?:;|\n)",
        ]

        # Extract line numbers for better tracking
        lines = content.split("\n")

        for i, line in enumerate(lines):
            for pattern in sql_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    sql_text = match.group(0)
                    self._process_sql_statement(sql_text, object_name, None, i + 1)

        # Also look for string-based SQL
        string_sql_pattern = r'["\']?\s*(SELECT|INSERT|UPDATE|DELETE)\s+.+?["\']'
        for i, line in enumerate(lines):
            matches = re.finditer(string_sql_pattern, line, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sql_text = match.group(0).strip("\"'")
                self._process_sql_statement(sql_text, object_name, None, i + 1)

    def _extract_datawindow_sql(
        self, content: str, object_name: str, _file_path: Path
    ) -> None:
        """Extract SQL from DataWindow definitions."""
        # Look for SQL Select statements in DataWindow syntax
        sql_select_pattern = r'retrieve\s*=\s*"([^"]+)"'
        matches = re.finditer(sql_select_pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            sql_text = match.group(1)
            # Clean up DataWindow SQL formatting
            sql_text = sql_text.replace("~n", " ").replace("~t", " ")
            sql_text = re.sub(r"\s+", " ", sql_text)

            self._process_sql_statement(sql_text, object_name, "DataWindow", None)

        # Also look for table definitions
        table_pattern = r"table\s*\(\s*column\s*=\s*\(([^)]+)\)"
        matches = re.finditer(table_pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            column_defs = match.group(1)
            self._extract_datawindow_columns(column_defs, object_name)

    def _extract_datawindow_columns(self, column_defs: str, object_name: str) -> None:
        """Extract column definitions from DataWindow syntax."""
        # Parse column definitions
        column_pattern = r"name\s*=\s*(\w+)\.(\w+)"
        matches = re.finditer(column_pattern, column_defs, re.IGNORECASE)

        for match in matches:
            table_name = match.group(1)
            column_name = match.group(2)

            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)

            self.tables[table_name].add_column(column_name)
            self.tables[table_name].used_in_objects.add(object_name)

    def _extract_transaction_config(self, content: str, object_name: str) -> None:
        """Extract transaction object configurations."""
        # Look for transaction object definitions
        trans_pattern = r"transaction\s+(\w+)"
        matches = re.finditer(trans_pattern, content, re.IGNORECASE)

        for match in matches:
            trans_name = match.group(1)
            if trans_name not in self.transaction_objects:
                self.transaction_objects[trans_name] = {
                    "name": trans_name,
                    "used_in": set(),
                }
            self.transaction_objects[trans_name]["used_in"].add(object_name)

        # Look for SQLCA property settings
        sqlca_patterns = [
            r'SQLCA\.DBMS\s*=\s*["\']([^"\']+)["\']',
            r'SQLCA\.Database\s*=\s*["\']([^"\']+)["\']',
            r'SQLCA\.ServerName\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in sqlca_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if "sqlca" not in self.transaction_objects:
                    self.transaction_objects["sqlca"] = {
                        "name": "sqlca",
                        "properties": {},
                        "used_in": set(),
                    }
                prop_name = pattern.split(r"\.")[1].split(r"\s*")[0]
                self.transaction_objects["sqlca"]["properties"][prop_name] = (
                    match.group(1)
                )
                self.transaction_objects["sqlca"]["used_in"].add(object_name)

    def _extract_connection_strings(self, content: str, object_name: str) -> None:
        """Extract database connection strings."""
        # Look for connection string patterns
        conn_patterns = [
            r'ConnectString\s*=\s*["\']([^"\']+)["\']',
            r'DBParm\s*=\s*["\']([^"\']+)["\']',
            r'DSN\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in conn_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                conn_str = match.group(1)
                self.connection_strings[object_name] = conn_str

    def _process_sql_statement(
        self,
        sql_text: str,
        pb_object: str,
        pb_function: str | None,
        line_number: int | None,
    ) -> None:
        """Process a SQL statement and extract schema information."""
        try:
            # Parse the SQL statement
            parsed = self.sql_parser.parse(sql_text)

            if isinstance(parsed, list):
                statements = parsed
            else:
                statements = parsed.get("statements", [])

            for stmt in statements:
                if isinstance(stmt, SelectStatement):
                    self._process_select_statement(
                        stmt, pb_object, pb_function, line_number, sql_text
                    )
                elif isinstance(stmt, InsertStatement):
                    self._process_insert_statement(
                        stmt, pb_object, pb_function, line_number, sql_text
                    )
                elif isinstance(stmt, UpdateStatement):
                    self._process_update_statement(
                        stmt, pb_object, pb_function, line_number, sql_text
                    )
                elif isinstance(stmt, DeleteStatement):
                    self._process_delete_statement(
                        stmt, pb_object, pb_function, line_number, sql_text
                    )
                elif isinstance(stmt, dict):
                    # Legacy parser result
                    self._process_legacy_statement(
                        stmt, pb_object, pb_function, line_number
                    )

        except (ValueError, AttributeError) as e:
            logger.debug("Error parsing SQL statement: %s", e)
            # Fall back to regex-based extraction
            self._extract_tables_from_sql_text(sql_text, pb_object)

    def _process_select_statement(
        self,
        stmt: SelectStatement,
        pb_object: str,
        pb_function: str | None,
        line_number: int | None,
        sql_text: str,
    ) -> None:
        """Process a SELECT statement."""
        tables = []
        columns = []

        # Extract tables from FROM clause
        if stmt.from_clause:
            for table_ref in stmt.from_clause.tables:
                if isinstance(table_ref, TableReference):
                    table_name = table_ref.table_name
                    if table_name not in self.tables:
                        self.tables[table_name] = TableInfo(name=table_name)
                    self.tables[table_name].add_operation("SELECT", pb_object)
                    tables.append(table_name)

        # Extract columns from result columns
        for result_col in stmt.result_columns:
            if result_col.expression:
                if isinstance(result_col.expression, ColumnReference):
                    col_name = result_col.expression.column_name
                    columns.append(col_name)
                    # Add column to appropriate table
                    if result_col.expression.table_name:
                        table_name = result_col.expression.table_name
                        if table_name in self.tables:
                            self.tables[table_name].add_column(col_name)
                    elif tables:
                        # Add to first table if no
                        # table specified
                        self.tables[tables[0]].add_column(col_name)

        # Process JOIN clauses
        if stmt.from_clause and stmt.from_clause.joins:
            for join in stmt.from_clause.joins:
                self._process_join_clause(join, pb_object)

        # Record the operation
        self.operations.append(
            DatabaseOperation(
                operation_type="SELECT",
                tables=tables,
                columns=columns,
                pb_object=pb_object,
                pb_function=pb_function,
                line_number=line_number,
                sql_text=sql_text,
            )
        )

    def _process_insert_statement(
        self,
        stmt: InsertStatement,
        pb_object: str,
        pb_function: str | None,
        line_number: int | None,
        sql_text: str,
    ) -> None:
        """Process an INSERT statement."""
        if stmt.table and isinstance(stmt.table, TableReference):
            table_name = stmt.table.table_name
            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)

            self.tables[table_name].add_operation("INSERT", pb_object)

            # Add columns
            if stmt.columns:
                for col in stmt.columns:
                    self.tables[table_name].add_column(col)

            # Record the operation
            self.operations.append(
                DatabaseOperation(
                    operation_type="INSERT",
                    tables=[table_name],
                    columns=stmt.columns or [],
                    pb_object=pb_object,
                    pb_function=pb_function,
                    line_number=line_number,
                    sql_text=sql_text,
                )
            )

    def _process_update_statement(
        self,
        stmt: UpdateStatement,
        pb_object: str,
        pb_function: str | None,
        line_number: int | None,
        sql_text: str,
    ) -> None:
        """Process an UPDATE statement."""
        if stmt.table and isinstance(stmt.table, TableReference):
            table_name = stmt.table.table_name
            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)

            self.tables[table_name].add_operation("UPDATE", pb_object)

            # Add columns from assignments
            columns = []
            for assignment in stmt.assignments:
                col_name = assignment.target_column
                self.tables[table_name].add_column(col_name)
                columns.append(col_name)

            # Record the operation
            self.operations.append(
                DatabaseOperation(
                    operation_type="UPDATE",
                    tables=[table_name],
                    columns=columns,
                    pb_object=pb_object,
                    pb_function=pb_function,
                    line_number=line_number,
                    sql_text=sql_text,
                )
            )

    def _process_delete_statement(
        self,
        stmt: DeleteStatement,
        pb_object: str,
        pb_function: str | None,
        line_number: int | None,
        sql_text: str,
    ) -> None:
        """Process a DELETE statement."""
        if stmt.table and isinstance(stmt.table, TableReference):
            table_name = stmt.table.table_name
            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)

            self.tables[table_name].add_operation("DELETE", pb_object)

            # Record the operation
            self.operations.append(
                DatabaseOperation(
                    operation_type="DELETE",
                    tables=[table_name],
                    columns=[],
                    pb_object=pb_object,
                    pb_function=pb_function,
                    line_number=line_number,
                    sql_text=sql_text,
                )
            )

    def _process_legacy_statement(
        self,
        stmt_dict: dict,
        pb_object: str,
        pb_function: str | None,
        line_number: int | None,
    ) -> None:
        """Process a legacy parser statement dictionary."""
        stmt_type = stmt_dict.get("type", "UNKNOWN")
        tables = stmt_dict.get("tables", [])
        columns = []

        for table_name in tables:
            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)
            self.tables[table_name].add_operation(stmt_type, pb_object)

        # Extract columns
        for col_info in stmt_dict.get("columns", []):
            if isinstance(col_info, dict):
                col_name = col_info.get("expression", "")
                if col_name and col_name != "*":
                    columns.append(col_name)
                    if tables:
                        self.tables[tables[0]].add_column(col_name)

        # Record the operation
        self.operations.append(
            DatabaseOperation(
                operation_type=stmt_type,
                tables=tables,
                columns=columns,
                pb_object=pb_object,
                pb_function=pb_function,
                line_number=line_number,
                sql_text=stmt_dict.get("text", ""),
            )
        )

    def _process_join_clause(self, join: JoinClause, pb_object: str) -> None:
        """Process a JOIN clause to extract relationships."""
        if join.table and isinstance(join.table, TableReference):
            right_table = join.table.table_name

            # Try to extract join condition
            if join.on_condition:
                # This is simplified - in reality we'd need to parse the condition
                # to extract the exact columns being joined
                logger.debug("Found join to %s in %s", right_table, pb_object)

    def _extract_tables_from_sql_text(self, sql_text: str, pb_object: str) -> None:
        """Extract tables from SQL text using regex (fallback method)."""
        # Extract table names from FROM clause
        from_pattern = r"FROM\s+(\w+)(?:\s+(\w+))?"
        matches = re.finditer(from_pattern, sql_text, re.IGNORECASE)

        for match in matches:
            table_name = match.group(1)
            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)
            self.tables[table_name].used_in_objects.add(pb_object)

        # Extract from JOIN clauses
        join_pattern = r"JOIN\s+(\w+)(?:\s+(\w+))?"
        matches = re.finditer(join_pattern, sql_text, re.IGNORECASE)

        for match in matches:
            table_name = match.group(1)
            if table_name not in self.tables:
                self.tables[table_name] = TableInfo(name=table_name)
            self.tables[table_name].used_in_objects.add(pb_object)

    def _analyze_relationships(self) -> None:
        """Analyze and identify table relationships."""
        # Look for foreign key patterns in column names
        for table_name, table_info in self.tables.items():
            for column in table_info.columns:
                # Common FK patterns: table_id, tableid, id_table
                fk_patterns = [
                    r"(\w+)_id$",
                    r"(\w+)id$",
                    r"id_(\w+)$",
                ]

                for pattern in fk_patterns:
                    match = re.match(pattern, column, re.IGNORECASE)
                    if match:
                        potential_ref_table = match.group(1)
                        # Check if referenced table exists
                        if potential_ref_table in self.tables:
                            table_info.foreign_keys[column] = (
                                f"{potential_ref_table}.id"
                            )

                            # Create relationship
                            rel = RelationshipInfo(
                                from_table=table_name,
                                from_column=column,
                                to_table=potential_ref_table,
                                to_column="id",
                                relationship_type="many-to-one",
                            )
                            self.relationships.append(rel)

        # Look for many-to-many junction tables
        for table_name in self.tables:
            # Junction tables often have names like
            # table1_table2
            if "_" in table_name:
                parts = table_name.split("_")
                if (
                    len(parts) == 2
                    and parts[0] in self.tables
                    and parts[1] in self.tables
                ):
                    # This might be a junction table
                    logger.info("Potential junction table found: %s", table_name)

    def _build_schema_result(self) -> dict[str, Any]:
        """Build the final schema result dictionary."""
        return {
            "tables": {
                name: {
                    "name": info.name,
                    "columns": sorted(info.columns),
                    "primary_keys": sorted(info.primary_keys),
                    "foreign_keys": info.foreign_keys,
                    "indexes": sorted(info.indexes),
                    "used_in_objects": sorted(info.used_in_objects),
                    "operations": dict(info.operations),
                }
                for name, info in self.tables.items()
            },
            "relationships": [
                {
                    "from_table": rel.from_table,
                    "from_column": rel.from_column,
                    "to_table": rel.to_table,
                    "to_column": rel.to_column,
                    "type": rel.relationship_type,
                    "join_type": rel.join_type,
                    "used_in_objects": sorted(rel.used_in_objects),
                }
                for rel in self.relationships
            ],
            "operations": [
                {
                    "type": op.operation_type,
                    "tables": op.tables,
                    "columns": op.columns,
                    "object": op.pb_object,
                    "function": op.pb_function,
                    "line": op.line_number,
                }
                for op in self.operations
            ],
            "connection_strings": self.connection_strings,
            "transaction_objects": {
                name: {
                    "name": info["name"],
                    "properties": info.get("properties", {}),
                    "used_in": sorted(info["used_in"]),
                }
                for name, info in self.transaction_objects.items()
            },
            "statistics": {
                "total_tables": len(self.tables),
                "total_columns": sum(len(t.columns) for t in self.tables.values()),
                "total_relationships": len(self.relationships),
                "total_operations": len(self.operations),
                "operation_counts": self._get_operation_counts(),
            },
        }

    def _get_operation_counts(self) -> dict[str, int]:
        """Get counts of each operation type."""
        counts = defaultdict(int)
        for op in self.operations:
            counts[op.operation_type] += 1
        return dict(counts)
