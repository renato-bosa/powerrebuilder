"""Library and behavioral classes for PowerBuilder.

This module contains classes for handling PowerBuilder libraries and behavioral elements.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from src.model.types.base import PBNode


@dataclass
class Export(PBNode):
    """Library export definition."""
    
    object_name: str = ""
    to_library: str | None = None


@dataclass
class Import(PBNode):
    """Library import definition."""
    
    object_name: str = ""
    from_library: str = ""


@dataclass
class LibraryObject(PBNode):
    """Library object definition."""
    
    name: str = ""
    object_type: str = ""  # window, menu, userobject, datawindow, etc.
    source_file: str | None = field(default=None)


@dataclass
class Library(PBNode):
    """PowerBuilder library object."""
    
    name: str = ""
    path: str = ""
    is_system: bool = False
    exports: list[Export] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)


@dataclass
class PBLibrary(PBNode):
    """PowerBuilder library containing various objects."""
    
    name: str = ""
    file_path: str = ""
    windows: list = field(default_factory=list)
    user_objects: list = field(default_factory=list)
    datawindows: list = field(default_factory=list)
    menus: list = field(default_factory=list)
    global_functions: list = field(default_factory=list)
    structures: list = field(default_factory=list)
    global_variables: list = field(default_factory=list)


# ─── Behavioral Elements ──────────────────────────────────────────────────

@dataclass
class BehavioralOption(PBNode):
    """Behavioral option (library or alias)."""
    
    option_type: str = ""
    value: str = ""


@dataclass
class Parameter(PBNode):
    """Behavioral element parameter."""
    
    name: str = ""
    type: str = ""
    direction: str = field(default="in")  # in, out, ref
    default_value: str | None = field(default=None)


@dataclass
class BehavioralElement(PBNode):
    """Base class for behavioral elements."""
    
    name: str = ""
    access_modifier: str = field(default="public")
    is_shared: bool = field(default=False)
    options: list[BehavioralOption] = field(default_factory=list)


@dataclass
class LibraryBehavior(BehavioralElement):
    """Library-based behavioral element."""
    
    library_name: str = ""
    entry_point: str = ""
    parameters: list[Parameter] = field(default_factory=list)


@dataclass
class AliasBehavior(BehavioralElement):
    """Alias-based behavioral element."""
    
    alias_name: str = ""
    target_name: str = ""
    parameters: list[Parameter] = field(default_factory=list)


# ─── Library Management Implementation ─────────────────────────────────

@dataclass
class LibraryDependency:
    """Represents a dependency between libraries."""
    
    source_library: str = ""
    target_library: str = ""
    dependency_type: str = ""  # 'import', 'export', 'reference'
    objects: list[str] = field(default_factory=list)


class LibraryManager:
    """Manages PowerBuilder libraries and their dependencies."""
    
    def __init__(self) -> None:
        """Initialize the library manager."""
        self.libraries: dict[str, Library] = {}
        self.dependencies: list[LibraryDependency] = []
        # object_name -> library_name
        self.object_registry: dict[str, str] = {}
        self.system_libraries = self._load_system_libraries()
    
    def _load_system_libraries(self) -> dict[str, set[str]]:
        """Load system library definitions."""
        # This would load from configuration or defaults
        return {
            "pbsystem": {"SystemFunctions", "Transaction", "DataStore"},
            "pbdatawindow": {"DataWindow", "DataWindowChild"},
            # Add more system libraries as needed
        }
    
    def add_library(self, library: Library) -> None:
        """Add a library to the manager.
        
        Args:
            library: Library object to add
        """
        self.libraries[library.name] = library
        
        # Register all exported objects
        for export in library.exports:
            self.object_registry[export.object_name] = library.name
        
        # Track dependencies from imports
        for import_def in library.imports:
            dep = LibraryDependency(
                source_library=library.name,
                target_library=import_def.from_library,
                dependency_type='import',
                objects=[import_def.object_name]
            )
            self.dependencies.append(dep)
    
    def resolve_object_library(self, object_name: str) -> str | None:
        """Resolve which library contains a given object.
        
        Args:
            object_name: Name of the object to find
            
        Returns:
            Library name containing the object, or None if not found
        """
        # Check object registry first
        if object_name in self.object_registry:
            return self.object_registry[object_name]
        
        # Check system libraries
        for lib_name, objects in self.system_libraries.items():
            if object_name in objects:
                return lib_name
        
        return None
    
    def get_library_dependencies(
        self, 
        library_name: str, 
        recursive: bool = True
    ) -> set[str]:
        """Get all libraries that a given library depends on.
        
        Args:
            library_name: Name of the library
            recursive: Whether to include transitive dependencies
            
        Returns:
            Set of library names this library depends on
        """
        dependencies = set()
        
        # Direct dependencies
        for dep in self.dependencies:
            if dep.source_library == library_name:
                dependencies.add(dep.target_library)
        
        if recursive and dependencies:
            # Get transitive dependencies
            to_process = list(dependencies)
            processed = {library_name}
            
            while to_process:
                current = to_process.pop(0)
                if current in processed:
                    continue
                
                processed.add(current)
                
                for dep in self.dependencies:
                    if dep.source_library == current and dep.target_library not in processed:
                        dependencies.add(dep.target_library)
                        to_process.append(dep.target_library)
        
        return dependencies
    
    def get_library_dependents(self, library_name: str) -> set[str]:
        """Get all libraries that depend on a given library.
        
        Args:
            library_name: Name of the library
            
        Returns:
            Set of library names that depend on this library
        """
        dependents = set()
        
        for dep in self.dependencies:
            if dep.target_library == library_name:
                dependents.add(dep.source_library)
        
        return dependents
    
    def find_circular_dependencies(self) -> list[list[str]]:
        """Find circular dependencies between libraries.
        
        Returns:
            List of circular dependency chains
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(lib: str, path: list[str]) -> None:
            if lib in rec_stack:
                # Found cycle
                cycle_start = path.index(lib)
                cycle = path[cycle_start:] + [lib]
                cycles.append(cycle)
                return
            
            if lib in visited:
                return
            
            visited.add(lib)
            rec_stack.add(lib)
            path.append(lib)
            
            # Visit dependencies
            for dep in self.get_library_dependencies(lib, recursive=False):
                dfs(dep, path.copy())
            
            path.pop()
            rec_stack.remove(lib)
        
        for lib_name in self.libraries:
            if lib_name not in visited:
                dfs(lib_name, [])
        
        return cycles
    
    def validate_dependencies(self) -> tuple[bool, list[str]]:
        """Validate all library dependencies.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check for missing libraries
        for dep in self.dependencies:
            if dep.target_library not in self.libraries and dep.target_library not in self.system_libraries:
                errors.append(
                    f"Library '{dep.source_library}' depends on missing library '{dep.target_library}'"
                )
        
        # Check for circular dependencies
        cycles = self.find_circular_dependencies()
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            errors.append(f"Circular dependency: {cycle_str}")
        
        # Check for unresolved objects
        for lib_name, library in self.libraries.items():
            for import_def in library.imports:
                resolved_lib = self.resolve_object_library(import_def.object_name)
                if not resolved_lib:
                    errors.append(
                        f"Library '{lib_name}' imports unresolved object '{import_def.object_name}'"
                    )
                elif resolved_lib != import_def.from_library:
                    errors.append(
                        f"Library '{lib_name}' expects '{import_def.object_name}' from '{import_def.from_library}' "
                        f"but it's actually in '{resolved_lib}'"
                    )
        
        return len(errors) == 0, errors
    
    def get_load_order(self) -> list[str]:
        """Get the correct order to load libraries based on dependencies.
        
        Returns:
            List of library names in load order
            
        Raises:
            ValueError: If circular dependencies exist
        """
        # Check for cycles first
        cycles = self.find_circular_dependencies()
        if cycles:
            raise ValueError(f"Cannot determine load order due to circular dependencies: {cycles}")
        
        # Topological sort
        in_degree = {lib: 0 for lib in self.libraries}
        
        # Calculate in-degrees
        for dep in self.dependencies:
            if dep.target_library in in_degree:
                in_degree[dep.target_library] += 1
        
        # Start with libraries that have no dependencies
        queue = [lib for lib, degree in in_degree.items() if degree == 0]
        load_order = []
        
        while queue:
            current = queue.pop(0)
            load_order.append(current)
            
            # Reduce in-degree for dependents
            for dep in self.dependencies:
                if dep.source_library == current and dep.target_library in in_degree:
                    in_degree[dep.target_library] -= 1
                    if in_degree[dep.target_library] == 0:
                        queue.append(dep.target_library)
        
        # System libraries come first
        system_libs = list(self.system_libraries.keys())
        return system_libs + load_order