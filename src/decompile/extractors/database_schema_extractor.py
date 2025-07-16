"""Database schema extractor for PowerBuilder applications."""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Any


@dataclass
class DatabaseOperation:
    """Represents a database operation (SELECT, INSERT, UPDATE, DELETE)."""

    operation_type: str
    tables: List[str]
    columns: List[str]
    conditions: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None


class DatabaseSchemaExtractor:
    """Extracts database schema information from PowerBuilder code."""

    def __init__(self):
        """Initialize the schema extractor."""
        self.operations: List[DatabaseOperation] = []
        self.tables: Dict[str, Set[str]] = {}
        self.relationships: List[Dict[str, str]] = []

    def extract_operation(self, sql: str, source_file: str = None, line_number: int = None) -> DatabaseOperation:
        """Extract database operation from SQL statement.

        Args:
            sql: SQL statement
            source_file: Source file containing the SQL
            line_number: Line number in source file

        Returns:
            DatabaseOperation object
        """
        # TODO: Implement SQL parsing
        # For now, return a stub operation
        return DatabaseOperation(
            operation_type="SELECT",
            tables=[],
            columns=[],
            source_file=source_file,
            line_number=line_number
        )

    def add_table(self, table_name: str, columns: List[str]) -> None:
        """Add a table and its columns to the schema.

        Args:
            table_name: Name of the table
            columns: List of column names
        """
        if table_name not in self.tables:
            self.tables[table_name] = set()
        self.tables[table_name].update(columns)

    def add_relationship(self, from_table: str, from_column: str, to_table: str, to_column: str) -> None:
        """Add a foreign key relationship.

        Args:
            from_table: Source table
            from_column: Source column
            to_table: Target table
            to_column: Target column
        """
        self.relationships.append({
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column
        })

    def get_schema_summary(self) -> Dict[str, Any]:
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
                "total_relationships": len(self.relationships)
            }
        }