"""PowerBuilder P-code to source code decompiler.

This module converts decoded P-code instructions to PowerBuilder source code.
"""

from dataclasses import dataclass
from pathlib import Path

from decompile.legacy.control_flow_v1 import BlockType, ControlBlock, ControlFlowAnalyzer
from decompile.legacy.expression_builder import ExpressionBuilder
from decompile.legacy.pcode_decoder_v1 import PCodeDecoder, PCodeInstruction


@dataclass
class DecompiledFunction:
    """Represents a decompiled PowerBuilder function."""
    name: str
    return_type: str
    parameters: list[tuple]  # (name, type)
    body: list[str]
    local_vars: list[tuple]  # (name, type)


class PCodeToSource:
    """Converts P-code instructions to PowerBuilder source code."""

    def __init__(self) -> None:
        """Initialize the decompiler."""
        self.decoder = PCodeDecoder()
        self.control_flow = ControlFlowAnalyzer()
        self.expression_builder = ExpressionBuilder()
        self.reset()

    def reset(self) -> None:
        """Reset decompiler state."""
        self.functions = []
        self.current_function = None
        self.strings = {}
        self.variables = {}
        self.code_lines = []
        self.indent_level = 0

    def decompile_file(self, file_path: Path) -> str:
        """Decompile a PowerBuilder binary file to source code.

        Args:
            file_path: Path to the binary file

        Returns:
            Decompiled PowerBuilder source code
        """
        # Read the file
        with open(file_path, 'rb') as f:
            data = f.read()

        # Find P-code start
        header2 = b'$PBExportComments$'
        pos = data.find(header2)
        pcode_start = -1
        if pos >= 0:
            # Find end of header line
            end = data.find(b'\n', pos)
            if end >= 0:
                pcode_start = end + 1

        if pcode_start < 0:
            return f"// Failed to find P-code start in {file_path}"

        # Decode the P-code into instructions
        pcode = data[pcode_start:]
        instructions = self.decoder.decode_pcode(pcode, pcode_start)

        if not instructions:
            return f"// Failed to decode {file_path}"

        # Extract metadata from strings
        self.strings = self.decoder.strings

        # Determine file type from extension
        file_ext = file_path.suffix.lower()

        if file_ext == '.fun':
            return self.decompile_function(instructions, file_path.stem)
        if file_ext == '.win':
            return self.decompile_window(instructions, file_path.stem)
        if file_ext == '.dwo':
            return self.decompile_datawindow(instructions, file_path.stem)
        if file_ext == '.udo':
            return self.decompile_userobject(instructions, file_path.stem)
        return self.decompile_generic(instructions, file_path.stem)

    def decompile_function(self, instructions: list[PCodeInstruction], name: str) -> str:
        """Decompile function P-code to source."""
        source_lines = []

        # Add export headers
        source_lines.append(f"$PBExportHeader${name}.fun")
        source_lines.append("$PBExportComments$")
        source_lines.append("")

        # Find function name and parameters in strings from instructions
        func_name = name
        param_names = []
        for inst in instructions:
            if inst.opcode_name == 'STRING' and inst.operand_values:
                value = inst.operand_values[0]
                if value.startswith('of_') or value.startswith('f_'):
                    func_name = value
                elif value.startswith('as_') or value.startswith('a_'):
                    # Likely a parameter name
                    param_names.append(value)

        # Extract string constants for expression builder
        for inst in instructions:
            if inst.opcode_name == 'STRING' and inst.operand_values:
                # Store string at instruction address for reference
                self.expression_builder.strings[inst.address] = inst.operand_values[0]

        # Start function declaration
        # TODO: Determine actual return type and parameters from P-code
        if param_names:
            params = ', '.join(f"string {p}" for p in param_names)
            source_lines.append(f"function string {func_name}({params})")
        else:
            source_lines.append(f"function integer {func_name}()")
        source_lines.append("")

        # Process instructions to generate body
        body_lines = self._process_instructions(instructions)
        source_lines.extend(body_lines)

        # End function
        source_lines.append("")
        source_lines.append("end function")

        return '\n'.join(source_lines)

    def decompile_window(self, instructions: list[PCodeInstruction], name: str) -> str:
        """Decompile window P-code to source."""
        source_lines = []

        # Add export headers
        source_lines.append(f"$PBExportHeader${name}.win")
        source_lines.append("$PBExportComments$")
        source_lines.append("")

        # Window declaration
        source_lines.append(f"type {name} from window")
        source_lines.append("end type")
        source_lines.append("")

        # Global type definition
        source_lines.append(f"global {name} {name}")
        source_lines.append("")

        # TODO: Add control definitions and event handlers
        source_lines.append("// Window controls and events would be decompiled here")

        return '\n'.join(source_lines)

    def decompile_datawindow(self, instructions: list[PCodeInstruction], name: str) -> str:
        """Decompile DataWindow P-code to source."""
        source_lines = []

        # Add export headers
        source_lines.append(f"$PBExportHeader${name}.dwo")
        source_lines.append("$PBExportComments$")
        source_lines.append("")

        # DataWindow object starts with release info
        source_lines.append("release 10;")
        source_lines.append('datawindow(units=0 timer_interval=0 processing=0 HTMLDW=no)')
        source_lines.append("")

        # TODO: Extract actual DataWindow definition from P-code
        source_lines.append("// DataWindow definition would be decompiled here")

        return '\n'.join(source_lines)

    def decompile_userobject(self, instructions: list[PCodeInstruction], name: str) -> str:
        """Decompile user object P-code to source."""
        source_lines = []

        # Add export headers
        source_lines.append(f"$PBExportHeader${name}.udo")
        source_lines.append("$PBExportComments$")
        source_lines.append("")

        # User object declaration
        source_lines.append(f"type {name} from userobject")
        source_lines.append("end type")
        source_lines.append("")

        source_lines.append(f"global {name} {name}")
        source_lines.append("")

        # TODO: Add properties and methods
        source_lines.append("// User object properties and methods would be decompiled here")

        return '\n'.join(source_lines)

    def decompile_generic(self, instructions: list[PCodeInstruction], name: str) -> str:
        """Generic decompilation for unknown file types."""
        source_lines = []

        source_lines.append(f"// Decompiled from {name}")
        source_lines.append("// File type not recognized")
        source_lines.append("")

        # Show decoded instructions as comments
        source_lines.append("// P-code instructions:")
        for inst in instructions[:50]:  # First 50 instructions
            source_lines.append(f"// {inst.text_format}")

        if len(instructions) > 50:
            source_lines.append(f"// ... and {len(instructions) - 50} more instructions")

        return '\n'.join(source_lines)

    def _process_instructions(self, instructions: list[PCodeInstruction]) -> list[str]:
        """Process P-code instructions to generate source code lines."""
        lines = []

        # Analyze control flow
        blocks = self.control_flow.analyze(instructions)

        # Extract strings and potential variable names
        strings = []
        for inst in instructions:
            if inst.opcode_name == 'STRING' and inst.operand_values:
                strings.append(inst.operand_values[0])

        # Look for variable patterns
        variables = set()
        for _i, inst in enumerate(instructions):
            if inst.opcode_name.startswith('LOAD_VAR'):
                if inst.operand_values:
                    var_index = inst.operand_values[0]
                    variables.add(var_index)

        # Generate variable declarations
        if variables:
            lines.append("// Local variables")
            for var_idx in sorted(variables)[:10]:  # Show first 10
                lines.append(f"any lv_{var_idx}")
            lines.append("")

        # Process main function block
        if blocks:
            main_func = blocks[0]  # First function
            lines.extend(self._process_block(main_func, instructions))
        else:
            # Fallback: show basic pattern recognition
            lines.extend(self._basic_pattern_recognition(instructions))

        return lines

    def _process_block(self, block: ControlBlock, instructions: list[PCodeInstruction]) -> list[str]:
        """Process a control flow block."""
        lines = []

        # Get instructions in this block
        block_instructions = [
            inst for inst in instructions
            if block.start_addr <= inst.address <= (block.end_addr or float('inf'))
        ]

        # Process based on block type
        if block.type == BlockType.FUNCTION:
            # Skip function start marker
            # Try to use expression builder for sequences
            lines.extend(self._process_instruction_sequence(block_instructions[1:]))

            # Process child blocks
            for child in block.children:
                if child.type == BlockType.IF:
                    lines.append("")

                    # Try to reconstruct the condition
                    condition = self._reconstruct_condition(child, instructions)
                    lines.append(f"if {condition} then")

                    self.indent_level += 1
                    child_lines = self._process_block(child, instructions)
                    for line in child_lines:
                        lines.append("    " + line)
                    self.indent_level -= 1
                    lines.append("end if")

        return lines

    def _process_instruction_sequence(self, instructions: list[PCodeInstruction]) -> list[str]:
        """Process a sequence of instructions using expression builder."""
        lines = []

        # Use expression builder to analyze sequences
        self.expression_builder.reset()

        i = 0
        while i < len(instructions):
            inst = instructions[i]

            # Skip certain instructions
            if inst.opcode_name in ['NOP', 'MARKER1', 'MARKER2', 'MARKER3', 'PADDING', 'STRING']:
                i += 1
                continue

            # Look for expression patterns
            if inst.opcode_name.startswith('LOAD_'):
                # Look ahead for expression sequence
                expr_end = self._find_expression_end(instructions, i)
                if expr_end > i:
                    # Process expression sequence
                    expr_instructions = instructions[i:expr_end+1]
                    statements = self.expression_builder.analyze_expression_sequence(expr_instructions)
                    lines.extend(statements)
                    i = expr_end + 1
                    continue

            # Handle other instructions
            line = self._process_single_instruction(inst)
            if line:
                lines.append(line)
            i += 1

        return lines

    def _find_expression_end(self, instructions: list[PCodeInstruction], start: int) -> int:
        """Find the end of an expression sequence."""
        i = start
        while i < len(instructions):
            inst = instructions[i]
            # Expression ends with STORE operation
            if inst.opcode_name.startswith('STORE_'):
                return i
            # Or if we hit a control flow instruction
            if inst.opcode_name in ['JUMP', 'JUMP_IF_FALSE', 'JUMP_IF_TRUE', 'CALL_FUNCTION', 'CALL_METHOD']:
                return i - 1
            i += 1
        return start

    def _reconstruct_condition(self, if_block: ControlBlock, instructions: list[PCodeInstruction]) -> str:
        """Try to reconstruct the condition for an if statement."""
        # Find the conditional jump instruction
        if if_block.condition_addr:
            for inst in instructions:
                if inst.address == if_block.condition_addr:
                    # Look back for comparison
                    idx = instructions.index(inst)
                    if idx > 0:
                        # Simple heuristic - look for recent loads/compares
                        for j in range(max(0, idx-5), idx):
                            if instructions[j].opcode_name == 'COMPARE':
                                return "/* condition */"
                    break
        return "/* condition */"

    def _process_single_instruction(self, inst: PCodeInstruction) -> str | None:
        """Process a single instruction and return PowerBuilder code."""
        # Skip certain instructions
        if inst.opcode_name in ['NOP', 'MARKER1', 'MARKER2', 'MARKER3', 'PADDING']:
            return None

        # Handle specific patterns
        if inst.opcode_name == 'STRING':
            # String constants are usually data, not code
            return None

        # Function calls that weren't caught by expression builder
        if inst.opcode_name in ['CALL_FUNCTION', 'CALL_METHOD']:
            return "// Function call"

        # Default: return as comment for now
        return f"// {inst.opcode_name} {' '.join(str(v) for v in inst.operand_values)}"

    def _basic_pattern_recognition(self, instructions: list[PCodeInstruction]) -> list[str]:
        """Basic pattern recognition when control flow analysis fails."""
        lines = []

        # Try expression builder on the whole sequence
        statements = self.expression_builder.analyze_expression_sequence(instructions)
        if statements:
            lines.extend(statements)

        # If no patterns found, show summary
        if not lines:
            lines.append("// P-code decompilation in progress")
            lines.append("// This function contains binary P-code that needs further analysis")
            lines.append("")
            lines.append("// Summary:")
            lines.append(f"// - {len(instructions)} total instructions")

            # Count instruction types
            opcode_counts = {}
            for inst in instructions:
                base_opcode = inst.opcode_name.split('_')[0]
                opcode_counts[base_opcode] = opcode_counts.get(base_opcode, 0) + 1

            for opcode, count in sorted(opcode_counts.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"// - {count} {opcode} operations")

        return lines


def main() -> None:
    """Test the decompiler with sample files."""
    base_path = Path("output/test_bytes_fix/dcm_accounting.pbd/dcm_accounting.pbd")

    # Test with different file types
    test_files = [
        base_path / "of_get_linked_acc.fun",
        base_path / "w_balance_sheet.win",
        base_path / "d_accounttype_dddw.dwo",
    ]

    decompiler = PCodeToSource()

    for file_path in test_files:
        if file_path.exists():

            source = decompiler.decompile_file(file_path)

            # Save decompiled source
            output_path = file_path.with_suffix('.pb')
            output_path.write_text(source)


if __name__ == "__main__":
    main()
