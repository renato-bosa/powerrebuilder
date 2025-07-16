"""Test application-level functionality."""

import pytest
from pathlib import Path

from src.model.base.pb_entity import PBSourcedEntity
from src.model.constructs.pb_access import AccessType, PBAccess
from src.model.entities.application import PBApplication, PBLibrary


def test_library_basic():






    """Test basic library functionality."""
    lib = PBLibrary(
        name="test_lib",
        path=Path("/path/to/lib"),
    )
    assert lib.name == "test_lib"
    assert lib.path == Path("/path/to/lib")
    assert not lib.is_system
    assert len(lib.objects) == 0


def test_library_objects():






    """Test library object management."""
    lib = PBLibrary(name="test_lib", path=Path("/path/to/lib"))

    # Add objects
    obj1 = PBSourcedEntity(name="object1")
    obj2 = PBSourcedEntity(name="object2")

    lib.add_object(obj1)
    lib.add_object(obj2)

    # Test object retrieval
    assert lib.get_object(obj1.qualified_name) == obj1
    assert lib.get_object(obj2.qualified_name) == obj2
    assert lib.get_object("nonexistent") is None


def test_application_basic():






    """Test basic application functionality."""
    app = PBApplication(name="test_app")
    assert app.name == "test_app"
    assert len(app.libraries) == 0
    assert len(app.global_variables) == 0
    assert len(app.shared_variables) == 0


def test_application_libraries():






    """Test application library management."""
    app = PBApplication(name="test_app")

    # Add libraries
    lib1 = PBLibrary(name="lib1", path=Path("/path/to/lib1"))
    lib2 = PBLibrary(name="lib2", path=Path("/path/to/lib2"), is_system=True)

    app.add_library(lib1)
    app.add_library(lib2)

    # Test library retrieval
    assert app.get_library("lib1") == lib1
    assert app.get_library("lib2") == lib2
    assert app.get_library("nonexistent") is None

    # Test system/user library filtering
    assert len(app.get_system_libraries()) == 1
    assert len(app.get_user_libraries()) == 1
    assert app.get_system_libraries()[0] == lib2
    assert app.get_user_libraries()[0] == lib1


def test_application_variables():






    """Test application variable management."""
    app = PBApplication(name="test_app")

    # Add variables
    app.add_global_variable("g_count", 0)
    app.add_shared_variable("s_name", "test")

    # Test variable retrieval
    assert app.get_global_variable("g_count") == 0
    assert app.get_shared_variable("s_name") == "test"
    assert app.get_global_variable("nonexistent") is None
    assert app.get_shared_variable("nonexistent") is None


def test_application_object_lookup():






    """Test application object lookup."""
    app = PBApplication(name="test_app")

    # Create library with objects
    lib = PBLibrary(name="test_lib", path=Path("/path/to/lib"))
    obj1 = PBSourcedEntity(name="window1")
    obj2 = PBSourcedEntity(name="window2")

    lib.add_object(obj1)
    lib.add_object(obj2)
    app.add_library(lib)

    # Test object lookup
    assert app.get_object("test_lib.window1") == obj1
    assert app.get_object("test_lib.window2") == obj2
    assert app.get_object("test_lib.nonexistent") is None
    assert app.get_object("nonexistent.window1") is None

    # Test getting all objects
    all_objects = app.get_all_objects()
    assert len(all_objects) == 2
    assert obj1 in all_objects
    assert obj2 in all_objects


def test_application_type_registry():






    """Test application type registry integration."""
    app = PBApplication(name="test_app")

    # Register a type
    int_type = app.type_registry.get_type("integer")
    assert int_type is not None

    # Create array type
    int_array = app.type_registry.create_array_type(int_type, [10])
    assert int_array.element_type == int_type
    assert int_array.dimensions == [10]


def test_application_access_tracking():






    """Test application access tracking integration."""
    app = PBApplication(name="test_app")

    # Create a function
    func = PBSourcedEntity(name="test_function")

    # Track some accesses
    app.access_tracker.add_access(
        PBAccess(
            name="access1",
            variable_name="counter",
            access_type=AccessType.READ,
            container=func,
        ),
    )

    # Verify tracking
    assert len(app.access_tracker.get_variable_accesses("counter")) == 1
    assert len(app.access_tracker.get_container_accesses(func.qualified_name)) == 1
