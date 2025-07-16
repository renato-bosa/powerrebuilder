"""Database operation formatter for converting PowerBuilder SQL to target database systems.

This module handles the conversion of PowerBuilder embedded SQL and DataWindow SQL
to various target database systems (PostgreSQL, MySQL, SQLite, etc.).
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


class DatabaseOperationFormatter:
    """Formats PowerBuilder database operations for target database systems."""

    def __init__(self, target_db: str = "postgresql"):
        """Initialize the database operation formatter.

        Args:
            target_db: Target database system ('postgresql', 'mysql', 'sqlite')
        """
        self.target_db = target_db.lower()

        # PowerBuilder to target DB function mappings
        self.function_map = {
            "postgresql": {
                "getdate()": "CURRENT_TIMESTAMP",
                "dateformat": "TO_CHAR",
                "convert": "CAST",
                "isnull": "COALESCE",
                "len": "LENGTH",
                "substring": "SUBSTRING",
                "charindex": "POSITION",
                "ltrim": "LTRIM",
                "rtrim": "RTRIM",
                "upper": "UPPER",
                "lower": "LOWER",
            },
            "mysql": {
                "getdate()": "NOW()",
                "dateformat": "DATE_FORMAT",
                "convert": "CAST",
                "isnull": "IFNULL",
                "len": "LENGTH",
                "substring": "SUBSTRING",
                "charindex": "LOCATE",
                "ltrim": "LTRIM",
                "rtrim": "RTRIM",
                "upper": "UPPER",
                "lower": "LOWER",
            },
            "sqlite": {
                "getdate()": "datetime('now')",
                "dateformat": "strftime",
                "convert": "CAST",
                "isnull": "IFNULL",
                "len": "LENGTH",
                "substring": "SUBSTR",
                "charindex": "INSTR",
                "ltrim": "LTRIM",
                "rtrim": "RTRIM",
                "upper": "UPPER",
                "lower": "LOWER",
            }
        }

        # PowerBuilder to target DB data type mappings
        self.type_map = {
            "postgresql": {
                "char": "VARCHAR",
                "varchar": "VARCHAR",
                "long varchar": "TEXT",
                "integer": "INTEGER",
                "smallint": "SMALLINT",
                "decimal": "DECIMAL",
                "number": "NUMERIC",
                "float": "REAL",
                "real": "REAL",
                "double": "DOUBLE PRECISION",
                "datetime": "TIMESTAMP",
                "date": "DATE",
                "time": "TIME",
                "blob": "BYTEA",
            },
            "mysql": {
                "char": "VARCHAR",
                "varchar": "VARCHAR",
                "long varchar": "TEXT",
                "integer": "INT",
                "smallint": "SMALLINT",
                "decimal": "DECIMAL",
                "number": "DECIMAL",
                "float": "FLOAT",
                "real": "FLOAT",
                "double": "DOUBLE",
                "datetime": "DATETIME",
                "date": "DATE",
                "time": "TIME",
                "blob": "BLOB",
            },
            "sqlite": {
                "char": "TEXT",
                "varchar": "TEXT",
                "long varchar": "TEXT",
                "integer": "INTEGER",
                "smallint": "INTEGER",
                "decimal": "REAL",
                "number": "REAL",
                "float": "REAL",
                "real": "REAL",
                "double": "REAL",
                "datetime": "TEXT",
                "date": "TEXT",
                "time": "TEXT",
                "blob": "BLOB",
            }
        }

    def format_sql(self, sql: str) -> str:
        """Format PowerBuilder SQL for the target database.

        Args:
            sql: PowerBuilder SQL statement

        Returns:
            Formatted SQL for target database
        """
        if not sql:
            return sql

        # Convert functions
        sql = self._convert_functions(sql)

        # Convert data types in DDL
        sql = self._convert_data_types(sql)

        # Handle PowerBuilder-specific syntax
        sql = self._handle_pb_specific_syntax(sql)

        # Format for target database
        sql = self._format_for_target_db(sql)

        return sql

    def _convert_functions(self, sql: str) -> str:
        """Convert PowerBuilder functions to target database functions."""
        if self.target_db not in self.function_map:
            return sql

        function_map = self.function_map[self.target_db]

        for pb_func, target_func in function_map.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(pb_func), re.IGNORECASE)
            sql = pattern.sub(target_func, sql)

        return sql

    def _convert_data_types(self, sql: str) -> str:
        """Convert PowerBuilder data types in DDL statements."""
        if self.target_db not in self.type_map:
            return sql

        type_map = self.type_map[self.target_db]

        # Only convert in CREATE TABLE or ALTER TABLE statements
        if "CREATE TABLE" in sql.upper() or "ALTER TABLE" in sql.upper():
            for pb_type, target_type in type_map.items():
                # Match data type declarations
                pattern = rf'\b{re.escape(pb_type)}\b(?=\s*(\(|\s|,|$))'
                sql = re.sub(pattern, target_type, sql, flags=re.IGNORECASE)

        return sql

    def _handle_pb_specific_syntax(self, sql: str) -> str:
        """Handle PowerBuilder-specific SQL syntax."""
        # Convert PowerBuilder parameter markers
        sql = self._convert_parameter_markers(sql)

        # Handle PowerBuilder-specific joins
        sql = self._convert_pb_joins(sql)

        # Handle PowerBuilder outer join syntax (+)
        sql = self._convert_outer_joins(sql)

        return sql

    def _convert_parameter_markers(self, sql: str) -> str:
        """Convert PowerBuilder parameter markers to target format."""
        if self.target_db == "postgresql":
            # Convert :param to $1, $2, etc.
            params = re.findall(r':(\w+)', sql)
            for i, param in enumerate(params, 1):
                sql = sql.replace(f':{param}', f'${i}')
        elif self.target_db in ("mysql", "sqlite"):
            # Convert :param to ?
            sql = re.sub(r':(\w+)', '?', sql)

        return sql

    def _convert_pb_joins(self, sql: str) -> str:
        """Convert PowerBuilder-specific join syntax."""
        # PowerBuilder uses *= for left outer join and =* for right outer join
        sql = re.sub(r'(\w+\.\w+)\s*\*=\s*(\w+\.\w+)', r'\1 = \2', sql)
        sql = re.sub(r'(\w+\.\w+)\s*=\*\s*(\w+\.\w+)', r'\1 = \2', sql)

        return sql

    def _convert_outer_joins(self, sql: str) -> str:
        """Convert Oracle-style outer joins to ANSI syntax."""
        # Convert table.column(+) to proper LEFT/RIGHT JOIN
        # This is a simplified conversion - real implementation would need full parsing
        if '(+)' in sql:
            logger.warning("Oracle-style outer join syntax detected. Manual review recommended.")
            sql = sql.replace('(+)', '')

        return sql

    def _format_for_target_db(self, sql: str) -> str:
        """Apply target database-specific formatting."""
        if self.target_db == "postgresql":
            # PostgreSQL-specific formatting
            # Convert double quotes to appropriate identifier quotes
            sql = re.sub(r'"(\w+)"', r'"\1"', sql)
        elif self.target_db == "mysql":
            # MySQL-specific formatting
            # Convert double quotes to backticks for identifiers
            sql = re.sub(r'"(\w+)"', r'`\1`', sql)
        elif self.target_db == "sqlite":
            # SQLite-specific formatting
            # SQLite is more permissive, but we'll keep standard quotes
            pass

        return sql

    def format_datawindow_sql(self, dw_sql: str) -> Tuple[str, List[str]]:
        """Format DataWindow SQL and extract retrieval arguments.

        Args:
            dw_sql: DataWindow SQL syntax

        Returns:
            Tuple of (formatted SQL, list of retrieval arguments)
        """
        # Extract retrieval arguments
        retrieval_args = []
        arg_pattern = r'retrieval_args\s*=\s*"([^"]*)"'
        match = re.search(arg_pattern, dw_sql)
        if match:
            args_str = match.group(1)
            retrieval_args = [arg.strip() for arg in args_str.split(',')]

        # Extract the actual SQL
        sql_pattern = r'retrieve\s*=\s*"([^"]*)"'
        match = re.search(sql_pattern, dw_sql)
        if match:
            sql = match.group(1)
            # Format the SQL
            sql = self.format_sql(sql)
        else:
            sql = dw_sql

        return sql, retrieval_args

    def generate_orm_query(self, sql: str, orm_type: str = "sqlalchemy") -> str:
        """Generate ORM query code from SQL.

        Args:
            sql: SQL statement
            orm_type: Type of ORM ('sqlalchemy', 'django', 'sqlmodel')

        Returns:
            ORM query code
        """
        # This is a simplified example - real implementation would need SQL parsing
        if orm_type == "sqlalchemy":
            if sql.upper().startswith("SELECT"):
                return self._generate_sqlalchemy_select(sql)
            elif sql.upper().startswith("INSERT"):
                return self._generate_sqlalchemy_insert(sql)
            elif sql.upper().startswith("UPDATE"):
                return self._generate_sqlalchemy_update(sql)
            elif sql.upper().startswith("DELETE"):
                return self._generate_sqlalchemy_delete(sql)

        return f"# TODO: Convert SQL to {orm_type} ORM:\n# {sql}"

    def _generate_sqlalchemy_select(self, sql: str) -> str:
        """Generate SQLAlchemy select query."""
        # Extract table name (simplified)
        table_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"session.query({table}).all()"
        return "# TODO: Parse SELECT statement"

    def _generate_sqlalchemy_insert(self, sql: str) -> str:
        """Generate SQLAlchemy insert statement."""
        # Extract table name (simplified)
        table_match = re.search(r'INSERT\s+INTO\s+(\w+)', sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"new_{table.lower()} = {table}(**data)\nsession.add(new_{table.lower()})\nsession.commit()"
        return "# TODO: Parse INSERT statement"

    def _generate_sqlalchemy_update(self, sql: str) -> str:
        """Generate SQLAlchemy update statement."""
        # Extract table name (simplified)
        table_match = re.search(r'UPDATE\s+(\w+)', sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"session.query({table}).filter_by(**conditions).update(values)"
        return "# TODO: Parse UPDATE statement"

    def _generate_sqlalchemy_delete(self, sql: str) -> str:
        """Generate SQLAlchemy delete statement."""
        # Extract table name (simplified)
        table_match = re.search(r'DELETE\s+FROM\s+(\w+)', sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"session.query({table}).filter_by(**conditions).delete()"
        return "# TODO: Parse DELETE statement"