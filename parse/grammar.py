"""PowerBuilder grammar and type handling.

This module provides grammar loading and type handling functionality.
"""

from __future__ import annotations

from typing import Any

from lark import Lark, Tree
from lark.exceptions import LarkError

from model.utils.type_system import (
    format_type_info,
    normalize_type_name,
    validate_simple_type,
)

from .constants import GRAMMAR_DIR
from .exceptions import GrammarLoadError
from .logging import get_logger

# Get module logger
logger = get_logger("grammar")


# ─── Grammar Loading ────────────────────────────────────────────────────
def load_grammar(
    name: str,
    *,
    start: str = 'file',
    error_recovery: bool = True,
    debug: bool = False,
    cache: bool = True,
) -> Lark:
    """Load a grammar file by name.

    Args:
        name: Name of the grammar file (without .lark extension)
        start: The start symbol for the grammar (defaults to 'file')
        error_recovery: Whether to enable error recovery
        debug: Whether to enable debug output
        cache: Whether to cache the grammar

    Returns:
        Loaded Lark grammar

    Raises:
        GrammarLoadError: If grammar file cannot be loaded
    """
    try:
        grammar_file = GRAMMAR_DIR / f'{name}.lark'
        logger.debug(f"Loading grammar file: {grammar_file}")

        with open(grammar_file, encoding='utf-8') as f:
            grammar_content = f.read()
            logger.debug(f"Grammar file loaded: {len(grammar_content)} bytes")

            return Lark(
                grammar_content,
                parser='earley',
                start=start,
                debug=debug,
                cache=cache,
                propagate_positions=True,
            )
    except FileNotFoundError:
        logger.error(f"Grammar file not found: {name}.lark")
        raise GrammarLoadError(f"Grammar file '{name}.lark' not found") from None
    except LarkError as e:
        logger.error(f"Error in grammar file {name}.lark: {e}")
        raise GrammarLoadError(f"Error in grammar '{name}': {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading grammar {name}.lark: {e}")
        raise GrammarLoadError(f"Failed to load grammar '{name}': {e}") from e


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
        grammar_file = GRAMMAR_DIR / f'{name}.lark'
        logger.debug(f"Extracting rules from grammar file: {grammar_file}")

        with open(grammar_file, encoding='utf-8') as f:
            rules = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('//') and ':' in line:
                    rule = line.split(':')[0].strip()
                    rules.append(rule)

            logger.debug(f"Found {len(rules)} rules in {name}.lark")
            return rules
    except FileNotFoundError:
        logger.error(f"Grammar file not found: {name}.lark")
        raise GrammarLoadError(f"Grammar file '{name}.lark' not found") from None
    except Exception as e:
        logger.error(f"Error extracting rules from {name}.lark: {e}")
        raise GrammarLoadError(f"Failed to extract rules from '{name}': {e}") from e


# ─── Type Handling ─────────────────────────────────────────────────────
# Use normalized basic types from type_system
BASIC_TYPES = {
    'int': 'integer',
    'str': 'string',
    'bool': 'boolean',
    'date': 'date',
    'time': 'time',
    'dec': 'decimal',
    'real': 'real',
    'char': 'character',
    'blob': 'blob',
    'any': 'any',
}


def normalize_type(type_name: str) -> str:
    """Normalize a type name to PowerBuilder standard.

    Deprecated: Use model.utils.type_system.normalize_type_name instead.

    Args:
        type_name: Raw type name

    Returns:
        Normalized type name
    """
    import warnings
    warnings.warn(
        "parse.grammar.normalize_type is deprecated. Use model.utils.type_system.normalize_type_name instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return normalize_type_name(type_name)


def validate_type(type_info: dict[str, Any]) -> bool:
    """Validate type information.

    This is a wrapper around model.utils.type_system.validate_simple_type.

    Deprecated: Use model.utils.type_system.validate_simple_type instead.

    Args:
        type_info: Type information dictionary

    Returns:
        True if type information is valid

    Raises:
        TypeValidationError: If type information is invalid
    """
    import warnings
    warnings.warn(
        "parse.grammar.validate_type is deprecated. Use model.utils.type_system.validate_simple_type instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_simple_type(type_info)


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
    if tree.data != 'type':
        raise ValueError(f'Invalid type tree: {tree.data}')

    type_info = {
        'name': str(tree.children[0]),
        'is_array': False,
        'array_bounds': None,
    }

    if len(tree.children) > 1:
        bounds_node = tree.children[1]
        if bounds_node.data == 'array_bounds':
            type_info['is_array'] = True
            type_info['array_bounds'] = [
                int(bound) for bound in bounds_node.children
            ]

    validate_simple_type(type_info)
    return type_info


def format_type(type_info: dict[str, str | bool | list[int]]) -> str:
    """Format a type dictionary as a string.

    This is a wrapper around model.utils.type_system.format_type_info.

    Deprecated: Use model.utils.type_system.format_type_info instead.

    Args:
        type_info: Type information dictionary

    Returns:
        Formatted type string
    """
    import warnings
    warnings.warn(
        "parse.grammar.format_type is deprecated. Use model.utils.type_system.format_type_info instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return format_type_info(type_info)
