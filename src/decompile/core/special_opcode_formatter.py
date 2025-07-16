"""Special opcode formatter for PowerBuilder P-code.

This module provides special formatting for PowerBuilder opcodes that require
custom handling beyond simple string conversion.
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)


class SpecialOpcodeFormatter:
    """Formats special PowerBuilder opcodes."""

    def __init__(self):
        """Initialize the special opcode formatter."""
        # Map of special opcodes to their formatting functions
        self.special_opcodes = {
            "CALL_SPECIAL": self._format_call_special,
            "CREATE_OBJECT": self._format_create_object,
            "TRIGGER_EVENT": self._format_trigger_event,
            "DATAWINDOW_OP": self._format_datawindow_op,
            "SQL_EXECUTE": self._format_sql_execute,
        }

    def format_opcode(self, opcode: str, operands: List[Any]) -> str:
        """Format a special opcode with its operands.

        Args:
            opcode: Opcode name
            operands: List of operands

        Returns:
            Formatted string representation
        """
        if opcode in self.special_opcodes:
            return self.special_opcodes[opcode](operands)
        else:
            # Default formatting
            if operands:
                return f"{opcode}({', '.join(str(op) for op in operands)})"
            else:
                return opcode

    def _format_call_special(self, operands: List[Any]) -> str:
        """Format CALL_SPECIAL opcode."""
        if len(operands) >= 2:
            obj_name = operands[0]
            method_name = operands[1]
            args = operands[2:] if len(operands) > 2 else []
            if args:
                args_str = ', '.join(str(arg) for arg in args)
                return f"{obj_name}.{method_name}({args_str})"
            else:
                return f"{obj_name}.{method_name}()"
        return "CALL_SPECIAL(invalid)"

    def _format_create_object(self, operands: List[Any]) -> str:
        """Format CREATE_OBJECT opcode."""
        if operands:
            class_name = operands[0]
            return f"CREATE {class_name}"
        return "CREATE(unknown)"

    def _format_trigger_event(self, operands: List[Any]) -> str:
        """Format TRIGGER_EVENT opcode."""
        if len(operands) >= 2:
            obj_name = operands[0]
            event_name = operands[1]
            return f"{obj_name}.TriggerEvent({event_name})"
        return "TriggerEvent(invalid)"

    def _format_datawindow_op(self, operands: List[Any]) -> str:
        """Format DATAWINDOW_OP opcode."""
        if operands:
            op_type = operands[0]
            if op_type == "RETRIEVE":
                return "DataWindow.Retrieve()"
            elif op_type == "UPDATE":
                return "DataWindow.Update()"
            elif op_type == "INSERTROW":
                return "DataWindow.InsertRow(0)"
            elif op_type == "DELETEROW":
                if len(operands) > 1:
                    return f"DataWindow.DeleteRow({operands[1]})"
                return "DataWindow.DeleteRow()"
        return "DataWindow.Operation()"

    def _format_sql_execute(self, operands: List[Any]) -> str:
        """Format SQL_EXECUTE opcode."""
        if operands:
            sql_statement = operands[0]
            return f'EXECUTE IMMEDIATE "{sql_statement}"'
        return "EXECUTE IMMEDIATE"

    def is_special_opcode(self, opcode: str) -> bool:
        """Check if an opcode requires special formatting.

        Args:
            opcode: Opcode name

        Returns:
            True if the opcode requires special formatting
        """
        return opcode in self.special_opcodes

    def get_special_opcodes(self) -> List[str]:
        """Get list of all special opcodes.

        Returns:
            List of special opcode names
        """
        return list(self.special_opcodes.keys())