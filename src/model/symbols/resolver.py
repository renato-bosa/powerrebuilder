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

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a PowerBuilder module."""
    path: Path
    module_type: str  # 'window', 'userobject', 'datawindow', 'menu', 'function', 'structure'
    # Symbols exported by this module
    exports: set[str] = field(default_factory=set)
    # Symbols imported from other modules
    imports: set[str] = field(default_factory=set)
    # Module names this depends on
    dependencies: set[str] = field(default_factory=set)


@dataclass
class SymbolReference:
    """A reference to a symbol from another module."""
    symbol_name: str
    source_module: str
    target_module: str | None = None
    reference_type: str = ""  # 'function', 'type', 'variable', 'event'
    line_number: int | None = None
    is_resolved: bool = False


@dataclass
class CrossModuleContext:
    """Context for cross-module reference resolution."""
    modules: dict[str, ModuleInfo] = field(default_factory=dict)
    symbol_table: dict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list))  # symbol -> [modules]
    references: list[SymbolReference] = field(default_factory=list)
    unresolved_references: list[SymbolReference] = field(default_factory=list)


class CrossModuleReferenceResolver:
    """Resolves references between PowerBuilder modules."""

    def __init__(self):
        """Initialize the cross-module reference resolver."""
        self.context = CrossModuleContext()
        self._builtin_symbols = self._load_builtin_symbols()

    def add_module(
        self,
        module_path: Path,
        module_type: str,
        exports: set[str],
        imports: set[str]
    ) -> None:
        """Add a module to the resolver.

        module_path: Path to the module file
        module_type: Type of module
        exports: Set of symbols exported by this module
        imports: Set of symbols imported by this module
        """
        module_name = module_path.stem

        # Create module info
        module_info = ModuleInfo(
            path=module_path,
            module_type=module_type,
            exports=exports,
            imports=imports,
        )

        # Add to context
        self.context.modules[module_name] = module_info

        # Update symbol table
        for symbol in exports:
            self.context.symbol_table[symbol].append(module_name)

    def resolve_references(self) -> None:
        """Resolve all cross-module references."""
        # First pass: identify dependencies between modules
        for module_name, module_info in self.context.modules.items():
            for imported_symbol in module_info.imports:
                reference = SymbolReference(
                    symbol_name=imported_symbol,
                    source_module=module_name,
                    reference_type=self._infer_reference_type(imported_symbol),
                )

                # Try to resolve the reference
                if self._resolve_symbol_reference(reference):
                    self.context.references.append(reference)
                    if reference.target_module:
                        module_info.dependencies.add(reference.target_module)
                else:
                    self.context.unresolved_references.append(reference)

    def _resolve_symbol_reference(self, reference: SymbolReference) -> bool:
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
        symbol: str
    ) -> str:
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

        if not candidate_modules:
            return ""

        # If only one candidate, return it
        if len(candidate_modules) == 1:
            return candidate_modules[0]

        # Try to find module in same directory
        if source_module in self.context.modules:
            source_path = self.context.modules[source_module].path
            source_dir = source_path.parent

            # Check for modules in same directory
            for module in candidate_modules:
                if module in self.context.modules:
                    if self.context.modules[module].path.parent == source_dir:
                        return module

        # Default to first candidate
        return candidate_modules[0]

    def _infer_reference_type(self, symbol: str) -> str:
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
        else:
            return "unknown"

    def _load_builtin_symbols(self) -> set[str]:
        """Load PowerBuilder builtin symbols."""
        # This would be loaded from a configuration file in production
        return {
            # System functions
            "messagebox", "open", "close", "create", "destroy", 
            "setnull", "isnull", "isvalid", "classname", "typeof",
            # String functions
            "len", "trim", "left", "right", "mid", "pos", "replace", 
            "upper", "lower", "string", "long", "integer", "double",
            # Date/time functions
            "today", "now", "year", "month", "day", "hour", "minute",
            # Math functions
            "abs", "ceiling", "floor", "mod", "round", "sqrt", "exp",
            # System objects
            "sqlca", "sqlda", "sqlsa", "error", "message",
            # Base types
            "powerobject", "nonvisualobject", "window", "userobject", 
            "datawindow", "datastore", "menu", "structure",
        }

    def get_module_dependencies(self, module_name: str) -> set[str]:
        """Get all modules that a given module depends on.

        module_name: Name of the module

        Set of module names this module depends on
        """
        if module_name in self.context.modules:
            return self.context.modules[module_name].dependencies
        return set()

    def get_dependency_graph(self) -> DependencyGraph:
        """Build and return a dependency graph.

        DependencyGraph object
        """
        graph = DependencyGraph()

        # Add all modules as nodes
        for module_name, module_info in self.context.modules.items():
            graph.add_node(module_name, module_type=module_info.module_type)

        # Add edges based on dependencies
        for module_name, module_info in self.context.modules.items():
            for dependency in module_info.dependencies:
                graph.add_edge(module_name, dependency)

        return graph

    def get_unresolved_symbols(self) -> list[tuple[str, str]]:
        """Get list of unresolved symbols.

        List of (module, symbol) tuples
        """
        return [
            (ref.source_module, ref.symbol_name)
            for ref in self.context.unresolved_references
        ]

    def export_analysis(self, output_path: Path) -> None:
        """Export analysis results to JSON.

        output_path: Path to output file
        """
        analysis = {
            "modules": {},
            "symbol_table": dict(self.context.symbol_table),
            "resolved_references": [],
            "unresolved_references": [],
            "dependency_graph": {},
        }

        # Module information
        for module_name, module_info in self.context.modules.items():
            analysis["modules"][module_name] = {
                "path": str(module_info.path),
                "type": module_info.module_type,
                "exports": list(module_info.exports),
                "imports": list(module_info.imports),
                "dependencies": list(module_info.dependencies),
            }

        # References
        for ref in self.context.references:
            analysis["resolved_references"].append({
                "symbol": ref.symbol_name,
                "source": ref.source_module,
                "target": ref.target_module,
                "type": ref.reference_type,
            })

        for ref in self.context.unresolved_references:
            analysis["unresolved_references"].append({
                "symbol": ref.symbol_name,
                "source": ref.source_module,
                "type": ref.reference_type,
            })

        # Dependency graph
        graph = self.get_dependency_graph()
        for module in graph.nodes():
            analysis["dependency_graph"][module] = {
                "depends_on": list(graph.successors(module)),
                "depended_by": list(graph.predecessors(module)),
            }

        # Write to file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)