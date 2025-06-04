"""Enhanced structured decompiler for PowerBuilder P-code.

This module coordinates the control flow analysis, expression lifting,
and output formatting to produce high-quality decompiled PowerBuilder code.
"""

import logging
from pathlib import Path

from ..analysis.control_flow_analyzer import BlockType, ControlBlock, ControlFlowAnalyzer
from ..core.expression_lifter import Expression, ExpressionLifter
from ..core.output_formatter import OutputFormatter
from ..core.pcode_decoder import DecodedObject, PCodeDecoderV2

logger = logging.getLogger(__name__)


class StructuredDecompiler:
    """Enhanced decompiler that produces structured PowerBuilder code."""

    def __init__(self, version: str = "pb80_0"):
        """Initialize the structured decompiler.
        
        Args:
            version: PowerBuilder version for opcode tables
        """
        self.version = version
        self.decoder = PCodeDecoderV2(version)
        self.cf_analyzer = ControlFlowAnalyzer()
        self.formatter = OutputFormatter()

        # Symbol tables
        self.locals: dict[int, str] = {}
        self.globals: dict[int, str] = {}
        self.methods: dict[int, str] = {}
        self.fields: dict[int, str] = {}
        self.strings: dict[int, str] = {}
        self.classes: dict[int, str] = {}

    def decompile_object(self, pbd_file, offset: int, size: int,
                        object_name: str) -> DecodedObject | None:
        """Decompile a single object from PBD.
        
        Args:
            pbd_file: Open PBD file handle
            offset: Object offset in PBD
            size: Object size
            object_name: Name of the object
            
        Returns:
            DecodedObject with structured code or None
        """
        # Decode P-code instructions
        decoded_obj = self.decoder.decode_pbd_object(pbd_file, offset, size, object_name)

        if not decoded_obj or not decoded_obj.instructions:
            logger.warning(f"No instructions found for {object_name}")
            return None

        # Extract symbol information from instructions
        self._extract_symbols(decoded_obj)

        # Analyze control flow
        control_blocks = self.cf_analyzer.analyze(decoded_obj.instructions)

        # Lift expressions and reconstruct statements
        self._lift_expressions(control_blocks)

        # Store structured information
        decoded_obj.metadata['control_blocks'] = control_blocks
        decoded_obj.metadata['locals'] = self.locals
        decoded_obj.metadata['methods'] = self.methods

        return decoded_obj

    def decompile_file(self, input_path: Path, output_path: Path | None = None) -> bool:
        """Decompile a standalone P-code file.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (optional)
            
        Returns:
            True if successful
        """
        try:
            # Read the file
            with open(input_path, 'rb') as f:
                data = f.read()

            # Create a mock PBD file object
            from io import BytesIO
            mock_pbd = BytesIO(data)

            # Decompile
            object_name = input_path.stem
            decoded_obj = self.decompile_object(mock_pbd, 0, len(data), object_name)

            if not decoded_obj:
                return False

            # Generate output
            control_blocks = decoded_obj.metadata.get('control_blocks', [])
            output_lines = self.formatter.format_object(
                decoded_obj, control_blocks, str(input_path),
            )

            # Write output
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(output_lines))
            else:
                print('\n'.join(output_lines))

            return True

        except Exception as e:
            logger.error(f"Failed to decompile {input_path}: {e}")
            return False

    def _extract_symbols(self, decoded_obj: DecodedObject) -> None:
        """Extract symbol information from instructions."""
        # Reset symbol tables
        self.locals.clear()
        self.globals.clear()
        self.methods.clear()
        self.fields.clear()
        self.strings.clear()
        self.classes.clear()

        # Standard locals
        self.locals[0] = "this"
        self.locals[1] = "return_value"

        # Scan instructions for symbol information
        for inst in decoded_obj.instructions:
            opcode = inst.opcode_name

            # String constants
            if opcode == "STRING" and inst.operand_values:
                idx = len(self.strings)
                self.strings[idx] = inst.operand_values[0]

            # Method names from calls
            elif opcode in ["GLOBFUNCCALL", "DOTFUNCCALL", "FUNCCALL"]:
                if inst.operand_values:
                    idx = inst.operand_values[0]
                    # Try to deduce method name from context
                    # This would need more sophisticated analysis
                    if idx not in self.methods:
                        if isinstance(idx, int):
                            self.methods[idx] = f"method_{idx:04x}"
                        else:
                            self.methods[idx] = f"method_{idx}"

            # Variable declarations (would need pattern matching)
            elif opcode == "DECLARE_LOCAL":
                if len(inst.operand_values) >= 2:
                    idx = inst.operand_values[0]
                    var_type = inst.operand_values[1]
                    self.locals[idx] = f"local_{idx}"

    def _lift_expressions(self, control_blocks: list[ControlBlock]) -> None:
        """Lift expressions in all control blocks."""
        for block in control_blocks:
            self._lift_block_expressions(block)

    def _lift_block_expressions(self, block: ControlBlock) -> None:
        """Lift expressions in a single control block."""
        if not block.instructions:
            return

        # Create expression lifter with our symbol tables
        lifter = ExpressionLifter()
        lifter.locals = self.locals.copy()
        lifter.globals = self.globals.copy()
        lifter.methods = self.methods.copy()
        lifter.fields = self.fields.copy()
        lifter.strings = self.strings.copy()

        # Process different block types
        if block.type == BlockType.IF:
            self._lift_if_block(block, lifter)
        elif block.type == BlockType.WHILE:
            self._lift_while_block(block, lifter)
        elif block.type == BlockType.FOR:
            self._lift_for_block(block, lifter)
        elif block.type == BlockType.CHOOSE_CASE:
            self._lift_case_block(block, lifter)
        else:
            # Basic block
            results = lifter.lift_instruction_sequence(block.instructions)
            block.statements = []

            for result in results:
                if isinstance(result, Expression):
                    block.statements.append(result.to_string())
                else:
                    block.statements.append(result)

        # Process nested blocks
        if hasattr(block, 'then_block') and block.then_block:
            self._lift_block_expressions(block.then_block)

        if hasattr(block, 'else_block') and block.else_block:
            self._lift_block_expressions(block.else_block)

        if hasattr(block, 'body') and block.body:
            self._lift_block_expressions(block.body)

        if hasattr(block, 'cases'):
            for case in block.cases:
                if 'body' in case:
                    self._lift_block_expressions(case['body'])

    def _lift_if_block(self, block: ControlBlock, lifter: ExpressionLifter) -> None:
        """Lift expressions for IF block."""
        # Extract condition from instructions before the jump
        condition_instructions = []

        for inst in block.instructions:
            if inst.opcode_name in ['JUMPFALSE', 'JUMPTRUE', 'BRFALSE', 'BRTRUE']:
                # This is the conditional jump
                break
            condition_instructions.append(inst)

        # Lift condition
        if condition_instructions:
            results = lifter.lift_instruction_sequence(condition_instructions)

            # The condition should be on the stack
            if lifter.stack:
                condition = lifter.stack.pop()
                block.metadata['condition'] = condition.to_string()

            # Handle any statements generated during condition evaluation
            block.statements = []
            for result in results:
                if isinstance(result, str):
                    block.statements.append(result)

    def _lift_while_block(self, block: ControlBlock, lifter: ExpressionLifter) -> None:
        """Lift expressions for WHILE block."""
        # For while loops, we need to identify the condition
        # This is typically at the beginning of the loop
        if block.body and block.body.instructions:
            # Look for condition check at start
            condition_instructions = []

            for i, inst in enumerate(block.body.instructions):
                if inst.opcode_name in ['JUMPFALSE', 'BRFALSE']:
                    # Found loop exit condition
                    condition_instructions = block.body.instructions[:i]
                    break

            if condition_instructions:
                results = lifter.lift_instruction_sequence(condition_instructions)

                if lifter.stack:
                    condition = lifter.stack.pop()
                    block.metadata['condition'] = condition.to_string()

    def _lift_for_block(self, block: ControlBlock, lifter: ExpressionLifter) -> None:
        """Lift expressions for FOR block."""
        # FOR loops have initialization, condition, and increment
        # This requires pattern matching on the instructions

        # For now, use placeholder
        if 'variable' not in block.metadata:
            block.metadata['variable'] = 'i'
        if 'start' not in block.metadata:
            block.metadata['start'] = '1'
        if 'end' not in block.metadata:
            block.metadata['end'] = '10'
        if 'step' not in block.metadata:
            block.metadata['step'] = '1'

    def _lift_case_block(self, block: ControlBlock, lifter: ExpressionLifter) -> None:
        """Lift expressions for CHOOSE CASE block."""
        # Extract the expression being switched on
        if block.instructions:
            # Look for the expression evaluation before the case jumps
            switch_instructions = []

            for inst in block.instructions:
                if inst.opcode_name in ['SWITCH', 'CASE_JUMP']:
                    break
                switch_instructions.append(inst)

            if switch_instructions:
                results = lifter.lift_instruction_sequence(switch_instructions)

                if lifter.stack:
                    expr = lifter.stack.pop()
                    block.metadata['expression'] = expr.to_string()


def decompile_with_structure(input_file: Path, output_file: Path | None = None,
                           version: str = "pb80_0") -> bool:
    """Convenience function to decompile a file with structured output.
    
    Args:
        input_file: Path to input P-code file
        output_file: Path to output file (optional)
        version: PowerBuilder version
        
    Returns:
        True if successful
    """
    decompiler = StructuredDecompiler(version)
    return decompiler.decompile_file(input_file, output_file)
