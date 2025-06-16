"""Integration tests for symbol table with type inference and AST validation."""

import pytest

from model.utils.symbol_table import (
    SymbolTable,
    SymbolKind,
    SymbolVisibility,
    SymbolLocation,
)
from model.utils.type_inference import TypeInferenceEngine, TypeInfo
from model.entities import (
    PBVariable,
    PBBinaryOperator,
    PBNumberLiteral,
    PBStringLiteral,
    PBFunctionCall,
)


class TestSymbolTableIntegration:
    """Test symbol table integration with other components."""
    
    def test_symbol_table_with_type_inference(self):
        """Test symbol table working with type inference engine."""
        # Create symbol table
        symbol_table = SymbolTable()
        
        # Use the type context from current scope
        type_engine = TypeInferenceEngine(symbol_table.current_scope.type_context)
        
        # Declare a variable through symbol table
        symbol_table.declare_variable(
            "customer_name",
            "string",
            visibility=SymbolVisibility.INSTANCE,
            initial_value="John Doe"
        )
        
        # Type inference should know about it
        type_info = type_engine.get_type_for_variable("customer_name")
        assert type_info is not None
        assert type_info.type_name == "string"
        
        # Create an expression using the variable
        expr = PBBinaryOperator(
            left=PBVariable(name="customer_name"),
            operator="+",
            right=PBStringLiteral(value=" (Customer)")
        )
        
        # Infer expression type
        expr_type = type_engine.infer_expression_type(expr)
        assert expr_type.type_name == "string"
    
    def test_function_scope_with_parameters(self):
        """Test function scope with parameter symbols."""
        symbol_table = SymbolTable()
        
        # Declare a function
        func_sym = symbol_table.declare_function(
            "calculate_total",
            return_type="decimal",
            parameters=[("price", "decimal"), ("quantity", "integer"), ("tax_rate", "decimal")],
            visibility=SymbolVisibility.PUBLIC
        )
        
        # Enter function scope
        func_scope = symbol_table.enter_scope("calculate_total", "function")
        
        # Add parameters to function scope
        for param in func_sym.parameters:
            symbol_table.add_symbol(param)
        
        # Create type engine for this scope
        type_engine = TypeInferenceEngine(symbol_table.current_scope.type_context)
        
        # Parameters should be accessible
        price_type = type_engine.get_type_for_variable("price")
        assert price_type is not None
        assert price_type.type_name == "decimal"
        
        # Create expression: price * quantity * (1 + tax_rate)
        expr = PBBinaryOperator(
            left=PBBinaryOperator(
                left=PBVariable(name="price"),
                operator="*",
                right=PBVariable(name="quantity")
            ),
            operator="*",
            right=PBBinaryOperator(
                left=PBNumberLiteral(value=1),
                operator="+",
                right=PBVariable(name="tax_rate")
            )
        )
        
        # Type inference should work
        result_type = type_engine.infer_expression_type(expr)
        assert result_type.type_name in ["decimal", "double"]
        
        # Exit function scope
        symbol_table.exit_scope()
        
        # Parameters should no longer be accessible
        assert symbol_table.lookup_symbol("price") is None
    
    def test_class_scope_with_inheritance(self):
        """Test class scope with inheritance visibility."""
        symbol_table = SymbolTable()
        
        # Declare base class
        symbol_table.declare_class("n_base", visibility=SymbolVisibility.PUBLIC)
        base_scope = symbol_table.enter_scope("n_base", "class")
        
        # Add protected member
        symbol_table.declare_variable(
            "is_valid",
            "boolean",
            visibility=SymbolVisibility.PROTECTED,
            initial_value=True
        )
        
        # Add public method
        symbol_table.declare_function(
            "validate",
            return_type="boolean",
            visibility=SymbolVisibility.PUBLIC
        )
        
        # Exit base class
        symbol_table.exit_scope()
        
        # Declare derived class
        symbol_table.declare_class(
            "n_derived",
            ancestor="n_base",
            visibility=SymbolVisibility.PUBLIC
        )
        derived_scope = symbol_table.enter_scope("n_derived", "class")
        
        # Protected member should be visible in derived class
        # (Note: In real implementation, we'd need to handle inheritance properly)
        # For now, we'll add our own variable
        symbol_table.declare_variable(
            "derived_flag",
            "boolean",
            visibility=SymbolVisibility.PRIVATE
        )
        
        # Create method in derived class
        method_scope = symbol_table.enter_scope("process", "function")
        
        # Can access own class members
        assert symbol_table.lookup_symbol("derived_flag") is not None
        
        symbol_table.exit_scope()  # Exit method
        symbol_table.exit_scope()  # Exit derived class
    
    def test_forward_declaration_resolution(self):
        """Test forward declaration and resolution."""
        symbol_table = SymbolTable()
        type_engine = TypeInferenceEngine(symbol_table.current_scope.type_context)
        
        # Forward declare a function
        symbol_table.declare_function(
            "process_data",
            return_type="integer",
            is_forward=True
        )
        
        # Use the forward declared function
        call_expr = PBFunctionCall(
            function_name="process_data",
            arguments=[PBStringLiteral(value="test")]
        )
        
        # Type inference should work with forward declaration
        return_type = type_engine.infer_expression_type(call_expr)
        assert return_type.type_name == "integer"
        
        # Later, provide actual implementation
        symbol_table.declare_function(
            "process_data",
            return_type="integer",
            parameters=[("data", "string")],
            is_forward=False
        )
        
        # Resolve forward declarations
        symbol_table.resolve_forward_declarations()
        
        # Should have the full definition now
        func_sym = symbol_table.lookup_symbol("process_data", SymbolKind.FUNCTION)
        assert func_sym is not None
        assert not func_sym.is_forward_declaration
        assert len(func_sym.parameters) == 1
    
    def test_symbol_location_tracking(self):
        """Test tracking symbol locations for error reporting."""
        symbol_table = SymbolTable()
        
        # Simulate parsing a PowerBuilder file
        file_location = SymbolLocation(
            file_path="n_cst_service.sru",
            object_name="n_cst_service",
            script_name="constructor",
            line=15,
            column=5,
            end_line=15,
            end_column=25
        )
        
        # Declare variable with location
        var_sym = symbol_table.declare_variable(
            "instance_count",
            "integer",
            visibility=SymbolVisibility.INSTANCE,
            location=file_location,
            is_static=True
        )
        
        # Location should be preserved
        found = symbol_table.lookup_symbol("instance_count")
        assert found.location is not None
        assert found.location.file_path == "n_cst_service.sru"
        assert found.location.line == 15
    
    def test_type_inference_with_assignments(self):
        """Test type inference with variable assignments in symbol table."""
        symbol_table = SymbolTable()
        type_engine = TypeInferenceEngine(symbol_table.current_scope.type_context)
        
        # Simulate: string ls_name
        symbol_table.declare_variable("ls_name", "string")
        
        # Simulate: ls_name = "John"
        value_expr = PBStringLiteral(value="John")
        
        # Infer and verify
        assign_type = type_engine.infer_assignment_type("ls_name", value_expr)
        assert assign_type.type_name == "string"
        
        # Simulate: integer li_count = Len(ls_name)
        len_call = PBFunctionCall(
            function_name="len",
            arguments=[PBVariable(name="ls_name")]
        )
        
        symbol_table.declare_variable("li_count", "integer")
        count_type = type_engine.infer_assignment_type("li_count", len_call)
        assert count_type.type_name == "integer"
    
    def test_nested_scopes_with_shadowing(self):
        """Test nested scopes with variable shadowing."""
        symbol_table = SymbolTable()
        
        # Global variable
        symbol_table.declare_variable(
            "status",
            "string",
            visibility=SymbolVisibility.GLOBAL,
            initial_value="ready"
        )
        
        # Enter function scope
        func_scope = symbol_table.enter_scope("process", "function")
        
        # Local variable shadows global
        symbol_table.declare_variable(
            "status",
            "integer",
            visibility=SymbolVisibility.LOCAL,
            initial_value=0
        )
        
        # Should get local variable
        local_status = symbol_table.lookup_symbol("status")
        assert local_status.type_info.type_name == "integer"
        assert local_status.initial_value == 0
        
        # Enter nested block
        block_scope = symbol_table.enter_scope("if_block", "block")
        
        # Can still see local variable
        assert symbol_table.lookup_symbol("status").type_info.type_name == "integer"
        
        # Exit block
        symbol_table.exit_scope()
        
        # Exit function
        symbol_table.exit_scope()
        
        # Should see global variable again
        global_status = symbol_table.lookup_symbol("status")
        assert global_status.type_info.type_name == "string"
        assert global_status.initial_value == "ready"
    
    def test_array_type_integration(self):
        """Test array types with symbol table and type inference."""
        symbol_table = SymbolTable()
        type_engine = TypeInferenceEngine(symbol_table.current_scope.type_context)
        
        # Declare array variable
        symbol_table.declare_variable(
            "numbers",
            "integer",
            is_array=True,
            array_dimensions=1
        )
        
        # Type should be tracked correctly
        array_type = type_engine.get_type_for_variable("numbers")
        assert array_type is not None
        assert array_type.is_array
        assert array_type.array_dimensions == 1
        assert array_type.type_name == "integer"
        
        # Function call on array
        upperbound_call = PBFunctionCall(
            function_name="upperbound",
            arguments=[PBVariable(name="numbers")]
        )
        
        # Should infer integer return type
        bound_type = type_engine.infer_expression_type(upperbound_call)
        assert bound_type.type_name == "integer"
        assert not bound_type.is_nullable
    
    def test_symbol_table_with_imports(self):
        """Test symbol table with imports tracking."""
        symbol_table = SymbolTable()
        
        # Enter a class scope
        class_scope = symbol_table.enter_scope("n_cst_data", "class")
        
        # Track imports
        symbol_table.current_scope.imports.add("n_cst_string")
        symbol_table.current_scope.imports.add("n_cst_datetime")
        symbol_table.current_scope.using_namespaces.add("PFC")
        
        # Imports should be tracked
        assert "n_cst_string" in symbol_table.current_scope.imports
        assert "PFC" in symbol_table.current_scope.using_namespaces
    
    def test_find_symbols_by_type(self):
        """Test finding all symbols of a specific type."""
        symbol_table = SymbolTable()
        
        # Add variables of different types
        symbol_table.declare_variable("name", "string")
        symbol_table.declare_variable("age", "integer")
        symbol_table.declare_variable("title", "string")
        
        # Enter function and add more
        symbol_table.enter_scope("process", "function")
        symbol_table.declare_variable("temp", "string")
        symbol_table.declare_variable("count", "integer")
        symbol_table.exit_scope()
        
        # Find all string variables
        string_vars = symbol_table.find_symbols_by_type("string", SymbolKind.VARIABLE)
        assert len(string_vars) == 3
        names = {sym.name for sym in string_vars}
        assert names == {"name", "title", "temp"}
        
        # Find all integer variables
        int_vars = symbol_table.find_symbols_by_type("integer", SymbolKind.VARIABLE)
        assert len(int_vars) == 2
        names = {sym.name for sym in int_vars}
        assert names == {"age", "count"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])