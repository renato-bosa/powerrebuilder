#!/usr/bin/env python3
"""Fix immediate import issues to get tests running."""

import subprocess
from pathlib import Path


def fix_ast_init() -> None:
    """Fix the broken AST __init__.py file."""
    ast_init = Path("src/model/ast/__init__.py")

    # Create a minimal working __init__.py
    new_content = '''"""AST module for PowerBuilder model."""

from __future__ import annotations

# Base nodes
from .nodes.base import Expression, Statement

# Type imports
from .nodes.declarations import Type, TypeCategory, Field

# SQL Node imports
from .nodes.sql import (
    SelectStatement, InsertStatement, UpdateStatement, DeleteStatement,
    ResultColumn, FromClause, TableReference, JoinClause, WhereClause,
    OrderByClause, OrderingTerm, LimitClause, SubqueryExpression,
    Assignment, ColumnReference, GroupByClause, HavingClause,
    WithClause, WithExpression, SetOperationStatement, SqlStatement,
    SqlParameter, ColonParameter, QuestionMarkParameter,
    SQLQuery, SQLCursor, SQLTransaction, SQLCommit, SQLRollback,
    SQLPrepare, SQLVariable, SQLFromClause
)

# Import literals
from .literals import (
    Literal, StringLiteral, IntegerLiteral, RealLiteral,
    NullLiteral, BooleanLiteral, Identifier,
    BinaryExpression, UnaryExpression, Function
)

# Import from functions module
from .functions import *

# Import from io module
from .io import *

# Import PowerBuilder types
from .pb_types import *

__all__ = [
    # Base classes
    "Expression", "Statement",
    # Types
    "Type", "TypeCategory", "Field",
    # Literals
    "Literal", "StringLiteral", "IntegerLiteral", "RealLiteral",
    "NullLiteral", "BooleanLiteral", "Identifier",
    "BinaryExpression", "UnaryExpression", "Function",
    # SQL
    "SelectStatement", "InsertStatement", "UpdateStatement", "DeleteStatement",
    "ResultColumn", "FromClause", "TableReference", "JoinClause", "WhereClause",
    "OrderByClause", "OrderingTerm", "LimitClause", "SubqueryExpression",
    "Assignment", "ColumnReference", "GroupByClause", "HavingClause",
    "WithClause", "WithExpression", "SetOperationStatement", "SqlStatement",
    "SqlParameter", "ColonParameter", "QuestionMarkParameter",
    "SQLQuery", "SQLCursor", "SQLTransaction", "SQLCommit", "SQLRollback",
    "SQLPrepare", "SQLVariable", "SQLFromClause",
]
'''

    ast_init.write_text(new_content)


def fix_missing_node_classes() -> None:
    """Create missing node classes that tests expect."""
    # Check what's missing in literals.py
    literals_file = Path("src/model/ast/literals.py")
    content = literals_file.read_text()

    # Add missing classes
    additions = []

    if "class NullLiteral" not in content:
        additions.append('''
@dataclass
class NullLiteral(Literal):
    """Null literal value."""

    value: None = None
    type: str = field(default="null", init=False)
''')

    if "class Identifier" not in content:
        additions.append('''
@dataclass
class Identifier(Expression):
    """Identifier node."""

    name: str = ""
    type: str = field(default="identifier", init=False)
''')

    if "class BinaryExpression" not in content:
        additions.append('''
@dataclass
class BinaryExpression(Expression):
    """Binary expression node."""

    left: Expression | None = None
    operator: str = ""
    right: Expression | None = None
''')

    if "class UnaryExpression" not in content:
        additions.append('''
@dataclass
class UnaryExpression(Expression):
    """Unary expression node."""

    operator: str = ""
    operand: Expression | None = None
''')

    if "class Function" not in content:
        additions.append('''
@dataclass
class Function(Expression):
    """Function call expression."""

    name: str = ""
    arguments: list[Expression] = field(default_factory=list)
''')

    if additions:
        content = content.rstrip() + "\n" + "\n".join(additions) + "\n"
        literals_file.write_text(content)


def fix_test_imports():
    """Fix common test import issues."""
    fixes = {
        # Model utils that no longer exist
        "from src.model.utils.common import": "from src.common.utils import",
        "from src.model.system.functions import": "from src.model.expressions import",
        "from tests.factories import": "from tests.utils.factories import",
        # Contracts consolidation
        "from src.contracts.extractors import": "from src.contracts import",
        "from src.contracts.parsers import": "from src.contracts import",
        "from src.contracts.decompilers import": "from src.contracts import",
        "from src.contracts.generators import": "from src.contracts import",
    }

    test_files = list(Path("tests").rglob("*.py"))
    fixed_count = 0

    for test_file in test_files:
        try:
            content = test_file.read_text()
            original = content

            for old, new in fixes.items():
                content = content.replace(old, new)

            if content != original:
                test_file.write_text(content)
                fixed_count += 1
        except Exception:
            pass

    return fixed_count


def main() -> None:
    """Run all fixes."""
    # Fix AST init
    fix_ast_init()

    # Add missing node classes
    fix_missing_node_classes()

    # Fix test imports
    fix_test_imports()

    # Try to collect tests again
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        check=False,
        capture_output=True,
        text=True,
    )

    # Count successful collections
    if result.returncode == 0:
        lines = result.stdout.strip().split("\n")
        len([l for l in lines if "<Function" in l or "<Method" in l])
    else:
        # Show remaining errors
        errors = result.stderr
        if "ModuleNotFoundError" in errors or "ImportError" in errors:
            # Extract unique error patterns
            import_errors = set()
            for line in errors.split("\n"):
                if "ModuleNotFoundError:" in line or "ImportError:" in line:
                    import_errors.add(line.strip())

            for _error in sorted(import_errors):
                pass


if __name__ == "__main__":
    main()
