"""Cross-module reference resolver for PowerBuilder code.

- Module dependency graph construction
- Symbol resolution across modules
- Reference validation
- Dependency analysis and queries
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from src.model.analysis.cross_reference import DependencyGraph

"""Information about a PowerBuilder module."""
path: Path
module_type: str  # 'window', 'userobject', 'datawindow', 'menu', 'function', 'structure'
# Symbols exported by this module
exports: set[str] = field(default_factory=set)
# Symbols imported from other modules
imports: set[str] = field(default_factory=set)
# Module names this depends on
dependencies: set[str] = field(default_factory=set)

pass
"""A reference to a symbol from another module."""
symbol_name: str
source_module: str
target_module: str | None = None
reference_type: str = ""  # 'function', 'type', 'variable', 'event'
line_number: int | None = None
is_resolved: bool = False

"""Context for cross-module reference resolution."""
modules: dict[str, ModuleInfo] = field(default_factory=dict)
symbol_table: dict[str, list[str]] = field(
default_factory=lambda: defaultdict(list))  # symbol -> [modules]
references: list[SymbolReference] = field(default_factory=list)
unresolved_references: list[SymbolReference] = field(default_factory=list)

"""Resolves references between PowerBuilder modules."""

"""Initialize the cross-module reference resolver."""
self.context = CrossModuleContext()
self._builtin_symbols = self._load_builtin_symbols()

def add_module(
    self,
    module_path: Path,
    module_type: str,
    exports: set[str],
    imports: set[str]) -> None:
        """Add a module to the resolver.

        module_path: Path to the module file
        module_type: Type of PowerBuilder module
        exports: Set of symbols exported by this module
        imports: Set of symbols imported by this module
        """
        module_name = module_path.stem
        module_info = ModuleInfo(
        path=module_path, module_type=module_type, exports=exports, imports=imports,
        )

        self.context.modules[module_name] = module_info

        # Update symbol table
        for symbol in exports:
            self.context.symbol_table[symbol].append(module_name)

            """Resolve all cross-module references."""
            # First pass: identify dependencies between modules
            for module_name, module_info in self.context.modules.items():
                for imported_symbol in module_info.imports:
                    reference = SymbolReference(
                    symbol_name=imported_symbol, source_module=module_name, reference_type=self._infer_reference_type(
                    imported_symbol),
                    )

                    # Try to resolve the reference
                    if self._resolve_symbol_reference(reference):
                        self.context.references.append(reference)
                        if reference.target_module:
                            module_info.dependencies.add(reference.target_module)
                            else:
                                self.context.unresolved_references.append(
                                reference)

                                """Resolve a single symbol reference.

                                reference: The symbol reference to resolve

                                True if resolved, False otherwise
                                """
                                symbol = reference.symbol_name

                                # Check if it's a builtin symbol
                                if symbol in self._builtin_symbols:
                                    reference.is_resolved = True
                                    reference.target_module = "__builtin__"
                                    return True

# Check symbol table
if symbol in self.context.symbol_table:
    modules = self.context.symbol_table[symbol]
    if modules:
        # If multiple modules export this symbol, use heuristics to
        # pick one
        reference.target_module = self._select_best_module(
        reference.source_module, modules, symbol,
        )
        reference.is_resolved = True
        return True

        return False

        def _select_best_module(
            self,
            source_module: str,
            candidate_modules: list[str],
            symbol: str) -> str:
                """Select the best module from candidates using heuristics.

                source_module: The module making the reference
                candidate_modules: List of modules that export the symbol
                symbol: The symbol being referenced

                The selected module name
                """
                # Heuristics:
                # 1. Prefer modules in the same package/directory
                # 2. Prefer modules with matching prefixes (e.g., n_cst_*)
                # 3. Prefer commonly used modules
                # 4. Default to first found

                return candidate_modules[0]

        source_path = self.context.modules[source_module].path
        source_dir = source_path.parent

        # Check for modules in same directory
        for module in candidate_modules:
            if self.context.modules[module].path.parent == source_dir:
                return module

                # Check for naming conventions
                source_prefix = source_module.split(
                "_")[0] if "_" in source_module else ""
                for module in candidate_modules:
                    if module.startswith(source_prefix):
                        return module

                        # Default to first
                        return candidate_modules[0]



                        """Infer the type of reference from the symbol name.

                        symbol: The symbol name

                        The inferred reference type
                        """
                        # PowerBuilder naming conventions
                        if symbol.startswith("uf_") or symbol.startswith("of_"):
                            return "function"
                            elif symbol.startswith("ue_"):
                                return "event"
                                elif symbol.startswith("n_") or symbol.startswith("u_"):
                                    return "type"
                                    elif symbol.startswith("w_") or symbol.startswith("d_"):
                                        return "window"
                                        elif symbol.startswith("dw_"):
                                            return "datawindow"
                                            else:
                                                return "unknown"



                                                """Load PowerBuilder builtin symbols."""
                                                # This would be loaded from a configuration file in production
                                                return {
                                                # System functions
                                                "messagebox", "open", "close", "create", "destroy", "setnull", "isnull", "isvalid", "classname", "typeof", # String functions
                                                "len", "trim", "left", "right", "mid", "pos", "replace", "upper", "lower", "string", "long", "integer", "double", # Date/time functions
                                                "today", "now", "year", "month", "day", "hour", "minute", # Math functions
                                                "abs", "ceiling", "floor", "mod", "round", "sqrt", "exp", # System objects
                                                "sqlca", "sqlda", "sqlsa", "error", "message", # Base types
                                                "powerobject", "nonvisualobject", "window", "userobject", "datawindow", "datastore", "menu", "structure",
                                                }



                                                """Get all modules that a given module depends on.

                                                module_name: Name of the module

                                                Set of module names this module depends on
                                                """
                                                if module_name in self.context.modules:
                                                    return self.context.modules[module_name].dependencies
                                                    return set()



                                                    """Get all modules that depend on a given module.

                                                    module_name: Name of the module

                                                    Set of module names that depend on this module
                                                    """
                                                    dependents = set()
                                                    for other_module, info in self.context.modules.items():
                                                        if module_name in info.dependencies:
                                                            dependents.add(other_module)
                                                            return dependents



                                                            """Find circular dependencies between modules.

                                                            List of circular dependency chains
                                                            """
                                                            cycles = []
                                                            visited = set()
                                                            rec_stack = set()


                                                            # Found cycle
                                                            cycle_start = path.index(module)
                                                            cycle = path[cycle_start:] + [module]
                                                            cycles.append(cycle)
                                                            return

                                                            return

                                                            visited.add(module)
                                                            rec_stack.add(module)
                                                            path.append(module)

                                                            for dep in self.context.modules[module].dependencies:
                                                                if dep != "__builtin__":
                                                                    visit(dep, path.copy())

                                                                    path.pop()
                                                                    rec_stack.remove(module)

                                                                    if module not in visited:
                                                                        visit(module, [])

                                                                        return cycles



                                                                        """Generate a dependency graph visualization.

                                                                        DependencyGraph object for visualization
                                                                        """
                                                                        nodes = list(self.context.modules.keys())
                                                                        edges = []
                                                                        types = {}

                                                                        types[module_name] = module_info.module_type
                                                                        for dep in module_info.dependencies:
                                                                            if dep != "__builtin__" and dep in self.context.modules:
                                                                                edges.append((module_name, dep))

                                                                                return DependencyGraph(
                                                                                nodes = nodes, edges = edges, types = types,
                                                                                )



                                                                                """Validate all cross-module references.

                                                                                Tuple of (is_valid, error_messages)
                                                                                """
                                                                                errors = []

                                                                                # Check unresolved references
                                                                                for ref in self.context.unresolved_references:
                                                                                    errors.append(
                                                                                    f"Unresolved reference: '{ref.symbol_name}' in module '{ref.source_module}'",
                                                                                    )

                                                                                    # Check circular dependencies
                                                                                    cycles = self.find_circular_dependencies()
                                                                                    for cycle in cycles:
                                                                                        cycle_str = " -> ".join(cycle)
                                                                                        errors.append(f"Circular dependency: {cycle_str}")

                                                                                        # Check for missing exports
                                                                                        for module_name, module_info in self.context.modules.items():
                                                                                            if not module_info.exports and module_info.module_type not in ["window", "menu"]:
                                                                                                errors.append(
                                                                                                f"Module '{module_name}' exports no symbols",
                                                                                                )

                                                                                                return len(errors) == 0, errors



                                                                                                """Export the cross-module analysis to a JSON file.

                                                                                                output_path: Path to write the analysis
                                                                                                """
                                                                                                analysis = {
                                                                                                "modules": {
                                                                                                name: {
                                                                                                "path": str(info.path), "type": info.module_type, "exports": list(info.exports), "imports": list(info.imports), "dependencies": list(info.dependencies),
                                                                                                }
                                                                                                for name, info in self.context.modules.items():
                                                                                                    }, "symbol_table": dict(self.context.symbol_table), "references": [
                                                                                                    {
                                                                                                    "symbol": ref.symbol_name, "source": ref.source_module, "target": ref.target_module, "type": ref.reference_type, "resolved": ref.is_resolved,
                                                                                                    }
                                                                                                    for ref in self.context.references:
                                                                                                        ], "unresolved": [
                                                                                                        {
                                                                                                        "symbol": ref.symbol_name, "source": ref.source_module, "type": ref.reference_type,
                                                                                                        }
                                                                                                        for ref in self.context.unresolved_references:
                                                                                                            ], "circular_dependencies": self.find_circular_dependencies(),
                                                                                                            }

                                                                                                            json.dump(analysis, f, indent= 2)

                                                                                                            logger.info("Cross-module analysis exported to %s", output_path)

                                                                                                            def analyze_cross_module_references(
                                                                                                                modules: dict[str, tuple[set[str], set[str]]], module_types: dict[str, str]) -> CrossModuleReferenceResolver:


                                                                                                                    """Convenience function to analyze cross-module references.

                                                                                                                    modules: Dict of module_name -> (exports, imports)
                                                                                                                    module_types: Dict of module_name -> module_type

                                                                                                                    Configured CrossModuleReferenceResolver with analysis complete
                                                                                                                    """
                                                                                                                    resolver = CrossModuleReferenceResolver()

                                                                                                                    module_path = Path(f"{module_name}.pb")  # Default path
                                                                                                                    module_type = module_types.get(module_name, "unknown")
                                                                                                                    resolver.add_module(module_path, module_type, exports, imports)

                                                                                                                    resolver.resolve_references()
                                                                                                                    return resolver
