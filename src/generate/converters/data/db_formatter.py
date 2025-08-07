"""Database operation formatter for converting PowerBuilder SQL to target database systems.

This module handles the conversion of PowerBuilder embedded SQL and DataWindow SQL
to various target database systems (PostgreSQL, MySQL, SQLite, etc.).
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseOperationFormatter:
    """Formats PowerBuilder database operations for target database systems."""

    def __init__(self, target_db: str = "postgresql") -> None:
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
            },
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
            },
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
        return self._format_for_target_db(sql)

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
                pattern = rf"\b{re.escape(pb_type)}\b(?=\s*(\(|\s|,|$))"
                sql = re.sub(pattern, target_type, sql, flags=re.IGNORECASE)

        return sql

    def _handle_pb_specific_syntax(self, sql: str) -> str:
        """Handle PowerBuilder-specific SQL syntax."""
        # Convert PowerBuilder parameter markers
        sql = self._convert_parameter_markers(sql)

        # Handle PowerBuilder-specific joins
        sql = self._convert_pb_joins(sql)

        # Handle PowerBuilder outer join syntax (+)
        return self._convert_outer_joins(sql)

    def _convert_parameter_markers(self, sql: str) -> str:
        """Convert PowerBuilder parameter markers to target format."""
        if self.target_db == "postgresql":
            # Convert :param to $1, $2, etc.
            params = re.findall(r":(\w+)", sql)
            for i, param in enumerate(params, 1):
                sql = sql.replace(f":{param}", f"${i}")
        elif self.target_db in ("mysql", "sqlite"):
            # Convert :param to ?
            sql = re.sub(r":(\w+)", "?", sql)

        return sql

    def _convert_pb_joins(self, sql: str) -> str:
        """Convert PowerBuilder-specific join syntax."""
        # PowerBuilder uses *= for left outer join and =* for right outer join
        sql = re.sub(r"(\w+\.\w+)\s*\*=\s*(\w+\.\w+)", r"\1 = \2", sql)
        return re.sub(r"(\w+\.\w+)\s*=\*\s*(\w+\.\w+)", r"\1 = \2", sql)

    def _convert_outer_joins(self, sql: str) -> str:
        """Convert Oracle-style outer joins to ANSI syntax."""
        # Convert table.column(+) to proper LEFT/RIGHT JOIN
        # This is a simplified conversion - real implementation would need full
        # parsing
        if "(+)" in sql:
            logger.warning(
                "Oracle-style outer join syntax detected. Manual review recommended."
            )
            sql = sql.replace("(+)", "")

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
            sql = re.sub(r'"(\w+)"', r"`\1`", sql)
        elif self.target_db == "sqlite":
            # SQLite-specific formatting
            # SQLite is more permissive, but we'll keep standard quotes
            pass

        return sql

    def format_datawindow_sql(self, dw_sql: str) -> tuple[str, list[str]]:
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
            retrieval_args = [arg.strip() for arg in args_str.split(",")]

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
        # This is a simplified example - real implementation would need SQL
        # parsing
        if orm_type == "sqlalchemy":
            if sql.upper().startswith("SELECT"):
                return self._generate_sqlalchemy_select(sql)
            if sql.upper().startswith("INSERT"):
                return self._generate_sqlalchemy_insert(sql)
            if sql.upper().startswith("UPDATE"):
                return self._generate_sqlalchemy_update(sql)
            if sql.upper().startswith("DELETE"):
                return self._generate_sqlalchemy_delete(sql)

        return f"# TODO: Convert SQL to {orm_type} ORM:\n# {sql}"

    def _generate_sqlalchemy_select(self, sql: str) -> str:
        """Generate SQLAlchemy select query."""
        # Extract table name (simplified)
        table_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"session.query({table}).all()"
        return "# TODO: Parse SELECT statement"

    def _generate_sqlalchemy_insert(self, sql: str) -> str:
        """Generate SQLAlchemy insert statement."""
        # Extract table name (simplified)
        table_match = re.search(r"INSERT\s+INTO\s+(\w+)", sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"new_{table.lower()} = {table}(**data)\nsession.add(new_{table.lower()})\nsession.commit()"
        return "# TODO: Parse INSERT statement"

    def _generate_sqlalchemy_update(self, sql: str) -> str:
        """Generate SQLAlchemy update statement."""
        # Extract table name (simplified)
        table_match = re.search(r"UPDATE\s+(\w+)", sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"session.query({table}).filter_by(**conditions).update(values)"
        return "# TODO: Parse UPDATE statement"

    def _generate_sqlalchemy_delete(self, sql: str) -> str:
        """Generate SQLAlchemy delete statement."""
        # Extract table name (simplified)
        table_match = re.search(r"DELETE\s+FROM\s+(\w+)", sql, re.IGNORECASE)
        if table_match:
            table = table_match.group(1)
            return f"session.query({table}).filter_by(**conditions).delete()"
        return "# TODO: Parse DELETE statement"

    def format_select(self, select_node: Any, target_lang: str = "python") -> str:
        """Format a SELECT statement AST node for the target language.

        Args:
            select_node: SelectStatement AST node
            target_lang: Target language ('python', 'dart')

        Returns:
            Formatted query code for target language
        """
        if target_lang == "python":
            return self._format_select_python(select_node)
        if target_lang == "dart":
            return self._format_select_dart(select_node)
        return f"// Unsupported target language: {target_lang}"

    def _format_select_python(self, select_node: Any) -> str:
        """Format SELECT for Python/SQLAlchemy."""
        lines = []

        # Extract main table
        main_table = None
        if hasattr(select_node, "from_clause") and select_node.from_clause:
            if select_node.from_clause.tables:
                main_table = select_node.from_clause.tables[0]
                if hasattr(main_table, "table_name"):
                    main_table = main_table.table_name

        if not main_table:
            return "# Unable to determine main table for query"

        # Start building query
        lines.append(f"query = session.query({main_table})")

        # Handle joins
        if hasattr(select_node, "from_clause") and select_node.from_clause:
            for join in select_node.from_clause.joins:
                join_table = (
                    join.table.table_name
                    if hasattr(join.table, "table_name")
                    else str(join.table)
                )
                join_type = join.join_operator.upper()

                if "LEFT" in join_type:
                    lines.append(f"query = query.outerjoin({join_table})")
                elif "RIGHT" in join_type:
                    lines.append(
                        "# Note: SQLAlchemy doesn't support right joins directly"
                    )
                    lines.append("# Consider restructuring as left join")
                elif "FULL" in join_type:
                    lines.append(f"query = query.outerjoin({join_table}, full=True)")
                else:
                    lines.append(f"query = query.join({join_table})")

                # Add join condition if present
                if join.on_condition:
                    lines.append(
                        f"# Join condition: {self._expression_to_string(join.on_condition)}"
                    )

        # Handle WHERE clause
        if hasattr(select_node, "where_clause") and select_node.where_clause:
            condition = self._convert_condition_to_sqlalchemy(
                select_node.where_clause.condition
            )
            lines.append(f"query = query.filter({condition})")

        # Handle GROUP BY
        if hasattr(select_node, "group_by_clause") and select_node.group_by_clause:
            for expr in select_node.group_by_clause.expressions:
                col_ref = self._expression_to_column_ref(expr)
                lines.append(f"query = query.group_by({col_ref})")

        # Handle HAVING
        if hasattr(select_node, "having_clause") and select_node.having_clause:
            condition = self._convert_condition_to_sqlalchemy(
                select_node.having_clause.condition
            )
            lines.append(f"query = query.having({condition})")

        # Handle ORDER BY
        if hasattr(select_node, "order_by_clause") and select_node.order_by_clause:
            for term in select_node.order_by_clause.terms:
                col_ref = self._expression_to_column_ref(term.expression)
                if term.direction and term.direction.upper() == "DESC":
                    lines.append(f"query = query.order_by({col_ref}.desc())")
                else:
                    lines.append(f"query = query.order_by({col_ref})")

        # Handle LIMIT/OFFSET
        if hasattr(select_node, "limit_clause") and select_node.limit_clause:
            if select_node.limit_clause.limit:
                limit_val = self._expression_to_string(select_node.limit_clause.limit)
                lines.append(f"query = query.limit({limit_val})")
            if select_node.limit_clause.offset:
                offset_val = self._expression_to_string(select_node.limit_clause.offset)
                lines.append(f"query = query.offset({offset_val})")

        # Execute query
        lines.append("\n# Execute query")
        lines.append("results = query.all()")

        return "\n".join(lines)

    def _format_select_dart(self, select_node: Any) -> str:
        """Format SELECT for Dart/Flutter."""
        lines = []
        parameters = []

        # Build SQL string with parameter placeholders
        sql_parts = ["SELECT"]

        # Handle DISTINCT
        if hasattr(select_node, "distinct_clause") and select_node.distinct_clause:
            sql_parts.append("DISTINCT")

        # Handle columns
        if hasattr(select_node, "result_columns") and select_node.result_columns:
            columns = []
            for col in select_node.result_columns:
                if hasattr(col, "expression"):
                    columns.append(self._expression_to_string(col.expression))
                else:
                    columns.append("*")
            sql_parts.append(", ".join(columns))
        else:
            sql_parts.append("*")

        # Handle FROM
        if hasattr(select_node, "from_clause") and select_node.from_clause:
            sql_parts.append("FROM")
            tables = []
            for table in select_node.from_clause.tables:
                if hasattr(table, "table_name"):
                    table_str = table.table_name
                    if hasattr(table, "alias") and table.alias:
                        table_str += f" AS {table.alias}"
                    tables.append(table_str)
            sql_parts.append(", ".join(tables))

            # Handle JOINs
            for join in select_node.from_clause.joins:
                join_type = join.join_operator.upper()
                table_name = (
                    join.table.table_name
                    if hasattr(join.table, "table_name")
                    else str(join.table)
                )
                sql_parts.append(f"{join_type} {table_name}")
                if join.on_condition:
                    sql_parts.append(
                        f"ON {self._expression_to_string(join.on_condition)}"
                    )

        # Handle WHERE clause
        if hasattr(select_node, "where_clause") and select_node.where_clause:
            sql_parts.append("WHERE")
            where_sql, where_params = self._convert_condition_to_dart(
                select_node.where_clause.condition
            )
            sql_parts.append(where_sql)
            parameters.extend(where_params)

        # Build complete SQL
        sql = " ".join(sql_parts)

        # Generate Dart code
        lines.append("// Execute SQL query")
        lines.append(f'final sql = "{sql}";')

        if parameters:
            lines.append(f"final params = {parameters};")
            lines.append(
                "final List<Map<String, dynamic>> results = await db.rawQuery(sql, params);"
            )
        else:
            lines.append(
                "final List<Map<String, dynamic>> results = await db.rawQuery(sql);"
            )

        lines.append("")
        lines.append("// Convert results to model objects")
        lines.append("return results.map((row) => ModelClass.fromMap(row)).toList();")

        return "\n".join(lines)

    def format_insert(self, insert_node: Any, target_lang: str = "python") -> str:
        """Format an INSERT statement AST node for the target language.

        Args:
            insert_node: InsertStatement AST node
            target_lang: Target language ('python', 'dart')

        Returns:
            Formatted insert code for target language
        """
        if target_lang == "python":
            return self._format_insert_python(insert_node)
        if target_lang == "dart":
            return self._format_insert_dart(insert_node)
        return f"// Unsupported target language: {target_lang}"

    def _format_insert_python(self, insert_node: Any) -> str:
        """Format INSERT for Python/SQLAlchemy."""
        lines = []

        if not hasattr(insert_node, "table") or not insert_node.table:
            return "# Unable to determine table for INSERT"

        table_name = (
            insert_node.table.table_name
            if hasattr(insert_node.table, "table_name")
            else str(insert_node.table)
        )

        # Handle INSERT with VALUES
        if hasattr(insert_node, "values") and insert_node.values:
            if hasattr(insert_node, "columns") and insert_node.columns:
                # Single row insert
                if len(insert_node.values) == 1:
                    lines.append(f"# Insert single row into {table_name}")
                    lines.append(f"new_record = {table_name}(")
                    for i, col in enumerate(insert_node.columns):
                        value = self._expression_to_string(insert_node.values[0][i])
                        lines.append(f"    {col}={value},")
                    lines.append(")")
                    lines.append("session.add(new_record)")
                    lines.append("session.commit()")
                else:
                    # Multiple row insert
                    lines.append(f"# Insert multiple rows into {table_name}")
                    lines.append("records = []")
                    for row in insert_node.values:
                        lines.append(f"records.append({table_name}(")
                        for i, col in enumerate(insert_node.columns):
                            value = self._expression_to_string(row[i])
                            lines.append(f"    {col}={value},")
                        lines.append("))")
                    lines.append("session.bulk_save_objects(records)")
                    lines.append("session.commit()")

        # Handle INSERT ... SELECT
        elif hasattr(insert_node, "select_statement") and insert_node.select_statement:
            lines.append(f"# INSERT INTO {table_name} SELECT ...")
            lines.append("# Execute as raw SQL for better performance")
            sql = self._build_insert_select_sql(insert_node)
            lines.append(f'session.execute(text("{sql}"))')
            lines.append("session.commit()")

        return "\n".join(lines)

    def _format_insert_dart(self, insert_node: Any) -> str:
        """Format INSERT for Dart/Flutter."""
        lines = []

        if not hasattr(insert_node, "table") or not insert_node.table:
            return "// Unable to determine table for INSERT"

        table_name = (
            insert_node.table.table_name
            if hasattr(insert_node.table, "table_name")
            else str(insert_node.table)
        )

        # Handle INSERT with VALUES
        if hasattr(insert_node, "values") and insert_node.values:
            if hasattr(insert_node, "columns") and insert_node.columns:
                if len(insert_node.values) == 1:
                    # Single row insert
                    lines.append(f"// Insert single row into {table_name}")
                    lines.append("final values = <String, dynamic>{")
                    for i, col in enumerate(insert_node.columns):
                        value = self._expression_to_string(insert_node.values[0][i])
                        lines.append(f"  '{col}': {value},")
                    lines.append("};")
                    lines.append(f"final id = await db.insert('{table_name}', values);")
                else:
                    # Multiple row insert
                    lines.append(f"// Insert multiple rows into {table_name}")
                    lines.append("final batch = db.batch();")
                    for row in insert_node.values:
                        lines.append("batch.insert(")
                        lines.append(f"  '{table_name}',")
                        lines.append("  <String, dynamic>{")
                        for i, col in enumerate(insert_node.columns):
                            value = self._expression_to_string(row[i])
                            lines.append(f"    '{col}': {value},")
                        lines.append("  },")
                        lines.append(");")
                    lines.append("await batch.commit();")

        return "\n".join(lines)

    def format_update(self, update_node: Any, target_lang: str = "python") -> str:
        """Format an UPDATE statement AST node for the target language.

        Args:
            update_node: UpdateStatement AST node
            target_lang: Target language ('python', 'dart')

        Returns:
            Formatted update code for target language
        """
        if target_lang == "python":
            return self._format_update_python(update_node)
        if target_lang == "dart":
            return self._format_update_dart(update_node)
        return f"// Unsupported target language: {target_lang}"

    def _format_update_python(self, update_node: Any) -> str:
        """Format UPDATE for Python/SQLAlchemy."""
        lines = []

        if not hasattr(update_node, "table") or not update_node.table:
            return "# Unable to determine table for UPDATE"

        table_name = (
            update_node.table.table_name
            if hasattr(update_node.table, "table_name")
            else str(update_node.table)
        )

        lines.append(f"# Update {table_name}")
        lines.append(f"query = session.query({table_name})")

        # Handle WHERE clause
        if hasattr(update_node, "where_clause") and update_node.where_clause:
            condition = self._convert_condition_to_sqlalchemy(
                update_node.where_clause.condition
            )
            lines.append(f"query = query.filter({condition})")

        # Build update values
        if hasattr(update_node, "assignments") and update_node.assignments:
            update_dict = {}
            for assignment in update_node.assignments:
                col = assignment.target_column
                val = self._expression_to_string(assignment.value)
                update_dict[col] = val

            lines.append(f"query.update({update_dict})")
            lines.append("session.commit()")

        return "\n".join(lines)

    def _format_update_dart(self, update_node: Any) -> str:
        """Format UPDATE for Dart/Flutter."""
        lines = []

        if not hasattr(update_node, "table") or not update_node.table:
            return "// Unable to determine table for UPDATE"

        table_name = (
            update_node.table.table_name
            if hasattr(update_node.table, "table_name")
            else str(update_node.table)
        )

        lines.append(f"// Update {table_name}")

        # Build update values
        if hasattr(update_node, "assignments") and update_node.assignments:
            lines.append("final values = <String, dynamic>{")
            for assignment in update_node.assignments:
                col = assignment.target_column
                val = self._expression_to_string(assignment.value)
                lines.append(f"  '{col}': {val},")
            lines.append("};")

            # Handle WHERE clause
            if hasattr(update_node, "where_clause") and update_node.where_clause:
                where_sql, where_params = self._convert_condition_to_dart(
                    update_node.where_clause.condition
                )
                lines.append(f"final whereClause = '{where_sql}';")
                lines.append(f"final whereArgs = {where_params};")
                lines.append("final count = await db.update(")
                lines.append(f"  '{table_name}',")
                lines.append("  values,")
                lines.append("  where: whereClause,")
                lines.append("  whereArgs: whereArgs,")
                lines.append(");")
            else:
                lines.append(f"final count = await db.update('{table_name}', values);")

        return "\n".join(lines)

    def format_delete(self, delete_node: Any, target_lang: str = "python") -> str:
        """Format a DELETE statement AST node for the target language.

        Args:
            delete_node: DeleteStatement AST node
            target_lang: Target language ('python', 'dart')

        Returns:
            Formatted delete code for target language
        """
        if target_lang == "python":
            return self._format_delete_python(delete_node)
        if target_lang == "dart":
            return self._format_delete_dart(delete_node)
        return f"// Unsupported target language: {target_lang}"

    def _format_delete_python(self, delete_node: Any) -> str:
        """Format DELETE for Python/SQLAlchemy."""
        lines = []

        if not hasattr(delete_node, "table") or not delete_node.table:
            return "# Unable to determine table for DELETE"

        table_name = (
            delete_node.table.table_name
            if hasattr(delete_node.table, "table_name")
            else str(delete_node.table)
        )

        lines.append(f"# Delete from {table_name}")
        lines.append(f"query = session.query({table_name})")

        # Handle WHERE clause
        if hasattr(delete_node, "where_clause") and delete_node.where_clause:
            condition = self._convert_condition_to_sqlalchemy(
                delete_node.where_clause.condition
            )
            lines.append(f"query = query.filter({condition})")

        lines.append("deleted_count = query.delete()")
        lines.append("session.commit()")
        lines.append("print(f'Deleted {deleted_count} rows')")

        return "\n".join(lines)

    def _format_delete_dart(self, delete_node: Any) -> str:
        """Format DELETE for Dart/Flutter."""
        lines = []

        if not hasattr(delete_node, "table") or not delete_node.table:
            return "// Unable to determine table for DELETE"

        table_name = (
            delete_node.table.table_name
            if hasattr(delete_node.table, "table_name")
            else str(delete_node.table)
        )

        lines.append(f"// Delete from {table_name}")

        # Handle WHERE clause
        if hasattr(delete_node, "where_clause") and delete_node.where_clause:
            where_sql, where_params = self._convert_condition_to_dart(
                delete_node.where_clause.condition
            )
            lines.append(f"final whereClause = '{where_sql}';")
            lines.append(f"final whereArgs = {where_params};")
            lines.append("final count = await db.delete(")
            lines.append(f"  '{table_name}',")
            lines.append("  where: whereClause,")
            lines.append("  whereArgs: whereArgs,")
            lines.append(");")
        else:
            lines.append(f"final count = await db.delete('{table_name}');")

        lines.append("print('Deleted $count rows');")

        return "\n".join(lines)

    # Helper methods for SQL parsing and conversion

    def _expression_to_string(self, expr: Any) -> str:
        """Convert an expression AST node to string representation."""
        if expr is None:
            return "null"

        # Handle literals
        if hasattr(expr, "value"):
            if isinstance(expr.value, str):
                return f"'{expr.value}'"
            return str(expr.value)

        # Handle column references
        if hasattr(expr, "column_name"):
            if hasattr(expr, "table_name") and expr.table_name:
                return f"{expr.table_name}.{expr.column_name}"
            return expr.column_name

        # Handle binary operations
        if (
            hasattr(expr, "operator")
            and hasattr(expr, "left")
            and hasattr(expr, "right")
        ):
            left = self._expression_to_string(expr.left)
            right = self._expression_to_string(expr.right)
            return f"{left} {expr.operator} {right}"

        # Handle function calls
        if hasattr(expr, "function_name"):
            args = []
            if hasattr(expr, "arguments"):
                args = [self._expression_to_string(arg) for arg in expr.arguments]
            return f"{expr.function_name}({', '.join(args)})"

        # Handle SQL parameters
        if hasattr(expr, "name") and hasattr(expr, "node_type"):
            if "Parameter" in expr.node_type:
                return f":{expr.name}" if expr.name else "?"

        # Default
        return str(expr)

    def _expression_to_column_ref(self, expr: Any) -> str:
        """Convert expression to SQLAlchemy column reference."""
        if hasattr(expr, "column_name"):
            if hasattr(expr, "table_name") and expr.table_name:
                return f"{expr.table_name}.c.{expr.column_name}"
            return expr.column_name
        return self._expression_to_string(expr)

    def _convert_condition_to_sqlalchemy(self, condition: Any) -> str:
        """Convert WHERE/HAVING condition to SQLAlchemy filter syntax."""
        if condition is None:
            return "True"

        # Handle binary operations
        if (
            hasattr(condition, "operator")
            and hasattr(condition, "left")
            and hasattr(condition, "right")
        ):
            left = self._expression_to_column_ref(condition.left)
            right = self._expression_to_string(condition.right)
            op = condition.operator.upper()

            if op == "=":
                return f"{left} == {right}"
            if op == "!=":
                return f"{left} != {right}"
            if op in ["<", ">", "<=", ">="]:
                return f"{left} {op} {right}"
            if op == "LIKE":
                return f"{left}.like({right})"
            if op == "IN":
                return f"{left}.in_({right})"
            if op == "NOT IN":
                return f"~{left}.in_({right})"
            if op == "IS NULL":
                return f"{left}.is_(None)"
            if op == "IS NOT NULL":
                return f"{left}.isnot(None)"
            if op == "AND":
                left_cond = self._convert_condition_to_sqlalchemy(condition.left)
                right_cond = self._convert_condition_to_sqlalchemy(condition.right)
                return f"and_({left_cond}, {right_cond})"
            if op == "OR":
                left_cond = self._convert_condition_to_sqlalchemy(condition.left)
                right_cond = self._convert_condition_to_sqlalchemy(condition.right)
                return f"or_({left_cond}, {right_cond})"

        return f"# TODO: Convert condition: {condition}"

    def _convert_condition_to_dart(self, condition: Any) -> tuple[str, list[Any]]:
        """Convert WHERE condition to Dart SQL syntax with parameters."""
        if condition is None:
            return "1=1", []

        parameters = []

        # Handle binary operations
        if (
            hasattr(condition, "operator")
            and hasattr(condition, "left")
            and hasattr(condition, "right")
        ):
            left = self._expression_to_string(condition.left)
            op = condition.operator.upper()

            if op in ["=", "!=", "<", ">", "<=", ">="]:
                parameters.append(self._extract_value(condition.right))
                return f"{left} {op} ?", parameters
            if op == "LIKE":
                parameters.append(self._extract_value(condition.right))
                return f"{left} LIKE ?", parameters
            if op == "IN":
                # Handle IN clause
                values = self._extract_list_values(condition.right)
                placeholders = ", ".join(["?" for _ in values])
                parameters.extend(values)
                return f"{left} IN ({placeholders})", parameters
            if op == "AND":
                left_sql, left_params = self._convert_condition_to_dart(condition.left)
                right_sql, right_params = self._convert_condition_to_dart(
                    condition.right
                )
                parameters.extend(left_params)
                parameters.extend(right_params)
                return f"({left_sql} AND {right_sql})", parameters
            if op == "OR":
                left_sql, left_params = self._convert_condition_to_dart(condition.left)
                right_sql, right_params = self._convert_condition_to_dart(
                    condition.right
                )
                parameters.extend(left_params)
                parameters.extend(right_params)
                return f"({left_sql} OR {right_sql})", parameters

        return "1=1", []

    def _extract_value(self, expr: Any) -> Any:
        """Extract the actual value from an expression node."""
        if hasattr(expr, "value"):
            return expr.value
        return str(expr)

    def _extract_list_values(self, expr: Any) -> list[Any]:
        """Extract values from a list expression."""
        if hasattr(expr, "elements"):
            return [self._extract_value(elem) for elem in expr.elements]
        return []

    def _build_insert_select_sql(self, insert_node: Any) -> str:
        """Build INSERT ... SELECT SQL statement."""
        parts = ["INSERT INTO"]

        # Table name
        table_name = (
            insert_node.table.table_name
            if hasattr(insert_node.table, "table_name")
            else str(insert_node.table)
        )
        parts.append(table_name)

        # Column list
        if hasattr(insert_node, "columns") and insert_node.columns:
            parts.append(f"({', '.join(insert_node.columns)})")

        # SELECT statement (simplified - would need full SQL generation)
        parts.append("SELECT ...")

        return " ".join(parts)

    def handle_powerbuilder_sql_syntax(self, sql: str) -> str:
        """Handle PowerBuilder-specific SQL syntax conversions.

        Args:
            sql: PowerBuilder SQL string

        Returns:
            Converted SQL string
        """
        # Handle PowerBuilder dynamic SQL parameters
        sql = re.sub(r":(\w+)", r"@\1", sql)  # Convert :param to @param

        # Handle PowerBuilder-specific functions
        pb_functions = {
            "today()": "CURRENT_DATE",
            "now()": "CURRENT_TIMESTAMP",
            "dw_retrieve()": "-- PowerBuilder DataWindow retrieve",
            "dw_update()": "-- PowerBuilder DataWindow update",
        }

        for pb_func, replacement in pb_functions.items():
            sql = sql.replace(pb_func, replacement)

        # Handle PowerBuilder outer join syntax
        # Convert *= to LEFT JOIN and =* to RIGHT JOIN
        if "*=" in sql or "=*" in sql:
            logger.warning(
                "PowerBuilder outer join syntax detected. Manual conversion required."
            )
            sql = sql.replace("*=", " LEFT OUTER JOIN ")
            sql = sql.replace("=*", " RIGHT OUTER JOIN ")

        # Handle PowerBuilder transaction syntax
        sql = sql.replace("USING SQLCA;", "")
        return sql.replace("USING ", "-- Transaction: ")

    def add_sql_injection_prevention(
        self, sql: str, parameters: dict[str, Any], target_lang: str = "python"
    ) -> tuple[str, dict[str, Any]]:
        """Add SQL injection prevention measures.

        Args:
            sql: SQL query string
            parameters: Query parameters
            target_lang: Target language

        Returns:
            Tuple of (safe SQL, sanitized parameters)
        """
        # Validate SQL doesn't contain obvious injection attempts
        dangerous_patterns = [
            r";\s*DROP\s+TABLE",
            r";\s*DELETE\s+FROM",
            r";\s*UPDATE\s+\w+\s+SET",
            r"--\s*$",
            r"/\*.*\*/",
            r"EXEC\s*\(",
            r"EXECUTE\s*\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning("Potential SQL injection detected: %s", pattern)
                raise ValueError("Potentially unsafe SQL detected")

        # Sanitize parameters
        safe_params = {}
        for key, value in parameters.items():
            if isinstance(value, str):
                # Remove dangerous characters
                value = value.replace("'", "''")  # Escape single quotes
                value = value.replace("\\", "\\\\")  # Escape backslashes
                value = re.sub(r"[^\w\s\-\.\@]", "", value)  # Remove special chars
            safe_params[key] = value

        # Convert to parameterized query format
        if target_lang == "python":
            # Use named parameters for Python
            sql = re.sub(r":(\w+)", r"%(\1)s", sql)
        elif target_lang == "dart":
            # Use positional parameters for Dart
            param_names = re.findall(r":(\w+)", sql)
            for _i, name in enumerate(param_names):
                sql = sql.replace(f":{name}", "?")

        return sql, safe_params
