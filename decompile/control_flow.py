"""Control flow reconstruction for PowerBuilder P-code.

This module analyzes P-code instructions to reconstruct control flow structures
like if/else blocks, loops, and function boundaries.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

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
    SWITCH = auto()
    CASE = auto()


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
    # Additional properties for pattern detection
    is_getter: bool = False
    is_setter: bool = False
    case_values: list[Any] = None  # For switch/case blocks

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.case_values is None:
            self.case_values = []


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

        # After basic blocks are identified, analyze patterns
        self.analyze_patterns()

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
            # Possible loop - analyze the pattern
            self._detect_loop_pattern(inst, target_addr, parent)

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

    def _detect_loop_pattern(self, jump_inst: PCodeInstruction, target_addr: int, parent: ControlBlock) -> None:
        """Detect and classify loop patterns from backward jumps."""
        # Find the instruction at the target address
        if target_addr not in self.instruction_map:
            return

        target_inst = self.instruction_map[target_addr]

        # Look for patterns to identify loop type
        # Pattern 1: WHILE loop - conditional jump at the beginning
        if self._is_while_loop_pattern(target_addr, jump_inst.address):
            self._create_while_loop(target_addr, jump_inst.address, parent)

        # Pattern 2: DO-WHILE loop - unconditional jump back, condition at end
        elif self._is_do_while_pattern(target_addr, jump_inst.address):
            self._create_do_while_loop(target_addr, jump_inst.address, parent)

        # Pattern 3: FOR loop - has initialization, condition, and increment
        elif self._is_for_loop_pattern(target_addr, jump_inst.address):
            self._create_for_loop(target_addr, jump_inst.address, parent)

    def _is_while_loop_pattern(self, start: int, end: int) -> bool:
        """Check if the code pattern matches a while loop."""
        # Look for conditional jump near the start
        for addr in range(start, min(start + 10, end)):
            if addr in self.instruction_map:
                inst = self.instruction_map[addr]
                if inst.opcode_name in ['JUMP_IF_FALSE', 'JUMP_IF_TRUE']:
                    target = self._extract_jump_target(inst)
                    # Check if it jumps past the loop
                    if target and target > end:
                        return True
        return False

    def _is_do_while_pattern(self, start: int, end: int) -> bool:
        """Check if the code pattern matches a do-while loop."""
        # Look for conditional jump near the end
        for addr in range(max(start, end - 10), end):
            if addr in self.instruction_map:
                inst = self.instruction_map[addr]
                if inst.opcode_name in ['JUMP_IF_TRUE', 'JUMP_IF_FALSE']:
                    target = self._extract_jump_target(inst)
                    # Check if it jumps back to loop start
                    if target and target == start:
                        return True
        return False

    def _is_for_loop_pattern(self, start: int, end: int) -> bool:
        """Check if the code pattern matches a for loop."""
        # For loops typically have:
        # 1. Initialization before the loop
        # 2. Condition check at the start
        # 3. Increment near the end

        # Look for STORE_VAR before loop start (initialization)
        init_found = False
        for addr in range(max(0, start - 10), start):
            if addr in self.instruction_map:
                inst = self.instruction_map[addr]
                if inst.opcode_name == 'STORE_VAR':
                    init_found = True
                    break

        # Look for comparison at start
        condition_found = self._is_while_loop_pattern(start, end)

        # Look for increment (ADD/SUB + STORE_VAR) near end
        increment_found = False
        for addr in range(max(start, end - 20), end):
            if addr in self.instruction_map:
                inst = self.instruction_map[addr]
                if inst.opcode_name in ['ADD', 'SUB', 'INCREMENT', 'DECREMENT']:
                    # Check if followed by STORE_VAR
                    next_addr = addr + 1
                    while next_addr < end and next_addr not in self.instruction_map:
                        next_addr += 1
                    if next_addr in self.instruction_map:
                        next_inst = self.instruction_map[next_addr]
                        if next_inst.opcode_name == 'STORE_VAR':
                            increment_found = True
                            break

        return init_found and condition_found and increment_found

    def _create_while_loop(self, start: int, end: int, parent: ControlBlock) -> None:
        """Create a WHILE loop block."""
        loop_block = ControlBlock(
            type=BlockType.WHILE,
            start_addr=start,
            end_addr=end,
            parent=parent,
        )
        parent.children.append(loop_block)
        self.blocks.append(loop_block)

    def _create_do_while_loop(self, start: int, end: int, parent: ControlBlock) -> None:
        """Create a DO-WHILE loop block."""
        loop_block = ControlBlock(
            type=BlockType.DO_WHILE,
            start_addr=start,
            end_addr=end,
            parent=parent,
        )
        parent.children.append(loop_block)
        self.blocks.append(loop_block)

    def _create_for_loop(self, start: int, end: int, parent: ControlBlock) -> None:
        """Create a FOR loop block."""
        loop_block = ControlBlock(
            type=BlockType.FOR,
            start_addr=start,
            end_addr=end,
            parent=parent,
        )
        parent.children.append(loop_block)
        self.blocks.append(loop_block)

    def analyze_patterns(self) -> None:
        """Analyze instruction patterns to identify high-level constructs."""
        # Pattern: TRY-CATCH-FINALLY blocks
        self._detect_exception_blocks()

        # Pattern: SWITCH/CASE statements
        self._detect_switch_statements()

        # Pattern: Property getters/setters
        self._detect_property_access()

    def _detect_exception_blocks(self) -> None:
        """Detect try-catch-finally blocks."""
        i = 0
        while i < len(self.instructions):
            inst = self.instructions[i]

            if inst.opcode_name == 'TRY_START' or inst.opcode_name == 'BEGIN_TRY':
                # Found start of try block
                try_start = inst.address

                # Find corresponding catch/finally
                catch_blocks = []
                finally_addr = None
                try_end = None

                j = i + 1
                while j < len(self.instructions):
                    next_inst = self.instructions[j]

                    if next_inst.opcode_name in ['CATCH', 'BEGIN_CATCH']:
                        catch_blocks.append(next_inst.address)
                    elif next_inst.opcode_name in ['FINALLY', 'BEGIN_FINALLY']:
                        finally_addr = next_inst.address
                    elif next_inst.opcode_name in ['END_TRY', 'TRY_END']:
                        try_end = next_inst.address
                        break

                    j += 1

                if try_end:
                    # Create try block
                    try_block = ControlBlock(
                        type=BlockType.TRY,
                        start_addr=try_start,
                        end_addr=try_end,
                    )
                    self.blocks.append(try_block)

                    # Create catch blocks
                    for catch_addr in catch_blocks:
                        catch_block = ControlBlock(
                            type=BlockType.CATCH,
                            start_addr=catch_addr,
                            parent=try_block,
                        )
                        try_block.children.append(catch_block)

                    # Create finally block if exists
                    if finally_addr:
                        finally_block = ControlBlock(
                            type=BlockType.FINALLY,
                            start_addr=finally_addr,
                            parent=try_block,
                        )
                        try_block.children.append(finally_block)

            i += 1

    def _detect_switch_statements(self) -> None:
        """Detect switch/case statement patterns."""
        # Look for patterns like:
        # 1. Load variable
        # 2. Series of comparisons and conditional jumps
        # 3. Jump table (if optimized)

        i = 0
        while i < len(self.instructions):
            inst = self.instructions[i]

            if inst.opcode_name == 'LOAD_VAR':
                # Check if followed by multiple comparisons
                if self._is_switch_pattern(i):
                    # Create switch block
                    # Implementation depends on specific P-code patterns
                    pass

            i += 1

    def _is_switch_pattern(self, start_idx: int) -> bool:
        """Check if instructions starting at index form a switch pattern."""
        if start_idx + 3 >= len(self.instructions):
            return False

        # Look for pattern: LOAD_VAR, COMPARE, JUMP_IF_FALSE, ...
        comparisons = 0
        i = start_idx + 1

        while i < len(self.instructions) and i < start_idx + 20:
            inst = self.instructions[i]
            if inst.opcode_name == 'COMPARE':
                comparisons += 1
            elif inst.opcode_name not in ['JUMP_IF_FALSE', 'JUMP_IF_TRUE', 'JUMP', 'PUSH_CONST']:
                break
            i += 1

        # If we found multiple comparisons, likely a switch
        return comparisons >= 3

    def _detect_property_access(self) -> None:
        """Detect property getter/setter patterns."""
        # Look for short functions that just load/store fields
        for block in self.blocks:
            if block.type == BlockType.FUNCTION:
                self._check_property_pattern(block)

    def _check_property_pattern(self, func_block: ControlBlock) -> None:
        """Check if a function block is a property getter or setter."""
        # Count instructions in function
        func_instructions = []
        for inst in self.instructions:
            if func_block.start_addr <= inst.address <= func_block.end_addr:
                func_instructions.append(inst)

        # Getter pattern: LOAD_FIELD, RETURN
        if len(func_instructions) <= 3:
            has_load_field = any(inst.opcode_name == 'LOAD_FIELD' for inst in func_instructions)
            has_return = any(inst.opcode_name == 'RETURN' for inst in func_instructions)
            if has_load_field and has_return:
                # Mark as getter
                func_block.is_getter = True

        # Setter pattern: LOAD_PARAM, STORE_FIELD, RETURN
        if len(func_instructions) <= 4:
            has_load_param = any(inst.opcode_name in ['LOAD_PARAM', 'LOAD_VAR'] for inst in func_instructions)
            has_store_field = any(inst.opcode_name == 'STORE_FIELD' for inst in func_instructions)
            if has_load_param and has_store_field:
                # Mark as setter
                func_block.is_setter = True

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
