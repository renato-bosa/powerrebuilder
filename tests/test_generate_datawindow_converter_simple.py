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
            label="Customer ID",
            data_type="int",
            width=100,
            alignment="right",
            format="#,##0",
            editable=False,
            validation=None
        )
        
        assert column.name == "customer_id"
        assert column.data_type == "int"
        assert column.width == 100
        assert column.alignment == "right"
        
        # Test to_dict method
        col_dict = column.to_dict()
        assert col_dict["name"] == "customer_id"
        assert col_dict["data_type"] == "int"
        assert col_dict["alignment"] == "TextAlign.right"
        assert col_dict["editable"] == "false"

    def test_datawindow_definition_creation(self):


        

        """Test DataWindowDefinition dataclass."""
        columns = [
            DataWindowColumn(
                name="id",
                label="ID",
                data_type="int",
                editable=False
            ),
            DataWindowColumn(
                name="name",
                label="Name",
                data_type="String",
                editable=True
            )
        ]
        
        dw_def = DataWindowDefinition(
            name="d_customer_list",
            sql="SELECT id, name FROM customer",
            presentation_style="grid",
            columns=columns
        )
        
        assert dw_def.name == "d_customer_list"
        assert len(dw_def.columns) == 2
        assert dw_def.presentation_style == "grid"
        assert dw_def.sql == "SELECT id, name FROM customer"
        
        # Test to_dict method
        dw_dict = dw_def.to_dict()
        assert dw_dict["name"] == "d_customer_list"
        assert dw_dict["presentation_style"] == "grid"
        assert len(dw_dict["columns"]) == 2

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
        syntax = 'datawindow(processing=0)'
        style = self.converter._extract_presentation_style(syntax)
        assert style == "grid"
        
        # Tabular style
        syntax = 'datawindow(processing=1)'
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
        assert columns[0].data_type == "int"  # Dart type after conversion
        assert columns[1].name == "customer_name"
        assert columns[1].data_type == "String"  # Dart type after conversion
        assert columns[2].name == "balance"
        assert columns[2].data_type == "double"  # Dart type after conversion

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
        
        assert dw_def.name == "CustomerList"  # Converted to PascalCase with prefix removed
        assert dw_def.presentation_style == "tabular"  # processing=1 means tabular
        assert len(dw_def.columns) == 2
        assert dw_def.columns[0].name == "id"
        assert dw_def.columns[0].data_type == "int"
        assert dw_def.columns[1].name == "name"
        assert dw_def.columns[1].data_type == "String"

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
            DataWindowColumn(
                name="photo", 
                label="Photo", 
                data_type="Uint8List",
                blob_metadata={"usage": "image", "display_widget": "PhotoBlobDisplay"}
            ),
            DataWindowColumn(
                name="document", 
                label="Document", 
                data_type="Uint8List",
                blob_metadata={"usage": "document", "display_widget": "DocumentBlobDisplay"}
            )
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
            DataWindowColumn(name="id", label="ID", data_type="int", editable=False)
        ]
        
        dw_def = DataWindowDefinition(
            name="d_test",
            sql="SELECT * FROM test_table",
            presentation_style="grid",
            columns=columns
        )
        
        result = dw_def.to_dict()
        
        assert result["name"] == "d_test"
        assert result["presentation_style"] == "grid"
        assert len(result["columns"]) == 1
        assert result["sql"] == "SELECT * FROM test_table"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])