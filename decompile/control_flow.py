"""Control flow reconstruction for PowerBuilder P-code.

This module analyzes P-code instructions to reconstruct control flow structures
like if/else blocks, loops, and function boundaries.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from decompile.pcode_decoder import PCodeInstruction


class BlockType(Enum):
    """Types of control flow blocks."""
    FUNCTION = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    DO_WHILE = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()


@dataclass
class ControlBlock:
    """Represents a control flow block."""
    type: BlockType
    start_addr: int
    end_addr: int | None = None
    condition_addr: int | None = None
    target_addr: int | None = None  # For jumps
    parent: Optional['ControlBlock'] = None
    children: list['ControlBlock'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class ControlFlowAnalyzer:
    """Analyzes P-code instructions to reconstruct control flow."""

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self.instructions: list[PCodeInstruction] = []
        self.instruction_map: dict[int, PCodeInstruction] = {}
        self.jump_targets: set[int] = set()
        self.function_starts: list[int] = []
        self.blocks: list[ControlBlock] = []
        self.current_block: ControlBlock | None = None

    def analyze(self, instructions: list[PCodeInstruction]) -> list[ControlBlock]:
        """Analyze instructions and return control flow blocks.

        Args:
            instructions: List of P-code instructions

        Returns:
            List of control flow blocks
        """
        self.instructions = instructions

        # Build instruction map
        self.instruction_map = {inst.address: inst for inst in instructions}

        # First pass: identify jump targets and function starts
        self._identify_control_points()

        # Second pass: build control flow blocks
        self._build_blocks()

        return self.blocks

    def _identify_control_points(self) -> None:
        """Identify jump targets and function starts."""
        for inst in self.instructions:
            # Function starts
            if inst.opcode_name == 'FUNCTION_START':
                self.function_starts.append(inst.address)

            # Jump targets
            elif inst.opcode_name in ['JUMP', 'JUMP_IF_FALSE', 'JUMP_IF_TRUE']:
                if inst.operand_values:
                    # Extract target address
                    target = inst.operand_values[0]
                    if isinstance(target, str) and target.startswith('L_'):
                        # Label format
                        addr_str = target[2:]  # Remove 'L_' prefix
                        try:
                            target_addr = int(addr_str, 16)
                            self.jump_targets.add(target_addr)
                        except ValueError:
                            pass
                    elif isinstance(target, int):
                        self.jump_targets.add(target)

    def _build_blocks(self) -> None:
        """Build control flow blocks from instructions."""
        # Process each function
        for i, func_start in enumerate(self.function_starts):
            # Find function end
            if i + 1 < len(self.function_starts):
                func_end = self.function_starts[i + 1] - 1
            else:
                # Last function extends to end of instructions
                func_end = self.instructions[-1].address

            # Create function block
            func_block = ControlBlock(
                type=BlockType.FUNCTION,
                start_addr=func_start,
                end_addr=func_end,
            )
            self.blocks.append(func_block)

            # Analyze within function
            self._analyze_function(func_block, func_start, func_end)

    def _analyze_function(self, func_block: ControlBlock, start: int, end: int) -> None:
        """Analyze control flow within a function."""
        i = 0
        while i < len(self.instructions):
            inst = self.instructions[i]

            # Skip if outside function bounds
            if inst.address < start or inst.address > end:
                i += 1
                continue

            # Handle conditional jumps (if statements)
            if inst.opcode_name in ['JUMP_IF_FALSE', 'JUMP_IF_TRUE']:
                self._handle_conditional_jump(inst, func_block, i)

            # Handle unconditional jumps
            elif inst.opcode_name == 'JUMP':
                self._handle_unconditional_jump(inst, func_block, i)

            i += 1

    def _handle_conditional_jump(self, inst: PCodeInstruction, parent: ControlBlock, idx: int) -> None:
        """Handle conditional jump instructions."""
        # Extract target address
        target_addr = self._extract_jump_target(inst)
        if target_addr is None:
            return

        # Create if block
        if_block = ControlBlock(
            type=BlockType.IF,
            start_addr=inst.address,
            condition_addr=inst.address,
            target_addr=target_addr,
            parent=parent,
        )
        parent.children.append(if_block)

        # Try to find the end of the if block
        # Usually it's the instruction before the jump target
        if target_addr in self.instruction_map:
            if_block.end_addr = target_addr - 1

    def _handle_unconditional_jump(self, inst: PCodeInstruction, parent: ControlBlock, idx: int) -> None:
        """Handle unconditional jump instructions."""
        # Could be end of if block, loop continue/break, or goto
        target_addr = self._extract_jump_target(inst)
        if target_addr is None:
            return

        # Check if this is a backward jump (potential loop)
        if target_addr < inst.address:
            # Possible loop
            pass  # TODO: Implement loop detection

    def _extract_jump_target(self, inst: PCodeInstruction) -> int | None:
        """Extract jump target address from instruction."""
        if not inst.operand_values:
            return None

        target = inst.operand_values[0]

        # Handle label format
        if isinstance(target, str) and target.startswith('L_'):
            addr_str = target[2:]  # Remove 'L_' prefix
            try:
                return int(addr_str, 16)
            except ValueError:
                return None

        # Handle hex string format
        elif isinstance(target, str) and target.startswith('0x'):
            try:
                return int(target, 16)
            except ValueError:
                return None

        # Handle integer format
        elif isinstance(target, int):
            return target

        return None

    def get_block_at_address(self, addr: int) -> ControlBlock | None:
        """Get the control block containing the given address."""
        for block in self.blocks:
            if block.start_addr <= addr <= (block.end_addr or float('inf')):
                # Check children
                for child in block.children:
                    child_block = self._get_block_recursive(child, addr)
                    if child_block:
                        return child_block
                return block
        return None

    def _get_block_recursive(self, block: ControlBlock, addr: int) -> ControlBlock | None:
        """Recursively search for block containing address."""
        if block.start_addr <= addr <= (block.end_addr or float('inf')):
            # Check children first
            for child in block.children:
                child_block = self._get_block_recursive(child, addr)
                if child_block:
                    return child_block
            return block
        return None
