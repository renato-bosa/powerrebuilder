"""Database schema extractor for PowerBuilder applications."""

import re
from dataclasses import dataclass
from typing import Any

from ...model.ast.nodes.sql import (
    ColumnReference,
    DeleteStatement,
    InsertStatement,
    SelectStatement,
    TableReference,
    UpdateStatement,
)
from ...parse.parser.sql import SQLParser


@dataclass
class DatabaseOperation:
    """Represents a database operation (SELECT, INSERT, UPDATE, DELETE)."""

    operation_type: str
    tables: list[str]
    columns: list[str]
    conditions: str | None = None
    source_file: str | None = None
    line_number: int | None = None


class DatabaseSchemaExtractor:
    """Extracts database schema information from PowerBuilder code."""

    def __init__(self) -> None:
        """Initialize the schema extractor."""
        self.operations: list[DatabaseOperation] = []
        self.tables: dict[str, set[str]] = {}
        self.relationships: list[dict[str, str]] = []
        self.sql_parser = SQLParser()

    def extract_operation(
        self, sql: str, source_file: str | None = None, line_number: int | None = None
    ) -> DatabaseOperation:
        """Extract database operation from SQL statement.

        Args:
            sql: SQL statement
            source_file: Source file containing the SQL
            line_number: Line number in source file

        Returns:
            DatabaseOperation object
        """
        # First try to parse with SQL parser
        try:
            parsed = self.sql_parser.parse(sql)

            # Handle different statement types
            if isinstance(parsed, list) and parsed:
                stmt = parsed[0]
            elif isinstance(parsed, dict) and "statements" in parsed:
                stmt = parsed["statements"][0] if parsed["statements"] else None
            else:
                stmt = parsed

            if isinstance(stmt, SelectStatement):
                return self._extract_from_select(stmt, source_file, line_number)
            if isinstance(stmt, InsertStatement):
                return self._extract_from_insert(stmt, source_file, line_number)
            if isinstance(stmt, UpdateStatement):
                return self._extract_from_update(stmt, source_file, line_number)
            if isinstance(stmt, DeleteStatement):
                return self._extract_from_delete(stmt, source_file, line_number)

        except Exception:
            # Fall back to regex parsing
            pass

        # Fallback to regex-based extraction
        return self._extract_with_regex(sql, source_file, line_number)

    def _extract_from_select(
        self, stmt: SelectStatement, source_file: str | None, line_number: int | None
    ) -> DatabaseOperation:
        """Extract operation from parsed SELECT statement."""
        tables = []
        columns = []

        # Extract tables from FROM clause
        if stmt.from_clause:
            for table_ref in stmt.from_clause.tables:
                if isinstance(table_ref, TableReference):
                    tables.append(table_ref.table_name)

        # Extract columns from result columns
        for result_col in stmt.result_columns:
            if result_col.expression and isinstance(
                result_col.expression, ColumnReference
            ):
                columns.append(result_col.expression.column_name)
                # Also track which table this column belongs to
                if (
                    result_col.expression.table_name
                    and result_col.expression.table_name in tables
                ):
                    self.add_table(
                        result_col.expression.table_name,
                        [result_col.expression.column_name],
                    )

        # Track table columns
        for table in tables:
            self.add_table(table, columns)

        # Extract conditions
        conditions = None
        if stmt.where_clause and stmt.where_clause.condition:
            conditions = str(stmt.where_clause.condition)

        return DatabaseOperation(
            operation_type="SELECT",
            tables=tables,
            columns=columns,
            conditions=conditions,
            source_file=source_file,
            line_number=line_number,
        )

    def _extract_from_insert(
        self, stmt: InsertStatement, source_file: str | None, line_number: int | None
    ) -> DatabaseOperation:
        """Extract operation from parsed INSERT statement."""
        tables = []
        columns = stmt.columns or []

        if stmt.table and isinstance(stmt.table, TableReference):
            table_name = stmt.table.table_name
            tables.append(table_name)
            self.add_table(table_name, columns)

        return DatabaseOperation(
            operation_type="INSERT",
            tables=tables,
            columns=columns,
            source_file=source_file,
            line_number=line_number,
        )

    def _extract_from_update(
        self, stmt: UpdateStatement, source_file: str | None, line_number: int | None
    ) -> DatabaseOperation:
        """Extract operation from parsed UPDATE statement."""
        tables = []
        columns = []

        if stmt.table and isinstance(stmt.table, TableReference):
            table_name = stmt.table.table_name
            tables.append(table_name)

            # Extract columns from assignments
            for assignment in stmt.assignments:
                columns.append(assignment.target_column)

            self.add_table(table_name, columns)

        # Extract conditions
        conditions = None
        if stmt.where_clause and stmt.where_clause.condition:
            conditions = str(stmt.where_clause.condition)

        return DatabaseOperation(
            operation_type="UPDATE",
            tables=tables,
            columns=columns,
            conditions=conditions,
            source_file=source_file,
            line_number=line_number,
        )

    def _extract_from_delete(
        self, stmt: DeleteStatement, source_file: str | None, line_number: int | None
    ) -> DatabaseOperation:
        """Extract operation from parsed DELETE statement."""
        tables = []

        if stmt.table and isinstance(stmt.table, TableReference):
            tables.append(stmt.table.table_name)

        # Extract conditions
        conditions = None
        if stmt.where_clause and stmt.where_clause.condition:
            conditions = str(stmt.where_clause.condition)

        return DatabaseOperation(
            operation_type="DELETE",
            tables=tables,
            columns=[],
            conditions=conditions,
            source_file=source_file,
            line_number=line_number,
        )

    def _extract_with_regex(
        self, sql: str, source_file: str | None, line_number: int | None
    ) -> DatabaseOperation:
        """Extract operation using regex patterns (fallback method)."""
        sql_upper = sql.upper()
        tables = []
        columns = []
        operation_type = "UNKNOWN"
        conditions = None

        # Determine operation type
        if "SELECT" in sql_upper:
            operation_type = "SELECT"
            # Extract tables from FROM clause
            from_match = re.search(r"FROM\s+(\w+(?:\s*,\s*\w+)*)", sql, re.IGNORECASE)
            if from_match:
                table_list = from_match.group(1)
                tables = [t.strip() for t in table_list.split(",")]

            # Extract columns from SELECT clause
            select_match = re.search(
                r"SELECT\s+(.+?)\s+FROM", sql, re.IGNORECASE | re.DOTALL
            )
            if select_match:
                col_list = select_match.group(1)
                # Simple column extraction (doesn't handle complex expressions)
                col_names = re.findall(r"\b(\w+)\b", col_list)
                columns = [
                    c
                    for c in col_names
                    if c.upper() not in ["SELECT", "DISTINCT", "AS"]
                ]

        elif "INSERT" in sql_upper:
            operation_type = "INSERT"
            # Extract table name
            insert_match = re.search(r"INSERT\s+INTO\s+(\w+)", sql, re.IGNORECASE)
            if insert_match:
                tables.append(insert_match.group(1))

            # Extract column names
            cols_match = re.search(
                r"INSERT\s+INTO\s+\w+\s*\(([^)]+)\)", sql, re.IGNORECASE
            )
            if cols_match:
                col_list = cols_match.group(1)
                columns = [c.strip() for c in col_list.split(",")]

        elif "UPDATE" in sql_upper:
            operation_type = "UPDATE"
            # Extract table name
            update_match = re.search(r"UPDATE\s+(\w+)", sql, re.IGNORECASE)
            if update_match:
                tables.append(update_match.group(1))

            # Extract column names from SET clause
            set_matches = re.findall(r"(\w+)\s*=", sql)
            columns = list(set(set_matches))  # Remove duplicates

        elif "DELETE" in sql_upper:
            operation_type = "DELETE"
            # Extract table name
            delete_match = re.search(r"DELETE\s+FROM\s+(\w+)", sql, re.IGNORECASE)
            if delete_match:
                tables.append(delete_match.group(1))

        # Extract WHERE conditions
        where_match = re.search(
            r"WHERE\s+(.+?)(?:GROUP|ORDER|$)", sql, re.IGNORECASE | re.DOTALL
        )
        if where_match:
            conditions = where_match.group(1).strip()

        # Track tables and columns
        for table in tables:
            self.add_table(table, columns)

        # Create and store operation
        operation = DatabaseOperation(
            operation_type=operation_type,
            tables=tables,
            columns=columns,
            conditions=conditions,
            source_file=source_file,
            line_number=line_number,
        )
        self.operations.append(operation)

        return operation

    def add_table(self, table_name: str, columns: list[str]) -> None:
        """Add a table and its columns to the schema.

        Args:
            table_name: Name of the table
            columns: List of column names
        """
        if table_name not in self.tables:
            self.tables[table_name] = set()
        self.tables[table_name].update(columns)

    def add_relationship(
        self, from_table: str, from_column: str, to_table: str, to_column: str
    ) -> None:
        """Add a foreign key relationship.

        Args:
            from_table: Source table
            from_column: Source column
            to_table: Target table
            to_column: Target column
        """
        self.relationships.append(
            {
                "from_table": from_table,
                "from_column": from_column,
                "to_table": to_table,
                "to_column": to_column,
            }
        )

    def get_schema_summary(self) -> dict[str, Any]:
        """Get a summary of the extracted schema.

        Returns:
            Dictionary containing schema information
        """
        return {
            "tables": {name: list(cols) for name, cols in self.tables.items()},
            "relationships": self.relationships,
            "operations": len(self.operations),
            "statistics": {
                "total_tables": len(self.tables),
                "total_columns": sum(len(cols) for cols in self.tables.values()),
                "total_relationships": len(self.relationships),
            },
        }
