"""Tests for enhanced symbol table management."""

import pytest

from model.utils.symbol_table import (
    SymbolTable,
    SymbolInfo,
    SymbolKind,
    SymbolVisibility,
    SymbolLocation,
    SymbolScope,
)
from model.utils.type_inference import TypeInfo


class TestSymbolTable:
    """Test the symbol table functionality."""
    
    def test_global_scope_initialization(self):

    
        
    
        """Test that global scope is properly initialized with built-ins."""
        table = SymbolTable()
        
        # Check built-in types
        integer_sym = table.lookup_symbol("integer")
        assert integer_sym is not None
        assert integer_sym.kind == SymbolKind.CLASS
        assert integer_sym.is_system
        
        # Check built-in constants
        null_sym = table.lookup_symbol("NULL")
        assert null_sym is not None
        assert null_sym.kind == SymbolKind.CONSTANT
        assert null_sym.type_info.type_name == "null"
        
        true_sym = table.lookup_symbol("TRUE")
        assert true_sym is not None
        assert true_sym.initial_value is True
    
    def test_variable_declaration(self):

    
        
    
        """Test variable declaration and lookup."""
        table = SymbolTable()
        
        # Declare a variable
        var_sym = table.declare_variable(
            "count",
            "integer",
            visibility=SymbolVisibility.LOCAL,
            initial_value=0
        )
        
        assert var_sym.name == "count"
        assert var_sym.kind == SymbolKind.VARIABLE
        assert var_sym.type_info.type_name == "integer"
        assert var_sym.initial_value == 0
        
        # Look it up
        found = table.lookup_symbol("count")
        assert found is var_sym
        
        # Look up with kind filter
        found = table.lookup_symbol("count", SymbolKind.VARIABLE)
        assert found is var_sym
        
        # Wrong kind filter
        found = table.lookup_symbol("count", SymbolKind.FUNCTION)
        assert found is None
    
    def test_function_declaration(self):

    
        
    
        """Test function declaration with parameters."""
        table = SymbolTable()
        
        # Declare a function
        func_sym = table.declare_function(
            "calculate",
            return_type="double",
            parameters=[("x", "double"), ("y", "double")],
            visibility=SymbolVisibility.PUBLIC
        )
        
        assert func_sym.name == "calculate"
        assert func_sym.kind == SymbolKind.FUNCTION
        assert func_sym.return_type.type_name == "double"
        assert len(func_sym.parameters) == 2
        
        # Check parameters
        assert func_sym.parameters[0].name == "x"
        assert func_sym.parameters[0].kind == SymbolKind.PARAMETER
        assert func_sym.parameters[0].type_info.type_name == "double"
    
    def test_class_declaration(self):

    
        
    
        """Test class/user object declaration."""
        table = SymbolTable()
        
        # Declare a class
        class_sym = table.declare_class(
            "n_cst_service",
            ancestor="nonvisualobject",
            visibility=SymbolVisibility.PUBLIC
        )
        
        assert class_sym.name == "n_cst_service"
        assert class_sym.kind == SymbolKind.CLASS
        assert class_sym.ancestor == "nonvisualobject"
        assert class_sym.type_info.type_name == "n_cst_service"
        
        # Declare a user object
        uo_sym = table.declare_class(
            "w_main",
            ancestor="window",
            is_user_object=True
        )
        
        assert uo_sym.kind == SymbolKind.USER_OBJECT
    
    def test_scope_management(self):

    
        
    
        """Test entering and exiting scopes."""
        table = SymbolTable()
        
        # Declare global variable
        table.declare_variable("global_var", "string", visibility=SymbolVisibility.GLOBAL)
        
        # Enter function scope
        func_scope = table.enter_scope("my_function", "function")
        assert table.current_scope == func_scope
        assert table.current_scope.name == "my_function"
        
        # Declare local variable
        table.declare_variable("local_var", "integer")
        
        # Can see both variables
        assert table.lookup_symbol("global_var") is not None
        assert table.lookup_symbol("local_var") is not None
        
        # Exit function scope
        old_scope = table.exit_scope()
        assert old_scope == func_scope
        assert table.current_scope == table.global_scope
        
        # Can only see global variable now
        assert table.lookup_symbol("global_var") is not None
        assert table.lookup_symbol("local_var") is None
    
    def test_visibility_rules(self):

    
        
    
        """Test PowerBuilder visibility rules."""
        table = SymbolTable()
        
        # Enter class scope
        class_scope = table.enter_scope("w_window", "class")
        
        # Declare different visibility members
        table.declare_variable("public_var", "string", visibility=SymbolVisibility.PUBLIC)
        table.declare_variable("private_var", "string", visibility=SymbolVisibility.PRIVATE)
        table.declare_variable("protected_var", "string", visibility=SymbolVisibility.PROTECTED)
        table.declare_variable("shared_var", "string", visibility=SymbolVisibility.SHARED)
        
        # Enter method scope within class
        method_scope = table.enter_scope("clicked", "function")
        
        # All should be visible within the class
        assert table.lookup_symbol("public_var") is not None
        assert table.lookup_symbol("private_var") is not None
        assert table.lookup_symbol("protected_var") is not None
        assert table.lookup_symbol("shared_var") is not None
        
        # Exit to class scope
        table.exit_scope()
        
        # Exit to global scope
        table.exit_scope()
        
        # Enter different class scope
        table.enter_scope("w_other", "class")
        
        # Only public should be visible from outside
        assert table.lookup_symbol("public_var") is None  # Not visible across classes
        assert table.lookup_symbol("private_var") is None
        assert table.lookup_symbol("protected_var") is None
        assert table.lookup_symbol("shared_var") is None
    
    def test_forward_declarations(self):

    
        
    
        """Test forward declaration handling."""
        table = SymbolTable()
        
        # Declare forward function
        forward_sym = table.declare_function(
            "future_func",
            return_type="integer",
            is_forward=True
        )
        
        assert forward_sym.is_forward_declaration
        assert len(table.forward_declarations) == 1
        
        # Declare actual function
        actual_sym = table.declare_function(
            "future_func",
            return_type="integer",
            parameters=[("x", "integer")],
            is_forward=False
        )
        
        # Should replace forward declaration
        found = table.lookup_symbol("future_func")
        assert found == actual_sym
        assert not found.is_forward_declaration
        assert len(found.parameters) == 1
    
    def test_symbol_search(self):

    
        
    
        """Test searching symbols by type."""
        table = SymbolTable()
        
        # Declare variables of different types
        table.declare_variable("str1", "string")
        table.declare_variable("str2", "string")
        table.declare_variable("int1", "integer")
        
        # Enter nested scope
        table.enter_scope("function1", "function")
        table.declare_variable("str3", "string")
        table.declare_variable("int2", "integer")
        table.exit_scope()
        
        # Find all string variables (filter by VARIABLE kind to exclude type definitions)
        string_vars = table.find_symbols_by_type("string", SymbolKind.VARIABLE)
        assert len(string_vars) == 3
        assert all(sym.type_info.type_name == "string" for sym in string_vars)
        assert all(sym.kind == SymbolKind.VARIABLE for sym in string_vars)
    
    def test_scope_path(self):

    
        
    
        """Test getting current scope path."""
        table = SymbolTable()
        
        assert table.get_scope_path() == ["global"]
        
        table.enter_scope("w_main", "class")
        assert table.get_scope_path() == ["global", "w_main"]
        
        table.enter_scope("clicked", "function")
        assert table.get_scope_path() == ["global", "w_main", "clicked"]
        
        table.enter_scope("if_block", "block")
        assert table.get_scope_path() == ["global", "w_main", "clicked", "if_block"]
        
        table.exit_scope()
        table.exit_scope()
        assert table.get_scope_path() == ["global", "w_main"]
    
    def test_array_variables(self):

    
        
    
        """Test array variable declarations."""
        table = SymbolTable()
        
        # Declare array variable
        arr_sym = table.declare_variable(
            "numbers",
            "integer",
            is_array=True,
            array_dimensions=2
        )
        
        assert arr_sym.type_info.is_array
        assert arr_sym.type_info.array_dimensions == 2
        assert arr_sym.type_info.type_name == "integer"
    
    def test_symbol_location(self):

    
        
    
        """Test symbol location tracking."""
        table = SymbolTable()
        
        location = SymbolLocation(
            file_path="w_main.srw",
            object_name="w_main",
            script_name="open",
            line=10,
            column=5
        )
        
        var_sym = table.declare_variable(
            "my_var",
            "string",
            location=location
        )
        
        assert var_sym.location is location
        assert var_sym.location.line == 10
        assert var_sym.location.object_name == "w_main"
    
    def test_symbol_attributes(self):

    
        
    
        """Test symbol attributes and decorators."""
        table = SymbolTable()
        
        # Declare variable with attributes
        var_sym = table.declare_variable(
            "config",
            "string",
            is_readonly=True,
            is_static=True
        )
        
        assert var_sym.is_readonly
        assert var_sym.is_static
        
        # Add custom attributes
        var_sym.attributes["deprecated"] = True
        var_sym.attributes["since_version"] = "1.0"
        var_sym.decorators.append("@deprecated")
        
        found = table.lookup_symbol("config")
        assert found.attributes["deprecated"] is True
        assert found.attributes["since_version"] == "1.0"
        assert "@deprecated" in found.decorators
    
    def test_get_all_symbols(self):

    
        
    
        """Test getting all visible symbols."""
        table = SymbolTable()
        
        # Add some symbols to global scope
        table.declare_variable("global_var", "string", visibility=SymbolVisibility.GLOBAL)
        table.declare_function("global_func", "integer", visibility=SymbolVisibility.GLOBAL)
        
        # Enter class scope
        table.enter_scope("my_class", "class")
        table.declare_variable("instance_var", "integer", visibility=SymbolVisibility.INSTANCE)
        table.declare_function("method", "void", visibility=SymbolVisibility.PUBLIC)
        
        # Get all symbols
        all_symbols = table.get_all_symbols()
        
        # Should include globals, built-ins, and local symbols
        assert "global_var" in all_symbols
        assert "global_func" in all_symbols
        assert "instance_var" in all_symbols
        assert "method" in all_symbols
        assert "integer" in all_symbols  # built-in type
        
        # Get only variables
        all_vars = table.get_all_symbols(SymbolKind.VARIABLE)
        assert "global_var" in all_vars
        assert "instance_var" in all_vars
        assert "global_func" not in all_vars
        assert "method" not in all_vars
    
    def test_type_context_integration(self):

    
        
    
        """Test integration with type inference context."""
        table = SymbolTable()
        
        # Declare variable
        table.declare_variable("count", "integer", initial_value=10)
        
        # Type context should be updated
        type_info = table.current_scope.type_context.get_variable_type("count")
        assert type_info is not None
        assert type_info.type_name == "integer"
        
        # Declare function
        table.declare_function("get_name", return_type="string")
        
        # Function return type should be in context
        func_type = table.current_scope.type_context.get_function_return_type("get_name")
        assert func_type is not None
        assert func_type.type_name == "string"
    
    def test_clear_symbol_table(self):

    
        
    
        """Test clearing the symbol table."""
        table = SymbolTable()
        
        # Add some symbols
        table.declare_variable("var1", "string")
        table.enter_scope("func1", "function")
        table.declare_variable("var2", "integer")
        
        # Clear
        table.clear()
        
        # Should be back to initial state
        assert table.current_scope == table.global_scope
        assert len(table._scope_stack) == 1
        assert len(table.forward_declarations) == 0
        
        # Built-ins should be restored
        assert table.lookup_symbol("integer") is not None
        assert table.lookup_symbol("NULL") is not None
        
        # User symbols should be gone
        assert table.lookup_symbol("var1") is None
        assert table.lookup_symbol("var2") is None
    
    def test_symbol_string_representation(self):

    
        
    
        """Test symbol string representation."""
        sym = SymbolInfo(
            name="my_var",
            kind=SymbolKind.VARIABLE,
            visibility=SymbolVisibility.PRIVATE,
            type_info=TypeInfo("string", is_nullable=True)
        )
        
        str_repr = str(sym)
        assert "private" in str_repr
        assert "variable" in str_repr
        assert "my_var" in str_repr
        assert "string?" in str_repr  # nullable


class TestSymbolScope:
    """Test the SymbolScope functionality."""
    
    def test_scope_hierarchy(self):

    
        
    
        """Test scope parent-child relationships."""
        global_scope = SymbolScope("global", "global")
        class_scope = global_scope.create_child_scope("MyClass", "class")
        method_scope = class_scope.create_child_scope("myMethod", "function")
        
        assert global_scope.parent is None
        assert class_scope.parent == global_scope
        assert method_scope.parent == class_scope
        
        assert len(global_scope.children) == 1
        assert global_scope.children[0] == class_scope
        assert len(class_scope.children) == 1
        assert class_scope.children[0] == method_scope
    
    def test_scope_imports(self):

    
        
    
        """Test tracking imports and using statements."""
        scope = SymbolScope("test", "class")
        
        scope.imports.add("System.Collections")
        scope.imports.add("System.IO")
        scope.using_namespaces.add("System")
        
        assert "System.Collections" in scope.imports
        assert "System.IO" in scope.imports
        assert "System" in scope.using_namespaces


if __name__ == "__main__":
    pytest.main([__file__, "-v"])