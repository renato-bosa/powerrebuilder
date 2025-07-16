"""Library management for PowerBuilder parsing.

This module provides comprehensive functionality for managing PowerBuilder library files,
including loading PBL/PBD files, caching parsed objects, symbol resolution, and dependency tracking.
"""

import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from threading import Lock

from src.extract.pbd.extractors.base import extract_pbl

logger = logging.getLogger(__name__)


@dataclass
class LibraryInfo:
    """Information about a loaded library."""
    path: Path
    load_time: float
    objects: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    is_compiled: bool = False  # True for PBD, False for PBL


@dataclass 
class SymbolInfo:
    """Information about a symbol in the library system."""
    name: str
    library_path: Path
    object_type: str  # window, userobject, function, etc.
    ast: Any  # The parsed AST
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


class SymbolCache:
    """Thread-safe cache for parsed symbols."""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, SymbolInfo] = {}
        self._access_order: List[str] = []
        self._lock = Lock()
        self.max_size = max_size

    def get(self, key: str) -> Optional[SymbolInfo]:
        """Get a symbol from cache, updating access order."""
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
            return None

    def put(self, key: str, value: SymbolInfo):
        """Add a symbol to cache, evicting LRU if needed."""
        with self._lock:
            if key in self._cache:
                # Update existing
                self._access_order.remove(key)
                self._access_order.append(key)
                self._cache[key] = value
            else:
                # Add new
                if len(self._cache) >= self.max_size:
                    # Evict LRU
                    lru_key = self._access_order.pop(0)
                    del self._cache[lru_key]
                    logger.debug(f"Evicted {lru_key} from symbol cache")

                self._cache[key] = value
                self._access_order.append(key)

    def clear(self):
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


class LibraryManager:
    """Manages PowerBuilder library files with full functionality."""

    # PowerBuilder object type prefixes
    OBJECT_PREFIXES = {
        'n_': 'userobject',      # Non-visual user object
        'u_': 'userobject',      # Visual user object  
        'w_': 'window',          # Window
        'd_': 'datawindow',      # DataWindow
        'm_': 'menu',            # Menu
        'f_': 'function',        # Global function
        'q_': 'query',           # Query object
        's_': 'structure',       # Structure
        'p_': 'pipeline',        # Pipeline object
        'a_': 'application',     # Application object
    }

    def __init__(self, library_paths: List[Path] = None, cache_size: int = 1000):
        """Initialize the library manager.

        Args:
            library_paths: List of paths to search for libraries
            cache_size: Maximum number of symbols to cache
        """
        self.library_paths = library_paths or []
        self.libraries: Dict[Path, LibraryInfo] = {}
        self.symbol_cache = SymbolCache(cache_size)
        self.symbol_index: Dict[str, Path] = {}  # symbol_name -> library_path
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.parser = None  # Lazily initialized
        self._lock = Lock()

        logger.info(f"LibraryManager initialized with {len(self.library_paths)} paths")

        # Auto-load libraries from configured paths
        self._auto_load_libraries()

    def _get_parser(self):
        """Get the parser, creating it lazily if needed."""
        if self.parser is None:
            from src.parse.parser.powerbuilder import UnifiedPowerBuilderParser
            self.parser = UnifiedPowerBuilderParser()
        return self.parser

    def _auto_load_libraries(self):
        """Automatically load libraries from configured paths."""
        for path in self.library_paths:
            if path.is_file() and path.suffix.lower() in ('.pbl', '.pbd'):
                try:
                    self.load_library(path)
                except Exception as e:
                    logger.error(f"Failed to auto-load library {path}: {e}")
            elif path.is_dir():
                # Search directory for library files
                for lib_file in path.glob('**/*.pb[ld]'):
                    try:
                        self.load_library(lib_file)
                    except Exception as e:
                        logger.error(f"Failed to auto-load library {lib_file}: {e}")

    def load_library(self, library_path: Path) -> LibraryInfo:
        """Load a PowerBuilder library file (PBL or PBD).

        Args:
            library_path: Path to the library file

        Returns:
            LibraryInfo object with loaded library data
        """
        library_path = Path(library_path).resolve()

        # Check if already loaded
        if library_path in self.libraries:
            logger.debug(f"Library already loaded: {library_path}")
            return self.libraries[library_path]

        logger.info(f"Loading library: {library_path}")
        start_time = time.time()

        # Create temporary extraction directory
        temp_dir = Path(f"/tmp/pb_lib_extract_{library_path.stem}_{os.getpid()}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Extract library contents
            extract_pbl(str(library_path), str(temp_dir))

            # Create library info
            lib_info = LibraryInfo(
                path=library_path,
                load_time=time.time() - start_time,
                is_compiled=library_path.suffix.lower() == '.pbd'
            )

            # Parse extracted objects
            self._parse_library_objects(lib_info, temp_dir)

            # Store library info
            with self._lock:
                self.libraries[library_path] = lib_info

            logger.info(f"Loaded library {library_path} with {len(lib_info.objects)} objects in {lib_info.load_time:.2f}s")
            return lib_info

        except Exception as e:
            logger.error(f"Failed to load library {library_path}: {e}")
            raise
        finally:
            # Clean up temp directory
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _parse_library_objects(self, lib_info: LibraryInfo, extract_dir: Path):
        """Parse all objects extracted from a library."""
        parser = self._get_parser()

        # Get supported extensions from UnifiedPowerBuilderParser
        supported_extensions = set(parser.EXTENSION_PARSERS.keys())

        for obj_file in extract_dir.iterdir():
            # Check if file extension is supported (without the dot)
            if obj_file.is_file() and obj_file.suffix[1:].lower() in supported_extensions:
                try:
                    # Parse to AST directly from file path
                    ast = parser.parse(obj_file)

                    # Get object name (filename without extension)
                    obj_name = obj_file.stem.lower()

                    # Store in library
                    lib_info.objects[obj_name] = ast

                    # Create symbol info
                    symbol_info = SymbolInfo(
                        name=obj_name,
                        library_path=lib_info.path,
                        object_type=self._detect_object_type(obj_name, obj_file.suffix),
                        ast=ast
                    )

                    # Extract dependencies from AST
                    symbol_info.dependencies = self._extract_dependencies(ast)
                    lib_info.dependencies.update(symbol_info.dependencies)

                    # Update indices
                    with self._lock:
                        self.symbol_index[obj_name] = lib_info.path
                        self.symbol_cache.put(obj_name, symbol_info)

                        # Update dependency graph
                        for dep in symbol_info.dependencies:
                            self.dependency_graph[dep].add(obj_name)

                except Exception as e:
                    logger.error(f"Failed to parse {obj_file}: {e}")

    def _detect_object_type(self, obj_name: str, file_ext: str) -> str:
        """Detect the type of a PowerBuilder object from its name and extension."""
        obj_name_lower = obj_name.lower()

        # Check common prefixes
        for prefix, obj_type in self.OBJECT_PREFIXES.items():
            if obj_name_lower.startswith(prefix):
                return obj_type

        # Check file extension
        ext_map = {
            '.srw': 'window',
            '.sru': 'userobject', 
            '.srf': 'function',
            '.srm': 'menu',
            '.srs': 'structure',
            '.sra': 'application',
            '.srd': 'datawindow',
            '.dwo': 'datawindow',
        }

        return ext_map.get(file_ext, 'unknown')

    def _extract_dependencies(self, ast: Any) -> Set[str]:
        """Extract dependencies from an AST."""
        dependencies = set()

        # This is a simplified implementation - extend based on your AST structure
        def walk_ast(node):
            if hasattr(node, '__dict__'):
                # Check for type references
                if hasattr(node, 'type_name'):
                    dependencies.add(node.type_name.lower())

                # Check for function calls
                if hasattr(node, 'function_name'):
                    dependencies.add(node.function_name.lower())

                # Check for ancestor/parent references
                if hasattr(node, 'ancestor'):
                    dependencies.add(node.ancestor.lower())

                # Recursively walk children
                for attr_name, attr_value in node.__dict__.items():
                    if isinstance(attr_value, list):
                        for item in attr_value:
                            walk_ast(item)
                    elif hasattr(attr_value, '__dict__'):
                        walk_ast(attr_value)

        walk_ast(ast)
        return dependencies

    def get_symbol(self, symbol_name: str, search_order: List[Path] = None) -> Optional[SymbolInfo]:
        """Get a symbol from the libraries with hierarchical search.

        Args:
            symbol_name: Name of the symbol to retrieve
            search_order: Optional list of library paths to search first

        Returns:
            SymbolInfo if found, None otherwise
        """
        symbol_name_lower = symbol_name.lower()

        # Check cache first
        cached = self.symbol_cache.get(symbol_name_lower)
        if cached:
            logger.debug(f"Symbol {symbol_name} found in cache")
            return cached

        # Search libraries in order
        search_paths = search_order or []
        search_paths.extend([p for p in self.libraries.keys() if p not in search_paths])

        for lib_path in search_paths:
            if lib_path in self.libraries:
                lib_info = self.libraries[lib_path]
                if symbol_name_lower in lib_info.objects:
                    # Create symbol info
                    symbol_info = SymbolInfo(
                        name=symbol_name_lower,
                        library_path=lib_path,
                        object_type=self._detect_object_type(symbol_name_lower, ''),
                        ast=lib_info.objects[symbol_name_lower]
                    )

                    # Cache and return
                    self.symbol_cache.put(symbol_name_lower, symbol_info)
                    logger.debug(f"Symbol {symbol_name} found in {lib_path}")
                    return symbol_info

        logger.debug(f"Symbol {symbol_name} not found in any library")
        return None

    def add_symbol(self, symbol_name: str, symbol_value: Any, library_path: Path = None):
        """Add a symbol to the library system.

        Args:
            symbol_name: Name of the symbol
            symbol_value: AST or parsed value of the symbol
            library_path: Optional library path to associate with
        """
        symbol_name_lower = symbol_name.lower()

        # Use current directory as default library
        if library_path is None:
            library_path = Path.cwd()

        # Ensure library exists in our system
        if library_path not in self.libraries:
            self.libraries[library_path] = LibraryInfo(
                path=library_path,
                load_time=0.0,
                is_compiled=False
            )

        # Add to library
        lib_info = self.libraries[library_path]
        lib_info.objects[symbol_name_lower] = symbol_value

        # Create symbol info
        symbol_info = SymbolInfo(
            name=symbol_name_lower,
            library_path=library_path,
            object_type=self._detect_object_type(symbol_name_lower, ''),
            ast=symbol_value
        )

        # Update indices - Note: symbol_index only tracks ONE library per symbol
        # This is a limitation - in real use, symbols should have unique names
        # For hierarchical search, we rely on searching libraries directly
        with self._lock:
            # Only update symbol_index if this is the first occurrence
            if symbol_name_lower not in self.symbol_index:
                self.symbol_index[symbol_name_lower] = library_path
            # Don't cache here - let get_symbol handle caching based on search order

    def resolve_dependencies(self, symbol_name: str) -> List[str]:
        """Resolve all dependencies for a symbol.

        Args:
            symbol_name: Name of the symbol

        Returns:
            List of dependent symbol names in dependency order
        """
        symbol_name_lower = symbol_name.lower()
        resolved = []
        visited = set()

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)

            # Get symbol info
            symbol_info = self.get_symbol(name)
            if symbol_info:
                # Visit dependencies first
                for dep in symbol_info.dependencies:
                    if dep not in visited:
                        visit(dep)

                # Add to resolved list
                resolved.append(name)

        visit(symbol_name_lower)
        return resolved

    def check_circular_dependencies(self, symbol_name: str) -> Optional[List[str]]:
        """Check for circular dependencies starting from a symbol.

        Args:
            symbol_name: Name of the symbol to check

        Returns:
            List representing the circular path if found, None otherwise
        """
        symbol_name_lower = symbol_name.lower()
        visited = set()
        rec_stack = []

        def has_cycle(name: str) -> Optional[List[str]]:
            visited.add(name)
            rec_stack.append(name)

            # Get symbol info
            symbol_info = self.get_symbol(name)
            if symbol_info:
                for dep in symbol_info.dependencies:
                    if dep not in visited:
                        cycle = has_cycle(dep)
                        if cycle:
                            return cycle
                    elif dep in rec_stack:
                        # Found cycle
                        cycle_start = rec_stack.index(dep)
                        return rec_stack[cycle_start:] + [dep]

            rec_stack.pop()
            return None

        return has_cycle(symbol_name_lower)

    def get_dependents(self, symbol_name: str) -> Set[str]:
        """Get all symbols that depend on the given symbol.

        Args:
            symbol_name: Name of the symbol

        Returns:
            Set of symbol names that depend on this symbol
        """
        symbol_name_lower = symbol_name.lower()
        return self.dependency_graph.get(symbol_name_lower, set()).copy()

    def export_symbol_table(self) -> Dict[str, Any]:
        """Export the complete symbol table for debugging/analysis."""
        table = {
            'libraries': {},
            'symbols': {},
            'dependencies': dict(self.dependency_graph)
        }

        # Export library info
        for lib_path, lib_info in self.libraries.items():
            table['libraries'][str(lib_path)] = {
                'load_time': lib_info.load_time,
                'object_count': len(lib_info.objects),
                'is_compiled': lib_info.is_compiled,
                'objects': list(lib_info.objects.keys())
            }

        # Export symbol info
        for symbol_name, lib_path in self.symbol_index.items():
            table['symbols'][symbol_name] = {
                'library': str(lib_path),
                'type': self._detect_object_type(symbol_name, '')
            }

        return table

    def clear_cache(self):
        """Clear the symbol cache."""
        self.symbol_cache.clear()
        logger.info("Symbol cache cleared")

    def unload_library(self, library_path: Path):
        """Unload a library and remove its symbols.

        Args:
            library_path: Path to the library to unload
        """
        library_path = Path(library_path).resolve()

        if library_path not in self.libraries:
            logger.warning(f"Library not loaded: {library_path}")
            return

        lib_info = self.libraries[library_path]

        with self._lock:
            # Remove symbols from indices
            for obj_name in lib_info.objects:
                if obj_name in self.symbol_index:
                    del self.symbol_index[obj_name]

                # Remove from dependency graph
                if obj_name in self.dependency_graph:
                    del self.dependency_graph[obj_name]

                # Remove as dependent from others
                for deps in self.dependency_graph.values():
                    deps.discard(obj_name)

            # Remove library
            del self.libraries[library_path]

        # Clear cache entries for this library
        self.symbol_cache.clear()  # Simple approach - clear all

        logger.info(f"Unloaded library: {library_path}")