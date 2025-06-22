"""Tests for the event converter module."""

import pytest
from generate.converters.event_converter import EventConverter


class TestEventConverter:
    """Test cases for PowerBuilder to Dart event conversion."""

    def setup_method(self):


        

        """Set up test instances."""
        self.converter = EventConverter()

    def test_convert_event_signature(self):


        

        """Test event signature conversion."""
        # Simple event with no parameters
        event = {
            "name": "clicked",
            "returns": "long",
            "arguments": []
        }
        signature = self.converter.convert_event_signature(event)
        assert signature == "void onClicked()"

        # Event with parameters
        event = {
            "name": "modified",
            "returns": "integer",
            "arguments": [
                {"name": "newtext", "type": "string"},
                {"name": "oldtext", "type": "string"}
            ]
        }
        signature = self.converter.convert_event_signature(event)
        assert signature == "void onModified(String newtext, String oldtext)"

        # Event with return value
        event = {
            "name": "validation",
            "returns": "boolean",
            "arguments": [
                {"name": "data", "type": "string"}
            ]
        }
        signature = self.converter.convert_event_signature(event)
        assert signature == "bool onValidation(String data)"

    def test_convert_event_body(self):


        

        """Test event body conversion."""
        # Simple assignment
        pb_code = """
        string ls_name
        ls_name = "John Doe"
        messagebox("Info", ls_name)
        """
        dart_code = self.converter.convert_event_body(pb_code)
        assert "String lsName;" in dart_code
        assert "lsName = 'John Doe';" in dart_code
        assert "showDialog(" in dart_code

        # If statement
        pb_code = """
        if isnull(as_value) then
            return -1
        else
            return 0
        end if
        """
        dart_code = self.converter.convert_event_body(pb_code)
        assert "if (asValue == null) {" in dart_code
        assert "return -1;" in dart_code
        assert "} else {" in dart_code
        assert "return 0;" in dart_code

    def test_convert_control_events(self):


        

        """Test conversion of control-specific events."""
        # Button click event
        event_map = self.converter.get_control_event_mapping("commandbutton")
        assert event_map["clicked"] == "onPressed"
        
        # Text field events
        event_map = self.converter.get_control_event_mapping("singlelineedit")
        assert event_map["modified"] == "onChanged"
        assert event_map["getfocus"] == "onFocusChange"
        
        # List box events
        event_map = self.converter.get_control_event_mapping("listbox")
        assert event_map["selectionchanged"] == "onSelectionChanged"
        assert event_map["doubleclicked"] == "onDoubleTap"

    def test_convert_window_events(self):


        

        """Test conversion of window events."""
        event_map = self.converter.get_window_event_mapping()
        assert event_map["open"] == "initState"
        assert event_map["close"] == "dispose"
        assert event_map["resize"] == "onResize"
        assert event_map["activate"] == "onResume"
        assert event_map["deactivate"] == "onPause"

    def test_convert_expression(self):


        

        """Test PowerBuilder expression conversion."""
        # Variable references
        assert self.converter.convert_expression("ls_name") == "lsName"
        assert self.converter.convert_expression("ii_count") == "iiCount"
        assert self.converter.convert_expression("ab_flag") == "abFlag"
        
        # Property access
        assert self.converter.convert_expression("this.text") == "this.text"
        assert self.converter.convert_expression("dw_1.rowcount()") == "dw1.rowCount()"
        
        # Function calls
        assert self.converter.convert_expression("len(ls_text)") == "lsText.length"
        assert self.converter.convert_expression("trim(ls_value)") == "lsValue.trim()"
        assert self.converter.convert_expression("upper(ls_name)") == "lsName.toUpperCase()"
        assert self.converter.convert_expression("lower(ls_name)") == "lsName.toLowerCase()"
        
        # Null checks
        assert self.converter.convert_expression("isnull(ls_value)") == "lsValue == null"
        assert self.converter.convert_expression("not isnull(ls_value)") == "lsValue != null"
        
        # Operators
        assert self.converter.convert_expression("a = b") == "a == b"
        assert self.converter.convert_expression("a <> b") == "a != b"
        assert self.converter.convert_expression("a and b") == "a && b"
        assert self.converter.convert_expression("a or b") == "a || b"
        assert self.converter.convert_expression("not a") == "!a"

    def test_convert_messagebox(self):


        

        """Test MessageBox conversion to Flutter dialog."""
        # Simple message box
        pb_code = 'messagebox("Title", "Message")'
        dart_code = self.converter.convert_messagebox(pb_code)
        assert "showDialog(" in dart_code
        assert "AlertDialog(" in dart_code
        assert "title: Text('Title')" in dart_code
        assert "content: Text('Message')" in dart_code
        
        # Message box with buttons
        pb_code = 'messagebox("Confirm", "Are you sure?", Question!, YesNo!)'
        dart_code = self.converter.convert_messagebox(pb_code)
        assert "showDialog(" in dart_code
        assert "actions: [" in dart_code
        assert "TextButton(" in dart_code

    def test_convert_datawindow_operations(self):


        

        """Test DataWindow operation conversion."""
        # Retrieve
        assert self.converter.convert_datawindow_operation("dw_1.retrieve()") == "await dw1.retrieve()"
        assert self.converter.convert_datawindow_operation("dw_1.retrieve(ls_id)") == "await dw1.retrieve(lsId)"
        
        # Update
        assert self.converter.convert_datawindow_operation("dw_1.update()") == "await dw1.update()"
        
        # Row operations
        assert self.converter.convert_datawindow_operation("dw_1.insertrow(0)") == "dw1.insertRow(0)"
        assert self.converter.convert_datawindow_operation("dw_1.deleterow(li_row)") == "dw1.deleteRow(liRow)"
        
        # Get/Set item
        assert self.converter.convert_datawindow_operation("dw_1.getitemstring(1, 'name')") == "dw1.getItemString(1, 'name')"
        assert self.converter.convert_datawindow_operation("dw_1.setitem(1, 'name', ls_value)") == "dw1.setItem(1, 'name', lsValue)"

    def test_convert_loop_structures(self):


        

        """Test loop structure conversion."""
        # For loop
        pb_code = """
        for li_i = 1 to 10
            li_sum = li_sum + li_i
        next
        """
        dart_code = self.converter.convert_loop(pb_code)
        assert "for (int liI = 1; liI <= 10; liI++) {" in dart_code
        assert "liSum = liSum + liI;" in dart_code
        
        # While loop
        pb_code = """
        do while li_count > 0
            li_count = li_count - 1
        loop
        """
        dart_code = self.converter.convert_loop(pb_code)
        assert "while (liCount > 0) {" in dart_code
        assert "liCount = liCount - 1;" in dart_code

    def test_convert_case_statement(self):


        

        """Test case statement conversion."""
        pb_code = """
        choose case ls_type
            case "A"
                li_result = 1
            case "B", "C"
                li_result = 2
            case else
                li_result = 0
        end choose
        """
        dart_code = self.converter.convert_case_statement(pb_code)
        assert "switch (lsType) {" in dart_code
        assert "case 'A':" in dart_code
        assert "liResult = 1;" in dart_code
        assert "break;" in dart_code
        assert "case 'B':" in dart_code
        assert "case 'C':" in dart_code
        assert "default:" in dart_code

    def test_convert_try_catch(self):


        

        """Test try-catch conversion."""
        pb_code = """
        try
            li_result = integer(ls_value)
        catch (runtimeerror e)
            messagebox("Error", e.getmessage())
            return -1
        end try
        """
        dart_code = self.converter.convert_try_catch(pb_code)
        assert "try {" in dart_code
        assert "liResult = int.parse(lsValue);" in dart_code
        assert "} catch (e) {" in dart_code
        assert "showDialog(" in dart_code
        assert "return -1;" in dart_code

    def test_convert_script_call(self):


        

        """Test script/function call conversion."""
        # Simple function call
        assert self.converter.convert_script_call("wf_validate()") == "wfValidate()"
        assert self.converter.convert_script_call("of_process(ls_data)") == "ofProcess(lsData)"
        
        # Function with multiple parameters
        assert self.converter.convert_script_call("wf_update(li_id, ls_name, ld_amount)") == "wfUpdate(liId, lsName, ldAmount)"
        
        # Global function
        assert self.converter.convert_script_call("gf_get_setting('key')") == "gfGetSetting('key')"

    def test_convert_property_access(self):


        

        """Test property access conversion."""
        # Control properties
        assert self.converter.convert_property_access("sle_name.text") == "sleName.text"
        assert self.converter.convert_property_access("cb_save.enabled") == "cbSave.enabled"
        
        # Window properties
        assert self.converter.convert_property_access("this.title") == "this.title"
        assert self.converter.convert_property_access("parent.width") == "parent.width"

    def test_convert_array_access(self):


        

        """Test array access conversion."""
        assert self.converter.convert_array_access("la_values[1]") == "laValues[0]"  # 1-based to 0-based
        assert self.converter.convert_array_access("la_data[li_index]") == "laData[liIndex - 1]"
        assert self.converter.convert_array_access("la_grid[li_row, li_col]") == "laGrid[liRow - 1][liCol - 1]"

    def test_event_handler_generation(self):


        

        """Test complete event handler generation."""
        event = {
            "name": "clicked",
            "control": "cb_save",
            "returns": "long",
            "arguments": [],
            "body": """
                string ls_name
                ls_name = sle_name.text
                
                if len(trim(ls_name)) = 0 then
                    messagebox("Error", "Name is required")
                    return -1
                end if
                
                if wf_save_data(ls_name) = 1 then
                    messagebox("Success", "Data saved")
                    close(parent)
                else
                    messagebox("Error", "Save failed")
                end if
                
                return 0
            """
        }
        
        dart_code = self.converter.generate_event_handler(event)
        
        assert "void cbSaveClicked() async {" in dart_code
        assert "String lsName;" in dart_code
        assert "lsName = sleName.text;" in dart_code
        assert "if (lsName.trim().length == 0) {" in dart_code
        assert "await showDialog(" in dart_code
        assert "return;" in dart_code  # -1 converted to void return
        assert "if (await wfSaveData(lsName) == 1) {" in dart_code
        assert "Navigator.pop(context);" in dart_code  # close(parent) conversion

    def test_convert_special_functions(self):


        

        """Test conversion of special PowerBuilder functions."""
        # String functions
        assert self.converter.convert_function_call("mid(ls_text, 2, 3)") == "lsText.substring(1, 4)"
        assert self.converter.convert_function_call("pos(ls_text, 'abc')") == "lsText.indexOf('abc')"
        assert self.converter.convert_function_call("replace(ls_text, 'old', 'new')") == "lsText.replaceAll('old', 'new')"
        
        # Date functions
        assert self.converter.convert_function_call("today()") == "DateTime.now().toLocal().toIso8601String().split('T')[0]"
        assert self.converter.convert_function_call("now()") == "DateTime.now()"
        
        # Type conversion
        assert self.converter.convert_function_call("string(li_value)") == "liValue.toString()"
        assert self.converter.convert_function_call("integer(ls_value)") == "int.parse(lsValue)"
        assert self.converter.convert_function_call("double(ls_value)") == "double.parse(lsValue)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])