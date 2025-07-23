"""Library and behavioral classes for PowerBuilder.

This module contains classes for handling PowerBuilder libraries and behavioral elements.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from src.model.types.base import PBNode

"""PowerBuilder library object."""

path: str
is_system: bool = False
exports: list[Export] = field(default_factory=list)
imports: list[Import] = field(default_factory=list)

pass
"""Library export definition."""

to_library: str | None = None

"""Library import definition."""

object_name: str

"""Library object definition."""

object_type: str = ""  # window, menu, userobject, datawindow, etc.
source_file: str | None = field(default=None)

# ─── PowerBuilder Library ──────────────────────────────────────────────────

"""PowerBuilder library containing various objects."""

file_path: str = ""
windows: list = field(default_factory=list)
user_objects: list = field(default_factory=list)
datawindows: list = field(default_factory=list)
menus: list = field(default_factory=list)
global_functions: list = field(default_factory=list)
structures: list = field(default_factory=list)
global_variables: list = field(default_factory=list)

# ─── Behavioral Elements ──────────────────────────────────────────────────

"""Behavioral option (library or alias)."""

value: str

"""Base class for behavioral elements."""

access_modifier: str = field(default="public")
is_shared: bool = field(default=False)
options: list[BehavioralOption] = field(default_factory=list)

"""Library-based behavioral element."""

library_name: str
entry_point: str
access_modifier: str = field(default="public")
is_shared: bool = field(default=False)
options: list[BehavioralOption] = field(default_factory=list)
parameters: list[Parameter] = field(default_factory=list)

"""Alias-based behavioral element."""

alias_name: str
target_name: str
access_modifier: str = field(default="public")
is_shared: bool = field(default=False)
options: list[BehavioralOption] = field(default_factory=list)
parameters: list[Parameter] = field(default_factory=list)

# ─── Parameter Handling ──────────────────────────────────────────────────

"""Behavioral element parameter."""

type: str
direction: str = field(default="in")  # in, out, ref
default_value: str | None = field(default=None)

# ─── Library Management Implementation ─────────────────────────────────

"""Represents a dependency between libraries."""

target_library: str
dependency_type: str  # 'import', 'export', 'reference'
objects: list[str] = field(default_factory=list)

"""Manages PowerBuilder libraries and their dependencies."""

"""Initialize the library manager."""
self.libraries: dict[str, Library] = {}
self.dependencies: list[LibraryDependency] = []
# object_name -> library_name
self.object_registry: dict[str, str] = {}
self.system_libraries = self._load_system_libraries()

"""Add a library to the manager.

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

        """Resolve which library contains a given object.

        object_name: Name of the object to find

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
                        recursive: bool = True) -> set[str]:
                            """Get all libraries that a given library depends on.

                            library_name: Name of the library
                            recursive: Whether to include transitive dependencies

                            Set of library names this library depends on
                            """
                            dependencies = set()

                            # Direct dependencies
                            for dep in self.dependencies:
                                if dep.source_library == library_name:
                                    dependencies.add(dep.target_library)

                                    # Get transitive dependencies
                                    to_process = list(dependencies)
                                    processed = {library_name}

                                    current = to_process.pop(0)
                                    if current in processed:
                                        continue

                    processed.add(current)

                    if dep.source_library == current and dep.target_library not in processed:
                        dependencies.add(dep.target_library)
                        to_process.append(dep.target_library)

                        return dependencies

                        """Get all libraries that depend on a given library.

                        library_name: Name of the library

                        Set of library names that depend on this library
                        """
                        dependents = set()

                        if dep.target_library == library_name:
                            dependents.add(dep.source_library)

                            return dependents

                            """Find circular dependencies between libraries.

                            List of circular dependency chains
                            """
                            cycles = []
                            visited = set()
                            rec_stack = set()

                            if lib in rec_stack:
                                # Found cycle
                                cycle_start = path.index(lib)
                                cycle = path[cycle_start:] + [lib]
                                cycles.append(cycle)
                                return

                                return

                                visited.add(lib)
                                rec_stack.add(lib)
                                path.append(lib)

                                # Visit dependencies
                                for dep in self.get_library_dependencies(lib, recursive=False):
                                    dfs(dep, path.copy())

                                    path.pop()
                                    rec_stack.remove(lib)

                                    if lib_name not in visited:
                                        dfs(lib_name, [])

                                        return cycles

                                        """Validate all library dependencies.

                                        Tuple of (is_valid, error_messages)
                                        """
                                        errors = []

                                        # Check for missing libraries
                                        for dep in self.dependencies:
                                            if dep.target_library not in self.libraries and dep.target_library not in self.system_libraries:
                                                errors.append(
                                                f"Library '{
                                                dep.source_library}' depends on missing library '{
                                                dep.target_library}'")

                                                # Check for circular dependencies
                                                cycles = self.find_circular_dependencies()
                                                for cycle in cycles:
                                                    cycle_str = " -> ".join(cycle)
                                                    errors.append(f"Circular dependency: {cycle_str}")

                                                    # Check for unresolved objects
                                                    for lib_name, library in self.libraries.items():
                                                        for import_def in library.imports:
                                                            resolved_lib = self.resolve_object_library(
                                                            import_def.object_name)
                                                            if not resolved_lib:
                                                                errors.append(
                                                                f"Library '{lib_name}' imports unresolved object '{
                                                                import_def.object_name}'")
                                                                elif resolved_lib != import_def.from_library:
                                                                    errors.append(
                                                                    f"Library '{lib_name}' expects '{
                                                                    import_def.object_name}' from '{
                                                                    import_def.from_library}' " f"but it's actually in '{resolved_lib}'")

                                                                    return len(errors) == 0, errors

                                                                    """Get the correct order to load libraries based on dependencies.

                                                                    List of library names in load order

                                                                    ValueError: If circular dependencies exist
                                                                    """
                                                                    # Check for cycles first
                                                                    cycles = self.find_circular_dependencies()
                                                                    if cycles:
                                                                        raise ValueError(
                                                                        f"Cannot determine load order due to circular dependencies: {cycles}")

                                                                        # Topological sort
                                                                        in_degree = {lib: 0 for lib in self.libraries}

                                                                        # Calculate in-degrees
                                                                        for dep in self.dependencies:
                                                                            if dep.target_library in in_degree:
                                                                                in_degree[dep.target_library] += 1

                                                                                # Find libraries with no dependencies
                                                                                queue = [lib for lib,
                                                                                degree in in_degree.items() if degree == 0]
                                                                                load_order = []

                                                                                current = queue.pop(0)
                                                                                load_order.append(current)

                                                                                # Reduce in-degree for dependents
                                                                                for dep in self.dependencies:
                                                                                    if dep.source_library == current and dep.target_library in in_degree:
                                                                                        in_degree[dep.target_library] -= 1
                                                                                        if in_degree[dep.target_library] == 0:
                                                                                            queue.append(dep.target_library)

                                                                                            # Add system libraries first
                                                                                            system_libs = list(
                                                                                            self.system_libraries.keys())
                                                                                            return system_libs + load_order

                                                                                            """Load PowerBuilder system library definitions.

                                                                                            Dictionary of system library names to their exported objects
                                                                                            """
                                                                                            return {
                                                                                            "pbsysfunc": {
                                                                                            "abs", "acos", "asc", "asin", "atan", "ceiling", "char", "cos", "date",
                                                                                            "datetime", "day", "daysafter", "dec", "double", "exp", "fact", "fileclose",
                                                                                            "filecopy", "filedelete", "fileexists", "filelength", "filemove", "fileopen",
                                                                                            "fileread", "filereadex", "fileseek", "filewrite", "filewriteex", "fill",
                                                                                            "fillw", "getapplication", "getcomputername", "getcurrentdirectory",
                                                                                            "getenvironment", "hour", "int", "integer", "isdate", "isempty", "isnull",
                                                                                            "isnumber", "istime", "isvalid", "lastpos", "left", "leftw", "len", "lenw",
                                                                                            "log", "logten", "long", "lower", "lowerw", "match", "max", "messagebox",
                                                                                            "mid", "midw", "min", "minute", "mod", "month", "now", "pi", "pos", "posw",
                                                                                            "profileint", "profilestring", "rand", "randomize", "real", "registrydelete",
                                                                                            "registryget", "registrykeys", "registryset", "registryvalues", "relativedate",
                                                                                            "relativetime", "replace", "replacew", "reverse", "reversew", "rgb", "right",
                                                                                            "rightw", "round", "second", "secondsafter", "setfileattributes", "setnull",
                                                                                            "setprofilestring", "sign", "sin", "sleep", "space", "spacew", "sqrt", "string",
                                                                                            "stringw", "tan", "time", "today", "trim", "trimw", "truncate", "upper", "upperw",
                                                                                            "wordcap", "year"
                                                                                            },
                                                                                            "pbdwfunc": {
                                                                                            "accepttext", "classify", "clipboard", "copy", "create", "datacount", "dbcancel",
                                                                                            "deleterow", "describe", "destroy", "dwogetvalue", "filter", "find", "findgroupchange",
                                                                                            "findnext", "getbandatpointer", "getbordercolor", "getchanges", "getchildcount",
                                                                                            "getchildid", "getclick", "getcolumn", "getcolumnname", "getformat", "getitem",
                                                                                            "getitemnumber", "getitemstatus", "getitemstring", "getitemtime", "getmessagetext",
                                                                                            "getnextmodified", "getobjectatpointer", "getrow", "getselectedrow", "getsort",
                                                                                            "getsqlpreview", "getsqlselect", "gettext", "getvalidate", "getvalue", "groupcalc",
                                                                                            "importclipboard", "importfile", "importstring", "insertdocument", "insertrow",
                                                                                            "isselected", "modify", "movetoinserted", "print", "printcancel", "reset", "resetupdate",
                                                                                            "resettransobject", "retrieve", "rowcount", "rowsdiscard", "rowsmove", "saveas",
                                                                                            "scrollnextpage", "scrollnextrow", "scrollpriorpage", "scrollpriorrow", "scrolltorow",
                                                                                            "selectall", "selectedcount", "selectedlength", "selectedline", "selectedstart",
                                                                                            "selectedtext", "selectrow", "selecttext", "setactioncode", "setbordercolor",
                                                                                            "setchanges", "setcolumn", "setfilter", "setformat", "setitem", "setitemstatus",
                                                                                            "setpointer", "setposition", "setredraw", "setrow", "setrowfocusindicator", "setsort",
                                                                                            "setsqlpreview", "setsqlselect", "settaborder", "settext", "settransobject",
                                                                                            "setvalidate", "sharedata", "sharedataoff", "sort", "update"
                                                                                            },
                                                                                            "pbwinapi": {
                                                                                            "beep", "choosecolor", "choosefont", "closehandle", "connecttoserver",
                                                                                            "createfile", "createprocess", "deletefile", "disconnectserver", "dragacceptfiles",
                                                                                            "dragfinish", "dragqueryfile", "dragquerypoint", "exitwindows", "findwindow",
                                                                                            "ftpgetfile", "ftpputfile", "getcommandline", "getcomputername", "getcursor",
                                                                                            "getdc", "getdesktopwindow", "getdlgitem", "getfileversioninfo", "getfocus",
                                                                                            "getforegroundwindow", "getkeyboardstate", "getkeynametext", "getkeystate",
                                                                                            "getlasterror", "getmodulefilename", "getmodulehandle", "getprivateprofilestring",
                                                                                            "getprocessheap", "getsystemdirectory", "getsystemmetrics", "gettemppath",
                                                                                            "getusername", "getwindow", "getwindowsdirectory", "getwindowtext", "globalalloc",
                                                                                            "globalfree", "globallock", "globalmemorystatusex", "globalunlock", "heapalloc",
                                                                                            "heapfree", "internetopen", "internetopenurl", "internetreadfile", "loadimage",
                                                                                            "loadlibrary", "localalloc", "localfree", "mapviewoffile", "openfilename",
                                                                                            "postmessage", "readfile", "regclosekey", "regcreatekey", "regdeletekey",
                                                                                            "regdeletevalue", "regopenkey", "regqueryvalue", "regsetvalue", "releasedc",
                                                                                            "sendmessage", "setcapture", "setcursor", "setfocus", "setforegroundwindow",
                                                                                            "setkeyboardstate", "setwindowlong", "setwindowpos", "setwindowtext", "shellexecute",
                                                                                            "showwindow", "systemparametersinfo", "terminateprocess", "waitforsingleobject",
                                                                                            "winexec", "writefile", "writeprivateprofilestring"
                                                                                            }
                                                                                            }

                                                                                            # ─── Convenience Functions ────────────────────────────────

                                                                                            """Create and initialize a library manager.

                                                                                            Configured LibraryManager instance
                                                                                            """
                                                                                            return LibraryManager()

                                                                                            def analyze_library_dependencies(
                                                                                                libraries: list[Library]) -> tuple[bool, list[str], LibraryManager]:
                                                                                                    """Analyze dependencies between libraries.

                                                                                                    libraries: List of Library objects to analyze

                                                                                                    Tuple of (is_valid, errors, library_manager)
                                                                                                    """
                                                                                                    manager = LibraryManager()

                                                                                                    manager.add_library(library)

                                                                                                    is_valid, errors = manager.validate_dependencies()
                                                                                                    return is_valid, errors, manager
