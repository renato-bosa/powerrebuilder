"""Tests for the type converter module."""

import pytest
from generate.converters.type_converter import TypeConverter


class TestTypeConverter:
    """Test cases for PowerBuilder to Dart type conversion."""

    def setup_method(self):


        

        """Set up test instances."""
        self.converter = TypeConverter()

    def test_basic_type_conversions(self):


        

        """Test basic PowerBuilder to Dart type conversions."""
        # Numeric types
        assert self.converter.convert_type("integer") == "int"
        assert self.converter.convert_type("long") == "int"
        assert self.converter.convert_type("decimal") == "double"
        assert self.converter.convert_type("real") == "double"
        assert self.converter.convert_type("double") == "double"
        assert self.converter.convert_type("uint") == "int"
        assert self.converter.convert_type("ulong") == "int"

        # String types
        assert self.converter.convert_type("string") == "String"
        assert self.converter.convert_type("char") == "String"

        # Boolean type
        assert self.converter.convert_type("boolean") == "bool"

        # Date/Time types
        assert self.converter.convert_type("date") == "DateTime"
        assert self.converter.convert_type("datetime") == "DateTime"
        assert self.converter.convert_type("time") == "DateTime"

    def test_array_type_conversions(self):


        

        """Test array type conversions."""
        assert self.converter.convert_type("integer[]") == "List<int>"
        assert self.converter.convert_type("string[]") == "List<String>"
        assert self.converter.convert_type("boolean[]") == "List<bool>"
        assert self.converter.convert_type("decimal[]") == "List<double>"
        assert self.converter.convert_type("date[]") == "List<DateTime>"

    def test_object_type_conversions(self):


        

        """Test object type conversions."""
        # Custom objects should preserve their names
        assert self.converter.convert_type("n_cst_service") == "NCstService"
        assert self.converter.convert_type("w_main") == "WMain"
        assert self.converter.convert_type("dw_customer") == "DwCustomer"
        assert self.converter.convert_type("uo_button") == "UoButton"

        # Object arrays
        assert self.converter.convert_type("n_cst_service[]") == "List<NCstService>"
        assert self.converter.convert_type("w_main[]") == "List<WMain>"

    def test_special_type_conversions(self):


        

        """Test special PowerBuilder type conversions."""
        assert self.converter.convert_type("any") == "dynamic"
        assert self.converter.convert_type("blob") == "Uint8List"
        assert self.converter.convert_type("powerobject") == "Object"
        assert self.converter.convert_type("structure") == "Map<String, dynamic>"

    def test_unknown_type_handling(self):


        

        """Test handling of unknown types."""
        # Unknown types should be preserved with a comment
        result = self.converter.convert_type("unknowntype")
        assert result == "dynamic /* unknowntype */"

    def test_type_case_insensitivity(self):


        

        """Test that type conversion is case-insensitive."""
        assert self.converter.convert_type("INTEGER") == "int"
        assert self.converter.convert_type("Integer") == "int"
        assert self.converter.convert_type("STRING") == "String"
        assert self.converter.convert_type("String") == "String"
        assert self.converter.convert_type("BOOLEAN") == "bool"

    def test_nullable_type_conversions(self):


        

        """Test nullable type conversions."""
        assert self.converter.convert_nullable_type("integer") == "int?"
        assert self.converter.convert_nullable_type("string") == "String?"
        assert self.converter.convert_nullable_type("boolean") == "bool?"
        assert self.converter.convert_nullable_type("decimal") == "double?"
        assert self.converter.convert_nullable_type("n_cst_service") == "NCstService?"

    def test_default_value_conversions(self):


        

        """Test default value conversions for different types."""
        assert self.converter.get_default_value("integer") == "0"
        assert self.converter.get_default_value("long") == "0"
        assert self.converter.get_default_value("decimal") == "0.0"
        assert self.converter.get_default_value("real") == "0.0"
        assert self.converter.get_default_value("double") == "0.0"
        assert self.converter.get_default_value("string") == "''"
        assert self.converter.get_default_value("char") == "''"
        assert self.converter.get_default_value("boolean") == "false"
        assert self.converter.get_default_value("date") == "DateTime.now()"
        assert self.converter.get_default_value("datetime") == "DateTime.now()"
        assert self.converter.get_default_value("any") == "null"
        assert self.converter.get_default_value("n_cst_service") == "null"

    def test_default_value_for_arrays(self):


        

        """Test default value conversions for array types."""
        assert self.converter.get_default_value("integer[]") == "[]"
        assert self.converter.get_default_value("string[]") == "[]"
        assert self.converter.get_default_value("n_cst_service[]") == "[]"

    def test_convert_value(self):


        

        """Test value conversion with type context."""
        # Integer values
        assert self.converter.convert_value("123", "integer") == "123"
        assert self.converter.convert_value("-456", "long") == "-456"
        
        # Decimal values
        assert self.converter.convert_value("123.45", "decimal") == "123.45"
        assert self.converter.convert_value("-67.89", "double") == "-67.89"
        
        # String values
        assert self.converter.convert_value('"Hello"', "string") == "'Hello'"
        assert self.converter.convert_value("'World'", "string") == "'World'"
        
        # Boolean values
        assert self.converter.convert_value("true", "boolean") == "true"
        assert self.converter.convert_value("false", "boolean") == "false"
        assert self.converter.convert_value("TRUE", "boolean") == "true"
        assert self.converter.convert_value("FALSE", "boolean") == "false"

    def test_is_numeric_type(self):


        

        """Test numeric type detection."""
        assert self.converter.is_numeric_type("integer") is True
        assert self.converter.is_numeric_type("long") is True
        assert self.converter.is_numeric_type("decimal") is True
        assert self.converter.is_numeric_type("real") is True
        assert self.converter.is_numeric_type("double") is True
        assert self.converter.is_numeric_type("uint") is True
        assert self.converter.is_numeric_type("ulong") is True
        
        assert self.converter.is_numeric_type("string") is False
        assert self.converter.is_numeric_type("boolean") is False
        assert self.converter.is_numeric_type("date") is False

    def test_is_string_type(self):


        

        """Test string type detection."""
        assert self.converter.is_string_type("string") is True
        assert self.converter.is_string_type("char") is True
        assert self.converter.is_string_type("STRING") is True
        assert self.converter.is_string_type("CHAR") is True
        
        assert self.converter.is_string_type("integer") is False
        assert self.converter.is_string_type("boolean") is False
        assert self.converter.is_string_type("date") is False

    def test_complex_type_conversions(self):


        

        """Test conversion of complex PowerBuilder types."""
        # Enumerated types
        assert self.converter.convert_type("alignment") == "Alignment"
        assert self.converter.convert_type("button") == "Button"
        
        # System objects
        assert self.converter.convert_type("transaction") == "Transaction"
        assert self.converter.convert_type("datastore") == "DataStore"
        assert self.converter.convert_type("datawindow") == "DataWindow"

    def test_convert_constant_value(self):


        

        """Test conversion of PowerBuilder constants."""
        # Numeric constants
        assert self.converter.convert_constant("123") == "123"
        assert self.converter.convert_constant("-456") == "-456"
        assert self.converter.convert_constant("123.45") == "123.45"
        
        # String constants
        assert self.converter.convert_constant('"Hello World"') == "'Hello World'"
        assert self.converter.convert_constant("'Single quotes'") == "'Single quotes'"
        
        # Boolean constants
        assert self.converter.convert_constant("TRUE") == "true"
        assert self.converter.convert_constant("FALSE") == "false"
        
        # NULL constant
        assert self.converter.convert_constant("NULL") == "null"
        assert self.converter.convert_constant("null") == "null"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])