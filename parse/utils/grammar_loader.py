"""PowerBuilder grammar and type handling.

This module provides grammar loading and type handling functionality.
"""

from typing import Any, Dict, List, Optional, Union

from __future__ import annotations

import logging

from lark import Lark, Tree
from lark.exceptions import LarkError

from common.types import (
    validate_simple_type,
)

from .constants import GRAMMAR_DIR
from .exceptions import GrammarLoadError

# Get module logger
logger = logging.getLogger(__name__)


# ─── Grammar Loading ────────────────────────────────────────────────────
def load_grammar(
    name: str,
    *,
    start: str = "file",
    parser: str = "lalr",
    error_recovery: bool = True,
    debug: bool = False,
    cache: bool = True,
    import_paths: list[str] | None = None,
) -> Lark:
    """Load a grammar file by name.

    Args:
        name: Name of the grammar file (without .lark extension)
        start: The start symbol for the grammar (defaults to 'file')
        parser: Parser algorithm to use ('lalr' or 'earley', defaults to 'lalr')
        error_recovery: Whether to enable error recovery
        debug: Whether to enable debug output
        cache: Whether to cache the grammar
        import_paths: List of paths for grammar imports

    Returns:
        Loaded Lark grammar

    Raises:
        GrammarLoadError: If grammar file cannot be loaded
    """
    try:
        grammar_file = GRAMMAR_DIR / f"{name}.lark"
        logger.debug("Loading grammar file: %s", grammar_file)

        with open(grammar_file, encoding="utf-8") as f:
            grammar_content = f.read()
            logger.debug("Grammar file loaded: %s bytes", len(grammar_content))

            # Prepare import paths
            if import_paths is None:
                import_paths = [str(GRAMMAR_DIR)]

            # Additional options based on parser type
            parser_options = {
                "parser": parser,
                "start": start,
                "debug": debug,
                "cache": cache,
                "propagate_positions": True,
                "import_paths": import_paths,
            }

            # Add parser-specific options
            if parser == "lalr":
                parser_options["maybe_placeholders"] = True

            return Lark(grammar_content, **parser_options)
    except FileNotFoundError:
        logger.exception("Grammar file not found: %s.lark", name)
        msg = f"Grammar file '{name}.lark' not found"
        raise GrammarLoadError(msg) from None
    except LarkError as e:
        logger.exception("Error in grammar file %s.lark: %s", name, e)
        msg = f"Error in grammar '{name}': {e}"
        raise GrammarLoadError(msg) from e
    except Exception as e:
        logger.exception("Unexpected error loading grammar %s.lark: %s", name, e)
        msg = f"Failed to load grammar '{name}': {e}"
        raise GrammarLoadError(msg) from e


def get_grammar_rules(name: str) -> list[str]:
    """Get all rules from a grammar file.

    Args:
        name: Name of the grammar file (without .lark extension)

    Returns:
        List of rule names

    Raises:
        GrammarLoadError: If grammar file cannot be loaded
    """
    try:
        grammar_file = GRAMMAR_DIR / f"{name}.lark"
        logger.debug("Extracting rules from grammar file: %s", grammar_file)

        with open(grammar_file, encoding="utf-8") as f:
            rules = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("//") and ":" in line:
                    rule = line.split(":")[0].strip()
                    rules.append(rule)

            logger.debug("Found %s rules in %s.lark", len(rules), name)
            return rules
    except FileNotFoundError:
        logger.exception("Grammar file not found: %s.lark", name)
        msg = f"Grammar file '{name}.lark' not found"
        raise GrammarLoadError(msg) from None
    except Exception as e:
        logger.exception("Error extracting rules from %s.lark: %s", name, e)
        msg = f"Failed to extract rules from '{name}': {e}"
        raise GrammarLoadError(msg) from e


# ─── Type Handling ─────────────────────────────────────────────────────


def parse_type(tree: Tree) -> dict[str, str | bool | list[int]]:
    """Parse a type from a parse tree.

    Args:
        tree: Parse tree node

    Returns:
        Dictionary with type information

    Raises:
        ValueError: If tree is invalid
        TypeValidationError: If parsed type is invalid
    """
    if tree.data != "type":
        msg = f"Invalid type tree: {tree.data}"
        raise ValueError(msg)

    type_info = {
        "name": str(tree.children[0]),
        "is_array": False,
        "array_bounds": None,
    }

    if len(tree.children) > 1:
        bounds_node = tree.children[1]
        if bounds_node.data == "array_bounds":
            type_info["is_array"] = True
            type_info["array_bounds"] = [int(bound) for bound in bounds_node.children]

    validate_simple_type(type_info)
    return type_info
