"""Output formatter for PowerBuilder decompiled code.

This module formats the decompiled instructions and control flow structures
into readable pseudo-PowerScript code.
"""

import logging
from typing import List, Dict, Any

from .pcode_decoder_v2 import DecodedObject, PCodeInstruction
from .control_flow_analyzer import ControlBlock, BlockType

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats decompiled code for output."""
    
    def __init__(self):
        """Initialize the formatter."""
        self.indent_level = 0
        self.indent_str = "    "  # 4 spaces
    
    def format_object(self, decoded_obj: DecodedObject, 
                     control_blocks: List[ControlBlock],
                     source_file: str) -> List[str]:
        """Format a complete decompiled object.
        
        Args:
            decoded_obj: The decoded object with instructions
            control_blocks: Control flow blocks
            source_file: Source PBD filename
            
        Returns:
            List of formatted output lines
        """
        lines = []
        
        # Add header comments
        lines.append(f"// Source: {source_file}")
        lines.append(f"// Object: {decoded_obj.name}")
        lines.append(f"// Type: {decoded_obj.type}")
        lines.append(f"// PowerBuilder Version: {decoded_obj.version}")
        lines.append("")
        
        # Format based on object type
        if decoded_obj.type == 'function':
            lines.extend(self._format_function(decoded_obj, control_blocks))
        elif decoded_obj.type == 'window':
            lines.extend(self._format_window(decoded_obj, control_blocks))
        elif decoded_obj.type == 'userobject':
            lines.extend(self._format_userobject(decoded_obj, control_blocks))
        elif decoded_obj.type == 'application':
            lines.extend(self._format_application(decoded_obj, control_blocks))
        else:
            # Generic formatting
            lines.extend(self._format_generic(decoded_obj, control_blocks))
        
        return lines
    
    def _format_function(self, decoded_obj: DecodedObject, 
                        control_blocks: List[ControlBlock]) -> List[str]:
        """Format a function object."""
        lines = []
        
        # Function signature (reconstructed from metadata if available)
        func_name = decoded_obj.name.replace('.fun', '')
        lines.append(f"function {func_name}()")
        lines.append("")
        
        # Local variables (if detected)
        if 'local_vars' in decoded_obj.metadata:
            for var in decoded_obj.metadata['local_vars']:
                lines.append(f"{self.indent_str}{var['type']} {var['name']}")
            lines.append("")
        
        # Function body
        self.indent_level = 1
        for block in control_blocks:
            lines.extend(self._format_block(block))
        self.indent_level = 0
        
        lines.append("")
        lines.append("end function")
        
        return lines
    
    def _format_window(self, decoded_obj: DecodedObject, 
                      control_blocks: List[ControlBlock]) -> List[str]:
        """Format a window object."""
        lines = []
        
        window_name = decoded_obj.name.replace('.win', '')
        lines.append(f"window {window_name}")
        lines.append("")
        
        # Events
        if control_blocks:
            lines.append("// Events")
            for block in control_blocks:
                if block.type == BlockType.EVENT:
                    lines.extend(self._format_event_block(block))
        
        lines.append("")
        lines.append("end window")
        
        return lines
    
    def _format_userobject(self, decoded_obj: DecodedObject,
                          control_blocks: List[ControlBlock]) -> List[str]:
        """Format a user object."""
        lines = []
        
        uo_name = decoded_obj.name.replace('.udo', '')
        lines.append(f"userobject {uo_name}")
        lines.append("")
        
        # Similar to window formatting
        if control_blocks:
            for block in control_blocks:
                lines.extend(self._format_block(block))
        
        lines.append("")
        lines.append("end userobject")
        
        return lines
    
    def _format_application(self, decoded_obj: DecodedObject,
                           control_blocks: List[ControlBlock]) -> List[str]:
        """Format an application object."""
        lines = []
        
        app_name = decoded_obj.name.replace('.app', '')
        lines.append(f"application {app_name}")
        lines.append("")
        
        # Application events
        if control_blocks:
            for block in control_blocks:
                lines.extend(self._format_block(block))
        
        lines.append("")
        lines.append("end application")
        
        return lines
    
    def _format_generic(self, decoded_obj: DecodedObject,
                       control_blocks: List[ControlBlock]) -> List[str]:
        """Format a generic object."""
        lines = []
        
        lines.append(f"// Generic object: {decoded_obj.name}")
        lines.append("")
        
        # Just format the blocks
        for block in control_blocks:
            lines.extend(self._format_block(block))
        
        return lines
    
    def _format_block(self, block: ControlBlock) -> List[str]:
        """Format a control flow block."""
        lines = []
        
        if block.type == BlockType.IF:
            lines.extend(self._format_if_block(block))
        elif block.type == BlockType.WHILE:
            lines.extend(self._format_while_block(block))
        elif block.type == BlockType.FOR:
            lines.extend(self._format_for_block(block))
        elif block.type == BlockType.DO_WHILE:
            lines.extend(self._format_do_while_block(block))
        elif block.type == BlockType.CHOOSE_CASE:
            lines.extend(self._format_choose_case_block(block))
        elif block.type == BlockType.TRY:
            lines.extend(self._format_try_block(block))
        elif block.type == BlockType.EVENT:
            lines.extend(self._format_event_block(block))
        else:
            # Basic block - just format statements
            if hasattr(block, 'statements') and block.statements:
                for stmt in block.statements:
                    lines.append(self._indent(stmt))
            elif hasattr(block, 'instructions') and block.instructions:
                # Raw instructions
                for inst in block.instructions:
                    lines.append(self._indent(f"// {inst.text_format}"))
        
        return lines
    
    def _format_if_block(self, block: ControlBlock) -> List[str]:
        """Format an IF block."""
        lines = []
        
        condition = block.metadata.get('condition', 'unknown_condition')
        lines.append(self._indent(f"if {condition} then"))
        
        self.indent_level += 1
        # Format then branch
        if hasattr(block, 'then_block') and block.then_block:
            lines.extend(self._format_block(block.then_block))
        
        # Format else branch if present
        if hasattr(block, 'else_block') and block.else_block:
            self.indent_level -= 1
            lines.append(self._indent("else"))
            self.indent_level += 1
            lines.extend(self._format_block(block.else_block))
        
        self.indent_level -= 1
        lines.append(self._indent("end if"))
        
        return lines
    
    def _format_while_block(self, block: ControlBlock) -> List[str]:
        """Format a WHILE loop."""
        lines = []
        
        condition = block.metadata.get('condition', 'unknown_condition')
        lines.append(self._indent(f"do while {condition}"))
        
        self.indent_level += 1
        if hasattr(block, 'body') and block.body:
            lines.extend(self._format_block(block.body))
        self.indent_level -= 1
        
        lines.append(self._indent("loop"))
        
        return lines
    
    def _format_for_block(self, block: ControlBlock) -> List[str]:
        """Format a FOR loop."""
        lines = []
        
        var = block.metadata.get('variable', 'i')
        start = block.metadata.get('start', '1')
        end = block.metadata.get('end', 'unknown')
        step = block.metadata.get('step', '1')
        
        if step == '1':
            lines.append(self._indent(f"for {var} = {start} to {end}"))
        else:
            lines.append(self._indent(f"for {var} = {start} to {end} step {step}"))
        
        self.indent_level += 1
        if hasattr(block, 'body') and block.body:
            lines.extend(self._format_block(block.body))
        self.indent_level -= 1
        
        lines.append(self._indent("next"))
        
        return lines
    
    def _format_do_while_block(self, block: ControlBlock) -> List[str]:
        """Format a DO WHILE loop."""
        lines = []
        
        lines.append(self._indent("do"))
        
        self.indent_level += 1
        if hasattr(block, 'body') and block.body:
            lines.extend(self._format_block(block.body))
        self.indent_level -= 1
        
        condition = block.metadata.get('condition', 'unknown_condition')
        lines.append(self._indent(f"loop while {condition}"))
        
        return lines
    
    def _format_choose_case_block(self, block: ControlBlock) -> List[str]:
        """Format a CHOOSE CASE block."""
        lines = []
        
        expr = block.metadata.get('expression', 'unknown_expression')
        lines.append(self._indent(f"choose case {expr}"))
        
        self.indent_level += 1
        
        # Format cases
        if hasattr(block, 'cases'):
            for case in block.cases:
                value = case.get('value', 'unknown')
                lines.append(self._indent(f"case {value}"))
                
                self.indent_level += 1
                if 'body' in case:
                    lines.extend(self._format_block(case['body']))
                self.indent_level -= 1
        
        # Format default case
        if hasattr(block, 'default_case') and block.default_case:
            lines.append(self._indent("case else"))
            self.indent_level += 1
            lines.extend(self._format_block(block.default_case))
            self.indent_level -= 1
        
        self.indent_level -= 1
        lines.append(self._indent("end choose"))
        
        return lines
    
    def _format_try_block(self, block: ControlBlock) -> List[str]:
        """Format a TRY block."""
        lines = []
        
        lines.append(self._indent("try"))
        
        self.indent_level += 1
        if hasattr(block, 'try_body') and block.try_body:
            lines.extend(self._format_block(block.try_body))
        self.indent_level -= 1
        
        # Format catch blocks
        if hasattr(block, 'catch_blocks'):
            for catch in block.catch_blocks:
                exception_type = catch.get('type', 'Exception')
                var_name = catch.get('variable', 'ex')
                lines.append(self._indent(f"catch ({exception_type} {var_name})"))
                
                self.indent_level += 1
                if 'body' in catch:
                    lines.extend(self._format_block(catch['body']))
                self.indent_level -= 1
        
        # Format finally block
        if hasattr(block, 'finally_block') and block.finally_block:
            lines.append(self._indent("finally"))
            self.indent_level += 1
            lines.extend(self._format_block(block.finally_block))
            self.indent_level -= 1
        
        lines.append(self._indent("end try"))
        
        return lines
    
    def _format_event_block(self, block: ControlBlock) -> List[str]:
        """Format an event block."""
        lines = []
        
        event_name = block.metadata.get('name', 'unknown_event')
        lines.append("")
        lines.append(f"event {event_name}()")
        
        self.indent_level = 1
        if hasattr(block, 'body') and block.body:
            lines.extend(self._format_block(block.body))
        elif hasattr(block, 'statements') and block.statements:
            for stmt in block.statements:
                lines.append(self._indent(stmt))
        self.indent_level = 0
        
        lines.append("end event")
        
        return lines
    
    def _indent(self, text: str) -> str:
        """Add indentation to a line of text."""
        if not text or text.isspace():
            return text
        return self.indent_str * self.indent_level + text