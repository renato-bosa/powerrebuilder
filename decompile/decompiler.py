"""PowerBuilder P-code decompiler orchestrator.

This module orchestrates the complete decompilation process by integrating:
- P-code decoding (binary to instructions)
- Stack simulation (expression reconstruction)
- Control flow analysis (structure recovery)
- Source code generation (PowerBuilder output)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from decompile.pcode_decoder import PCodeDecoder, PCodeInstruction
from decompile.stack_simulator import StackSimulator, StackValue, Expression
from decompile.control_flow import ControlFlowAnalyzer, ControlBlock, BlockType

logger = logging.getLogger(__name__)


@dataclass
class DecompilationContext:
    """Context for the decompilation process."""
    file_path: Path
    instructions: List[PCodeInstruction] = field(default_factory=list)
    control_blocks: List[ControlBlock] = field(default_factory=list)
    statements: List[str] = field(default_factory=list)
    variables: Dict[int, str] = field(default_factory=dict)
    functions: Dict[int, str] = field(default_factory=dict)
    strings: Dict[int, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class PowerBuilderDecompiler:
    """Orchestrates the complete P-code decompilation process."""
    
    def __init__(self):
        self.decoder = PCodeDecoder()
        self.stack_sim = StackSimulator()
        self.cf_analyzer = ControlFlowAnalyzer()
        
    def decompile_file(self, file_path: Path) -> str:
        """Decompile a P-code file to PowerBuilder source.
        
        Args:
            file_path: Path to the P-code file
            
        Returns:
            Decompiled PowerBuilder source code
        """
        logger.info(f"Starting decompilation of {file_path}")
        
        context = DecompilationContext(file_path=file_path)
        
        try:
            # Step 1: Decode P-code binary to instructions
            self._decode_instructions(context)
            
            # Step 2: Analyze control flow
            self._analyze_control_flow(context)
            
            # Step 3: Simulate stack and reconstruct expressions
            self._reconstruct_expressions(context)
            
            # Step 4: Generate PowerBuilder source
            source = self._generate_source(context)
            
            return source
            
        except Exception as e:
            logger.error(f"Decompilation failed for {file_path}: {e}")
            context.errors.append(str(e))
            return self._generate_error_output(context)
    
    def _decode_instructions(self, context: DecompilationContext) -> None:
        """Decode P-code binary to instructions."""
        logger.debug(f"Decoding instructions from {context.file_path}")
        
        # Set current file for better logging
        self.decoder.current_file = str(context.file_path)
        
        with open(context.file_path, 'rb') as f:
            data = f.read()
        
        # Find P-code start (after headers)
        pcode_start = data.find(b'$PBExportComments$')
        if pcode_start >= 0:
            end = data.find(b'\n', pcode_start)
            if end >= 0:
                pcode_start = end + 1
        else:
            pcode_start = 0
        
        # Decode instructions
        pcode = data[pcode_start:]
        context.instructions = self.decoder.decode_pcode(pcode, pcode_start)
        
        # Extract string pool and function names
        context.strings = self.decoder.strings
        # Function names would need to be populated from a symbol table or metadata
        # For now, we'll use empty dict
        context.functions = {}
        
        logger.info(f"Decoded {len(context.instructions)} instructions")
    
    def _analyze_control_flow(self, context: DecompilationContext) -> None:
        """Analyze control flow structures."""
        logger.debug("Analyzing control flow")
        
        context.control_blocks = self.cf_analyzer.analyze(context.instructions)
        
        logger.info(f"Identified {len(context.control_blocks)} control blocks")
    
    def _reconstruct_expressions(self, context: DecompilationContext) -> None:
        """Simulate stack execution to reconstruct expressions."""
        logger.debug("Reconstructing expressions from stack operations")
        
        # Reset stack simulator
        self.stack_sim.reset()
        
        # Copy function names to stack simulator
        self.stack_sim.function_names = context.functions
        
        # Process instructions in order
        for inst in context.instructions:
            try:
                self.stack_sim.simulate_instruction(
                    inst.address,
                    inst.opcode_name,
                    inst.operand_values
                )
            except Exception as e:
                logger.warning(f"Error simulating instruction at {inst.address:04X}: {e}")
                context.errors.append(f"Stack simulation error at {inst.address:04X}: {e}")
        
        # Get reconstructed statements
        context.statements = self.stack_sim.get_statements()
        
        logger.info(f"Reconstructed {len(context.statements)} statements")
    
    def _generate_source(self, context: DecompilationContext) -> str:
        """Generate PowerBuilder source code from decompiled components."""
        logger.debug("Generating PowerBuilder source")
        
        lines = []
        
        # Add file header
        lines.append(f"// Decompiled from: {context.file_path.name}")
        lines.append("// Generated by SIME Finch PowerBuilder Decompiler")
        lines.append("")
        
        # Determine the type of object from file extension
        file_type = context.file_path.suffix.lower()
        
        if file_type == '.fun':
            lines.extend(self._generate_function(context))
        elif file_type == '.win':
            lines.extend(self._generate_window(context))
        elif file_type == '.dwo':
            lines.extend(self._generate_datawindow(context))
        elif file_type == '.udo':
            lines.extend(self._generate_userobject(context))
        else:
            lines.extend(self._generate_generic(context))
        
        return '\n'.join(lines)
    
    def _generate_function(self, context: DecompilationContext) -> List[str]:
        """Generate PowerBuilder function source."""
        lines = []
        
        # Try to determine function signature
        func_name = context.file_path.stem
        
        # Look for function declaration pattern in instructions
        # This is a simplified version - real implementation would be more sophisticated
        lines.append(f"function {func_name}()")
        lines.append("")
        
        # Add variable declarations (if detected)
        if context.variables:
            for var_idx, var_info in context.variables.items():
                lines.append(f"    // Variable {var_idx}: {var_info}")
            lines.append("")
        
        # Add the decompiled statements
        if context.statements:
            for stmt in context.statements:
                lines.append(f"    {stmt}")
        else:
            # Fallback: show instruction-level pseudocode
            lines.extend(self._generate_instruction_pseudocode(context))
        
        lines.append("end function")
        
        return lines
    
    def _generate_window(self, context: DecompilationContext) -> List[str]:
        """Generate PowerBuilder window source."""
        lines = []
        
        window_name = context.file_path.stem
        lines.append(f"window {window_name}")
        lines.append("")
        
        # Add window content
        lines.extend(self._generate_generic_body(context))
        
        lines.append("end window")
        
        return lines
    
    def _generate_datawindow(self, context: DecompilationContext) -> List[str]:
        """Generate PowerBuilder DataWindow source."""
        lines = []
        
        dw_name = context.file_path.stem
        lines.append(f"datawindow {dw_name}")
        lines.append("")
        
        # DataWindows have different structure
        lines.append("// DataWindow object decompilation not fully implemented")
        lines.append("// Showing raw instruction data:")
        lines.append("")
        
        lines.extend(self._generate_instruction_pseudocode(context))
        
        return lines
    
    def _generate_userobject(self, context: DecompilationContext) -> List[str]:
        """Generate PowerBuilder user object source."""
        lines = []
        
        uo_name = context.file_path.stem
        lines.append(f"userobject {uo_name}")
        lines.append("")
        
        lines.extend(self._generate_generic_body(context))
        
        lines.append("end userobject")
        
        return lines
    
    def _generate_generic(self, context: DecompilationContext) -> List[str]:
        """Generate generic decompiled output."""
        lines = []
        
        lines.append(f"// Unknown object type: {context.file_path.suffix}")
        lines.append("")
        
        lines.extend(self._generate_generic_body(context))
        
        return lines
    
    def _generate_generic_body(self, context: DecompilationContext) -> List[str]:
        """Generate generic body content."""
        lines = []
        
        if context.statements:
            for stmt in context.statements:
                lines.append(f"    {stmt}")
        else:
            lines.extend(self._generate_instruction_pseudocode(context))
        
        return lines
    
    def _generate_instruction_pseudocode(self, context: DecompilationContext) -> List[str]:
        """Generate instruction-level pseudocode as fallback."""
        lines = []
        
        current_block = None
        indent = 0
        
        for inst in context.instructions:
            # Check if we're in a new control block
            block = self.cf_analyzer.get_block_at_address(inst.address)
            if block != current_block:
                if current_block and block and block.parent == current_block:
                    # Entering nested block
                    indent += 1
                elif current_block and block and current_block.parent == block:
                    # Exiting nested block
                    indent -= 1
                current_block = block
                
                # Add block header
                if block:
                    if block.type == BlockType.FUNCTION:
                        lines.append("// Function block")
                    elif block.type == BlockType.IF:
                        lines.append("    " * indent + "if <condition> then")
                        indent += 1
                    elif block.type == BlockType.ELSE:
                        indent -= 1
                        lines.append("    " * indent + "else")
                        indent += 1
            
            # Add the instruction
            prefix = "    " * indent
            
            # Try to make the output more readable
            if inst.opcode_name == "PUSH_CONST":
                lines.append(f"{prefix}// push {inst.operand_values[0] if inst.operand_values else '?'}")
            elif inst.opcode_name == "LOAD_VAR":
                var_idx = inst.operand_values[0] if inst.operand_values else '?'
                lines.append(f"{prefix}// load variable {var_idx}")
            elif inst.opcode_name == "STORE_VAR":
                var_idx = inst.operand_values[0] if inst.operand_values else '?'
                lines.append(f"{prefix}// store to variable {var_idx}")
            elif inst.opcode_name == "CALL_FUNCTION":
                func_idx = inst.operand_values[0] if inst.operand_values else '?'
                func_name = context.functions.get(func_idx, f"func_{func_idx}")
                lines.append(f"{prefix}// call {func_name}()")
            elif inst.opcode_name == "STRING":
                string_val = inst.operand_values[0] if inst.operand_values else ''
                lines.append(f"{prefix}// string \"{string_val}\"")
            else:
                # Generic instruction
                operands = ', '.join(str(op) for op in inst.operand_values)
                if operands:
                    lines.append(f"{prefix}// {inst.opcode_name} {operands}")
                else:
                    lines.append(f"{prefix}// {inst.opcode_name}")
        
        return lines
    
    def _generate_error_output(self, context: DecompilationContext) -> str:
        """Generate error output when decompilation fails."""
        lines = [
            f"// Decompilation failed for: {context.file_path.name}",
            "// Errors:",
        ]
        
        for error in context.errors:
            lines.append(f"//   - {error}")
        
        lines.extend([
            "",
            "// Partial output:",
            ""
        ])
        
        # Try to show what we could decode
        if context.instructions:
            lines.append(f"// Decoded {len(context.instructions)} instructions")
            lines.append("// First few instructions:")
            for inst in context.instructions[:10]:
                lines.append(f"//   {inst.text_format}")
        
        return '\n'.join(lines)


def main():
    """Command-line interface for the decompiler."""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python decompiler.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create decompiler and process file
    decompiler = PowerBuilderDecompiler()
    
    try:
        print(f"Decompiling {input_file}...")
        source = decompiler.decompile_file(input_file)
        
        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(source, encoding='utf-8')
        
        print(f"Successfully decompiled to {output_file}")
        
    except Exception as e:
        print(f"Error during decompilation: {e}")
        logger.exception("Decompilation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()