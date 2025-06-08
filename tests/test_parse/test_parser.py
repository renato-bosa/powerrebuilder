"""Tests for PowerBuilder parser functionality."""

from pathlib import Path

import pytest

from model.pb_datawindow import PBDataWindow as DataWindow
from model.ast import TryCatchStatement

from model.library import Library  # LibraryManager not implemented yet
from model.pb_transaction.transaction_stubs import TransactionBlock, TransactionStatement
from parse.parse_coordinator import parse_file

# Test data
DATAWINDOW_TEST = """
type dw_customer from datawindow
{
    table(name="customer" keys=("id") )
    column(name="id" type="long" key="yes")
    column(name="name" type="string" width="50")
    compute(name="full_name" expr="name + ' ' + lastname")
    text(name="title" x="10" y="10" text="Customer Details")
}
"""

TRANSACTION_TEST = """
using sqlca
{
    insert into customer values (:name, :address);
    commit using sqlca;
}
"""

EXCEPTION_TEST = """
try {
    delete from customer where id = :id;
} catch (SQLException e) {
    MessageBox("Error", "Failed to delete customer");
} finally {
    Disconnect;
}
"""

LIBRARY_TEST = """
library customer_lib system
{
    import base.window;
    export w_customer_list;

    type w_customer_list from window
    {
        // Window definition
    }
}
"""

def test_parse_datawindow():
    """Test parsing DataWindow syntax."""
    ast = parse_file(DATAWINDOW_TEST)
    assert isinstance(ast, DataWindow)
    assert ast.name == "dw_customer"
    assert len(ast.columns) == 2
    assert ast.columns[0].name == "id"
    assert ast.columns[0].type == "long"

def test_parse_transaction():
    """Test parsing transaction blocks."""
    ast = parse_file(TRANSACTION_TEST)
    assert isinstance(ast, TransactionBlock)
    assert ast.transaction.name == "sqlca"
    assert len(ast.statements) == 2
    assert isinstance(ast.statements[1], TransactionStatement)
    assert ast.statements[1].type == "COMMIT"

def test_parse_exception():
    """Test parsing exception handling."""
    ast = parse_file(EXCEPTION_TEST)
    assert isinstance(ast, TryCatchStatement)
    assert len(ast.catch_blocks) == 1
    catch = ast.catch_blocks[0]
    assert catch.exception_type.name == "SQLException"
    assert catch.variable_name == "e"
    assert ast.finally_block is not None

def test_parse_library():
    """Test parsing library definitions."""
    ast = parse_file(LIBRARY_TEST)
    assert isinstance(ast, Library)
    assert ast.name == "customer_lib"
    assert ast.is_system
    assert len(ast.imports) == 1
    assert ast.imports[0].from_library == "base"
    assert len(ast.exports) == 1
    assert ast.exports[0].object_name == "w_customer_list"

@pytest.mark.skip(reason="LibraryManager not implemented yet")
def test_library_manager():
    """Test library dependency management."""
    return  # LibraryManager not implemented
    manager = LibraryManager()

    # Add some test libraries
    lib1 = Library("lib1", Path("lib1.pbl"))
    lib1.add_import("lib2", "window1")
    manager.add_library(lib1)

    lib2 = Library("lib2", Path("lib2.pbl"))
    lib2.add_import("lib3", "basewin")
    manager.add_library(lib2)

    lib3 = Library("lib3", Path("lib3.pbl"), is_system=True)
    manager.add_library(lib3)

    # Test dependency resolution
    deps = manager.get_library_dependencies("lib1")
    assert deps == {"lib2", "lib3"}

    # Test validation
    lib1.add_import("nonexistent", "something")
    errors = manager.validate_dependencies()
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
