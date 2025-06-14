"""PowerBuilder library management.

This module provides the LibraryManager class for managing PowerBuilder library
imports and dependencies. It handles library resolution, symbol exports, and
dependency graph management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .exceptions import ParseError

logger = logging.getLogger(__name__)


@dataclass
class Library:
    """Represents a PowerBuilder library.

    Attributes:
        name: Library name (without extension)
        path: Full path to library file
        exports: Exported symbols (classes, functions, etc.)
        imports: Libraries this library depends on
        metadata: Additional library metadata
    """

    name: str
    path: Path
    exports: dict[str, Any] = field(default_factory=dict)
    imports: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_export(self, symbol: str) -> Any | None:
        """Get an exported symbol by name."""
        return self.exports.get(symbol)

    def add_export(self, symbol: str, value: Any) -> None:
        """Add an exported symbol."""
        self.exports[symbol] = value

    def add_import(self, library_name: str) -> None:
        """Add an import dependency."""
        self.imports.add(library_name)


class LibraryManager:
    """Manages PowerBuilder library imports and dependencies.

    This class provides functionality for:
    - Resolving library imports from multiple search paths
    - Tracking exported symbols from libraries
    - Building and analyzing dependency graphs
    - Detecting circular dependencies
    - Caching parsed libraries for performance

    Attributes:
        library_paths: List of directories to search for libraries
        _cache: Cache of loaded libraries
        _import_graph: Dependency graph (library -> set of imported libraries)
        _parser: Parser instance for parsing library files
    """

    def __init__(self, library_paths: list[Path] | None = None) -> None:
        """Initialize LibraryManager.

        Args:
            library_paths: List of paths to search for libraries.
                         Defaults to current directory.
        """
        if library_paths is None:
            library_paths = [Path.cwd()]

        self.library_paths = [Path(p) for p in library_paths]
        self._cache: dict[str, Library] = {}
        self._import_graph: dict[str, set[str]] = {}
        self._file_cache: dict[
            tuple[str, ...], Path | None
        ] = {}  # Cache for _find_library_file

        logger.debug(f"LibraryManager initialized with paths: {self.library_paths}")

    def add_library_path(self, path: Path) -> None:
        """Add a search path for libraries.

        Args:
            path: Directory to add to search paths
        """
        path = Path(path)
        if path not in self.library_paths:
            self.library_paths.append(path)
            # Clear file cache when paths change
            self._file_cache.clear()
            logger.debug(f"Added library path: {path}")

    def resolve_import(self, import_name: str) -> Library | None:
        """Resolve an import to a library.

        This method searches for the library in the following order:
        1. Check cache for already loaded library
        2. Search in library paths with various extensions
        3. Handle wildcards in import names
        4. Build dependency graph

        Args:
            import_name: Name of library to import (may include wildcards)

        Returns:
            Loaded Library object or None if not found
        """
        # Normalize import name
        base_name = import_name.replace("*", "").strip()

        # Check cache first
        if base_name in self._cache:
            logger.debug(f"Using cached library: {base_name}")
            return self._cache[base_name]

        # Search for library file
        library_file = self._find_library_file(base_name)
        if not library_file:
            logger.warning(f"Library not found: {import_name}")
            return None

        # Load and parse library
        try:
            library = self._load_library(library_file)

            # Handle wildcard imports
            if "*" in import_name:
                # For wildcard imports, we might need to load multiple files
                # or handle special PowerBuilder import semantics
                logger.debug(f"Processing wildcard import: {import_name}")

            return library

        except Exception as e:
            logger.exception(f"Failed to load library {import_name}: {e}")
            return None

    def _find_library_file(self, library_name: str) -> Path | None:
        """Find library file in search paths with caching.

        Args:
            library_name: Base name of library (without extension)

        Returns:
            Path to library file or None if not found
        """
        # Create cache key from library name and current paths
        cache_key = (library_name, *[str(p) for p in self.library_paths])

        # Check cache first
        if cache_key in self._file_cache:
            cached_result = self._file_cache[cache_key]
            if cached_result:
                logger.debug(f"Found library in cache: {cached_result}")
            return cached_result

        # Common PowerBuilder library extensions
        extensions = [".pbl", ".pbd", ".dll", ".pbx", ""]

        for lib_path in self.library_paths:
            for ext in extensions:
                # Try exact match
                candidate = lib_path / f"{library_name}{ext}"
                if candidate.exists() and candidate.is_file():
                    logger.debug(f"Found library: {candidate}")
                    self._file_cache[cache_key] = candidate
                    return candidate

                # Try case-insensitive match on case-sensitive filesystems
                for file in lib_path.iterdir():
                    if file.is_file() and file.stem.lower() == library_name.lower():
                        if not ext or file.suffix.lower() == ext.lower():
                            logger.debug(f"Found library (case-insensitive): {file}")
                            self._file_cache[cache_key] = file
                            return file

        # Cache negative result too
        self._file_cache[cache_key] = None
        return None

    def _load_library(self, library_file: Path) -> Library:
        """Load and parse a library file.

        Args:
            library_file: Path to library file

        Returns:
            Loaded Library object

        Raises:
            ParseError: If library cannot be parsed
        """
        library_name = library_file.stem

        # Create library object
        library = Library(
            name=library_name,
            path=library_file,
            metadata={
                "file_type": library_file.suffix.lower(),
                "size": library_file.stat().st_size,
                "modified": library_file.stat().st_mtime,
            },
        )

        # Parse library based on file type
        if library_file.suffix.lower() in [".pbl", ".pbd"]:
            # PowerBuilder library - extract exports
            self._extract_pb_exports(library)
        elif library_file.suffix.lower() == ".dll":
            # DLL - extract exported functions
            self._extract_dll_exports(library)
        else:
            # Source file - parse for exports
            self._parse_source_exports(library)

        # Cache the library
        self._cache[library_name] = library

        # Update dependency graph
        self._import_graph[library_name] = library.imports

        logger.info(
            f"Loaded library {library_name} with {len(library.exports)} exports"
        )

        return library

    def _extract_pb_exports(self, library: Library) -> None:
        """Extract exports from PowerBuilder library file.

        Args:
            library: Library object to populate
        """
        # This would use the extract module to read PBL/PBD files
        # For now, provide a basic implementation
        logger.debug(f"Extracting exports from PB library: {library.path}")

        # Placeholder: In real implementation, use extract module
        # to enumerate objects in the library
        library.metadata["pb_version"] = "Unknown"

    def _extract_dll_exports(self, library: Library) -> None:
        """Extract exports from DLL file.

        Args:
            library: Library object to populate
        """
        logger.debug(f"Extracting exports from DLL: {library.path}")

        # Placeholder: In real implementation, use PE parsing
        # to enumerate exported functions

    def _parse_source_exports(self, library: Library) -> None:
        """Parse source file for exported symbols.

        Args:
            library: Library object to populate
        """
        logger.debug(f"Parsing source exports from: {library.path}")

        try:
            # Parse the source file
            content = library.path.read_text(encoding="utf-8")

            # Use parser to extract exported symbols
            # This is simplified - real implementation would parse properly

            # Look for global functions
            if "global function" in content.lower():
                # Extract function declarations
                logger.debug("Found global function declarations")

            # Look for global types
            if "global type" in content.lower():
                # Extract type declarations
                logger.debug("Found global type declarations")

        except Exception as e:
            logger.exception(f"Failed to parse source exports: {e}")

    def get_exported_symbols(self, library_name: str) -> dict[str, Any]:
        """Get all exported symbols from a library.

        Args:
            library_name: Name of library

        Returns:
            Dictionary of symbol name to symbol value/metadata
        """
        library = self.resolve_import(library_name)
        if library:
            return library.exports.copy()
        return {}

    def get_symbol(
        self, symbol_name: str, search_libraries: list[str] | None = None
    ) -> Any | None:
        """Search for a symbol across libraries.

        Args:
            symbol_name: Name of symbol to find
            search_libraries: Optional list of libraries to search.
                            If None, searches all loaded libraries.

        Returns:
            Symbol value/metadata or None if not found
        """
        if search_libraries is None:
            search_libraries = list(self._cache.keys())

        for lib_name in search_libraries:
            if lib_name in self._cache:
                library = self._cache[lib_name]
                symbol = library.get_export(symbol_name)
                if symbol is not None:
                    logger.debug(
                        f"Found symbol '{symbol_name}' in library '{lib_name}'"
                    )
                    return symbol

        return None

    def check_circular_dependencies(self) -> list[list[str]]:
        """Detect circular dependencies in import graph.

        Returns:
            List of circular dependency chains found
        """

        def find_cycles(
            node: str, path: list[str], visited: set[str], rec_stack: set[str]
        ) -> list[list[str]]:
            """DFS to find cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            cycles = []

            for neighbor in self._import_graph.get(node, set()):
                if neighbor not in visited:
                    cycles.extend(find_cycles(neighbor, path[:], visited, rec_stack))
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)
            return cycles

        all_cycles = []
        visited = set()

        for node in self._import_graph:
            if node not in visited:
                rec_stack = set()
                cycles = find_cycles(node, [], visited, rec_stack)
                all_cycles.extend(cycles)

        # Remove duplicate cycles
        unique_cycles = []
        for cycle in all_cycles:
            # Normalize cycle to start with smallest element
            if cycle:
                min_idx = cycle.index(min(cycle))
                normalized = cycle[min_idx:] + cycle[:min_idx]
                if normalized not in unique_cycles:
                    unique_cycles.append(normalized)

        return unique_cycles

    def get_dependency_order(self) -> list[str]:
        """Get libraries in dependency order (topological sort).

        Returns:
            List of library names in order they should be loaded

        Raises:
            ParseError: If circular dependencies exist
        """
        # Check for circular dependencies first
        cycles = self.check_circular_dependencies()
        if cycles:
            msg = f"Circular dependencies detected: {cycles}"
            raise ParseError(msg)

        # Perform topological sort
        visited = set()
        order = []

        def visit(node: str) -> None:
            if node in visited:
                return
            visited.add(node)

            # Visit dependencies first
            for dep in self._import_graph.get(node, set()):
                visit(dep)

            order.append(node)

        # Visit all nodes
        for node in self._import_graph:
            visit(node)

        return order

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._import_graph.clear()
        self._file_cache.clear()
        logger.debug("Cleared all caches")

    def get_library_info(self) -> dict[str, dict[str, Any]]:
        """Get information about loaded libraries.

        Returns:
            Dictionary with library names as keys and info dicts as values
        """
        info = {}

        for name, library in self._cache.items():
            info[name] = {
                "path": str(library.path),
                "exports_count": len(library.exports),
                "imports": list(library.imports),
                "metadata": library.metadata,
            }

        return info


# Singleton instance for convenience
_default_manager: LibraryManager | None = None


def get_default_library_manager() -> LibraryManager:
    """Get the default LibraryManager instance.

    Returns:
        Shared LibraryManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = LibraryManager()
    return _default_manager
