"""Constants for parse utilities."""

from pathlib import Path

# Base directory for grammars
GRAMMAR_DIR = Path(__file__).parent.parent / "grammar"

# Grammar files
POWERBUILDER_GRAMMAR = GRAMMAR_DIR / "powerbuilder.lark"
SQL_GRAMMAR = GRAMMAR_DIR / "sql.lark"
TRANSACTION_GRAMMAR = GRAMMAR_DIR / "transactions.lark"