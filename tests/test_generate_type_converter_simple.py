"""Simple tests for the type converter module."""

import pytest

from generate.converters.type_converter import TypeConverter


class TestTypeConverter:
    """Test cases for PowerBuilder to Dart type conversion."""

    def setup_method(self):




        """Set up test instances."""
        # Use defaults by not providing a mapping file
        self.converter = TypeConverter()

    def test_basic_type_conversions(self):




        """Test basic PowerBuilder to Dart type conversions."""
        # Basic type conversions
        assert self.converter.convert_type("integer") == "int"
        assert self.converter.convert_type("long") == "int"
        assert self.converter.convert_type("decimal") == "double"
        assert self.converter.convert_type("real") == "double"
        assert self.converter.convert_type("double") == "double"
        assert self.converter.convert_type("string") == "String"
        assert self.converter.convert_type("char") == "String"
        assert self.converter.convert_type("boolean") == "bool"
        assert self.converter.convert_type("date") == "DateTime"
        assert self.converter.convert_type("datetime") == "DateTime"

    def test_nullable_type_conversions(self):




        """Test nullable type conversions."""
        assert self.converter.convert_type("integer", nullable=True) == "int?"
        assert self.converter.convert_type("string", nullable=True) == "String?"
        assert self.converter.convert_type("boolean", nullable=True) == "bool?"
        assert self.converter.convert_type("date", nullable=True) == "DateTime?"

    def test_array_type_conversions(self):




        """Test array type conversions."""
        assert self.converter.convert_type("integer[]") == "List<int>"
        assert self.converter.convert_type("string[]") == "List<String>"
        assert self.converter.convert_type("boolean[]") == "List<bool>"

        # Nullable arrays
        assert self.converter.convert_type("integer[]", nullable=True) == "List<int>?"

    def test_custom_type_conversions(self):




        """Test custom type conversions."""
        # Unknown types are treated as custom classes
        assert self.converter.convert_type("n_cst_service") == "NCstService"
        assert self.converter.convert_type("w_main_window") == "WMainWindow"

        # With nullable
        assert self.converter.convert_type("n_cst_service", nullable=True) == "NCstService?"

    def test_default_values(self):




        """Test default value generation."""
        assert self.converter.get_default_value("integer") == "0"
        assert self.converter.get_default_value("string") == "''"
        assert self.converter.get_default_value("boolean") == "false"
        assert self.converter.get_default_value("date") == "DateTime.now()"
        assert self.converter.get_default_value("integer[]") == "[]"
        assert self.converter.get_default_value("custom_type") == "null"

    def test_type_imports(self):




        """Test import generation for types."""
        # Blob type requires imports
        imports = self.converter.get_imports_for_type("blob")
        assert "import 'dart:typed_data';" in imports
        assert "import 'dart:convert';" in imports

    def test_primitive_type_check(self):




        """Test primitive type checking."""
        assert self.converter.is_primitive_type("integer") is True
        assert self.converter.is_primitive_type("string") is True
        assert self.converter.is_primitive_type("boolean") is True
        assert self.converter.is_primitive_type("custom_type") is False

    def test_special_types(self):




        """Test special type conversions."""
        # Decimal with precision
        assert self.converter.convert_type("decimal(10,2)") == "double"

        # Char with length
        assert self.converter.convert_type("char(50)") == "String"

        # Blob type
        assert self.converter.convert_type("blob") == "Uint8List"

    def test_case_insensitivity(self):




        """Test case insensitive type conversion."""
        assert self.converter.convert_type("INTEGER") == "int"
        assert self.converter.convert_type("String") == "String"
        assert self.converter.convert_type("BOOLEAN") == "bool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
