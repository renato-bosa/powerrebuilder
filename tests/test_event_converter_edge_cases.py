"""Test cases for EventConverter edge cases and complex expressions."""

from generate.converters.logic.event_converter import EventConverter
from generate.converters.utils.expression_converter import ExpressionConverter
from generate.converters.utils.type_converter import TypeConverter


class TestEventConverterEdgeCases:
    """Test edge cases for complex expressions in event conversion."""

    def setup_method(self):




        """Set up test fixtures."""
        self.type_converter = TypeConverter()
        self.expression_converter = ExpressionConverter(self.type_converter)
        self.event_converter = EventConverter(self.type_converter, self.expression_converter)

    def test_complex_return_with_method_chaining(self):




        """Test complex return statements with method chaining."""
        # Test case 1: Method chaining
        statement = "return Parent.GetWindow().GetFrame().GetData()"
        result = self.event_converter._convert_return_statement(statement, "String")
        # Should contain converted method chain
        assert "widget" in result or "parent" in result.lower()
        assert "getWindow" in result or "GetWindow" in result
        assert "return" in result

        # Test case 2: DataWindow method chaining
        statement = "return dw_1.GetItemNumber(GetCurrentRow(), \"amount\") * GetTaxRate()"
        result = self.event_converter._convert_complex_return(statement, "double")
        assert "dw1.getItemNumber" in result
        assert "getCurrentRow()" in result
        assert "getTaxRate()" in result

    def test_iif_expression_conversion(self):




        """Test IIF (ternary) expression conversion."""
        statement = 'return IIF(IsValid(dw_1), dw_1.GetItemString(1, "status"), "N/A")'
        result = self.event_converter._convert_complex_return(statement, "String")
        assert "?" in result
        assert ":" in result
        assert "isValid(dw1)" in result
        assert '"N/A"' in result

    def test_array_access_with_complex_indices(self):




        """Test array access with complex index expressions."""
        # Test case 1: Multi-dimensional array
        lhs = "data_array[row_index][col_index]"
        rhs = "new_value"
        result = self.event_converter._convert_array_assignment(lhs, rhs)
        assert "dataArray" in result
        assert "rowIndex" in result or "row_index" in result
        assert "colIndex" in result or "col_index" in result
        assert "newValue" in result or "new_value" in result

        # Test case 2: Array with expression index
        lhs = "menu_items[GetCurrentIndex() + offset_value]"
        rhs = "selected_item"
        result = self.event_converter._convert_array_assignment(lhs, rhs)
        assert "menuItems[getCurrentIndex() + offsetValue]" in result

    def test_structure_member_access(self):




        """Test structure member access patterns."""
        # Test case 1: Nested structure access
        expr = "employee_data[current_emp].address.street"
        result = self.event_converter._convert_array_access(expr)
        assert "employeeData[currentEmp].address.street" in result

        # Test case 2: Deep nesting
        expr = "company.departments[dept_id].employees[emp_index].salary"
        result = self.event_converter._convert_property_chain(expr)
        assert "company.departments.employees.salary" in result

    def test_type_casting_expressions(self):




        """Test PowerBuilder type casting conversion."""
        # Test case 1: Integer casting
        expr = "Integer(String(decimal_value * 100))"
        result = self.event_converter._convert_type_cast(expr)
        assert "int.parse" in result
        assert "toString()" in result

        # Test case 2: Nested casting
        expr = "Long(dw_1.GetItemString(row, \"id\"))"
        result = self.event_converter._convert_type_cast(expr)
        assert "int.parse" in result

        # Test case 3: Decimal with null handling
        expr = 'Dec(IsNull(raw_value, "0"))'
        result = self.event_converter._convert_type_cast(expr)
        assert "double.parse" in result

    def test_complex_assignment_with_operators(self):




        """Test complex assignment expressions."""
        # Test case 1: Compound assignment with expression
        statement = "total_amount += GetItemAmount(row) * (1 + GetTaxRate() / 100)"
        result = self.event_converter._convert_complex_assignment(statement)
        assert "totalAmount" in result
        assert "getItemAmount" in result
        assert "getTaxRate" in result

        # Test case 2: Bitwise operations
        statement = "flags &= ~(READONLY_FLAG | SYSTEM_FLAG)"
        result = self.event_converter._convert_complex_assignment(statement)
        assert "flags = flags &" in result
        assert "readOnlyFlag" in result
        assert "systemFlag" in result

        # Test case 3: String concatenation
        statement = 'message_text += "Row " + String(row_num) + ": " + GetErrorMessage(code)'
        result = self.event_converter._convert_complex_assignment(statement)
        assert "Row" in result
        assert "${" in result  # String interpolation

    def test_complex_conditional_expressions(self):




        """Test complex conditional expression conversion."""
        # Test case 1: Mixed AND/OR with parentheses
        condition = '(status = "ACTIVE" OR status = "PENDING") AND (amount > 1000 OR priority = "HIGH")'
        result = self.event_converter._convert_complex_condition(condition)
        assert "(status == " in result
        assert " || " in result
        assert " && " in result

        # Test case 2: Nested NOT operators
        condition = "NOT (IsNull(value) OR NOT IsValid(object))"
        result = self.event_converter._convert_complex_condition(condition)
        assert "!(value == null || !(object != null))" in result

    def test_method_call_conversion(self):




        """Test method call conversion with various patterns."""
        # Test case 1: Method with complex parameters
        statement = "ProcessData(GetRow(current_index), CalculateValue(base * rate), \"STATUS\")"
        result = self.event_converter._convert_method_call(statement)
        assert "processData(" in result
        assert "getRow(currentIndex)" in result
        assert "calculateValue(base * rate)" in result

        # Test case 2: Chained method calls
        statement = "dw_1.SetFilter(\"status='A'\").Filter().RowCount()"
        result = self.event_converter._convert_method_call(statement)
        assert "dw1.setFilter" in result
        assert ".filter()" in result
        assert ".rowCount()" in result

    def test_event_specific_patterns(self):




        """Test event-specific conversion patterns."""
        # Test case 1: DataWindow itemchanged event
        body = [
            'IF dwo.name = "amount" THEN',
            '    IF Double(data) > GetCreditLimit(GetItemNumber(row, "customer_id")) THEN',
            '        MessageBox("Error", "Amount exceeds credit limit")',
            "        RETURN 1",
            "    END IF",
            "END IF",
        ]
        result = self.event_converter._convert_event_body(body, "itemchanged", "int", {0: "0", 1: "1"})
        assert any("if (dwo.name == " in line for line in result)
        assert any("double.parse" in line for line in result)
        assert any("showDialog" in line for line in result)

        # Test case 2: closequery event with save logic
        body = [
            "IF DataModified() THEN",
            '    CHOOSE CASE MessageBox("Save", "Save changes?", Question!, YesNoCancel!)',
            "        CASE 1",
            "            IF NOT Save() THEN RETURN 1",
            "        CASE 3",
            "            RETURN 1",
            "    END CHOOSE",
            "END IF",
        ]
        result = self.event_converter._convert_event_body(body, "closequery", "bool", {0: "true", 1: "false"})
        assert any("dataModified()" in line for line in result)

    def test_string_interpolation_conversion(self):




        """Test string concatenation to interpolation conversion."""
        # Test case 1: Simple concatenation
        expr = '"Row " + String(row_num) + ": " + error_msg'
        result = self.event_converter._convert_string_concat(expr)
        assert "'Row ${rowNum}: ${errorMsg}'" in result or "Row" in result

        # Test case 2: Complex concatenation
        expr = '"Total: " + String(amount * rate) + " (" + percent + "%)"'
        result = self.event_converter._convert_string_concat(expr)
        assert "Total:" in result
        assert "${" in result

    def test_edge_case_error_handling(self):




        """Test error handling for edge cases."""
        # Test case 1: Invalid return expression
        statement = "return ComplexExpression(That.Cannot.Be.Parsed)"
        result = self.event_converter._convert_return_statement(statement, "dynamic")
        assert "return" in result
        assert ("TODO" in result or "null" in result)

        # Test case 2: Invalid assignment
        statement = "invalid[syntax] := not_valid"
        result = self.event_converter._convert_assignment_statement(statement)
        assert "TODO" in result
