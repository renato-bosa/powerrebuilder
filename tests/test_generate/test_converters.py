#!/usr/bin/env python3
"""Comprehensive test suite for Generate converters."""

import pytest
from model.ast import (
    ASTAssignment,
    BinaryExpression,
    Block,
    BooleanLiteral,
    CaseStatement,
    Event,
    ForLoop,
    FunctionDefinition,
    IfStatement,
    IntegerLiteral,
    Parameter,
    ReturnStatement,
    StringLiteral,
    Type,
    Variable,
    WhileLoop,
    ArrayAccess,
    ColumnReference,
    DataWindow,
    Window,
    Button,
    TextBox,
    ComboBox,
    DataGrid
)
from model.ast.types import BasicType, TypeCategory
from model.ast.functions import Signature
from generate.converters.ast_converter import ASTConverter
from generate.converters.datawindow_converter import DataWindowConverter
from generate.converters.event_converter import EventConverter
from generate.converters.expression_converter import ExpressionConverter
from generate.converters.type_converter import TypeConverter
from generate.converters.ui_converter import UIConverter


class TestTypeConverter:
    """Test PowerBuilder to Dart type conversion."""
    
    def test_basic_type_conversion(self):
        """Test conversion of basic types."""
        converter = TypeConverter()
        
        test_cases = [
            (Type(name="integer", category=TypeCategory.BASIC), "int"),
            (Type(name="long", category=TypeCategory.BASIC), "int"),
            (Type(name="string", category=TypeCategory.BASIC), "String"),
            (Type(name="boolean", category=TypeCategory.BASIC), "bool"),
            (Type(name="real", category=TypeCategory.BASIC), "double"),
            (Type(name="decimal", category=TypeCategory.BASIC), "double"),
            (Type(name="date", category=TypeCategory.BASIC), "DateTime"),
            (Type(name="time", category=TypeCategory.BASIC), "DateTime"),
            (Type(name="datetime", category=TypeCategory.BASIC), "DateTime"),
        ]
        
        for pb_type, expected_dart in test_cases:
            result = converter.convert_type(pb_type)
            assert result == expected_dart
    
    def test_array_type_conversion(self):
        """Test conversion of array types."""
        converter = TypeConverter()
        
        # Single dimensional array
        int_array = Type(name="integer", category=TypeCategory.BASIC, is_array=True)
        result = converter.convert_type(int_array)
        assert result == "List<int>"
        
        # String array
        string_array = Type(name="string", category=TypeCategory.BASIC, is_array=True)
        result = converter.convert_type(string_array)
        assert result == "List<String>"
    
    def test_custom_type_conversion(self):
        """Test conversion of custom types."""
        converter = TypeConverter()
        
        # Custom type should remain as-is
        custom_type = Type(name="n_custom_object", category=TypeCategory.CUSTOM)
        result = converter.convert_type(custom_type)
        assert result == "NCustomObject"  # Should convert to PascalCase
    
    def test_nullable_type_conversion(self):
        """Test conversion of nullable types."""
        converter = TypeConverter()
        
        nullable_int = Type(name="integer", category=TypeCategory.BASIC, is_nullable=True)
        result = converter.convert_type(nullable_int)
        assert result == "int?"
        
        nullable_string = Type(name="string", category=TypeCategory.BASIC, is_nullable=True)
        result = converter.convert_type(nullable_string)
        assert result == "String?"


class TestExpressionConverter:
    """Test expression conversion to Dart."""
    
    def test_literal_conversion(self):
        """Test conversion of literal values."""
        converter = ExpressionConverter()
        
        # Integer literal
        int_lit = IntegerLiteral(value=42)
        assert converter.convert_expression(int_lit) == "42"
        
        # String literal
        str_lit = StringLiteral(value="Hello World")
        assert converter.convert_expression(str_lit) == '"Hello World"'
        
        # Boolean literals
        true_lit = BooleanLiteral(value=True)
        assert converter.convert_expression(true_lit) == "true"
        
        false_lit = BooleanLiteral(value=False)
        assert converter.convert_expression(false_lit) == "false"
    
    def test_variable_conversion(self):
        """Test conversion of variable references."""
        converter = ExpressionConverter()
        
        var = Variable(name="li_count")
        assert converter.convert_expression(var) == "liCount"  # camelCase conversion
        
        var_with_prefix = Variable(name="this.width")
        assert converter.convert_expression(var_with_prefix) == "this.width"
    
    def test_binary_expression_conversion(self):
        """Test conversion of binary expressions."""
        converter = ExpressionConverter()
        
        # Arithmetic expression
        expr = BinaryExpression(
            left=Variable(name="a"),
            operator="+",
            right=IntegerLiteral(value=10)
        )
        assert converter.convert_expression(expr) == "a + 10"
        
        # Comparison expression
        comp = BinaryExpression(
            left=Variable(name="count"),
            operator=">",
            right=IntegerLiteral(value=0)
        )
        assert converter.convert_expression(comp) == "count > 0"
        
        # PowerBuilder specific operators
        pb_and = BinaryExpression(
            left=Variable(name="a"),
            operator="and",
            right=Variable(name="b")
        )
        assert converter.convert_expression(pb_and) == "a && b"
        
        pb_or = BinaryExpression(
            left=Variable(name="x"),
            operator="or",
            right=Variable(name="y")
        )
        assert converter.convert_expression(pb_or) == "x || y"
    
    def test_array_access_conversion(self):
        """Test conversion of array access."""
        converter = ExpressionConverter()
        
        arr_access = ArrayAccess(
            array=Variable(name="items"),
            index=IntegerLiteral(value=0)
        )
        assert converter.convert_expression(arr_access) == "items[0]"
        
        # Multi-dimensional array
        multi_arr = ArrayAccess(
            array=ArrayAccess(
                array=Variable(name="matrix"),
                index=Variable(name="i")
            ),
            index=Variable(name="j")
        )
        assert converter.convert_expression(multi_arr) == "matrix[i][j]"


class TestEventConverter:
    """Test event conversion to Dart."""
    
    def test_simple_event_conversion(self):
        """Test conversion of simple events."""
        converter = EventConverter()
        
        # Button click event
        click_event = Event(
            name="clicked",
            parameters=[],
            body=Block(statements=[
                ReturnStatement(value=IntegerLiteral(value=0))
            ])
        )
        
        result = converter.convert_event(click_event, "button")
        assert "onPressed:" in result
        assert "() {" in result
        assert "return 0;" in result
    
    def test_event_with_parameters(self):
        """Test conversion of events with parameters."""
        converter = EventConverter()
        
        # Custom event with parameters
        custom_event = Event(
            name="itemchanged",
            parameters=[
                Parameter(name="row", type=Type(name="long", category=TypeCategory.BASIC)),
                Parameter(name="dwo", type=Type(name="dwobject", category=TypeCategory.CUSTOM))
            ],
            body=Block(statements=[])
        )
        
        result = converter.convert_event(custom_event, "datawindow")
        assert "onItemChanged:" in result
        assert "(int row, DwObject dwo)" in result
    
    def test_event_mapping(self):
        """Test PowerBuilder to Flutter event mapping."""
        converter = EventConverter()
        
        # Common PowerBuilder events
        assert converter.get_flutter_event_name("clicked", "button") == "onPressed"
        assert converter.get_flutter_event_name("doubleclicked", "any") == "onDoubleTap"
        assert converter.get_flutter_event_name("getfocus", "textbox") == "onFocusChange"
        assert converter.get_flutter_event_name("modified", "textbox") == "onChanged"


class TestUIConverter:
    """Test UI control conversion."""
    
    def test_button_conversion(self):
        """Test button conversion to Flutter."""
        converter = UIConverter()
        
        button = Button(
            name="cb_ok",
            text="OK",
            x=10,
            y=20,
            width=100,
            height=30,
            enabled=True,
            visible=True
        )
        
        result = converter.convert_control(button)
        assert "ElevatedButton" in result
        assert "onPressed:" in result
        assert 'Text("OK")' in result
    
    def test_textbox_conversion(self):
        """Test textbox conversion to Flutter."""
        converter = UIConverter()
        
        textbox = TextBox(
            name="sle_name",
            text="",
            x=10,
            y=50,
            width=200,
            height=25,
            enabled=True,
            visible=True,
            max_length=50
        )
        
        result = converter.convert_control(textbox)
        assert "TextField" in result
        assert "controller:" in result
        assert "maxLength: 50" in result
    
    def test_combobox_conversion(self):
        """Test combobox conversion to Flutter."""
        converter = UIConverter()
        
        combo = ComboBox(
            name="ddlb_status",
            items=["Active", "Inactive", "Pending"],
            selected_index=0,
            x=10,
            y=100,
            width=150,
            height=25
        )
        
        result = converter.convert_control(combo)
        assert "DropdownButton" in result
        assert "value:" in result
        assert "items:" in result
    
    def test_window_conversion(self):
        """Test window conversion to Flutter screen."""
        converter = UIConverter()
        
        window = Window(
            name="w_main",
            title="Main Window",
            width=800,
            height=600,
            controls=[
                Button(name="cb_ok", text="OK", x=10, y=10, width=80, height=25)
            ]
        )
        
        result = converter.convert_window(window)
        assert "class WMainScreen extends StatefulWidget" in result
        assert "Scaffold" in result
        assert 'appBar: AppBar(title: Text("Main Window"))' in result
        assert "ElevatedButton" in result


class TestDataWindowConverter:
    """Test DataWindow conversion."""
    
    def test_datawindow_to_datagrid(self):
        """Test DataWindow to DataGrid conversion."""
        converter = DataWindowConverter()
        
        datawindow = DataWindow(
            name="d_employee",
            sql_select="SELECT emp_id, emp_name FROM employee",
            columns=[
                {"name": "emp_id", "type": "integer", "label": "ID"},
                {"name": "emp_name", "type": "string", "label": "Name"}
            ]
        )
        
        result = converter.convert_datawindow(datawindow)
        assert "DataTable" in result
        assert "columns: [" in result
        assert 'DataColumn(label: Text("ID"))' in result
        assert 'DataColumn(label: Text("Name"))' in result
        assert "rows:" in result
    
    def test_datawindow_with_computed_fields(self):
        """Test DataWindow with computed fields."""
        converter = DataWindowConverter()
        
        datawindow = DataWindow(
            name="d_sales",
            columns=[
                {"name": "quantity", "type": "integer"},
                {"name": "price", "type": "decimal"},
                {"name": "total", "type": "decimal", "computed": "quantity * price"}
            ]
        )
        
        result = converter.convert_datawindow(datawindow)
        # Should handle computed fields
        assert "DataColumn" in result


class TestASTConverter:
    """Test full AST conversion."""
    
    def test_function_conversion(self):
        """Test function definition conversion."""
        converter = ASTConverter()
        
        func = FunctionDefinition(
            signature=Signature(
                name="calculate_total",
                return_type=Type(name="decimal", category=TypeCategory.BASIC),
                parameters=[
                    Parameter(name="quantity", type=Type(name="integer", category=TypeCategory.BASIC)),
                    Parameter(name="price", type=Type(name="decimal", category=TypeCategory.BASIC))
                ]
            ),
            body=Block(statements=[
                ReturnStatement(
                    value=BinaryExpression(
                        left=Variable(name="quantity"),
                        operator="*",
                        right=Variable(name="price")
                    )
                )
            ])
        )
        
        result = converter.convert_function(func)
        assert "double calculateTotal(int quantity, double price)" in result
        assert "return quantity * price;" in result
    
    def test_if_statement_conversion(self):
        """Test if statement conversion."""
        converter = ASTConverter()
        
        if_stmt = IfStatement(
            condition=BinaryExpression(
                left=Variable(name="count"),
                operator=">",
                right=IntegerLiteral(value=0)
            ),
            then_branch=Block(statements=[
                ASTAssignment(
                    target=Variable(name="result"),
                    value=StringLiteral(value="Found")
                )
            ]),
            else_branch=Block(statements=[
                ASTAssignment(
                    target=Variable(name="result"),
                    value=StringLiteral(value="Not found")
                )
            ])
        )
        
        result = converter.convert_statement(if_stmt)
        assert "if (count > 0)" in result
        assert 'result = "Found";' in result
        assert "else" in result
        assert 'result = "Not found";' in result
    
    def test_for_loop_conversion(self):
        """Test for loop conversion."""
        converter = ASTConverter()
        
        for_loop = ForLoop(
            variable="i",
            start=IntegerLiteral(value=1),
            end=IntegerLiteral(value=10),
            step=IntegerLiteral(value=1),
            body=Block(statements=[])
        )
        
        result = converter.convert_statement(for_loop)
        assert "for (int i = 1; i <= 10; i++)" in result
    
    def test_case_statement_conversion(self):
        """Test case statement conversion."""
        converter = ASTConverter()
        
        case_stmt = CaseStatement(
            expression=Variable(name="status"),
            cases=[
                (StringLiteral(value="A"), Block(statements=[])),
                (StringLiteral(value="B"), Block(statements=[]))
            ],
            default_body=Block(statements=[])
        )
        
        result = converter.convert_statement(case_stmt)
        assert "switch (status)" in result
        assert 'case "A":' in result
        assert 'case "B":' in result
        assert "default:" in result


class TestConverterIntegration:
    """Test converter integration scenarios."""
    
    def test_full_window_conversion(self):
        """Test converting a complete window with controls and events."""
        ui_converter = UIConverter()
        event_converter = EventConverter()
        
        # Create a window with button and click event
        window = Window(
            name="w_login",
            title="Login",
            width=400,
            height=300,
            controls=[
                TextBox(name="sle_username", x=50, y=50, width=200, height=25),
                TextBox(name="sle_password", x=50, y=100, width=200, height=25),
                Button(name="cb_login", text="Login", x=50, y=150, width=100, height=30)
            ],
            events=[
                Event(
                    name="cb_login_clicked",
                    parameters=[],
                    body=Block(statements=[])
                )
            ]
        )
        
        result = ui_converter.convert_window(window)
        assert "WLoginScreen" in result
        assert "TextField" in result  # Username and password fields
        assert "ElevatedButton" in result  # Login button
    
    def test_datawindow_integration(self):
        """Test DataWindow with full conversion."""
        dw_converter = DataWindowConverter()
        
        datawindow = DataWindow(
            name="d_customer_list",
            sql_select="SELECT id, name, email, status FROM customers",
            columns=[
                {"name": "id", "type": "integer", "label": "ID"},
                {"name": "name", "type": "string", "label": "Customer Name"},
                {"name": "email", "type": "string", "label": "Email"},
                {"name": "status", "type": "string", "label": "Status"}
            ],
            retrieve_args=["status_filter"]
        )
        
        result = dw_converter.convert_datawindow(datawindow)
        assert "DataTable" in result
        assert "Customer Name" in result
        assert len([line for line in result.split('\n') if 'DataColumn' in line]) == 4