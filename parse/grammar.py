"""Grammar management for PowerBuilder parsing.

This module provides the GrammarManager class for managing multiple Lark grammar files
and their dependencies. It handles grammar loading, caching, and parser creation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import logging
from pathlib import Path

from lark import Lark
from lark.exceptions import GrammarError

from .constants import FileType
from .exceptions import GrammarNotFoundError

logger = logging.getLogger(__name__)


class GrammarManager:
    """Manages multiple Lark grammar files and their dependencies.

    This class provides centralized management of grammar files used for parsing
    different PowerBuilder file types. It handles:
    - Loading grammar files from disk
    - Caching parsed grammar objects
    - Resolving grammar dependencies and imports
    - Creating appropriate parsers for different file types

    Attributes:
        grammar_dir: Directory containing grammar files
        _cache: Cache of loaded Lark parser instances
        _grammars: Cache of raw grammar strings
        _dependencies: Tracks grammar import dependencies
    """

    def __init__(self, grammar_dir: Path | None = None) -> None:
        """Initialize GrammarManager.

        Args:
            grammar_dir: Directory containing grammar files. Defaults to parse/grammar/
        """
        if grammar_dir is None:
            grammar_dir = Path(__file__).parent / "grammar"

        self.grammar_dir = Path(grammar_dir)
        if not self.grammar_dir.exists():
            msg = f"Grammar directory not found: {self.grammar_dir}"
            raise GrammarNotFoundError(msg)

        self._cache: dict[str, Lark] = {}
        self._grammars: dict[str, str] = {}
        self._dependencies: dict[str, set[str]] = {}

        # Mapping of file types to grammar names
        self._file_type_mapping = {
            FileType.WINDOW: "powerbuilder",
            FileType.USER_OBJECT: "powerbuilder",
            FileType.FUNCTION: "powerbuilder",
            FileType.STRUCTURE: "powerbuilder",
            FileType.MENU: "powerbuilder",
            FileType.APPLICATION: "powerbuilder",
            FileType.DATAWINDOW: "datawindow",
            FileType.QUERY: "sql",
            FileType.PIPELINE: "powerbuilder",
            FileType.PROJECT: "powerbuilder",
            FileType.PROXY: "powerbuilder",
        }

        logger.debug("GrammarManager initialized with directory: %s", self.grammar_dir)

    def load_grammar(self, name: str, start: str | None = None, **kwargs) -> Lark:
        """Load and cache a grammar by name.

        Args:
            name: Name of the grammar file (without .lark extension)
            start: Start rule for the parser. Defaults to grammar's default
            **kwargs: Additional arguments passed to Lark constructor

        Returns:
            Configured Lark parser instance

        Raises:
            GrammarNotFoundError: If grammar file not found
            GrammarError: If grammar syntax is invalid
        """
        # Create cache key including start rule and kwargs
        cache_key = f"{name}:{start}:{hash(frozenset(kwargs.items()))}"

        # Check cache first
        if cache_key in self._cache:
            logger.debug("Using cached parser for %s", name)
            return self._cache[cache_key]

        # Load grammar content
        grammar_content = self._load_grammar_content(name)

        # Create parser
        try:
            parser_kwargs = {
                "parser": "earley",  # More robust for ambiguous grammars
                "lexer": "contextual",  # Better keyword handling
                "propagate_positions": True,  # Track source positions
                "maybe_placeholders": True,  # Handle optional rules
            }
            parser_kwargs.update(kwargs)

            if start:
                parser_kwargs["start"] = start

            parser = Lark(grammar_content, **parser_kwargs)

            # Cache the parser
            self._cache[cache_key] = parser
            logger.info("Successfully loaded grammar: %s", name)

            return parser

        except GrammarError as e:
            logger.exception("Grammar error in %s: %s", name, e)
            raise
        except Exception as e:
            logger.exception("Failed to create parser for %s: %s", name, e)
            msg = f"Failed to create parser for {name}: {e}"
            raise GrammarError(msg)

    def _load_grammar_content(self, name: str) -> str:
        """Load grammar content from file, resolving imports.

        Args:
            name: Grammar name

        Returns:
            Complete grammar content with imports resolved
        """
        # Check grammar cache
        if name in self._grammars:
            return self._grammars[name]

        grammar_file = self.grammar_dir / f"{name}.lark"
        if not grammar_file.exists():
            msg = f"Grammar file not found: {grammar_file}"
            raise GrammarNotFoundError(msg)

        # Read grammar file
        try:
            content = grammar_file.read_text(encoding="utf-8")
        except Exception as e:
            msg = f"Failed to read grammar file {grammar_file}: {e}"
            raise GrammarError(msg)

        # Resolve imports (simplified - Lark handles %import directives)
        # Track dependencies for circular dependency detection
        self._dependencies[name] = self._extract_imports(content)

        # Cache grammar content
        self._grammars[name] = content

        return content

    def _extract_imports(self, grammar_content: str) -> set[str]:
        """Extract import dependencies from grammar content.

        Args:
            grammar_content: Raw grammar content

        Returns:
            Set of imported grammar names
        """
        imports = set()
        for line in grammar_content.splitlines():
            line = line.strip()
            if line.startswith("%import"):
                # Extract grammar name from import statement
                # Format: %import common.WS -> "common"
                parts = line.split()
                if len(parts) >= 2:
                    import_path = parts[1].split(".")[0]
                    imports.add(import_path)
        return imports

    def register_grammar(self, name: str, content: str) -> None:
        """Register a grammar string directly.

        Useful for testing or dynamic grammar generation.

        Args:
            name: Name to register the grammar under
            content: Grammar content
        """
        self._grammars[name] = content
        self._dependencies[name] = self._extract_imports(content)
        # Clear any cached parsers for this grammar
        keys_to_remove = [k for k in self._cache if k.startswith(f"{name}:")]
        for key in keys_to_remove:
            del self._cache[key]
        logger.debug("Registered grammar: %s", name)

    def get_parser(self, file_type: FileType | str) -> Lark:
        """Get appropriate parser for file type.

        Args:
            file_type: FileType enum or string file extension

        Returns:
            Configured parser for the file type

        Raises:
            ValueError: If file type is not supported
        """
        # Convert string to FileType if needed
        if isinstance(file_type, str):
            # Remove leading dot if present
            ext = file_type.lstrip(".")
            try:
                file_type = FileType(ext)
            except ValueError:
                msg = f"Unsupported file type: {file_type}"
                raise ValueError(msg)

        # Get grammar name for file type
        grammar_name = self._file_type_mapping.get(file_type)
        if not grammar_name:
            msg = f"No grammar mapping for file type: {file_type}"
            raise ValueError(msg)

        # Special handling for different file types
        start_rule = None
        kwargs = {}

        if file_type == FileType.DATAWINDOW:
            start_rule = "datawindow"
        elif file_type == FileType.QUERY:
            start_rule = "sql_statements"
            kwargs["lexer"] = "basic"  # SQL doesn't need contextual lexer

        return self.load_grammar(grammar_name, start=start_rule, **kwargs)

    def clear_cache(self) -> None:
        """Clear grammar and parser caches."""
        self._cache.clear()
        self._grammars.clear()
        self._dependencies.clear()
        logger.debug("Cleared grammar cache")

    def check_circular_dependencies(self) -> list[list[str]]:
        """Check for circular dependencies in grammar imports.

        Returns:
            List of circular dependency chains found
        """

        def find_cycles(
            node: str, path: list[str], visited: set[str]
        ) -> list[list[str]]:
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                return [path[cycle_start:] + [node]]

            if node in visited:
                return []

            visited.add(node)
            path.append(node)

            cycles = []
            for dep in self._dependencies.get(node, set()):
                cycles.extend(find_cycles(dep, path[:], visited))

            return cycles

        all_cycles = []
        visited = set()

        for grammar in self._dependencies:
            if grammar not in visited:
                cycles = find_cycles(grammar, [], visited)
                all_cycles.extend(cycles)

        return all_cycles

    def get_grammar_info(self) -> dict[str, dict]:
        """Get information about loaded grammars.

        Returns:
            Dictionary with grammar names as keys and info dicts as values
        """
        info = {}
        for name in self._grammars:
            info[name] = {
                "loaded": name in self._grammars,
                "cached_parsers": sum(
                    1 for k in self._cache if k.startswith(f"{name}:")
                ),
                "dependencies": list(self._dependencies.get(name, set())),
                "file": str(self.grammar_dir / f"{name}.lark"),
            }
        return info


# Singleton instance for convenience
_default_manager: GrammarManager | None = None


def get_default_manager() -> GrammarManager:
    """Get the default GrammarManager instance.

    Returns:
        Shared GrammarManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = GrammarManager()
    return _default_manager
