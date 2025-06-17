"""Simple formatter that generates parseable PowerBuilder code.

This formatter focuses on generating syntactically valid PowerBuilder code
rather than trying to perfectly reconstruct the original source.
"""

import logging

from .pcode_decoder import DecodedObject

logger = logging.getLogger(__name__)


class SimpleFormatter:
    """Simple formatter that generates valid PowerBuilder syntax."""

    def format_object(
        self, decoded_obj: DecodedObject, file_path: str = ""
    ) -> list[str]:
        """Format a decoded object into valid PowerBuilder syntax.

        Args:
            decoded_obj: The decoded object with instructions
            file_path: Path to the source file

        Returns:
            List of formatted output lines
        """
        lines = []

        # Add header comments
        lines.append(f"// Source: {file_path}")
        lines.append(f"// Object: {decoded_obj.name}")
        lines.append(f"// Type: {decoded_obj.type}")
        lines.append("// Auto-generated stub")
        lines.append("")

        # Generate based on object type
        object_name = decoded_obj.name.split(".")[0]  # Remove extension

        if decoded_obj.type == "function":
            lines.extend(self._format_function(object_name, decoded_obj))
        elif decoded_obj.type == "window":
            lines.extend(self._format_window(object_name, decoded_obj))
        elif decoded_obj.type == "userobject":
            lines.extend(self._format_userobject(object_name, decoded_obj))
        elif decoded_obj.type == "menu":
            lines.extend(self._format_menu(object_name, decoded_obj))
        elif decoded_obj.type == "application":
            lines.extend(self._format_application(object_name, decoded_obj))
        else:
            # Default to function
            lines.extend(self._format_function(object_name, decoded_obj))

        return lines

    def _format_function(self, name: str, decoded_obj: DecodedObject) -> list[str]:
        """Format as a function."""
        lines = []

        # Function declaration
        lines.append(f"global function integer {name}()")
        lines.append("")

        # Add minimal body
        lines.extend(self._generate_minimal_body(decoded_obj))

        lines.append("")
        lines.append("end function")

        return lines

    def _format_window(self, name: str, decoded_obj: DecodedObject) -> list[str]:
        """Format as a window."""
        lines = []

        # Window declaration
        lines.append(f"global type {name} from window")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Constructor event
        lines.append(f"on {name}.create")
        lines.append("end on")
        lines.append("")

        # Destructor event
        lines.append(f"on {name}.destroy")
        lines.append("end on")
        lines.append("")

        # Add common events based on instructions
        events = self._detect_events(decoded_obj)
        for event_name in events:
            lines.append(f"event {event_name}()")
            lines.append("// Event implementation")
            lines.append("return 0")
            lines.append("end event")
            lines.append("")

        return lines

    def _format_userobject(self, name: str, decoded_obj: DecodedObject) -> list[str]:
        """Format as a user object."""
        lines = []

        # User object declaration
        lines.append(f"global type {name} from userobject")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Constructor
        lines.append(f"on {name}.create")
        lines.append("end on")
        lines.append("")

        # Destructor
        lines.append(f"on {name}.destroy")
        lines.append("end on")
        lines.append("")

        # Add detected functions
        functions = self._detect_functions(decoded_obj)
        for func_name in functions:
            lines.append(f"public function integer {func_name}()")
            lines.append("// Function implementation")
            lines.append("return 0")
            lines.append("end function")
            lines.append("")

        return lines

    def _format_menu(self, name: str, decoded_obj: DecodedObject) -> list[str]:
        """Format as a menu."""
        lines = []

        # Menu declaration
        lines.append(f"global type {name} from menu")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Constructor
        lines.append(f"on {name}.create")
        lines.append(f"{name} = this")
        lines.append("end on")
        lines.append("")

        # Destructor
        lines.append(f"on {name}.destroy")
        lines.append("end on")

        return lines

    def _format_application(self, name: str, decoded_obj: DecodedObject) -> list[str]:
        """Format as an application object."""
        lines = []

        # Application declaration
        lines.append(f"global type {name} from application")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Open event
        lines.append("event open()")
        lines.append("// Application initialization")
        lines.append("end event")
        lines.append("")

        # Close event
        lines.append("event close()")
        lines.append("// Application cleanup")
        lines.append("end event")

        return lines

    def _generate_minimal_body(self, decoded_obj: DecodedObject) -> list[str]:
        """Generate minimal valid body based on instructions."""
        lines = []

        # Analyze instructions to determine what the function might do
        has_db_ops = False
        has_arithmetic = False
        has_special_ops = False

        # First pass: detect operation types and format special opcodes
        for inst in decoded_obj.instructions:
            if inst.opcode_name == "RETURN":
                # RETURN doesn't affect operation type detection
                continue
            elif inst.opcode_name.startswith("DB"):
                has_db_ops = True
            elif inst.opcode_name in ["ADD", "SUB", "MULT", "DIV"]:
                has_arithmetic = True
            elif self._is_special_opcode(inst.opcode_name):
                has_special_ops = True

        # Generate appropriate body with special opcode formatting
        if has_special_ops:
            lines.append("// Special operations detected")
            lines.extend(self._format_instructions_with_special_handling(decoded_obj))
        elif has_db_ops:
            lines.append("// Database operations detected")
            lines.append("integer li_result = 0")
            lines.append("")
            lines.append("// TODO: Implement database logic")
            lines.append("")
            lines.append("return li_result")
        elif has_arithmetic:
            lines.append("// Arithmetic operations detected")
            lines.append("integer li_result = 0")
            lines.append("")
            lines.append("// TODO: Implement calculation logic")
            lines.append("")
            lines.append("return li_result")
        else:
            lines.append("// TODO: Implementation")
            lines.append("return 0")

        return lines

    def _detect_events(self, decoded_obj: DecodedObject) -> list[str]:
        """Detect likely events from instructions."""
        events = []

        # Look for common event patterns
        for inst in decoded_obj.instructions:
            if inst.opcode_name == "EVENTCALL":
                # Could be calling common events
                events.append("clicked")
                break

        # Add standard events if we found any event calls
        if events:
            events.extend(["constructor", "destructor"])

        return list(set(events))  # Remove duplicates

    def _detect_functions(self, decoded_obj: DecodedObject) -> list[str]:
        """Detect likely functions from instructions."""
        functions = []

        # Look for function call patterns
        call_count = 0
        for inst in decoded_obj.instructions:
            if "CALL" in inst.opcode_name:
                call_count += 1

        # Generate some sample functions based on complexity
        if call_count > 10:
            functions.extend(["initialize", "process", "validate"])
        elif call_count > 5:
            functions.extend(["initialize", "process"])
        elif call_count > 0:
            functions.append("initialize")

        return functions
    
    def _is_special_opcode(self, opcode_name: str) -> bool:
        """Check if an opcode requires special formatting."""
        special_opcodes = {
            # Jump instructions
            "JUMP", "JUMPTRUE", "JUMPFALSE",
            # Call instructions
            "GLOBFUNCCALL", "CALL_FUNCTION", "DLLFUNCCALL", "DOTFUNCCALL",
            "EVENTCALL", "SYSFUNCCALL", "CLASS_CALL",
            # Push constant instructions
            "PUSH_CONST_INT", "PUSH_CONST_UINT", "PUSH_CONST_LONG", "PUSH_CONST_ULONG",
            "PUSH_CONST_DEC", "PUSH_CONST_FLOAT", "PUSH_CONST_DOUBLE",
            "PUSH_CONST_STRING", "PUSH_CONST_BOOL", "PUSH_CONST_ENUM",
            "PUSH_CONST_TIME", "PUSH_CONST_DATE",
            # Variable references
            "PUSH_LOCAL_VAR", "PUSH_SHARED_VAR", "PUSH_GLOBAL_VAR",
            # Database operations
            "DBOPEN", "DBSELECT", "DBFETCH", "DBINSERT", "DBUPDATE", "DBDELETE",
            "DBEXECUTE", "DBPREPARE", "DBDESCRIBE",
        }
        return opcode_name in special_opcodes
    
    def _format_instructions_with_special_handling(self, decoded_obj: DecodedObject) -> list[str]:
        """Format instructions with special handling for specific opcodes."""
        lines = []
        
        # Build label map for jumps
        label_map = {}
        for i, inst in enumerate(decoded_obj.instructions):
            if inst.opcode_name in ["JUMP", "JUMPTRUE", "JUMPFALSE"]:
                # Calculate target address
                if inst.operand_values and len(inst.operand_values) > 0:
                    offset = inst.operand_values[0]
                    target_addr = inst.address + offset + len(inst.opcode) + len(inst.operands)
                    label_map[target_addr] = f"L_{target_addr:04X}"
        
        # Format instructions
        for i, inst in enumerate(decoded_obj.instructions):
            # Check if this instruction is a jump target
            if inst.address in label_map:
                lines.append(f"{label_map[inst.address]}:")
            
            # Format the instruction based on its type
            formatted = self._format_special_instruction(inst, label_map)
            if formatted:
                lines.append(f"    {formatted}")
            else:
                # Fallback to generic format
                lines.append(f"    // {inst.text_format}")
        
        # Ensure we have a return statement
        if not any("return" in line.lower() for line in lines):
            lines.append("    return 0")
        
        return lines
    
    def _format_special_instruction(self, inst, label_map: dict) -> str:
        """Format a single instruction with special handling."""
        opcode = inst.opcode_name
        
        # Jump instructions
        if opcode == "JUMP":
            if inst.operand_values and len(inst.operand_values) > 0:
                offset = inst.operand_values[0]
                target_addr = inst.address + offset + len(inst.opcode) + len(inst.operands)
                if target_addr in label_map:
                    return f"goto {label_map[target_addr]}"
            return f"// {opcode} <unknown target>"
        
        elif opcode == "JUMPTRUE":
            if inst.operand_values and len(inst.operand_values) > 0:
                offset = inst.operand_values[0]
                target_addr = inst.address + offset + len(inst.opcode) + len(inst.operands)
                if target_addr in label_map:
                    # Use actual stack value if available
                    return f"if lb_condition then goto {label_map[target_addr]}"
            return f"// {opcode} <unknown target>"
        
        elif opcode == "JUMPFALSE":
            if inst.operand_values and len(inst.operand_values) > 0:
                offset = inst.operand_values[0]
                target_addr = inst.address + offset + len(inst.opcode) + len(inst.operands)
                if target_addr in label_map:
                    # Use actual stack value if available
                    return f"if not lb_condition then goto {label_map[target_addr]}"
            return f"// {opcode} <unknown target>"
        
        # Call instructions
        elif opcode == "GLOBFUNCCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                func_id = inst.operand_values[0]
                # Try to resolve function name from constant pool if available
                func_name = self._resolve_function_name(func_id)
                if func_name:
                    return f"{func_name}()"
                return f"gf_function_{func_id}() // Global function call"
            return f"// {opcode}"
        
        elif opcode == "CALL_FUNCTION":
            if inst.operand_values and len(inst.operand_values) > 0:
                func_id = inst.operand_values[0]
                func_name = self._resolve_function_name(func_id)
                if func_name:
                    return f"{func_name}()"
                return f"lf_function_{func_id}() // Local function call"
            return f"// {opcode}"
        
        elif opcode == "DLLFUNCCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                dll_func_id = inst.operand_values[0]
                dll_name = self._resolve_dll_function(dll_func_id)
                if dll_name:
                    return f"{dll_name}() // DLL function"
                return f"external_function_{dll_func_id}() // DLL function call"
            return f"// {opcode}"
            
        elif opcode == "DOTFUNCCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                method_id = inst.operand_values[0]
                method_name = self._resolve_method_name(method_id)
                if method_name:
                    return f"lo_object.{method_name}() // Method call"
                return f"lo_object.method_{method_id}() // Method call"
            return f"// {opcode}"
            
        elif opcode == "SYSFUNCCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                sys_func_id = inst.operand_values[0]
                sys_func = self._resolve_system_function(sys_func_id)
                if sys_func:
                    return f"{sys_func}() // System function"
                return f"system_function_{sys_func_id}() // System function call"
            return f"// {opcode}"
            
        elif opcode == "CLASS_CALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                class_id = inst.operand_values[0]
                class_name = self._resolve_class_name(class_id)
                if class_name:
                    return f"{class_name}.constructor() // Class constructor"
                return f"class_{class_id}.constructor() // Class call"
            return f"// {opcode}"
        
        elif opcode == "EVENTCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                event_id = inst.operand_values[0]
                event_name = self._resolve_event_name(event_id)
                if event_name:
                    return f"this.event {event_name}()"
                return f"this.event event_{event_id}()"
            return f"// {opcode}"
        
        # Push constant instructions
        elif opcode == "PUSH_CONST_INT":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"li_value = {value} // Push integer"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_UINT":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"lui_value = {value} // Push unsigned integer"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_LONG":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"ll_value = {value} // Push long"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_ULONG":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"lul_value = {value} // Push unsigned long"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_DEC":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"ld_value = {value} // Push decimal"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_FLOAT":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"lf_value = {value} // Push float"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_DOUBLE":
            if inst.operand_values and len(inst.operand_values) > 0:
                value = inst.operand_values[0]
                return f"ld_value = {value} // Push double"
            return f"// {opcode}"
        
        elif opcode == "PUSH_CONST_STRING":
            if inst.operand_values and len(inst.operand_values) > 0:
                str_id = inst.operand_values[0]
                str_value = self._resolve_string_constant(str_id)
                if str_value:
                    return f'ls_value = "{str_value}" // Push string'
                return f'ls_value = "string_{str_id}" // Push string constant'
            return f"// {opcode}"
        
        elif opcode == "PUSH_CONST_BOOL":
            if inst.operand_values and len(inst.operand_values) > 0:
                bool_val = inst.operand_values[0]
                pb_bool = "TRUE" if bool_val else "FALSE"
                return f"lb_value = {pb_bool} // Push boolean"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_ENUM":
            if inst.operand_values and len(inst.operand_values) > 0:
                enum_val = inst.operand_values[0]
                enum_name = self._resolve_enum_value(enum_val)
                if enum_name:
                    return f"le_value = {enum_name} // Push enum"
                return f"le_value = enum_{enum_val} // Push enum constant"
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_TIME":
            if inst.operand_values and len(inst.operand_values) > 0:
                time_val = inst.operand_values[0]
                return f'lt_value = Time("{time_val}") // Push time'
            return f"// {opcode}"
            
        elif opcode == "PUSH_CONST_DATE":
            if inst.operand_values and len(inst.operand_values) > 0:
                date_val = inst.operand_values[0]
                return f'ld_value = Date("{date_val}") // Push date'
            return f"// {opcode}"
        
        # Variable references
        elif opcode == "PUSH_LOCAL_VAR":
            if inst.operand_values and len(inst.operand_values) > 0:
                var_idx = inst.operand_values[0]
                var_name = self._resolve_local_variable(var_idx)
                if var_name:
                    return f"// Reference: {var_name}"
                return f"// Reference: local_var_{var_idx}"
            return f"// {opcode}"
            
        elif opcode == "PUSH_SHARED_VAR":
            if inst.operand_values and len(inst.operand_values) > 0:
                var_id = inst.operand_values[0]
                var_name = self._resolve_shared_variable(var_id)
                if var_name:
                    return f"// Reference: {var_name}"
                return f"// Reference: shared_var_{var_id}"
            return f"// {opcode}"
        
        elif opcode == "PUSH_GLOBAL_VAR":
            if inst.operand_values and len(inst.operand_values) > 0:
                var_id = inst.operand_values[0]
                var_name = self._resolve_global_variable(var_id)
                if var_name:
                    return f"// Reference: {var_name}"
                return f"// Reference: global_var_{var_id}"
            return f"// {opcode}"
        
        # Database operations
        elif opcode == "DBSELECT":
            return "SELECT * FROM table USING SQLCA;"
        
        elif opcode == "DBINSERT":
            return "INSERT INTO table VALUES (...) USING SQLCA;"
        
        elif opcode == "DBUPDATE":
            return "UPDATE table SET column = value WHERE condition USING SQLCA;"
        
        elif opcode == "DBDELETE":
            return "DELETE FROM table WHERE condition USING SQLCA;"
        
        elif opcode == "DBFETCH":
            return "FETCH cursor INTO :variable;"
            
        elif opcode == "DBEXECUTE":
            return "EXECUTE IMMEDIATE ls_sql USING SQLCA;"
            
        elif opcode == "DBPREPARE":
            return "PREPARE sqlsa FROM ls_sql USING SQLCA;"
            
        elif opcode == "DBDESCRIBE":
            return "DESCRIBE sqlsa INTO sqlda;"
        
        elif opcode == "DBOPEN":
            return "OPEN cursor;"
        
        elif opcode == "DBCLOSE":
            return "CLOSE cursor;"
        
        # Return instruction
        elif opcode == "RETURN":
            if inst.operand_values and len(inst.operand_values) > 0:
                ret_type = inst.operand_values[0]
                if ret_type == 0:
                    return "return"
                else:
                    # Try to get actual return value from stack
                    return f"return lv_result // Return type: {ret_type}"
            return "return"
        
        # Default: return None to use generic formatting
        return None
    
    # Helper methods for resolving names/values
    def _resolve_function_name(self, func_id: int) -> str:
        """Resolve function name from ID."""
        # This would typically look up in a symbol table or constant pool
        # For now, return None to use default naming
        return None
        
    def _resolve_dll_function(self, dll_func_id: int) -> str:
        """Resolve DLL function name from ID."""
        # Common Windows API functions
        dll_functions = {
            0: "GetWindowTextA",
            1: "SetWindowTextA",
            2: "MessageBoxA",
            3: "GetSystemTime",
            4: "Sleep"
        }
        return dll_functions.get(dll_func_id)
        
    def _resolve_method_name(self, method_id: int) -> str:
        """Resolve method name from ID."""
        # Common PowerBuilder methods
        common_methods = {
            0: "settext",
            1: "gettext",
            2: "visible",
            3: "enabled",
            4: "setfocus"
        }
        return common_methods.get(method_id)
        
    def _resolve_system_function(self, sys_func_id: int) -> str:
        """Resolve system function name from ID."""
        # PowerBuilder system functions
        sys_functions = {
            0: "Len",
            1: "Trim",
            2: "Upper",
            3: "Lower",
            4: "Mid",
            5: "Left",
            6: "Right",
            7: "IsNull",
            8: "SetNull",
            9: "String",
            10: "Integer",
            11: "Long",
            12: "Double",
            13: "Date",
            14: "Time",
            15: "DateTime"
        }
        return sys_functions.get(sys_func_id)
        
    def _resolve_class_name(self, class_id: int) -> str:
        """Resolve class name from ID."""
        # Common PowerBuilder classes
        common_classes = {
            0: "datawindow",
            1: "datastore",
            2: "transaction",
            3: "error",
            4: "message"
        }
        return common_classes.get(class_id)
        
    def _resolve_event_name(self, event_id: int) -> str:
        """Resolve event name from ID."""
        # Common PowerBuilder events
        common_events = {
            0: "clicked",
            1: "doubleclicked",
            2: "constructor",
            3: "destructor",
            4: "open",
            5: "close",
            6: "activate",
            7: "deactivate",
            8: "resize",
            9: "key",
            10: "modified",
            11: "itemchanged"
        }
        return common_events.get(event_id)
        
    def _resolve_string_constant(self, str_id: int) -> str:
        """Resolve string constant from ID."""
        # This would typically look up in a string table
        # For now, return None to use default naming
        return None
        
    def _resolve_enum_value(self, enum_val: int) -> str:
        """Resolve enum value name from ID."""
        # Common PowerBuilder enum values
        enum_values = {
            0: "StyleLowered!",
            1: "StyleRaised!",
            2: "StyleShadowBox!",
            3: "AlignLeft!",
            4: "AlignCenter!",
            5: "AlignRight!"
        }
        return enum_values.get(enum_val)
        
    def _resolve_local_variable(self, var_idx: int) -> str:
        """Resolve local variable name from index."""
        # Common local variable naming
        if var_idx == 0:
            return "al_arg1"
        elif var_idx == 1:
            return "al_arg2"
        elif var_idx == 2:
            return "li_return"
        return None
        
    def _resolve_shared_variable(self, var_id: int) -> str:
        """Resolve shared variable name from ID."""
        # This would typically look up in a shared variable table
        return None
        
    def _resolve_global_variable(self, var_id: int) -> str:
        """Resolve global variable name from ID."""
        # Common global variables
        global_vars = {
            0: "SQLCA",
            1: "SQLDA",
            2: "SQLSA",
            3: "Error",
            4: "Message"
        }
        return global_vars.get(var_id)
