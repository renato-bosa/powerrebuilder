"""Simple formatter that generates parseable PowerBuilder code.

This formatter focuses on generating syntactically valid PowerBuilder code
rather than trying to perfectly reconstruct the original source.
"""

import logging
from typing import Any

from src.decompile.pcode.decoder import DecodedObject

logger = logging.getLogger(__name__)


class SimpleFormatter:
    """Simple formatter that generates valid PowerBuilder syntax."""

    def __init__(self):
        """Initialize the formatter."""
        self._string_table = {}
        self._function_table = {}
        self._variable_table = {}
        self._current_object = None

    def format_object(
        self,
        decoded_obj: DecodedObject,
        file_path: str = "",
    ) -> list[str]:
        """Format a decoded object into valid PowerBuilder syntax.

        Args:
            decoded_obj: The decoded object with instructions
            file_path: Path to the source file

        Returns:
            List of formatted output lines
        """
        lines = []

        # Store current object for reference
        self._current_object = decoded_obj

        # Initialize tables from metadata
        self._init_tables_from_metadata(decoded_obj)

        # Add header comments
        lines.append(f"// Source: {file_path}")
        lines.append(f"// Object: {decoded_obj.name}")
        lines.append(f"// Type: {decoded_obj.type}")
        lines.append("")

        # Generate based on object type
        object_name = decoded_obj.name.split(".")[0]  # Remove extension

        if decoded_obj.type == "function":
            lines.extend(
                self._format_function(
                    object_name, decoded_obj))
        elif decoded_obj.type == "window":
            lines.extend(
                self._format_window(
                    object_name, decoded_obj))
        elif decoded_obj.type == "userobject":
            lines.extend(
                self._format_userobject(
                    object_name, decoded_obj))
        elif decoded_obj.type == "menu":
            lines.extend(self._format_menu(
                object_name, decoded_obj))
        elif decoded_obj.type == "application":
            lines.extend(
                self._format_application(
                    object_name, decoded_obj))
        else:
            # Default to function
            lines.extend(self._format_function(
                object_name, decoded_obj))

        return lines

    def _format_function(
        self,
        name: str,
        decoded_obj: DecodedObject
    ) -> list[str]:
        """Format as a function."""
        lines = []

        # Function declaration
        lines.append(f"function integer {name}()")
        lines.append("")

        # Function body
        lines.append("// Auto-generated function")
        lines.append("// P-code instructions found: " + str(len(decoded_obj.instructions)))
        lines.append("")

        # Add basic structure
        lines.extend(self._format_instructions_as_comments(decoded_obj.instructions))
        lines.append("")
        lines.append("return 1")
        lines.append("end function")

        return lines

    def _format_window(
        self,
        name: str,
        decoded_obj: DecodedObject
    ) -> list[str]:
        """Format as a window."""
        lines = []

        # Window declaration
        lines.append("forward")
        lines.append(f"global type {name} from window")
        lines.append("end type")
        lines.append("end forward")
        lines.append("")

        lines.append(f"global type {name} from window")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Add events if we have P-code
        if decoded_obj.instructions:
            lines.append(f"on {name}.create")
            lines.append("// Auto-generated window create")
            lines.append("end on")
            lines.append("")

            lines.append(f"on {name}.destroy")
            lines.append("// Auto-generated window destroy")
            lines.append("end on")

        return lines

    def _format_userobject(
        self,
        name: str,
        decoded_obj: DecodedObject
    ) -> list[str]:
        """Format as a user object."""
        lines = []

        # UserObject declaration
        lines.append("forward")
        lines.append(f"global type {name} from userobject")
        lines.append("end type")
        lines.append("end forward")
        lines.append("")

        lines.append(f"global type {name} from userobject")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Add constructor if we have P-code
        if decoded_obj.instructions:
            lines.append(f"on {name}.create")
            lines.append("// Auto-generated user object create")
            lines.append("end on")
            lines.append("")

            lines.append(f"on {name}.destroy")
            lines.append("// Auto-generated user object destroy")
            lines.append("end on")

        return lines

    def _format_menu(
        self,
        name: str,
        decoded_obj: DecodedObject
    ) -> list[str]:
        """Format as a menu."""
        lines = []

        # Menu declaration
        lines.append("forward")
        lines.append(f"global type {name} from menu")
        lines.append("end type")
        lines.append("end forward")
        lines.append("")

        lines.append(f"global type {name} from menu")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Add menu items comment
        if decoded_obj.instructions:
            lines.append("// Menu items would be defined here")
            lines.append("// P-code instructions found: " + str(len(decoded_obj.instructions)))

        return lines

    def _format_application(
        self,
        name: str,
        decoded_obj: DecodedObject
    ) -> list[str]:
        """Format as an application object."""
        lines = []

        # Application declaration
        lines.append("forward")
        lines.append(f"global type {name} from application")
        lines.append("end type")
        lines.append(f"global transaction sqlca")
        lines.append(f"global dynamicdescriptionarea sqlda")
        lines.append(f"global dynamicstagingarea sqlsa")
        lines.append(f"global error error")
        lines.append(f"global message message")
        lines.append("end forward")
        lines.append("")

        lines.append(f"global type {name} from application")
        lines.append("end type")
        lines.append("")

        # Add application events if we have P-code
        if decoded_obj.instructions:
            lines.append(f"on {name}.create")
            lines.append("appname = \"" + name + "\"")
            lines.append("message = create message")
            lines.append("sqlca = create transaction")
            lines.append("sqlda = create dynamicdescriptionarea")
            lines.append("sqlsa = create dynamicstagingarea")
            lines.append("error = create error")
            lines.append("end on")
            lines.append("")

            lines.append(f"on {name}.destroy")
            lines.append("destroy(sqlca)")
            lines.append("destroy(sqlda)")
            lines.append("destroy(sqlsa)")
            lines.append("destroy(error)")
            lines.append("destroy(message)")
            lines.append("end on")

        return lines

    def _format_instructions_as_comments(self, instructions) -> list[str]:
        """Format P-code instructions as comments for debugging."""
        lines = []
        
        if not instructions:
            lines.append("// No P-code instructions found")
            return lines
        
        lines.append("// P-code instructions:")
        for i, instr in enumerate(instructions[:10]):  # Show first 10
            comment = f"// {i:04d}: {instr.opcode_name}"
            if instr.operands:
                comment += f" {instr.operands}"
            lines.append(comment)
        
        if len(instructions) > 10:
            lines.append(f"// ... and {len(instructions) - 10} more instructions")
        
        return lines

    def _init_tables_from_metadata(self, decoded_obj: DecodedObject) -> None:
        """Initialize lookup tables from object metadata."""
        metadata = decoded_obj.metadata or {}
        
        # Extract string table if available
        if "strings" in metadata:
            self._string_table = metadata["strings"]
        
        # Extract function table if available
        if "functions" in metadata:
            self._function_table = metadata["functions"]
        
        # Extract variable table if available
        if "variables" in metadata:
            self._variable_table = metadata["variables"]