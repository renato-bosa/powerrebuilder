"""Special opcode formatter for PowerBuilder decompiled code.

This module provides enhanced formatting for specific opcodes that require
special handling to produce more readable and meaningful output.
"""

import logging
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)


class SpecialOpcodeFormatter:
    """Formats special opcodes for better readability in decompiled output."""
    
    def __init__(self, string_table: dict[int, str] = None, function_table: dict[int, str] = None, field_table: dict[int, str] = None) -> None:

    
        """Initialize the special opcode formatter.
        
        Args:
            string_table: Map of string indices to string values
            function_table: Map of function indices to function names
            field_table: Map of field indices to field names
        """
        self.strings = string_table or {}
        self.functions = function_table or {}
        self.fields = field_table or {}
        
        # PowerBuilder system functions
        self.system_functions = {
            0x00: "MessageBox", 0x01: "IsNull", 0x02: "IsValid", 0x03: "SetNull", 0x04: "String", 0x05: "Integer", 0x06: "Long", 0x07: "Double", 0x08: "Date", 0x09: "Time", 0x0A: "DateTime", 0x0B: "Upper", 0x0C: "Lower", 0x0D: "Trim", 0x0E: "Len", 0x0F: "Mid", 0x10: "Left", 0x11: "Right", 0x12: "Pos", 0x13: "Replace", }
        
        # PowerBuilder events
        self.event_names = {
            0x00: "clicked", 0x01: "doubleclicked", 0x02: "rbuttondown", 0x03: "constructor", 0x04: "destructor", 0x05: "open", 0x06: "close", 0x07: "activate", 0x08: "deactivate", 0x09: "resize", 0x0A: "key", 0x0B: "timer", }
        
    def format_opcode(self, opcode: str, operands: list, stack_context: list = None) -> str | None:

        
        
        
        """Format a special opcode into readable output.
        
        Args:
            opcode: The opcode name
            operands: List of operand values
            stack_context: Optional stack context for complex operations
            
        Returns:
            Formatted string or None if opcode doesn't need special formatting
        """
        # Database operations
        if opcode.startswith("DB"):
            return self._format_database_op(opcode, operands, stack_context)
            
        # Control flow operations
        if opcode in ["JUMP", "JUMPTRUE", "JUMPFALSE", "GOSUB", "RETURN_SUB"]:
            return self._format_control_flow(opcode, operands)
            
        # Event operations (must come before function calls check)
        if opcode == "EVENTCALL" or "EVENT" in opcode:
            return self._format_event_call(operands)
            
        # System function calls
        if opcode == "SYSFUNCCALL" and operands:
            return self._format_system_call(operands[0], stack_context)
            
        # Function calls
        if "FUNCCALL" in opcode or "CALL" in opcode:
            return self._format_function_call(opcode, operands, stack_context)
            
        # Array operations
        if "ARRAY" in opcode or opcode in ["LOWERBOUND", "UPPERBOUND"]:
            return self._format_array_op(opcode, operands, stack_context)
            
        # Exception handling
        if opcode in ["PUSH_TRY", "POP_TRY", "CATCH_EXCEPTION", "THROW_EXCEPTION"]:
            return self._format_exception_op(opcode, operands)
            
        # Object creation/destruction
        if opcode in ["CREATE_EXT_OBJ", "CREATE_USING", "DESTROY"]:
            return self._format_object_lifecycle(opcode, operands, stack_context)
            
        # Special PowerBuilder constructs
        if opcode == "HALT":
            return self._format_halt(operands)
        elif opcode == "EXIT":
            return "EXIT"
        elif opcode == "CHOOSE":
            return self._format_choose(stack_context)
        elif opcode == "DYNAMIC":
            return self._format_dynamic(stack_context)
            
        # Type operations
        if opcode in ["TYPEOF", "INSTANCEOF", "CLASSNAME"]:
            return self._format_type_op(opcode, operands, stack_context)
            
        # Advanced string operations
        if opcode in ["MATCH", "REPLACE_ALL", "SPLIT", "JOIN"]:
            return self._format_string_op(opcode, operands, stack_context)
            
        return None
        
    def _format_database_op(self, opcode: str, operands: list, stack_context: list = None) -> str:

        
        
        
        """Format database operations."""
        if opcode == "DBOPEN":
            cursor_name = self._get_cursor_name(operands)
            return f"OPEN {cursor_name}"
            
        elif opcode == "DBCLOSE":
            cursor_name = self._get_cursor_name(operands)
            return f"CLOSE {cursor_name}"
            
        elif opcode == "DBFETCH":
            cursor_name = self._get_cursor_name(operands)
            # In real implementation, we'd get variable list from stack
            return f"FETCH {cursor_name} INTO :variables"
            
        elif opcode == "DBSELECT":
            # Format: DBSELECT num_cols, cursor_id, sql_string_id
            if len(operands) >= 3:
                num_cols = operands[0]
                sql_idx = operands[2]
                sql = self.strings.get(sql_idx, f"sql_{sql_idx}")
                return f"SELECT /* {num_cols} columns */ {sql}"
            return "SELECT /* embedded SQL */"
            
        elif opcode == "DBINSERT":
            table_info = self._get_table_info(operands)
            return f"INSERT INTO {table_info}"
            
        elif opcode == "DBUPDATE":
            table_info = self._get_table_info(operands)
            return f"UPDATE {table_info} SET ..."
            
        elif opcode == "DBDELETE":
            table_info = self._get_table_info(operands)
            return f"DELETE FROM {table_info}"
            
        elif opcode == "DBEXECUTE":
            if operands and len(operands) > 0:
                sql_idx = operands[0]
                sql = self.strings.get(sql_idx, f"sql_{sql_idx}")
                return f"EXECUTE IMMEDIATE {sql}"
            return "EXECUTE IMMEDIATE"
            
        elif opcode == "DBCOMMIT":
            return "COMMIT"
            
        elif opcode == "DBROLLBACK":
            return "ROLLBACK"
            
        elif opcode == "DBSTART":
            return "/* Start transaction */"
            
        elif opcode == "DBSTOP":
            return "/* End transaction */"
            
        elif opcode == "DBPREPARE":
            return "PREPARE sql_statement FROM :sql_string"
            
        elif opcode in ["DBSELECTBLOB", "DBUPDATEBLOB"]:
            action = "SELECTBLOB" if "SELECT" in opcode else "UPDATEBLOB"
            return f"{action} /* blob column operation */"
            
        return f"/* Database operation: {opcode} */"
    
    def _format_system_call(self, func_idx: int, stack_context: list = None) -> str:

    
        
    
        """Format system function calls."""
        func_name = self.system_functions.get(func_idx, f"SystemFunction_{func_idx}")
        
        # Determine argument count based on function
        arg_info = {
            "MessageBox": 2, # title, message
            "IsNull": 1, # value
            "IsValid": 1, # object
            "SetNull": 1, # variable
            "String": 1, # value
            "Integer": 1, # value
            "Long": 1, # value
            "Double": 1, # value
            "Date": 1, # value
            "Time": 1, # value
            "DateTime": 1, # value
            "Upper": 1, # string
            "Lower": 1, # string
            "Trim": 1, # string
            "Len": 1, # string
            "Mid": 3, # string, start, length
            "Left": 2, # string, length
            "Right": 2, # string, length
            "Pos": 2, # string, substring
            "Replace": 3, # string, old, new
        }
        
        expected_args = arg_info.get(func_name, 1)
        
        # Build arguments from stack context
        args = []
        if stack_context and len(stack_context) >= expected_args:
            args = stack_context[-expected_args:]
        
        arg_list = ", ".join(args) if args else ""
        return f"{func_name}({arg_list})"
    
    def _format_halt(self, operands: list) -> str:

    
        
    
        """Format HALT statement."""
        if operands and operands[0] == 1:
            return "HALT CLOSE"
        return "HALT"
    
    def _format_choose(self, stack_context: list = None) -> str:

    
        
    
        """Format CHOOSE CASE construct."""
        if stack_context and stack_context:
            expr = stack_context[-1]
            return f"CHOOSE CASE {expr}"
        return "CHOOSE CASE expression"
    
    def _format_dynamic(self, stack_context: list = None) -> str:

    
        
    
        """Format DYNAMIC property/method access."""
        if stack_context and len(stack_context) >= 2:
            obj = stack_context[-2]
            prop = stack_context[-1]
            return f"{obj}.DYNAMIC {prop}"
        return "DYNAMIC property_access"
    
    def _format_object_lifecycle(self, opcode: str, operands: list, stack_context: list = None) -> str:

    
        
    
        """Format object creation/destruction operations."""
        if opcode == "CREATE_EXT_OBJ":
            if operands:
                class_idx = operands[0]
                class_name = self.strings.get(class_idx, f"class_{class_idx}")
                return f"CREATE {class_name}"
            return "CREATE object"
            
        elif opcode == "CREATE_USING":
            if stack_context and stack_context:
                class_name = stack_context[-1]
                return f"CREATE USING {class_name}"
            return "CREATE USING class_name"
            
        elif opcode == "DESTROY":
            if stack_context and stack_context:
                obj = stack_context[-1]
                return f"DESTROY {obj}"
            return "DESTROY object"
            
        return f"/* Object lifecycle: {opcode} */"
    
    def _format_type_op(self, opcode: str, operands: list, stack_context: list = None) -> str:

    
        
    
        """Format type operations."""
        if not stack_context:
            return f"/* {opcode} */"
            
        obj = stack_context[-1] if stack_context else "object"
        
        if opcode == "TYPEOF":
            return f"TypeOf({obj})"
        elif opcode == "INSTANCEOF":
            if len(stack_context) >= 2:
                type_name = stack_context[-2]
                return f"{obj} INSTANCEOF {type_name}"
            return f"{obj} INSTANCEOF type"
        elif opcode == "CLASSNAME":
            return f"ClassName({obj})"
            
        return f"/* Type operation: {opcode} */"
    
    def _format_string_op(self, opcode: str, operands: list, stack_context: list = None) -> str:

    
        
    
        """Format advanced string operations."""
        if not stack_context:
            return f"/* {opcode} */"
            
        if opcode == "MATCH":
            if len(stack_context) >= 2:
                string = stack_context[-2]
                pattern = stack_context[-1]
                return f"Match({string}, {pattern})"
            return "Match(string, pattern)"
            
        elif opcode == "REPLACE_ALL":
            if len(stack_context) >= 3:
                string = stack_context[-3]
                old_val = stack_context[-2]
                new_val = stack_context[-1]
                return f"ReplaceAll({string}, {old_val}, {new_val})"
            return "ReplaceAll(string, old, new)"
            
        elif opcode == "SPLIT":
            if len(stack_context) >= 2:
                string = stack_context[-2]
                delimiter = stack_context[-1]
                return f"Split({string}, {delimiter})"
            return "Split(string, delimiter)"
            
        elif opcode == "JOIN":
            if len(stack_context) >= 2:
                array = stack_context[-2]
                delimiter = stack_context[-1]
                return f"Join({array}, {delimiter})"
            return "Join(array, delimiter)"
            
        return f"/* String operation: {opcode} */"
        
    def _format_control_flow(self, opcode: str, operands: list) -> str:

        
        
        
        """Format control flow operations."""
        if not operands:
            return f"/* {opcode} */"
            
        offset = operands[0]
        if opcode == "JUMP":
            return f"goto L_{offset:04X}"
        elif opcode == "JUMPTRUE":
            return f"if (condition) goto L_{offset:04X}"
        elif opcode == "JUMPFALSE":
            return f"if not (condition) goto L_{offset:04X}"
        elif opcode == "GOSUB":
            return f"gosub L_{offset:04X}"
            
        return f"/* {opcode} to offset {offset} */"
        
    def _format_function_call(self, opcode: str, operands: list, stack_context: list = None) -> str:

        
        
        
        """Format function calls."""
        if not operands:
            return f"/* {opcode} */"
            
        func_idx = operands[0]
        func_name = self.functions.get(func_idx, f"function_{func_idx}")
        
        # Determine function type
        if "GLOB" in opcode:
            call_type = "global"
        elif "DLL" in opcode:
            call_type = "external"
        elif "SYS" in opcode:
            call_type = "system"
        elif "DOT" in opcode:
            call_type = "method"
        elif "CLASS" in opcode:
            call_type = "class"
        else:
            call_type = ""
            
        # Format argument count if available
        arg_count = ""
        if len(operands) > 1:
            arg_count = f" /* {operands[1]} args */"
            
        if call_type:
            return f"{func_name}(){arg_count} /* {call_type} function */"
        else:
            return f"{func_name}(){arg_count}"
            
    def _format_array_op(self, opcode: str, operands: list, stack_context: list = None) -> str:

            
        
            
        """Format array operations."""
        if opcode == "ARRAYLIST":
            if operands:
                size = operands[0]
                return f"/* Create array list with {size} elements */"
            return "/* Create array list */"
            
        elif opcode == "BUILD_UNBOUNDED_ARRAYLIST":
            return "/* Build unbounded array */"
            
        elif opcode == "BUILD_BOUNDED_ARRAYLIST":
            return "/* Build bounded array */"
            
        elif "TRANSFORM" in opcode and "ARRAY" in opcode:
            return f"/* Array transformation: {opcode} */"
            
        elif "BOUND" in opcode:
            if "LOWER" in opcode:
                return "LowerBound(array, dimension)"
            elif "UPPER" in opcode:
                return "UpperBound(array, dimension)"
            else:
                return f"/* Array bound operation: {opcode} */"
                
        return f"/* Array operation: {opcode} */"
        
    def _format_exception_op(self, opcode: str, operands: list) -> str:

        
        
        
        """Format exception handling operations."""
        if opcode == "PUSH_TRY":
            return "TRY"
        elif opcode == "POP_TRY":
            return "/* End TRY block */"
        elif opcode == "CATCH_EXCEPTION":
            if operands:
                exc_type = operands[0]
                return f"CATCH (Exception_{exc_type} e)"
            return "CATCH (Exception e)"
        elif opcode == "THROW_EXCEPTION":
            return "THROW"
            
        return f"/* Exception: {opcode} */"
        
    def _format_event_call(self, operands: list) -> str:

        
        
        
        """Format event calls."""
        if len(operands) >= 2:
            event_idx = operands[0]
            obj_idx = operands[1]
            event_name = self.functions.get(event_idx, f"event_{event_idx}")
            return f"TriggerEvent('{event_name}')"
        return "TriggerEvent()"
        
    def _format_object_creation(self, opcode: str, operands: list, stack_context: list = None) -> str:

        
        
        
        """Format object creation operations."""
        if opcode == "CREATE_EXT_OBJ":
            return "CREATE object"
        elif opcode == "CREATE_USING":
            if stack_context and stack_context:
                class_name = stack_context[-1] if stack_context else "unknown"
                return f"CREATE USING '{class_name}'"
            return "CREATE USING class_name"
            
        return f"/* Object creation: {opcode} */"
        
    def _get_cursor_name(self, operands: list) -> str:

        
        
        
        """Get cursor name from operands."""
        if operands and len(operands) > 0:
            cursor_idx = operands[0]
            return f"cursor_{cursor_idx}"
        return "cursor"
        
    def _get_table_info(self, operands: list) -> str:

        
        
        
        """Get table information from operands."""
        if operands and len(operands) > 0:
            table_idx = operands[0]
            return self.strings.get(table_idx, f"table_{table_idx}")
        return "table_name"