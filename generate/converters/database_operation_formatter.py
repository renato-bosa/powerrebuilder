"""Database operation formatter for PowerBuilder to modern code conversion.

This module converts PowerBuilder database operations into Flutter/Dart
and Python/SQLModel code with proper error handling and async support.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DatabaseOperation:
    """Represents a database operation."""
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE, FETCH, etc.
    table_name: str | None = None
    columns: list[str] = None
    conditions: str | None = None
    variables: list[str] = None
    cursor_name: str | None = None
    sql_statement: str | None = None

    def __post_init__(self) -> None:


        if self.columns is None:
            self.columns = []
        if self.variables is None:
            self.variables = []


class DatabaseOperationFormatter:
    """Formats database operations for target platforms."""

    def __init__(self, target: str = "flutter") -> None:


        """Initialize the formatter.

        Args:
            target: Target platform ('flutter' or 'python')
        """
        self.target = target

    def format_database_operations(self, operations: list[str], context: dict[str, Any] = None) -> list[str]:




        """Format a list of database operations.

        Args:
            operations: List of database operation strings
            context: Context information (variables, types, etc.)

        Returns:
            List of formatted code lines
        """
        if not operations:
            return []

        formatted_lines = []

        # Analyze operations to determine pattern
        has_transaction = any("COMMIT" in op or "ROLLBACK" in op for op in operations)
        has_cursor = any("OPEN" in op or "FETCH" in op for op in operations)

        if has_transaction:
            formatted_lines.extend(self._format_transaction_block(operations, context))
        elif has_cursor:
            formatted_lines.extend(self._format_cursor_operations(operations, context))
        else:
            # Format individual operations
            for op in operations:
                parsed_op = self._parse_operation(op)
                if parsed_op:
                    lines = self._format_single_operation(parsed_op, context)
                    formatted_lines.extend(lines)

        return formatted_lines

    def _parse_operation(self, operation: str) -> DatabaseOperation | None:




        """Parse a database operation string."""
        operation = operation.strip()

        # SELECT operation
        if operation.upper().startswith("SELECT"):
            return self._parse_select(operation)

        # INSERT operation
        elif operation.upper().startswith("INSERT"):
            return self._parse_insert(operation)

        # UPDATE operation
        elif operation.upper().startswith("UPDATE"):
            return self._parse_update(operation)

        # DELETE operation
        elif operation.upper().startswith("DELETE"):
            return self._parse_delete(operation)

        # FETCH operation
        elif operation.upper().startswith("FETCH"):
            return self._parse_fetch(operation)

        # OPEN/CLOSE cursor
        elif operation.upper().startswith("OPEN"):
            return self._parse_cursor_open(operation)
        elif operation.upper().startswith("CLOSE"):
            return self._parse_cursor_close(operation)

        # Transaction operations
        elif operation.upper() in ["COMMIT", "ROLLBACK"]:
            return DatabaseOperation(operation_type=operation.upper())

        return None

    def _parse_select(self, operation: str) -> DatabaseOperation:




        """Parse SELECT statement."""
        # Extract columns (simplified)
        match = re.search(r"SELECT\s+(.+?)\s+FROM\s+(\w+)", operation, re.IGNORECASE)
        if match:
            columns_str = match.group(1)
            table_name = match.group(2)

            # Parse columns
            columns = [col.strip() for col in columns_str.split(", ")]

            # Look for WHERE clause
            where_match = re.search(r"WHERE\s+(.+)", operation, re.IGNORECASE)
            conditions = where_match.group(1) if where_match else None

            # Look for INTO clause (embedded SQL)
            into_match = re.search(r"INTO\s+:(.+?)\s+FROM", operation, re.IGNORECASE)
            variables = []
            if into_match:
                vars_str = into_match.group(1)
                variables = [var.strip() for var in vars_str.split(", ")]

            return DatabaseOperation(
                operation_type="SELECT", table_name=table_name, columns=columns, conditions=conditions, variables=variables, sql_statement=operation,
            )

        return DatabaseOperation(operation_type="SELECT", sql_statement=operation)

    def _parse_insert(self, operation: str) -> DatabaseOperation:




        """Parse INSERT statement."""
        match = re.search(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)", operation, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            columns = [col.strip() for col in match.group(2).split(", ")]

            # Look for VALUES clause
            values_match = re.search(r"VALUES\s*\(([^)]+)\)", operation, re.IGNORECASE)
            variables = []
            if values_match:
                values_str = values_match.group(1)
                # Extract variable names (starting with :)
                variables = re.findall(r":(\w+)", values_str)

            return DatabaseOperation(
                operation_type="INSERT", table_name=table_name, columns=columns, variables=variables, sql_statement=operation,
            )

        return DatabaseOperation(operation_type="INSERT", sql_statement=operation)

    def _parse_update(self, operation: str) -> DatabaseOperation:




        """Parse UPDATE statement."""
        match = re.search(r"UPDATE\s+(\w+)\s+SET", operation, re.IGNORECASE)
        if match:
            table_name = match.group(1)

            # Extract SET assignments
            set_match = re.search(r"SET\s+(.+?)(?:\s+WHERE|$)", operation, re.IGNORECASE)
            columns = []
            variables = []
            if set_match:
                assignments = set_match.group(1).split(", ")
                for assignment in assignments:
                    if "=" in assignment:
                        col = assignment.split("=")[0].strip()
                        columns.append(col)
                        # Extract variables
                        var_matches = re.findall(r":(\w+)", assignment)
                        variables.extend(var_matches)

            # Look for WHERE clause
            where_match = re.search(r"WHERE\s+(.+)", operation, re.IGNORECASE)
            conditions = where_match.group(1) if where_match else None

            return DatabaseOperation(
                operation_type="UPDATE", table_name=table_name, columns=columns, conditions=conditions, variables=variables, sql_statement=operation,
            )

        return DatabaseOperation(operation_type="UPDATE", sql_statement=operation)

    def _parse_delete(self, operation: str) -> DatabaseOperation:




        """Parse DELETE statement."""
        match = re.search(r"DELETE\s+FROM\s+(\w+)", operation, re.IGNORECASE)
        if match:
            table_name = match.group(1)

            # Look for WHERE clause
            where_match = re.search(r"WHERE\s+(.+)", operation, re.IGNORECASE)
            conditions = where_match.group(1) if where_match else None

            return DatabaseOperation(
                operation_type="DELETE", table_name=table_name, conditions=conditions, sql_statement=operation,
            )

        return DatabaseOperation(operation_type="DELETE", sql_statement=operation)

    def _parse_fetch(self, operation: str) -> DatabaseOperation:




        """Parse FETCH statement."""
        match = re.search(r"FETCH\s+(\w+)\s+INTO\s+:(.+)", operation, re.IGNORECASE)
        if match:
            cursor_name = match.group(1)
            variables = [var.strip() for var in match.group(2).split(", ")]

            return DatabaseOperation(
                operation_type="FETCH", cursor_name=cursor_name, variables=variables,
            )

        return DatabaseOperation(operation_type="FETCH", sql_statement=operation)

    def _parse_cursor_open(self, operation: str) -> DatabaseOperation:




        """Parse OPEN cursor statement."""
        match = re.search(r"OPEN\s+(\w+)", operation, re.IGNORECASE)
        if match:
            cursor_name = match.group(1)
            return DatabaseOperation(
                operation_type="OPEN", cursor_name=cursor_name,
            )

        return DatabaseOperation(operation_type="OPEN")

    def _parse_cursor_close(self, operation: str) -> DatabaseOperation:




        """Parse CLOSE cursor statement."""
        match = re.search(r"CLOSE\s+(\w+)", operation, re.IGNORECASE)
        if match:
            cursor_name = match.group(1)
            return DatabaseOperation(
                operation_type="CLOSE", cursor_name=cursor_name,
            )

        return DatabaseOperation(operation_type="CLOSE")

    def _format_single_operation(self, operation: DatabaseOperation, context: dict[str, Any] = None) -> list[str]:




        """Format a single database operation."""
        if self.target == "flutter":
            return self._format_flutter_operation(operation, context)
        elif self.target == "python":
            return self._format_python_operation(operation, context)
        else:
            return [f"// Unsupported target: {self.target}"]

    def _format_flutter_operation(self, operation: DatabaseOperation, context: dict[str, Any] = None) -> list[str]:




        """Format operation for Flutter/Dart."""
        lines = []

        if operation.operation_type == "SELECT":
            if operation.variables:
                # Embedded SQL with INTO clause
                lines.append("// Fetch single row")
                lines.append("try {")
                lines.append(f"  final result = await database.rawQuery(")
                lines.append(f'    "{operation.sql_statement}", ')
                if operation.conditions and ":" in operation.conditions:
                    # Extract parameters from conditions
                    params = re.findall(r":(\w+)", operation.conditions)
                    lines.append(f"    [{", ".join(params)}], ")
                lines.append("  )")
                lines.append("  if (result.isNotEmpty) {")
                lines.append("    final row = result.first;")
                for i, var in enumerate(operation.variables):
                    col = operation.columns[i] if i < len(operation.columns) else f"col{i}"
                    lines.append(f'    {var} = row["{col}"];')
                lines.append("  }")
                lines.append("} catch (e) {")
                lines.append('  debugPrint("Database error: $e");')
                lines.append("  return -1; // Error")
                lines.append("}")
            else:
                # Regular SELECT
                lines.append("// Query multiple rows")
                lines.append("try {")
                lines.append(f"  final results = await database.query(")
                lines.append(f'    "{operation.table_name}",')
                if operation.columns and operation.columns[0] != "*":
                    lines.append(f"    columns: {operation.columns},")
                if operation.conditions:
                    lines.append(f'    where: "{operation.conditions}",')
                lines.append("  );")
                lines.append("  return results;")
                lines.append("} catch (e) {")
                lines.append('  debugPrint("Database error: $e");')
                lines.append("  return [];")
                lines.append("}")

        elif operation.operation_type == "INSERT":
            lines.append("// Insert record")
            lines.append("try {")
            lines.append(f"  final id = await database.insert(")
            lines.append(f'    "{operation.table_name}",')
            lines.append("    {")
            for i, col in enumerate(operation.columns):
                var = operation.variables[i] if i < len(operation.variables) else f"value{i}"
                lines.append(f'      "{col}": {var},')
            lines.append("    },")
            lines.append("  );")
            lines.append("  return id > 0 ? 1 : -1; // Success/Failure")
            lines.append("} catch (e) {")
            lines.append('  debugPrint("Insert error: $e");')
            lines.append("  return -1;")
            lines.append("}")

        elif operation.operation_type == "UPDATE":
            lines.append("// Update record")
            lines.append("try {")
            lines.append(f"  final count = await database.update(")
            lines.append(f'    "{operation.table_name}",')
            lines.append("    {")
            for i, col in enumerate(operation.columns):
                var = operation.variables[i] if i < len(operation.variables) else f"value{i}"
                lines.append(f'      "{col}": {var},')
            lines.append("    },")
            if operation.conditions:
                lines.append(f'    where: "{operation.conditions}",')
            lines.append("  );")
            lines.append("  return count > 0 ? 1 : 0; // Rows affected")
            lines.append("} catch (e) {")
            lines.append('  debugPrint("Update error: $e");')
            lines.append("  return -1;")
            lines.append("}")

        elif operation.operation_type == "DELETE":
            lines.append("// Delete record")
            lines.append("try {")
            lines.append(f"  final count = await database.delete(")
            lines.append(f'    "{operation.table_name}",')
            if operation.conditions:
                lines.append(f'    where: "{operation.conditions}",')
            lines.append("  );")
            lines.append("  return count > 0 ? 1 : 0; // Rows affected")
            lines.append("} catch (e) {")
            lines.append('  debugPrint("Delete error: $e");')
            lines.append("  return -1;")
            lines.append("}")

        elif operation.operation_type == "COMMIT":
            lines.append("// Commit transaction")
            lines.append("await database.batch().commit();")

        elif operation.operation_type == "ROLLBACK":
            lines.append("// Rollback transaction")
            lines.append("// Note: SQLite doesn't support rollback in Flutter")
            lines.append("// Consider using database.transaction() instead")

        return lines

    def _format_python_operation(self, operation: DatabaseOperation, 
                               context: dict[str, Any] = None) -> list[str]:




        """Format operation for Python/SQLModel."""
        lines = []

        if operation.operation_type == "SELECT":
            if operation.variables:
                # Single row fetch
                lines.append("# Fetch single row")
                lines.append("try:")
                lines.append(f"    result = session.execute(")
                lines.append(f'        text("{operation.sql_statement}")')
                if operation.conditions and ":" in operation.conditions:
                    params = re.findall(r":(\w+)", operation.conditions)
                    param_dict = ", ".join([f'"{p}": {p}' for p in params])
                    lines.append(f"        .bindparams({{{param_dict}}})")
                lines.append("    ).first()")
                lines.append("    if result:")
                for i, var in enumerate(operation.variables):
                    lines.append(f"        {var} = result[{i}]")
                lines.append("except Exception as e:")
                lines.append('    logger.error(f"Database error: {e}")')
                lines.append("    return -1")
            else:
                # Multiple rows
                lines.append("# Query multiple rows")
                lines.append("try:")
                if operation.table_name and operation.table_name != operation.sql_statement:
                    # Use ORM query
                    model_name = self._to_pascal_case(operation.table_name)
                    lines.append(f"    query = session.query({model_name})")
                    if operation.conditions:
                        lines.append(f"    query = query.filter({operation.conditions})")
                    lines.append("    return query.all()")
                else:
                    # Raw SQL
                    lines.append(f"    results = session.execute(")
                    lines.append(f'        text("{operation.sql_statement}")')
                    lines.append("    ).fetchall()")
                    lines.append("    return results")
                lines.append("except Exception as e:")
                lines.append('    logger.error(f"Query error: {e}")')
                lines.append("    return []")

        elif operation.operation_type == "INSERT":
            lines.append("# Insert record")
            lines.append("try:")
            if operation.table_name:
                model_name = self._to_pascal_case(operation.table_name)
                lines.append(f"    new_record = {model_name}(")
                for i, col in enumerate(operation.columns):
                    var = operation.variables[i] if i < len(operation.variables) else f"value{i}"
                    lines.append(f"        {col}={var},")
                lines.append("    )")
                lines.append("    session.add(new_record)")
                lines.append("    session.commit()")
                lines.append("    return 1  # Success")
            lines.append("except Exception as e:")
            lines.append("    session.rollback()")
            lines.append('    logger.error(f"Insert error: {e}")')
            lines.append("    return -1")

        elif operation.operation_type == "UPDATE":
            lines.append("# Update record")
            lines.append("try:")
            if operation.table_name:
                model_name = self._to_pascal_case(operation.table_name)
                lines.append(f"    query = session.query({model_name})")
                if operation.conditions:
                    lines.append(f"    query = query.filter({operation.conditions})")
                lines.append("    count = query.update({")
                for i, col in enumerate(operation.columns):
                    var = operation.variables[i] if i < len(operation.variables) else f"value{i}"
                    lines.append(f'        "{col}": {var},')
                lines.append("    })")
                lines.append("    session.commit()")
                lines.append("    return count  # Rows affected")
            lines.append("except Exception as e:")
            lines.append("    session.rollback()")
            lines.append('    logger.error(f"Update error: {e}")')
            lines.append("    return -1")

        elif operation.operation_type == "DELETE":
            lines.append("# Delete record")
            lines.append("try:")
            if operation.table_name:
                model_name = self._to_pascal_case(operation.table_name)
                lines.append(f"    query = session.query({model_name})")
                if operation.conditions:
                    lines.append(f"    query = query.filter({operation.conditions})")
                lines.append("    count = query.delete()")
                lines.append("    session.commit()")
                lines.append("    return count  # Rows affected")
            lines.append("except Exception as e:")
            lines.append("    session.rollback()")
            lines.append('    logger.error(f"Delete error: {e}")')
            lines.append("    return -1")

        elif operation.operation_type == "COMMIT":
            lines.append("# Commit transaction")
            lines.append("session.commit()")

        elif operation.operation_type == "ROLLBACK":
            lines.append("# Rollback transaction")
            lines.append("session.rollback()")

        return lines

    def _format_transaction_block(self, operations: list[str], 
                                context: dict[str, Any] = None) -> list[str]:




        """Format a transaction block."""
        lines = []

        if self.target == "flutter":
            lines.append("// Transaction block")
            lines.append("await database.transaction((txn) async {")
            lines.append("  try {")

            # Process operations within transaction
            for op in operations:
                if op.upper() not in ["COMMIT", "ROLLBACK"]:
                    parsed_op = self._parse_operation(op)
                    if parsed_op:
                        op_lines = self._format_single_operation(parsed_op, context)
                        # Adjust indentation and replace 'database' with 'txn'
                        for line in op_lines:
                            adjusted = line.replace("database.", "txn.")
                            lines.append(f"    {adjusted}")

            lines.append("    return 1; // Success")
            lines.append("  } catch (e) {")
            lines.append('    debugPrint("Transaction error: $e");')
            lines.append("    throw e; // Automatic rollback")
            lines.append("  }")
            lines.append("});")

        elif self.target == "python":
            lines.append("# Transaction block")
            lines.append("try:")
            lines.append("    with session.begin():")

            # Process operations within transaction
            for op in operations:
                if op.upper() not in ["COMMIT", "ROLLBACK"]:
                    parsed_op = self._parse_operation(op)
                    if parsed_op:
                        op_lines = self._format_single_operation(parsed_op, context)
                        for line in op_lines:
                            lines.append(f"        {line}")

            lines.append("    return 1  # Success")
            lines.append("except Exception as e:")
            lines.append('    logger.error(f"Transaction error: {e}")')
            lines.append("    return -1  # Automatic rollback")

        return lines

    def _format_cursor_operations(self, operations: list[str], 
                                context: dict[str, Any] = None) -> list[str]:




        """Format cursor-based operations."""
        lines = []
        cursor_name = None

        # Extract cursor name
        for op in operations:
            if "OPEN" in op.upper() or "FETCH" in op.upper():
                match = re.search(r"(OPEN|FETCH)\s+(\w+)", op, re.IGNORECASE)
                if match:
                    cursor_name = match.group(2)
                    break

        if self.target == "flutter":
            lines.append("// Cursor operations")
            lines.append("// Note: Flutter SQLite doesn't support cursors directly")
            lines.append("// Using query with limit/offset instead")
            lines.append("")
            lines.append("int offset = 0;")
            lines.append("const int batchSize = 100;")
            lines.append("List<Map<String, dynamic>> allResults = [];")
            lines.append("")
            lines.append("while (true) {")
            lines.append("  final batch = await database.query(")
            lines.append('    "table_name",')
            lines.append("    limit: batchSize,")
            lines.append("    offset: offset,")
            lines.append("  );")
            lines.append("")
            lines.append("  if (batch.isEmpty) break;")
            lines.append("")
            lines.append("  for (final row in batch) {")
            lines.append("    // Process each row")
            lines.append("    allResults.add(row);")
            lines.append("  }")
            lines.append("")
            lines.append("  offset += batchSize;")
            lines.append("}")

        elif self.target == "python":
            lines.append("# Cursor operations")
            lines.append(f"# Cursor: {cursor_name or "unnamed"}")
            lines.append("")

            # Find the SQL for the cursor
            sql_statement = None
            for op in operations:
                parsed = self._parse_operation(op)
                if parsed and parsed.operation_type == "SELECT":
                    sql_statement = parsed.sql_statement
                    break

            lines.append("# Execute query with server-side cursor")
            lines.append("from sqlalchemy import text")
            lines.append("")
            lines.append("with session.connection() as conn:")
            lines.append(f'    result = conn.execute(text("{sql_statement or "SELECT * FROM table"}").execution_options(stream_results=True))')
            lines.append("")
            lines.append("    # Fetch rows in batches")
            lines.append("    while True:")
            lines.append("        rows = result.fetchmany(100)")
            lines.append("        if not rows:")
            lines.append("            break")
            lines.append("")
            lines.append("        for row in rows:")
            lines.append("            # Process each row")
            lines.append("            pass")

        return lines

    def _to_pascal_case(self, name: str) -> str:




        """Convert name to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def generate_repository_methods(self, table_name: str, 
                                  operations: list[str]) -> dict[str, list[str]]:




        """Generate repository methods for CRUD operations.

        Args:
            table_name: Name of the database table
            operations: List of operations to generate

        Returns:
            Dictionary of method_name -> code lines
        """
        methods = {}
        model_name = self._to_pascal_case(table_name)

        if self.target == "flutter":
            # Generate Dart repository methods
            if "SELECT" in operations:
                methods["getAll"] = self._generate_flutter_get_all(table_name, model_name)
                methods["getById"] = self._generate_flutter_get_by_id(table_name, model_name)

            if "INSERT" in operations:
                methods["create"] = self._generate_flutter_create(table_name, model_name)

            if "UPDATE" in operations:
                methods["update"] = self._generate_flutter_update(table_name, model_name)

            if "DELETE" in operations:
                methods["delete"] = self._generate_flutter_delete(table_name, model_name)

        elif self.target == "python":
            # Generate Python repository methods
            if "SELECT" in operations:
                methods["get_all"] = self._generate_python_get_all(table_name, model_name)
                methods["get_by_id"] = self._generate_python_get_by_id(table_name, model_name)

            if "INSERT" in operations:
                methods["create"] = self._generate_python_create(table_name, model_name)

            if "UPDATE" in operations:
                methods["update"] = self._generate_python_update(table_name, model_name)

            if "DELETE" in operations:
                methods["delete"] = self._generate_python_delete(table_name, model_name)

        return methods

    def _generate_flutter_get_all(self, table_name: str, model_name: str) -> list[str]:




        """Generate Flutter getAll method."""
        return [
            f"Future<List<{model_name}>> getAll{model_name}s() async {{",
            "  try {",
            f'    final List<Map<String, dynamic>> maps = await database.query("{table_name}");',
            f"    return List.generate(maps.length, (i) => {model_name}.fromMap(maps[i]));",
            "  } catch (e) {",
            f'    debugPrint("Error fetching {table_name}: $e");',
            "    return [];",
            "  }",
            "}",
        ]

    def _generate_flutter_get_by_id(self, table_name: str, model_name: str) -> list[str]:




        """Generate Flutter getById method."""
        return [
            f"Future<{model_name}?> get{model_name}ById(int id) async {{",
            "  try {",
            f"    final List<Map<String, dynamic>> maps = await database.query(",
            f'      "{table_name}",',
            '      where: "id = ?",',
            "      whereArgs: [id],",
            "    );",
            "",
            "    if (maps.isNotEmpty) {",
            f"      return {model_name}.fromMap(maps.first);",
            "    }",
            "    return null;",
            "  } catch (e) {",
            f'    debugPrint("Error fetching {model_name} by id: $e");',
            "    return null;",
            "  }",
            "}",
        ]

    def _generate_flutter_create(self, table_name: str, model_name: str) -> list[str]:




        """Generate Flutter create method."""
        return [
            f"Future<int> create{model_name}({model_name} item) async {{",
            "  try {",
            f"    final id = await database.insert(",
            f'      "{table_name}",',
            "      item.toMap(),",
            "      conflictAlgorithm: ConflictAlgorithm.replace,",
            "    );",
            "    return id;",
            "  } catch (e) {",
            f'    debugPrint("Error creating {model_name}: $e");',
            "    return -1;",
            "  }",
            "}",
        ]

    def _generate_flutter_update(self, table_name: str, model_name: str) -> list[str]:




        """Generate Flutter update method."""
        return [
            f"Future<int> update{model_name}({model_name} item) async {{",
            "  try {",
            f"    final count = await database.update(",
            f'      "{table_name}",',
            "      item.toMap(),",
            '      where: "id = ?",',
            "      whereArgs: [item.id],",
            "    );",
            "    return count;",
            "  } catch (e) {",
            f'    debugPrint("Error updating {model_name}: $e");',
            "    return 0;",
            "  }",
            "}",
        ]

    def _generate_flutter_delete(self, table_name: str, model_name: str) -> list[str]:




        """Generate Flutter delete method."""
        return [
            f"Future<int> delete{model_name}(int id) async {{",
            "  try {",
            f"    final count = await database.delete(",
            f'      "{table_name}",',
            '      where: "id = ?",',
            "      whereArgs: [id],",
            "    );",
            "    return count;",
            "  } catch (e) {",
            f'    debugPrint("Error deleting {model_name}: $e");',
            "    return 0;",
            "  }",
            "}",
        ]

    def _generate_python_get_all(self, table_name: str, model_name: str) -> list[str]:




        """Generate Python get_all method."""
        return [
            f"def get_all_{table_name}s(session: Session) -> list[{model_name}]:",
            '    """Get all records from {table_name} table."""',
            "    try:",
            f"        return session.query({model_name}).all()",
            "    except Exception as e:",
            f'        logger.error(f"Error fetching {table_name}s: {{e}}")',
            "        return []",
        ]

    def _generate_python_get_by_id(self, table_name: str, model_name: str) -> list[str]:




        """Generate Python get_by_id method."""
        return [
            f"def get_{table_name}_by_id(session: Session, id: int) -> {model_name}, None: ",
            '    """Get a record by ID."""',
            "    try:",
            f"        return session.query({model_name}).filter({model_name}.id == id).first()",
            "    except Exception as e:",
            f'        logger.error(f"Error fetching {model_name} by id: {{e}}")',
            "        return None",
        ]

    def _generate_python_create(self, table_name: str, model_name: str) -> list[str]:




        """Generate Python create method."""
        return [
            f"def create_{table_name}(session: Session, item: {model_name}) -> {model_name}:",
            '    """Create a new record."""',
            "    try:",
            "        session.add(item)",
            "        session.commit()",
            "        session.refresh(item)",
            "        return item",
            "    except Exception as e:",
            "        session.rollback()",
            f'        logger.error(f"Error creating {model_name}: {{e}}")',
            "        raise",
        ]

    def _generate_python_update(self, table_name: str, model_name: str) -> list[str]:




        """Generate Python update method."""
        return [
            f"def update_{table_name}(session: Session, id: int, updates: dict) -> {model_name}, None: ",
            '    """Update a record."""',
            "    try:",
            f"        item = session.query({model_name}).filter({model_name}.id == id).first()",
            "        if item:",
            "            for key, value in updates.items():",
            "                setattr(item, key, value)",
            "            session.commit()",
            "            session.refresh(item)",
            "        return item",
            "    except Exception as e:",
            "        session.rollback()",
            f'        logger.error(f"Error updating {model_name}: {{e}}")',
            "        return None",
        ]

    def _generate_python_delete(self, table_name: str, model_name: str) -> list[str]:




        """Generate Python delete method."""
        return [
            f"def delete_{table_name}(session: Session, id: int) -> bool:",
            '    """Delete a record."""',
            "    try:",
            f"        item = session.query({model_name}).filter({model_name}.id == id).first()",
            "        if item:",
            "            session.delete(item)",
            "            session.commit()",
            "            return True",
            "        return False",
            "    except Exception as e:",
            "        session.rollback()",
            f'        logger.error(f"Error deleting {model_name}: {{e}}")',
            "        return False",
        ]
