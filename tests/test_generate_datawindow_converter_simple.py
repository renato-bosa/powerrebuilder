"""Simple tests for the DataWindow converter module."""

import pytest
from generate.converters.datawindow_converter import DataWindowConverter, DataWindowColumn, DataWindowDefinition
from generate.converters.type_converter import TypeConverter
from generate.converters.blob_converter import BlobConverter


class TestDataWindowConverter:
    """Test cases for PowerBuilder DataWindow to Flutter conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.type_converter = TypeConverter()
        self.blob_converter = BlobConverter()
        self.converter = DataWindowConverter(
            type_converter=self.type_converter,
            blob_converter=self.blob_converter
        )

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None
        assert hasattr(self.converter, 'type_converter')
        assert hasattr(self.converter, 'blob_converter')

    def test_datawindow_column_creation(self):
        """Test DataWindowColumn dataclass."""
        column = DataWindowColumn(
            name="customer_id",
            pb_type="number",
            dart_type="int",
            is_key=True,
            is_nullable=False,
            db_name="cust.id",
            initial_value="0"
        )
        
        assert column.name == "customer_id"
        assert column.dart_type == "int"
        assert column.is_key is True
        
        # Test to_dict method
        col_dict = column.to_dict()
        assert col_dict["name"] == "customer_id"
        assert col_dict["is_key"] is True

    def test_datawindow_definition_creation(self):
        """Test DataWindowDefinition dataclass."""
        columns = [
            DataWindowColumn(
                name="id",
                pb_type="number",
                dart_type="int",
                is_key=True
            ),
            DataWindowColumn(
                name="name",
                pb_type="char(50)",
                dart_type="String"
            )
        ]
        
        dw_def = DataWindowDefinition(
            name="d_customer_list",
            table="customer",
            presentation_style="grid",
            columns=columns,
            sql_select="SELECT id, name FROM customer"
        )
        
        assert dw_def.name == "d_customer_list"
        assert len(dw_def.columns) == 2
        assert dw_def.presentation_style == "grid"
        
        # Test model names generation
        assert dw_def.model_class_name == "DCustomerList"
        assert dw_def.model_file_name == "d_customer_list.dart"

    def test_extract_sql(self):
        """Test SQL extraction from DataWindow syntax."""
        syntax = '''
        release 8;
        datawindow(units=0 timer_interval=0)
        table(column=(name=id type=number dbname="customer.id")
              column=(name=name type=char(50) dbname="customer.name"))
        retrieve="SELECT customer.id, customer.name FROM customer"
        '''
        
        sql = self.converter._extract_sql(syntax)
        assert sql is not None
        assert "SELECT" in sql
        assert "customer.id" in sql

    def test_extract_presentation_style(self):
        """Test presentation style extraction."""
        # Grid style
        syntax = 'datawindow(processing=1)'
        style = self.converter._extract_presentation_style(syntax)
        assert style == "grid"
        
        # Tabular style
        syntax = 'datawindow(processing=0)'
        style = self.converter._extract_presentation_style(syntax)
        assert style == "tabular"
        
        # Freeform style
        syntax = 'datawindow(processing=2)'
        style = self.converter._extract_presentation_style(syntax)
        assert style == "freeform"

    def test_extract_columns(self):
        """Test column extraction from DataWindow syntax."""
        syntax = '''
        table(column=(type=number updatewhereclause=yes name=customer_id dbname="customer.id" )
              column=(type=char(50) updatewhereclause=yes name=customer_name dbname="customer.name" )
              column=(type=decimal(2) updatewhereclause=yes name=balance dbname="customer.balance" ))
        '''
        
        columns = self.converter._extract_columns(syntax)
        
        assert len(columns) == 3
        assert columns[0].name == "customer_id"
        assert columns[0].pb_type == "number"
        assert columns[1].name == "customer_name"
        assert columns[1].pb_type == "char(50)"
        assert columns[2].name == "balance"
        assert columns[2].pb_type == "decimal(2)"

    def test_convert_simple_datawindow(self):
        """Test converting a simple DataWindow."""
        dw_syntax = '''
        release 19;
        datawindow(units=0 timer_interval=0 color=1073741824 processing=1)
        table(column=(type=number updatewhereclause=yes name=id dbname="customer.id" )
              column=(type=char(100) updatewhereclause=yes name=name dbname="customer.name" ))
        retrieve="SELECT customer.id, customer.name FROM customer"
        '''
        
        dw_def = self.converter.convert_datawindow(dw_syntax, "d_customer_list")
        
        assert dw_def.name == "d_customer_list"
        assert dw_def.presentation_style == "grid"
        assert len(dw_def.columns) == 2
        assert dw_def.columns[0].name == "id"
        assert dw_def.columns[0].dart_type == "int"
        assert dw_def.columns[1].name == "name"
        assert dw_def.columns[1].dart_type == "String"

    def test_convert_where_clause(self):
        """Test WHERE clause conversion."""
        # Simple equality
        where = "status = 'A'"
        result = self.converter._convert_where_clause(where)
        assert result == "status = 'A'"
        
        # With parameters
        where = "customer_id = :customer_id"
        result = self.converter._convert_where_clause(where)
        assert result == "customer_id = @customer_id"

    def test_blob_column_handling(self):
        """Test handling of blob columns."""
        columns = [
            DataWindowColumn(name="id", label="ID", data_type="int"),
            DataWindowColumn(name="photo", label="Photo", data_type="Uint8List"),
            DataWindowColumn(name="document", label="Document", data_type="Uint8List")
        ]
        
        dw_def = DataWindowDefinition(
            name="d_customer",
            presentation_style="freeform",
            columns=columns
        )
        
        blob_columns = dw_def.get_blob_columns()
        assert len(blob_columns) == 2
        assert blob_columns[0].name == "photo"
        assert blob_columns[1].name == "document"

    def test_to_dict_conversion(self):
        """Test DataWindowDefinition to_dict conversion."""
        columns = [
            DataWindowColumn(name="id", pb_type="number", dart_type="int", is_key=True)
        ]
        
        dw_def = DataWindowDefinition(
            name="d_test",
            table="test_table",
            presentation_style="grid",
            columns=columns
        )
        
        result = dw_def.to_dict()
        
        assert result["name"] == "d_test"
        assert result["table"] == "test_table"
        assert result["presentation_style"] == "grid"
        assert len(result["columns"]) == 1
        assert result["model_class_name"] == "DTest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])