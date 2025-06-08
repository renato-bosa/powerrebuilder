"""Tests for LibraryManager."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from parse import LibraryManager, Library, get_default_library_manager
from parse.exceptions import ParseError


class TestLibrary:
    """Test Library class."""
    
    def test_library_creation(self):
        """Test creating a Library instance."""
        lib = Library(
            name="mylib",
            path=Path("/path/to/mylib.pbl")
        )
        
        assert lib.name == "mylib"
        assert lib.path == Path("/path/to/mylib.pbl")
        assert lib.exports == {}
        assert lib.imports == set()
        assert lib.metadata == {}
    
    def test_add_export(self):
        """Test adding exports to library."""
        lib = Library("mylib", Path("mylib.pbl"))
        
        lib.add_export("MyClass", {"type": "class", "public": True})
        lib.add_export("myFunction", {"type": "function", "returns": "integer"})
        
        assert len(lib.exports) == 2
        assert lib.get_export("MyClass") == {"type": "class", "public": True}
        assert lib.get_export("myFunction") == {"type": "function", "returns": "integer"}
        assert lib.get_export("nonexistent") is None
    
    def test_add_import(self):
        """Test adding import dependencies."""
        lib = Library("mylib", Path("mylib.pbl"))
        
        lib.add_import("baselib")
        lib.add_import("utillib")
        lib.add_import("baselib")  # Duplicate
        
        assert lib.imports == {"baselib", "utillib"}


class TestLibraryManager:
    """Test LibraryManager class."""
    
    def test_init_default_path(self):
        """Test initialization with default path."""
        manager = LibraryManager()
        assert len(manager.library_paths) == 1
        assert manager.library_paths[0] == Path.cwd()
    
    def test_init_custom_paths(self):
        """Test initialization with custom paths."""
        paths = [Path("/lib1"), Path("/lib2")]
        manager = LibraryManager(paths)
        
        assert len(manager.library_paths) == 2
        assert manager.library_paths[0] == Path("/lib1")
        assert manager.library_paths[1] == Path("/lib2")
    
    def test_add_library_path(self):
        """Test adding library search paths."""
        manager = LibraryManager([])
        
        manager.add_library_path(Path("/new/path"))
        assert Path("/new/path") in manager.library_paths
        
        # Should not add duplicates
        manager.add_library_path(Path("/new/path"))
        assert manager.library_paths.count(Path("/new/path")) == 1
    
    def test_find_library_file(self, tmp_path):
        """Test finding library files."""
        # Create test library files
        lib_dir = tmp_path / "libs"
        lib_dir.mkdir()
        
        (lib_dir / "mylib.pbl").touch()
        (lib_dir / "other.pbd").touch()
        (lib_dir / "util.dll").touch()
        
        manager = LibraryManager([lib_dir])
        
        # Test exact match
        assert manager._find_library_file("mylib") == lib_dir / "mylib.pbl"
        assert manager._find_library_file("other") == lib_dir / "other.pbd"
        assert manager._find_library_file("util") == lib_dir / "util.dll"
        
        # Test not found
        assert manager._find_library_file("nonexistent") is None
    
    def test_find_library_file_case_insensitive(self, tmp_path):
        """Test case-insensitive library file search."""
        lib_dir = tmp_path / "libs"
        lib_dir.mkdir()
        
        (lib_dir / "MyLib.pbl").touch()
        
        manager = LibraryManager([lib_dir])
        
        # Should find despite case difference
        found = manager._find_library_file("mylib")
        assert found is not None
        assert found.name.lower() == "mylib.pbl"
    
    def test_resolve_import_cached(self, tmp_path):
        """Test resolving cached import."""
        manager = LibraryManager()
        
        # Pre-populate cache
        lib = Library("testlib", Path("testlib.pbl"))
        manager._cache["testlib"] = lib
        
        # Should return cached library
        result = manager.resolve_import("testlib")
        assert result is lib
    
    def test_resolve_import_not_found(self):
        """Test resolving non-existent import."""
        manager = LibraryManager([])
        
        result = manager.resolve_import("nonexistent")
        assert result is None
    
    @patch.object(LibraryManager, '_load_library')
    @patch.object(LibraryManager, '_find_library_file')
    def test_resolve_import_loads_library(self, mock_find, mock_load):
        """Test resolving import loads library."""
        manager = LibraryManager()
        
        # Mock finding library file
        mock_find.return_value = Path("/path/to/lib.pbl")
        
        # Mock loading library
        lib = Library("lib", Path("/path/to/lib.pbl"))
        mock_load.return_value = lib
        
        result = manager.resolve_import("lib")
        
        assert result is lib
        mock_find.assert_called_once_with("lib")
        mock_load.assert_called_once_with(Path("/path/to/lib.pbl"))
    
    def test_load_library_pbl(self, tmp_path):
        """Test loading PowerBuilder library."""
        lib_file = tmp_path / "test.pbl"
        lib_file.touch()
        
        manager = LibraryManager()
        
        with patch.object(manager, '_extract_pb_exports') as mock_extract:
            lib = manager._load_library(lib_file)
            
            assert lib.name == "test"
            assert lib.path == lib_file
            assert lib.metadata["file_type"] == ".pbl"
            assert "test" in manager._cache
            assert "test" in manager._import_graph
            mock_extract.assert_called_once()
    
    def test_load_library_source(self, tmp_path):
        """Test loading source file library."""
        lib_file = tmp_path / "test.sru"
        lib_file.write_text("global function integer test_func()\nreturn 42\nend function")
        
        manager = LibraryManager()
        lib = manager._load_library(lib_file)
        
        assert lib.name == "test"
        assert lib.path == lib_file
        assert lib.metadata["file_type"] == ".sru"
    
    def test_get_exported_symbols(self):
        """Test getting exported symbols."""
        manager = LibraryManager()
        
        # Create and cache a library
        lib = Library("testlib", Path("testlib.pbl"))
        lib.add_export("func1", {"type": "function"})
        lib.add_export("class1", {"type": "class"})
        manager._cache["testlib"] = lib
        
        symbols = manager.get_exported_symbols("testlib")
        
        assert len(symbols) == 2
        assert "func1" in symbols
        assert "class1" in symbols
        
        # Test non-existent library
        assert manager.get_exported_symbols("nonexistent") == {}
    
    def test_get_symbol(self):
        """Test searching for symbols across libraries."""
        manager = LibraryManager()
        
        # Create test libraries
        lib1 = Library("lib1", Path("lib1.pbl"))
        lib1.add_export("shared_func", {"lib": "lib1"})
        lib1.add_export("func1", {"unique": "lib1"})
        
        lib2 = Library("lib2", Path("lib2.pbl"))
        lib2.add_export("func2", {"unique": "lib2"})
        
        manager._cache["lib1"] = lib1
        manager._cache["lib2"] = lib2
        
        # Search all libraries
        assert manager.get_symbol("func1") == {"unique": "lib1"}
        assert manager.get_symbol("func2") == {"unique": "lib2"}
        assert manager.get_symbol("nonexistent") is None
        
        # Search specific libraries
        assert manager.get_symbol("shared_func", ["lib1"]) == {"lib": "lib1"}
        assert manager.get_symbol("func1", ["lib2"]) is None
    
    def test_circular_dependencies(self):
        """Test circular dependency detection."""
        manager = LibraryManager()
        
        # Create circular dependency: A -> B -> C -> A
        manager._import_graph = {
            "A": {"B"},
            "B": {"C"},
            "C": {"A"},
            "D": {"E"},
            "E": set(),
        }
        
        cycles = manager.check_circular_dependencies()
        
        assert len(cycles) == 1
        cycle = cycles[0]
        # Cycle should contain A, B, C in some order
        assert set(cycle) == {"A", "B", "C"}
    
    def test_no_circular_dependencies(self):
        """Test when no circular dependencies exist."""
        manager = LibraryManager()
        
        # Create acyclic graph
        manager._import_graph = {
            "A": {"B", "C"},
            "B": {"D"},
            "C": {"D"},
            "D": set(),
        }
        
        cycles = manager.check_circular_dependencies()
        assert cycles == []
    
    def test_dependency_order(self):
        """Test topological sort of dependencies."""
        manager = LibraryManager()
        
        # Create dependency graph: A depends on B,C; B depends on D; C depends on D
        manager._import_graph = {
            "A": {"B", "C"},
            "B": {"D"},
            "C": {"D"},
            "D": set(),
        }
        
        order = manager.get_dependency_order()
        
        # D should come before B and C
        # B and C should come before A
        assert order.index("D") < order.index("B")
        assert order.index("D") < order.index("C")
        assert order.index("B") < order.index("A")
        assert order.index("C") < order.index("A")
    
    def test_dependency_order_with_cycle(self):
        """Test that circular dependencies raise error."""
        manager = LibraryManager()
        
        # Create circular dependency
        manager._import_graph = {
            "A": {"B"},
            "B": {"A"},
        }
        
        with pytest.raises(ParseError, match="Circular dependencies"):
            manager.get_dependency_order()
    
    def test_clear_cache(self):
        """Test clearing library cache."""
        manager = LibraryManager()
        
        # Add some data
        manager._cache["lib1"] = Library("lib1", Path("lib1.pbl"))
        manager._import_graph["lib1"] = {"lib2"}
        
        manager.clear_cache()
        
        assert len(manager._cache) == 0
        assert len(manager._import_graph) == 0
    
    def test_get_library_info(self):
        """Test getting library information."""
        manager = LibraryManager()
        
        # Create test library
        lib = Library("testlib", Path("/path/to/testlib.pbl"))
        lib.add_export("func", {})
        lib.add_import("baselib")
        lib.metadata["version"] = "1.0"
        
        manager._cache["testlib"] = lib
        
        info = manager.get_library_info()
        
        assert "testlib" in info
        assert info["testlib"]["path"] == "/path/to/testlib.pbl"
        assert info["testlib"]["exports_count"] == 1
        assert info["testlib"]["imports"] == ["baselib"]
        assert info["testlib"]["metadata"]["version"] == "1.0"
    
    def test_get_default_library_manager_singleton(self):
        """Test that get_default_library_manager returns singleton."""
        manager1 = get_default_library_manager()
        manager2 = get_default_library_manager()
        
        assert manager1 is manager2