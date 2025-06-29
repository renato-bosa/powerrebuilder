"""PowerBuilder DataWindow relationship extraction.

Analyzes SQL queries and DataWindow definitions to extract foreign key
relationships, joins, and data dependencies for generating proper
Flutter/Dart data models and repository methods.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from model.expressions import (BinaryExpression, Expression)
from model.ast.sql import (
    ColumnReference,
    FromClause,
    JoinClause,
    SelectStatement,
    TableReference,
    WhereClause,
)

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between tables."""
    ONE_TO_ONE = auto()
    ONE_TO_MANY = auto()
    MANY_TO_ONE = auto()
    MANY_TO_MANY = auto()
    LOOKUP = auto()  # For dropdown/combobox data sources


class JoinType(Enum):
    """SQL join types."""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL JOIN"
    CROSS = "CROSS JOIN"


@dataclass
class ColumnMapping:
    """Represents a column mapping in a relationship."""
    source_table: str
    source_column: str
    target_table: str
    target_column: str

    def __str__(self) -> str:


        return f"{self.source_table}.{self.source_column} -> {self.target_table}.{self.target_column}"


@dataclass
class Relationship:
    """Represents a relationship between two tables."""
    name: str  # e.g., "customer_orders"
    source_table: str
    target_table: str
    relationship_type: RelationshipType
    join_type: JoinType
    column_mappings: list[ColumnMapping] = field(default_factory=list)
    join_condition: str | None = None  # Original SQL condition
    is_optional: bool = False  # True for LEFT/RIGHT joins
    cascade_delete: bool = False
    cascade_update: bool = False

    def to_dict(self) -> dict[str, Any]:




        """Convert to dictionary for template rendering."""
        return {
            "name": self.name, "source_table": self.source_table, "target_table": self.target_table, "type": self.relationship_type.name.lower(), "join_type": self.join_type.value, "mappings": [
                {
                    "source": f"{m.source_column}", "target": f"{m.target_column}",
                }
                for m in self.column_mappings
            ], "is_optional": self.is_optional, "cascade_delete": self.cascade_delete, "cascade_update": self.cascade_update,
        }


class RelationshipExtractor:
    """Extracts relationships from SQL queries and DataWindow definitions."""

    def __init__(self) -> None:




        """Initialize the relationship extractor."""
        # Common foreign key naming patterns
        self.fk_patterns = [
            re.compile(r"^(\w+)_id$"), # table_id
            re.compile(r"^id_(\w+)$"), # id_table
            re.compile(r"^fk_(\w+)$"), # fk_table
            re.compile(r"^(\w+)_fk$"), # table_fk
            re.compile(r"^(\w+)_code$"), # table_code
            re.compile(r"^(\w+)_num$"), # table_num
            re.compile(r"^(\w+)_no$"), # table_no
        ]

        # Primary key patterns
        self.pk_patterns = [
            re.compile(r"^id$"), re.compile(r"^(\w+)_id$"), # table_id as PK
            re.compile(r"^pk_(\w+)$"), re.compile(r"^(\w+)_pk$"), ]

    def extract_from_select(self, select_stmt: SelectStatement) -> list[Relationship]:




        """Extract relationships from a SELECT statement.

        Args:
            select_stmt: Parsed SELECT statement AST

        Returns:
            List of extracted relationships
        """
        relationships = []

        if not select_stmt.from_clause:
            logger.debug("No from_clause in SELECT statement")
            return relationships

        logger.debug("From clause has %s joins", len(select_stmt.from_clause.joins) if select_stmt.from_clause.joins else 0)

        # Extract from JOIN clauses
        for join in select_stmt.from_clause.joins:
            logger.debug("Processing join: %s on %s", join.join_operator, join.table)
            rel = self._extract_from_join(join, select_stmt.from_clause)
            if rel:
                relationships.append(rel)
            else:
                logger.debug("No relationship extracted from this join")

        # Extract from WHERE clause (implicit joins)
        if select_stmt.where_clause:
            implicit_rels = self._extract_from_where(
                select_stmt.where_clause, select_stmt.from_clause,
            )
            relationships.extend(implicit_rels)

        # Deduplicate relationships
        return self._deduplicate_relationships(relationships)

    def _extract_from_join(self, join: JoinClause, from_clause: FromClause) -> Relationship | None:




        """Extract relationship from a JOIN clause.

        Args:
            join: JOIN clause AST node
            from_clause: FROM clause containing table references

        Returns:
            Extracted relationship or None
        """
        if not join.table:
            logger.debug("No table in join clause")
            return None
        if not join.on_condition:
            logger.debug("No on_condition in join clause")
            return None

        logger.debug("Join table: %s, on_condition: %s", join.table, join.on_condition)

        # Build alias to table name mapping
        alias_map = self._build_alias_map(from_clause)
        logger.debug("Alias map: %s", alias_map)

        # Get join type
        join_type_str = join.join_operator.upper()
        join_type = self._parse_join_type(join_type_str)
        logger.debug("Join type: %s", join_type)

        # Get target table
        target_table = self._get_table_name(join.table)
        if not target_table:
            logger.debug("Could not get target table name")
            return None
        logger.debug("Target table: %s", target_table)

        # Find source table (usually the first table in FROM or previous join)
        source_table = self._find_source_table(from_clause)
        if not source_table:
            logger.debug("Could not find source table")
            return None
        logger.debug("Source table: %s", source_table)

        # Extract column mappings from ON condition
        mappings = self._extract_column_mappings(join.on_condition, alias_map)
        if not mappings:
            logger.debug("No column mappings found")
            return None
        logger.debug("Found %s column mappings", len(mappings))

        # Filter mappings to only include ones between source and target tables
        relevant_mappings = []
        for mapping in mappings:
            logger.debug("Checking mapping: %s.%s -> %s.%s", mapping.source_table, mapping.source_column, mapping.target_table, mapping.target_column)
            logger.debug("Source table: %s, Target table: %s", source_table, target_table)
            if (mapping.source_table in [source_table, target_table] and
                mapping.target_table in [source_table, target_table]):
                relevant_mappings.append(mapping)
                logger.debug("Mapping is relevant")
            else:
                logger.debug("Mapping is not relevant")

        if not relevant_mappings:
            logger.debug("No relevant mappings found")
            return None
        logger.debug("Found %s relevant mappings", len(relevant_mappings))

        # Determine relationship type
        rel_type = self._determine_relationship_type(
            source_table, target_table, relevant_mappings, join_type,
        )

        # Create relationship
        rel_name = f"{source_table}_{target_table}"
        is_optional = join_type in [JoinType.LEFT, JoinType.RIGHT, JoinType.FULL]

        return Relationship(
            name=rel_name, source_table=source_table, target_table=target_table, relationship_type=rel_type, join_type=join_type, column_mappings=relevant_mappings, join_condition=self._expression_to_sql(join.on_condition), is_optional=is_optional,
        )

    def _extract_from_where(self, where_clause: WhereClause, from_clause: FromClause) -> list[Relationship]:




        """Extract implicit relationships from WHERE clause.

        Args:
            where_clause: WHERE clause AST node
            from_clause: FROM clause containing table references

        Returns:
            List of extracted relationships
        """
        relationships = []

        if not where_clause.condition:
            return relationships

        # Build alias map
        alias_map = self._build_alias_map(from_clause)

        # Get all tables in FROM clause
        tables = self._get_all_tables(from_clause)
        if len(tables) < 2:
            return relationships

        # Find equality conditions between columns of different tables
        mappings = self._extract_column_mappings(where_clause.condition, alias_map)

        # Group mappings by table pairs
        table_pairs: dict[tuple[str, str] | list[ColumnMapping]] = {}
        for mapping in mappings:
            if mapping.source_table != mapping.target_table:
                pair = tuple(sorted([mapping.source_table, mapping.target_table]))
                if pair not in table_pairs:
                    table_pairs[pair] = []
                table_pairs[pair].append(mapping)

        # Create relationships for each table pair
        for (table1, table2), pair_mappings in table_pairs.items():
            rel_type = self._determine_relationship_type(
                table1, table2, pair_mappings, JoinType.INNER,
            )

            rel = Relationship(
                name=f"{table1}_{table2}_implicit", source_table=table1, target_table=table2, relationship_type=rel_type, join_type=JoinType.INNER, column_mappings=pair_mappings, is_optional=False,
            )
            relationships.append(rel)

        return relationships

    def _parse_join_type(self, join_str: str) -> JoinType:




        """Parse join type from string."""
        join_upper = join_str.upper()

        if "LEFT" in join_upper:
            return JoinType.LEFT
        elif "RIGHT" in join_upper:
            return JoinType.RIGHT
        elif "FULL" in join_upper:
            return JoinType.FULL
        elif "CROSS" in join_upper:
            return JoinType.CROSS
        else:
            return JoinType.INNER

    def _get_table_name(self, table_ref: TableReference | Any) -> str | None:




        """Extract table name from table reference."""
        if isinstance(table_ref, TableReference):
            return table_ref.table_name
        elif hasattr(table_ref, "table_name"):
            return table_ref.table_name
        return None

    def _find_source_table(self, from_clause: FromClause) -> str | None:




        """Find the source table for a join (usually the first table)."""
        if from_clause.tables:
            return self._get_table_name(from_clause.tables[0])
        return None

    def _get_all_tables(self, from_clause: FromClause) -> list[str]:




        """Get all table names from FROM clause."""
        tables = []

        # Add tables from FROM
        for table_ref in from_clause.tables:
            table_name = self._get_table_name(table_ref)
            if table_name:
                tables.append(table_name)

        # Add tables from JOINs
        for join in from_clause.joins:
            table_name = self._get_table_name(join.table)
            if table_name:
                tables.append(table_name)

        return tables

    def _extract_column_mappings(self, expr: Expression, alias_map: dict[str, str | None] = None) -> list[ColumnMapping]:




        """Extract column equality mappings from an expression.

        Args:
            expr: Expression to analyze (usually from ON or WHERE)
            alias_map: Optional mapping of alias to table name

        Returns:
            List of column mappings found
        """
        mappings = []

        logger.debug("Extracting mappings from expression type: %s", type(expr))

        if isinstance(expr, BinaryExpression):
            logger.debug("Binary expression operator: %s", expr.operator)
            if expr.operator == "=":
                # Check if both sides are column references
                left_col = self._extract_column_ref(expr.left, alias_map)
                right_col = self._extract_column_ref(expr.right, alias_map)

                logger.debug("Left column: %s, Right column: %s", left_col, right_col)

                if left_col and right_col:
                    # Create mapping
                    mapping = ColumnMapping(
                        source_table=left_col[0], source_column=left_col[1], target_table=right_col[0], target_column=right_col[1],
                    )
                    mappings.append(mapping)
                    logger.debug("Added mapping: %s", mapping)

            elif expr.operator.upper() == "AND":
                # Recursively extract from both sides
                mappings.extend(self._extract_column_mappings(expr.left, alias_map))
                mappings.extend(self._extract_column_mappings(expr.right, alias_map))

        return mappings

    def _extract_column_ref(self, expr: Expression, alias_map: dict[str, str | None] = None) -> tuple[str, str | None]:




        """Extract table and column name from expression.

        Args:
            expr: Expression to extract from
            alias_map: Optional mapping of alias to table name

        Returns:
            Tuple of (table_name, column_name) or None
        """
        if isinstance(expr, ColumnReference):
            if expr.table_name:
                # Resolve alias if we have a mapping
                table_name = expr.table_name
                if alias_map and table_name in alias_map:
                    table_name = alias_map[table_name]
                return (table_name, expr.column_name)
            else:
                # Try to infer table from column name
                # This is a simplified approach - in practice, you'd need schema info
                return (self._infer_table_from_column(expr.column_name), expr.column_name)

        return None

    def _infer_table_from_column(self, column_name: str) -> str:




        """Infer table name from column name using common patterns."""
        # Try to match foreign key patterns
        for pattern in self.fk_patterns:
            match = pattern.match(column_name)
            if match:
                return match.group(1)

        # Default to "unknown"
        return "unknown"

    def _determine_relationship_type(self, source_table: str, target_table: str, mappings: list[ColumnMapping], join_type: JoinType) -> RelationshipType:




        """Determine the type of relationship based on mappings and join type.

        Args:
            source_table: Source table name
            target_table: Target table name
            mappings: Column mappings between tables
            join_type: Type of SQL join

        Returns:
            Determined relationship type
        """
        # Simple heuristics - in practice, you'd need schema information
        # to properly determine cardinality

        # Check if any mapping involves a primary key
        has_pk_mapping = False
        for mapping in mappings:
            if self._is_primary_key(mapping.source_column) or \
               self._is_primary_key(mapping.target_column):
                has_pk_mapping = True
                break

        # Check if any mapping looks like a foreign key
        has_fk_mapping = False
        for mapping in mappings:
            if self._is_foreign_key(mapping.source_column) or \
               self._is_foreign_key(mapping.target_column):
                has_fk_mapping = True
                break

        # Determine relationship type
        if has_pk_mapping and has_fk_mapping:
            # Classic foreign key relationship
            return RelationshipType.MANY_TO_ONE
        elif len(mappings) > 1:
            # Multiple column join might indicate many-to-many
            return RelationshipType.MANY_TO_MANY
        elif "_lookup" in source_table.lower() or "_lookup" in target_table.lower():
            return RelationshipType.LOOKUP
        else:
            # Default to one-to-many
            return RelationshipType.ONE_TO_MANY

    def _is_primary_key(self, column_name: str) -> bool:




        """Check if column name matches primary key patterns."""
        column_lower = column_name.lower()
        for pattern in self.pk_patterns:
            if pattern.match(column_lower):
                return True
        return False

    def _is_foreign_key(self, column_name: str) -> bool:




        """Check if column name matches foreign key patterns."""
        column_lower = column_name.lower()
        for pattern in self.fk_patterns:
            if pattern.match(column_lower):
                return True
        return False

    def _expression_to_sql(self, expr: Expression) -> str:




        """Convert expression back to SQL string for documentation."""
        # Simplified conversion - in practice, use a proper SQL generator
        if isinstance(expr, BinaryExpression):
            left = self._expression_to_sql(expr.left)
            right = self._expression_to_sql(expr.right)
            return f"{left} {expr.operator} {right}"
        elif isinstance(expr, ColumnReference):
            if expr.table_name:
                return f"{expr.table_name}.{expr.column_name}"
            return expr.column_name
        else:
            return str(expr)

    def _deduplicate_relationships(self, relationships: list[Relationship]) -> list[Relationship]:




        """Remove duplicate relationships."""
        unique = {}
        for rel in relationships:
            # Create a key based on tables and mappings
            key = (
                tuple(sorted([rel.source_table, rel.target_table])), tuple(sorted(str(m) for m in rel.column_mappings)),
            )
            if key not in unique:
                unique[key] = rel

        return list(unique.values())

    def generate_repository_methods(self, relationships: list[Relationship]) -> dict[str, list[str]]:




        """Generate repository method signatures for relationships.

        Args:
            relationships: List of relationships

        Returns:
            Dictionary mapping table names to list of method signatures
        """
        methods_by_table: dict[str, list[str]] = {}

        for rel in relationships:
            # Add methods to source table repository
            if rel.source_table not in methods_by_table:
                methods_by_table[rel.source_table] = []

            # Generate method based on relationship type
            if rel.relationship_type == RelationshipType.ONE_TO_MANY:
                # Get related items
                method = f"Future<List<{self._to_pascal_case(rel.target_table)}>> get{self._to_pascal_case(rel.target_table)}s(int id)"
                methods_by_table[rel.source_table].append(method)

            elif rel.relationship_type == RelationshipType.MANY_TO_ONE:
                # Get parent item
                method = f"Future<{self._to_pascal_case(rel.target_table)}?> get{self._to_pascal_case(rel.target_table)}()"
                methods_by_table[rel.source_table].append(method)

            elif rel.relationship_type == RelationshipType.MANY_TO_MANY:
                # Get related items through junction
                method = f"Future<List<{self._to_pascal_case(rel.target_table)}>> get{self._to_pascal_case(rel.target_table)}s(int id)"
                methods_by_table[rel.source_table].append(method)

            elif rel.relationship_type == RelationshipType.LOOKUP:
                # Get lookup value
                method = f"Future<{self._to_pascal_case(rel.target_table)}?> get{self._to_pascal_case(rel.target_table)}Lookup(String code)"
                methods_by_table[rel.source_table].append(method)

        return methods_by_table

    def _to_pascal_case(self, name: str) -> str:




        """Convert table name to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def _build_alias_map(self, from_clause: FromClause) -> dict[str, str]:




        """Build mapping of table aliases to table names.

        Args:
            from_clause: FROM clause containing table references

        Returns:
            Dictionary mapping alias to table name
        """
        alias_map = {}

        # Add tables from FROM clause
        for table_ref in from_clause.tables:
            if hasattr(table_ref, "alias") and table_ref.alias:
                table_name = self._get_table_name(table_ref)
                if table_name:
                    alias_map[table_ref.alias] = table_name

        # Add tables from JOINs
        for join in from_clause.joins:
            if hasattr(join.table, "alias") and join.table.alias:
                table_name = self._get_table_name(join.table)
                if table_name:
                    alias_map[join.table.alias] = table_name

        return alias_map
