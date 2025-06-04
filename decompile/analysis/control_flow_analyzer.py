"""Control flow analyzer for PowerBuilder P-code.

This module analyzes P-code instructions to reconstruct high-level
control flow structures like loops, conditionals, and exception handling.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional

from .pcode_decoder_v2 import PCodeInstruction

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Types of control flow blocks."""
    BASIC = auto()
    IF = auto()
    WHILE = auto()
    FOR = auto()
    DO_WHILE = auto()
    REPEAT_UNTIL = auto()
    CHOOSE_CASE = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    EVENT = auto()
    FUNCTION = auto()


@dataclass
class ControlBlock:
    """Represents a control flow block."""
    type: BlockType
    start_addr: int
    end_addr: int
    instructions: list[PCodeInstruction] = field(default_factory=list)
    statements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # For nested structures
    then_block: Optional['ControlBlock'] = None
    else_block: Optional['ControlBlock'] = None
    body: Optional['ControlBlock'] = None
    cases: list[dict[str, Any]] = field(default_factory=list)
    default_case: Optional['ControlBlock'] = None
    catch_blocks: list[dict[str, Any]] = field(default_factory=list)
    finally_block: Optional['ControlBlock'] = None


class ControlFlowAnalyzer:
    """Analyzes P-code to reconstruct control flow."""

    def __init__(self):
        """Initialize the analyzer."""
        self.blocks: list[ControlBlock] = []
        self.labels: dict[int, str] = {}
        self.jump_targets: set[int] = set()

    def analyze(self, instructions: list[PCodeInstruction]) -> list[ControlBlock]:
        """Analyze instructions and return control flow blocks.
        
        Args:
            instructions: List of P-code instructions
            
        Returns:
            List of control flow blocks
        """
        if not instructions:
            return []

        # First pass: identify jump targets and labels
        self._identify_jump_targets(instructions)

        # Second pass: split into basic blocks
        basic_blocks = self._split_basic_blocks(instructions)

        # Third pass: identify and merge control structures
        control_blocks = self._identify_control_structures(basic_blocks)

        return control_blocks

    def _identify_jump_targets(self, instructions: list[PCodeInstruction]) -> None:
        """Identify all jump targets in the code."""
        for inst in instructions:
            if inst.opcode_name in ['JUMP', 'JUMPTRUE', 'JUMPFALSE',
                                   'BRFALSE', 'BRTRUE', 'JMP']:
                if inst.operand_values and isinstance(inst.operand_values[0], int):
                    # Calculate absolute target
                    target = inst.address + 1 + len(inst.operands) + inst.operand_values[0]
                    self.jump_targets.add(target)
                    self.labels[target] = f"L_{target:04X}"

    def _split_basic_blocks(self, instructions: list[PCodeInstruction]) -> list[ControlBlock]:
        """Split instructions into basic blocks."""
        blocks = []
        current_block = None

        for i, inst in enumerate(instructions):
            # Start new block if:
            # 1. This is the first instruction
            # 2. This instruction is a jump target
            # 3. Previous instruction was a jump/return
            start_new_block = (
                i == 0 or
                inst.address in self.jump_targets or
                (i > 0 and self._is_terminator(instructions[i-1]))
            )

            if start_new_block:
                if current_block:
                    blocks.append(current_block)
                current_block = ControlBlock(
                    type=BlockType.BASIC,
                    start_addr=inst.address,
                    end_addr=inst.address,
                )

            current_block.instructions.append(inst)
            current_block.end_addr = inst.address

        if current_block:
            blocks.append(current_block)

        return blocks

    def _is_terminator(self, inst: PCodeInstruction) -> bool:
        """Check if instruction terminates a basic block."""
        return inst.opcode_name in [
            'JUMP', 'JUMPTRUE', 'JUMPFALSE', 'RETURN', 'HALT',
            'THROW', 'RETHROW', 'BRFALSE', 'BRTRUE', 'JMP',
        ]

    def _identify_control_structures(self, basic_blocks: list[ControlBlock]) -> list[ControlBlock]:
        """Identify high-level control structures from basic blocks."""
        control_blocks = []
        i = 0

        while i < len(basic_blocks):
            block = basic_blocks[i]

            # Check for various patterns
            if_block = self._check_if_pattern(basic_blocks, i)
            if if_block:
                control_blocks.append(if_block)
                # Skip blocks that were merged into the if
                i = self._find_block_index(basic_blocks, if_block.end_addr) + 1
                continue

            while_block = self._check_while_pattern(basic_blocks, i)
            if while_block:
                control_blocks.append(while_block)
                i = self._find_block_index(basic_blocks, while_block.end_addr) + 1
                continue

            for_block = self._check_for_pattern(basic_blocks, i)
            if for_block:
                control_blocks.append(for_block)
                i = self._find_block_index(basic_blocks, for_block.end_addr) + 1
                continue

            # No pattern matched, keep as basic block
            control_blocks.append(block)
            i += 1

        return control_blocks

    def _check_if_pattern(self, blocks: list[ControlBlock], start_idx: int) -> ControlBlock | None:
        """Check for IF-THEN-ELSE pattern."""
        if start_idx >= len(blocks):
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        last_inst = block.instructions[-1]

        # Check for conditional jump
        if last_inst.opcode_name in ['JUMPFALSE', 'JUMPTRUE', 'BRFALSE', 'BRTRUE']:
            if_block = ControlBlock(
                type=BlockType.IF,
                start_addr=block.start_addr,
                end_addr=block.end_addr,
                metadata={'condition': self._extract_condition(block)},
            )

            # Find then and else branches
            jump_target = self._get_jump_target(last_inst)

            # Then branch is the next block(s) until jump target
            then_start_idx = start_idx + 1
            then_end_idx = self._find_block_index(blocks, jump_target)

            if then_start_idx < len(blocks) and then_end_idx > then_start_idx:
                then_instructions = []
                for idx in range(then_start_idx, then_end_idx):
                    if idx < len(blocks):
                        then_instructions.extend(blocks[idx].instructions)

                if then_instructions:
                    if_block.then_block = ControlBlock(
                        type=BlockType.BASIC,
                        start_addr=then_instructions[0].address,
                        end_addr=then_instructions[-1].address,
                        instructions=then_instructions,
                    )

                # Update end address
                if_block.end_addr = blocks[then_end_idx - 1].end_addr if then_end_idx > 0 else if_block.end_addr

            # Check for else branch (if then branch ends with jump)
            if (if_block.then_block and
                if_block.then_block.instructions and
                if_block.then_block.instructions[-1].opcode_name == 'JUMP'):

                else_jump_target = self._get_jump_target(if_block.then_block.instructions[-1])
                else_start_idx = then_end_idx
                else_end_idx = self._find_block_index(blocks, else_jump_target)

                if else_start_idx < len(blocks) and else_end_idx > else_start_idx:
                    else_instructions = []
                    for idx in range(else_start_idx, else_end_idx):
                        if idx < len(blocks):
                            else_instructions.extend(blocks[idx].instructions)

                    if else_instructions:
                        if_block.else_block = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=else_instructions[0].address,
                            end_addr=else_instructions[-1].address,
                            instructions=else_instructions,
                        )

                        # Update end address
                        if_block.end_addr = else_jump_target

            return if_block

        return None

    def _check_while_pattern(self, blocks: list[ControlBlock], start_idx: int) -> ControlBlock | None:
        """Check for WHILE loop pattern."""
        if start_idx >= len(blocks):
            return None

        block = blocks[start_idx]

        # Look for backward jump that creates a loop
        for i in range(start_idx + 1, len(blocks)):
            if i >= len(blocks):
                break

            check_block = blocks[i]
            if not check_block.instructions:
                continue

            last_inst = check_block.instructions[-1]

            # Check for backward jump
            if last_inst.opcode_name in ['JUMP', 'JUMPTRUE']:
                target = self._get_jump_target(last_inst)

                # Is it jumping back to our block or before?
                if target <= block.start_addr:
                    # Found a loop
                    while_block = ControlBlock(
                        type=BlockType.WHILE,
                        start_addr=target,
                        end_addr=check_block.end_addr,
                        metadata={'condition': self._extract_condition(block)},
                    )

                    # Collect loop body
                    body_instructions = []
                    for idx in range(start_idx, i + 1):
                        if idx < len(blocks):
                            body_instructions.extend(blocks[idx].instructions)

                    while_block.body = ControlBlock(
                        type=BlockType.BASIC,
                        start_addr=body_instructions[0].address if body_instructions else target,
                        end_addr=body_instructions[-1].address if body_instructions else target,
                        instructions=body_instructions,
                    )

                    return while_block

        return None

    def _check_for_pattern(self, blocks: list[ControlBlock], start_idx: int) -> ControlBlock | None:
        """Check for FOR loop pattern."""
        # FOR loops in PowerBuilder typically have:
        # 1. Initialization
        # 2. Condition check
        # 3. Body
        # 4. Increment
        # 5. Jump back to condition

        # This is a simplified check - real FOR loop detection would be more complex
        if start_idx >= len(blocks) - 2:
            return None

        # Look for initialization followed by condition
        init_block = blocks[start_idx]

        # Check if next block has a conditional jump
        if start_idx + 1 < len(blocks):
            cond_block = blocks[start_idx + 1]
            if (cond_block.instructions and
                cond_block.instructions[-1].opcode_name in ['JUMPFALSE', 'BRFALSE']):

                # Look for backward jump that completes the loop
                jump_target = self._get_jump_target(cond_block.instructions[-1])

                for i in range(start_idx + 2, len(blocks)):
                    if i >= len(blocks):
                        break

                    check_block = blocks[i]
                    if not check_block.instructions:
                        continue

                    last_inst = check_block.instructions[-1]

                    if (last_inst.opcode_name == 'JUMP' and
                        self._get_jump_target(last_inst) == cond_block.start_addr):

                        # Found a FOR loop pattern
                        for_block = ControlBlock(
                            type=BlockType.FOR,
                            start_addr=init_block.start_addr,
                            end_addr=check_block.end_addr,
                            metadata={
                                'variable': 'loop_var',  # Would need to extract from init
                                'start': '0',
                                'end': 'unknown',
                                'step': '1',
                            },
                        )

                        # Collect loop body (between condition and increment)
                        body_instructions = []
                        for idx in range(start_idx + 2, i):
                            if idx < len(blocks):
                                body_instructions.extend(blocks[idx].instructions)

                        for_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].address if body_instructions else cond_block.end_addr,
                            end_addr=body_instructions[-1].address if body_instructions else check_block.start_addr,
                            instructions=body_instructions,
                        )

                        return for_block

        return None

    def _extract_condition(self, block: ControlBlock) -> str:
        """Extract condition expression from block."""
        # This would analyze the instructions to reconstruct the condition
        # For now, return a placeholder
        return "condition_expression"

    def _get_jump_target(self, inst: PCodeInstruction) -> int:
        """Get the target address of a jump instruction."""
        if inst.operand_values and isinstance(inst.operand_values[0], int):
            # Calculate absolute target
            return inst.address + 1 + len(inst.operands) + inst.operand_values[0]
        return inst.address

    def _find_block_index(self, blocks: list[ControlBlock], address: int) -> int:
        """Find the index of the block containing the given address."""
        for i, block in enumerate(blocks):
            if block.start_addr <= address <= block.end_addr:
                return i
        return len(blocks)  # Not found, return past end
