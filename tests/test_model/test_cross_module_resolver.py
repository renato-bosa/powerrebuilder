"""Tests for the cross-module reference resolver."""

from pathlib import Path

import pytest

from model.core.analysis import DependencyGraph
from model.cross_module_resolver import (
    CrossModuleReferenceResolver,
    analyze_cross_module_references,
)


class TestCrossModuleReferenceResolver:
    """Test cases for CrossModuleReferenceResolver."""

    def test_add_module(self):




        """Test adding modules to the resolver."""
        resolver = CrossModuleReferenceResolver()

        # Add a module
        module_path = Path("n_cst_service.pb")
        exports = {"uf_process", "uf_calculate", "n_cst_service"}
        imports = {"messagebox", "n_cst_logger"}

        resolver.add_module(module_path, "userobject", exports, imports)

        assert "n_cst_service" in resolver.context.modules
        module = resolver.context.modules["n_cst_service"]
        assert module.module_type == "userobject"
        assert module.exports == exports
        assert module.imports == imports

        # Check symbol table
        assert "uf_process" in resolver.context.symbol_table
        assert "n_cst_service" in resolver.context.symbol_table["uf_process"]

    def test_resolve_builtin_references(self):




        """Test resolution of builtin PowerBuilder symbols."""
        resolver = CrossModuleReferenceResolver()

        # Add a module that uses builtin functions
        resolver.add_module(
            Path("w_main.pb"),
            "window",
            {"w_main"},
            {"messagebox", "open", "string"},
        )

        resolver.resolve_references()

        # Check that builtin references are resolved
        assert len(resolver.context.references) == 3
        for ref in resolver.context.references:
            assert ref.is_resolved
            assert ref.target_module == "__builtin__"

    def test_resolve_cross_module_references(self):




        """Test resolution of references between modules."""
        resolver = CrossModuleReferenceResolver()

        # Add multiple modules
        resolver.add_module(
            Path("n_cst_logger.pb"),
            "userobject",
            {"n_cst_logger", "uf_log"},
            {"string"},
        )

        resolver.add_module(
            Path("n_cst_service.pb"),
            "userobject",
            {"n_cst_service", "uf_process"},
            {"n_cst_logger", "uf_log"},
        )

        resolver.resolve_references()

        # Check that cross-module references are resolved
        service_refs = [r for r in resolver.context.references 
                       if r.source_module == "n_cst_service"]

        logger_ref = next((r for r in service_refs if r.symbol_name == "n_cst_logger"), None)
        assert logger_ref is not None
        assert logger_ref.is_resolved
        assert logger_ref.target_module == "n_cst_logger"

        # Check dependencies
        assert "n_cst_logger" in resolver.context.modules["n_cst_service"].dependencies

    def test_unresolved_references(self):




        """Test handling of unresolved references."""
        resolver = CrossModuleReferenceResolver()

        # Add a module with unresolved reference
        resolver.add_module(
            Path("w_test.pb"),
            "window",
            {"w_test"},
            {"n_missing_object", "uf_unknown_function"},
        )

        resolver.resolve_references()

        assert len(resolver.context.unresolved_references) == 2
        for ref in resolver.context.unresolved_references:
            assert not ref.is_resolved
            assert ref.target_module is None

    def test_circular_dependencies(self):




        """Test detection of circular dependencies."""
        resolver = CrossModuleReferenceResolver()

        # Create circular dependency: A -> B -> C -> A
        resolver.add_module(
            Path("n_a.pb"),
            "userobject",
            {"n_a", "uf_a"},
            {"n_b"},
        )

        resolver.add_module(
            Path("n_b.pb"),
            "userobject",
            {"n_b", "uf_b"},
            {"n_c"},
        )

        resolver.add_module(
            Path("n_c.pb"),
            "userobject",
            {"n_c", "uf_c"},
            {"n_a"},
        )

        resolver.resolve_references()

        cycles = resolver.find_circular_dependencies()
        assert len(cycles) > 0

        # Should find the cycle A -> B -> C -> A
        cycle = cycles[0]
        assert len(cycle) == 4  # Including return to start
        assert set(cycle[:3]) == {"n_a", "n_b", "n_c"}

    def test_module_dependencies_queries(self):




        """Test querying module dependencies and dependents."""
        resolver = CrossModuleReferenceResolver()

        # Set up module dependencies
        resolver.add_module(Path("n_base.pb"), "userobject", {"n_base"}, set())
        resolver.add_module(Path("n_service.pb"), "userobject", {"n_service"}, {"n_base"})
        resolver.add_module(Path("w_main.pb"), "window", {"w_main"}, {"n_service", "n_base"})

        resolver.resolve_references()

        # Test get_module_dependencies
        main_deps = resolver.get_module_dependencies("w_main")
        assert "n_service" in main_deps
        assert "n_base" in main_deps

        # Test get_module_dependents
        base_deps = resolver.get_module_dependents("n_base")
        assert "n_service" in base_deps
        assert "w_main" in base_deps

    def test_reference_type_inference(self):




        """Test inference of reference types from naming conventions."""
        resolver = CrossModuleReferenceResolver()

        test_cases = [
            ("uf_calculate", "function"),
            ("of_process", "function"),
            ("ue_clicked", "event"),
            ("n_cst_service", "type"),
            ("u_datawindow", "type"),
            ("w_main", "window"),
            ("dw_report", "datawindow"),
            ("some_variable", "unknown"),
        ]

        for symbol, expected_type in test_cases:
            assert resolver._infer_reference_type(symbol) == expected_type

    def test_validation(self):




        """Test reference validation."""
        resolver = CrossModuleReferenceResolver()

        # Add valid modules
        resolver.add_module(
            Path("n_service.pb"),
            "userobject",
            {"n_service", "uf_process"},
            {"messagebox"},
        )

        # Add module with unresolved reference
        resolver.add_module(
            Path("w_test.pb"),
            "window",
            {"w_test"},
            {"n_missing"},
        )

        resolver.resolve_references()

        is_valid, errors = resolver.validate_references()
        assert not is_valid
        assert any("Unresolved reference" in error for error in errors)

    def test_dependency_graph_generation(self):




        """Test dependency graph generation."""
        resolver = CrossModuleReferenceResolver()

        # Create simple dependency structure
        resolver.add_module(Path("n_a.pb"), "userobject", {"n_a"}, {"n_b"})
        resolver.add_module(Path("n_b.pb"), "userobject", {"n_b"}, set())

        resolver.resolve_references()

        graph = resolver.generate_dependency_graph()

        assert isinstance(graph, DependencyGraph)
        assert "n_a" in graph.nodes
        assert "n_b" in graph.nodes
        assert ("n_a", "n_b") in graph.edges

    def test_analyze_cross_module_references_function(self):




        """Test the convenience analyze function."""
        modules = {
            "n_logger": ({"n_logger", "uf_log"}, {"string"}),
            "n_service": ({"n_service", "uf_process"}, {"n_logger"}),
        }

        module_types = {
            "n_logger": "userobject",
            "n_service": "userobject",
        }

        resolver = analyze_cross_module_references(modules, module_types)

        assert len(resolver.context.modules) == 2
        assert len(resolver.context.references) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
