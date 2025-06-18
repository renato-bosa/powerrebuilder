"""Simple tests for the event converter module."""

import pytest
from generate.converters.event_converter import EventConverter
from generate.converters.type_converter import TypeConverter
from generate.converters.expression_converter import ExpressionConverter


class TestEventConverter:
    """Test cases for PowerBuilder to Dart event conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.type_converter = TypeConverter()
        self.expression_converter = ExpressionConverter()
        self.converter = EventConverter(
            type_converter=self.type_converter,
            expression_converter=self.expression_converter
        )

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None
        assert hasattr(self.converter, 'type_converter')
        assert hasattr(self.converter, 'expression_converter')
        assert hasattr(self.converter, 'event_mappings')

    def test_convert_simple_event(self):
        """Test conversion of a simple event."""
        event = self.converter.convert_event(
            event_name="clicked",
            parameters=[],
            body=["messagebox('Info', 'Button clicked')"]
        )
        
        assert event is not None
        assert event.name == "onClicked"
        assert event.method_type == "callback"

    def test_convert_lifecycle_event(self):
        """Test conversion of lifecycle events."""
        # Open event -> initState
        event = self.converter.convert_event(
            event_name="open",
            parameters=[],
            body=["// Initialize"]
        )
        
        assert event is not None
        assert event.name == "initState"
        assert event.method_type == "lifecycle"
        assert event.is_override is True

    def test_convert_event_body_simple(self):
        """Test simple event body conversion."""
        body = ["integer li_result", "li_result = 10"]
        converted = self.converter._convert_event_body(body, "clicked")
        
        assert len(converted) > 0
        assert any("int liResult" in line for line in converted)
        assert any("liResult = 10" in line for line in converted)

    def test_convert_return_statement(self):
        """Test return statement conversion."""
        # Integer return
        result = self.converter._convert_return_statement("return 0", "int")
        assert result == "return 0;"
        
        # Void return
        result = self.converter._convert_return_statement("return", None)
        assert result == "return;"
        
        # Expression return
        result = self.converter._convert_return_statement("return li_count + 1", "int")
        assert "return" in result
        assert ";" in result

    def test_convert_assignment_statement(self):
        """Test assignment statement conversion."""
        # Simple assignment
        result = self.converter._convert_assignment_statement("ls_name = 'John'")
        assert "lsName = 'John'" in result
        
        # Variable declaration
        result = self.converter._convert_assignment_statement("string ls_text")
        assert "String lsText" in result

    def test_convert_if_statement(self):
        """Test if statement conversion."""
        # Simple if
        result = self.converter._convert_if_statement("if li_count > 0 then")
        assert "if (liCount > 0) {" in result
        
        # If with complex condition
        result = self.converter._convert_if_statement("if isnull(ls_value) then")
        assert "if (lsValue == null) {" in result

    def test_convert_method_call(self):
        """Test method call conversion."""
        # MessageBox
        result = self.converter._convert_method_call("messagebox('Title', 'Message')")
        assert "showDialog" in result or "// messagebox" in result.lower()
        
        # Close window
        result = self.converter._convert_method_call("close(this)")
        assert "Navigator.pop" in result or "close" in result

    def test_default_return_values(self):
        """Test default return value generation."""
        assert self.converter._get_default_value("int") == "0"
        assert self.converter._get_default_value("String") == "''"
        assert self.converter._get_default_value("bool") == "false"
        assert self.converter._get_default_value("double") == "0.0"
        assert self.converter._get_default_value("dynamic") == "null"

    def test_callback_parameter_extraction(self):
        """Test extracting parameters from callback signatures."""
        # TextField onChanged
        params = self.converter._get_callback_parameters("void Function(String)")
        assert len(params) == 1
        assert params[0].dart_type == "String"
        assert params[0].name == "value"
        
        # onTap callback
        params = self.converter._get_callback_parameters("void Function()")
        assert len(params) == 0

    def test_callback_return_type_extraction(self):
        """Test extracting return type from callback signatures."""
        assert self.converter._get_callback_return_type("void Function()") == "void"
        assert self.converter._get_callback_return_type("bool Function()") == "bool"
        assert self.converter._get_callback_return_type("Future<void> Function()") == "Future<void>"

    def test_needs_set_state(self):
        """Test detection of state changes that need setState."""
        assert self.converter._needs_set_state("_counter") is True
        assert self.converter._needs_set_state("_isLoading") is True
        assert self.converter._needs_set_state("counter") is False
        assert self.converter._needs_set_state("localVar") is False

    def test_event_with_parameters(self):
        """Test event conversion with parameters."""
        from model.entities.function_entities import Parameter
        from model.ast.types import Type
        
        params = [
            Parameter(name="newtext", type=Type("string"))
        ]
        
        event = self.converter.convert_event(
            event_name="modified",
            parameters=params,
            body=["// Handle text change"]
        )
        
        assert event is not None
        assert len(event.parameters) == 1
        assert event.parameters[0].name == "newtext"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])