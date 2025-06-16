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
                pass
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
                    return f"if (condition) then goto {label_map[target_addr]}"
            return f"// {opcode} <unknown target>"
        
        elif opcode == "JUMPFALSE":
            if inst.operand_values and len(inst.operand_values) > 0:
                offset = inst.operand_values[0]
                target_addr = inst.address + offset + len(inst.opcode) + len(inst.operands)
                if target_addr in label_map:
                    return f"if not (condition) then goto {label_map[target_addr]}"
            return f"// {opcode} <unknown target>"
        
        # Call instructions
        elif opcode == "GLOBFUNCCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                func_id = inst.operand_values[0]
                return f"// Call global function #{func_id}"
            return f"// {opcode}"
        
        elif opcode == "CALL_FUNCTION":
            if inst.operand_values and len(inst.operand_values) > 0:
                func_id = inst.operand_values[0]
                return f"// Call function #{func_id}"
            return f"// {opcode}"
        
        elif opcode == "DLLFUNCCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                dll_func_id = inst.operand_values[0]
                return f"// Call DLL function #{dll_func_id}"
            return f"// {opcode}"
        
        elif opcode == "EVENTCALL":
            if inst.operand_values and len(inst.operand_values) > 0:
                event_id = inst.operand_values[0]
                return f"// Trigger event #{event_id}"
            return f"// {opcode}"
        
        # Push constant instructions
        elif opcode == "PUSH_CONST_INT":
            if inst.operand_values and len(inst.operand_values) > 0:
                const_id = inst.operand_values[0]
                return f"// Push integer constant #{const_id}"
            return f"// {opcode}"
        
        elif opcode == "PUSH_CONST_STRING":
            if inst.operand_values and len(inst.operand_values) > 0:
                str_id = inst.operand_values[0]
                return f'// Push string constant #{str_id}'
            return f"// {opcode}"
        
        elif opcode == "PUSH_CONST_BOOL":
            if inst.operand_values and len(inst.operand_values) > 0:
                bool_val = inst.operand_values[0]
                return f"// Push boolean {bool(bool_val)}"
            return f"// {opcode}"
        
        # Variable references
        elif opcode == "PUSH_LOCAL_VAR":
            if inst.operand_values and len(inst.operand_values) > 0:
                var_idx = inst.operand_values[0]
                return f"// Push local variable #{var_idx}"
            return f"// {opcode}"
        
        elif opcode == "PUSH_GLOBAL_VAR":
            if inst.operand_values and len(inst.operand_values) > 0:
                var_id = inst.operand_values[0]
                return f"// Push global variable #{var_id}"
            return f"// {opcode}"
        
        # Database operations
        elif opcode == "DBSELECT":
            return "// Execute SELECT statement"
        
        elif opcode == "DBINSERT":
            return "// Execute INSERT statement"
        
        elif opcode == "DBUPDATE":
            return "// Execute UPDATE statement"
        
        elif opcode == "DBDELETE":
            return "// Execute DELETE statement"
        
        elif opcode == "DBFETCH":
            return "// Fetch from cursor"
        
        elif opcode == "DBOPEN":
            return "// Open database cursor"
        
        elif opcode == "DBCLOSE":
            return "// Close database cursor"
        
        # Return instruction
        elif opcode == "RETURN":
            if inst.operand_values and len(inst.operand_values) > 0:
                ret_type = inst.operand_values[0]
                if ret_type == 0:
                    return "return"
                else:
                    return f"return // type: {ret_type}"
            return "return"
        
        # Default: return None to use generic formatting
        return None
