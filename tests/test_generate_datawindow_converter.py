"""Tests for the DataWindow converter module."""

import pytest

from generate.converters.datawindow_converter import DataWindowConverter


class TestDataWindowConverter:
    """Test cases for PowerBuilder DataWindow to Flutter conversion."""

    def setup_method(self):




        """Set up test instances."""
        self.converter = DataWindowConverter()

    def test_basic_datawindow_conversion(self):




        """Test basic DataWindow structure conversion."""
        dw_def = {
            "name": "dw_customer",
            "dataobject": "d_customer_list",
            "columns": [
                {"name": "customer_id", "type": "number", "dbname": "customer.id"},
                {"name": "customer_name", "type": "char(50)", "dbname": "customer.name"},
                {"name": "balance", "type": "decimal(2)", "dbname": "customer.balance"},
            ],
        }

        result = self.converter.convert_datawindow(dw_def)

        assert result["widget_type"] == "DataTable"
        assert len(result["columns"]) == 3
        assert result["columns"][0]["label"] == "Customer Id"
        assert result["columns"][0]["type"] == "int"
        assert result["columns"][1]["label"] == "Customer Name"
        assert result["columns"][1]["type"] == "String"
        assert result["columns"][2]["label"] == "Balance"
        assert result["columns"][2]["type"] == "double"

    def test_convert_column_definition(self):




        """Test column definition conversion."""
        # Numeric column
        col = {"name": "qty", "type": "number", "dbname": "order.quantity"}
        result = self.converter.convert_column(col)
        assert result["name"] == "qty"
        assert result["type"] == "int"
        assert result["label"] == "Qty"

        # String column with length
        col = {"name": "description", "type": "char(255)", "dbname": "product.desc"}
        result = self.converter.convert_column(col)
        assert result["type"] == "String"
        assert result["maxLength"] == 255

        # Date column
        col = {"name": "order_date", "type": "date", "dbname": "order.date"}
        result = self.converter.convert_column(col)
        assert result["type"] == "DateTime"
        assert result["format"] == "date"

    def test_convert_presentation_styles(self):




        """Test DataWindow presentation style conversion."""
        # Grid style
        dw_def = {"presentation_style": "grid", "columns": []}
        result = self.converter.convert_datawindow(dw_def)
        assert result["widget_type"] == "DataTable"
        assert result["style"] == "grid"

        # Tabular style
        dw_def = {"presentation_style": "tabular", "columns": []}
        result = self.converter.convert_datawindow(dw_def)
        assert result["widget_type"] == "DataTable"
        assert result["style"] == "tabular"

        # Freeform style
        dw_def = {"presentation_style": "freeform", "columns": []}
        result = self.converter.convert_datawindow(dw_def)
        assert result["widget_type"] == "Form"
        assert result["style"] == "freeform"

        # Group style
        dw_def = {"presentation_style": "group", "columns": []}
        result = self.converter.convert_datawindow(dw_def)
        assert result["widget_type"] == "GroupedListView"
        assert result["style"] == "group"

    def test_convert_retrieval_arguments(self):




        """Test retrieval argument conversion."""
        dw_def = {
            "retrieval_arguments": [
                {"name": "customer_id", "type": "number"},
                {"name": "start_date", "type": "date"},
                {"name": "status", "type": "string"},
            ],
        }

        result = self.converter.convert_retrieval_arguments(dw_def["retrieval_arguments"])

        assert len(result) == 3
        assert result[0]["name"] == "customerId"
        assert result[0]["type"] == "int"
        assert result[1]["name"] == "startDate"
        assert result[1]["type"] == "DateTime"
        assert result[2]["name"] == "status"
        assert result[2]["type"] == "String"

    def test_convert_computed_fields(self):




        """Test computed field conversion."""
        computed = [
            {
                "name": "full_name",
                "expression": "first_name + ' ' + last_name",
                "type": "string",
            },
            {
                "name": "total_amount",
                "expression": "quantity * unit_price",
                "type": "decimal",
            },
        ]

        result = self.converter.convert_computed_fields(computed)

        assert len(result) == 2
        assert result[0]["name"] == "fullName"
        assert result[0]["getter"] == "firstName + ' ' + lastName"
        assert result[0]["type"] == "String"
        assert result[1]["name"] == "totalAmount"
        assert result[1]["getter"] == "quantity * unitPrice"
        assert result[1]["type"] == "double"

    def test_convert_validation_rules(self):




        """Test validation rule conversion."""
        validations = [
            {
                "column": "age",
                "rule": "age >= 0 and age <= 150",
                "message": "Age must be between 0 and 150",
            },
            {
                "column": "email",
                "rule": "pos(email, '@') > 0",
                "message": "Invalid email address",
            },
        ]

        result = self.converter.convert_validation_rules(validations)

        assert len(result) == 2
        assert result[0]["field"] == "age"
        assert result[0]["validator"] == "(value) => value >= 0 && value <= 150"
        assert result[0]["errorMessage"] == "Age must be between 0 and 150"
        assert result[1]["field"] == "email"
        assert result[1]["validator"] == "(value) => value.contains('@')"

    def test_generate_data_model(self):




        """Test data model class generation."""
        dw_def = {
            "name": "dw_product",
            "columns": [
                {"name": "product_id", "type": "number"},
                {"name": "product_name", "type": "char(100)"},
                {"name": "price", "type": "decimal(2)"},
                {"name": "in_stock", "type": "char(1)"},
            ],
        }

        model_code = self.converter.generate_data_model(dw_def)

        assert "class DwProductModel {" in model_code
        assert "final int productId;" in model_code
        assert "final String productName;" in model_code
        assert "final double price;" in model_code
        assert "final bool inStock;" in model_code
        assert "DwProductModel({" in model_code
        assert "required this.productId," in model_code
        assert "factory DwProductModel.fromJson" in model_code
        assert "Map<String, dynamic> toJson()" in model_code

    def test_generate_datatable_widget(self):




        """Test DataTable widget generation."""
        dw_def = {
            "name": "dw_order_list",
            "columns": [
                {"name": "order_id", "type": "number"},
                {"name": "customer_name", "type": "char(50)"},
                {"name": "order_date", "type": "date"},
                {"name": "total", "type": "decimal(2)"},
            ],
        }

        widget_code = self.converter.generate_datatable_widget(dw_def)

        assert "class DwOrderListWidget extends StatefulWidget" in widget_code
        assert "DataTable(" in widget_code
        assert "DataColumn(label: Text('Order Id'))" in widget_code
        assert "DataColumn(label: Text('Customer Name'))" in widget_code
        assert "DataColumn(label: Text('Order Date'))" in widget_code
        assert "DataColumn(label: Text('Total'))" in widget_code
        assert "DataRow(" in widget_code
        assert "DataCell(" in widget_code

    def test_convert_sort_specifications(self):




        """Test sort specification conversion."""
        sort_specs = [
            {"column": "customer_name", "order": "A"},
            {"column": "order_date", "order": "D"},
        ]

        result = self.converter.convert_sort_specs(sort_specs)

        assert len(result) == 2
        assert result[0]["field"] == "customerName"
        assert result[0]["ascending"] is True
        assert result[1]["field"] == "orderDate"
        assert result[1]["ascending"] is False

    def test_convert_filter_expressions(self):




        """Test filter expression conversion."""
        filters = [
            "status = 'A'",
            "amount > 1000",
            "order_date >= today()",
        ]

        result = self.converter.convert_filters(filters)

        assert len(result) == 3
        assert result[0] == "status == 'A'"
        assert result[1] == "amount > 1000"
        assert result[2] == "orderDate >= DateTime.now().toLocal()"

    def test_convert_group_definitions(self):




        """Test group definition conversion."""
        groups = [
            {
                "level": 1,
                "column": "category",
                "header_height": 20,
                "trailer_height": 30,
            },
            {
                "level": 2,
                "column": "subcategory",
                "header_height": 15,
                "trailer_height": 20,
            },
        ]

        result = self.converter.convert_groups(groups)

        assert len(result) == 2
        assert result[0]["groupBy"] == "category"
        assert result[0]["level"] == 1
        assert result[1]["groupBy"] == "subcategory"
        assert result[1]["level"] == 2

    def test_convert_aggregate_functions(self):




        """Test aggregate function conversion."""
        aggregates = [
            {"function": "sum", "column": "amount", "group_level": 0},
            {"function": "count", "column": "*", "group_level": 1},
            {"function": "avg", "column": "price", "group_level": 0},
        ]

        result = self.converter.convert_aggregates(aggregates)

        assert len(result) == 3
        assert result[0]["type"] == "sum"
        assert result[0]["field"] == "amount"
        assert result[0]["scope"] == "total"
        assert result[1]["type"] == "count"
        assert result[1]["field"] == "*"
        assert result[1]["scope"] == "group"
        assert result[2]["type"] == "average"
        assert result[2]["field"] == "price"

    def test_generate_repository_class(self):




        """Test repository class generation for data operations."""
        dw_def = {
            "name": "dw_customer",
            "dataobject": "d_customer_list",
            "table": "customer",
            "key_columns": ["customer_id"],
            "updateable": True,
        }

        repo_code = self.converter.generate_repository_class(dw_def)

        assert "class DwCustomerRepository" in repo_code
        assert "Future<List<DwCustomerModel>> retrieve" in repo_code
        assert "Future<bool> update(DwCustomerModel model)" in repo_code
        assert "Future<bool> insert(DwCustomerModel model)" in repo_code
        assert "Future<bool> delete(int customerId)" in repo_code

    def test_convert_edit_styles(self):




        """Test edit style conversion for columns."""
        edit_styles = [
            {"column": "status", "style": "ddlb", "values": "A\tActive/I\tInactive"},
            {"column": "notes", "style": "edit", "limit": 500},
            {"column": "active", "style": "checkbox", "on": "Y", "off": "N"},
            {"column": "amount", "style": "editmask", "mask": "###,###.00"},
        ]

        result = self.converter.convert_edit_styles(edit_styles)

        assert result[0]["widget"] == "DropdownButton"
        assert result[0]["items"] == [{"value": "A", "label": "Active"}, {"value": "I", "label": "Inactive"}]
        assert result[1]["widget"] == "TextField"
        assert result[1]["maxLength"] == 500
        assert result[2]["widget"] == "Checkbox"
        assert result[2]["trueValue"] == "Y"
        assert result[2]["falseValue"] == "N"
        assert result[3]["widget"] == "TextFormField"
        assert result[3]["inputFormatter"] == "NumberFormat('#,##0.00')"

    def test_convert_column_properties(self):




        """Test detailed column property conversion."""
        column = {
            "name": "product_name",
            "type": "char(100)",
            "dbname": "product.name",
            "initial": '"New Product"',
            "protect": "0",
            "background.color": "16777215",
            "font.face": "Arial",
            "font.height": "-10",
            "alignment": "0",
        }

        result = self.converter.convert_column_properties(column)

        assert result["editable"] is True
        assert result["initialValue"] == "'New Product'"
        assert result["backgroundColor"] == "Colors.white"
        assert result["textStyle"]["fontFamily"] == "'Arial'"
        assert result["textStyle"]["fontSize"] == 13.3
        assert result["alignment"] == "TextAlign.left"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
