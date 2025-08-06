"""Unified control flow analyzer for PowerBuilder P-code.

This module combines the best features from both the basic and enhanced
control flow analyzers into a single, comprehensive implementation.
"""

import logging
from dataclasses import dataclass, field

from src.decompile.pcode.decoder import PCodeInstruction
from src.decompile.types import BlockType, ControlBlock

logger = logging.getLogger(__name__)


@dataclass
class FunctionBoundary:
    """Represents a function boundary in P-code."""

    end_addr: int | None = None
    name: str | None = None
    entry_points: set[int] = field(default_factory=set)
    exit_points: set[int] = field(default_factory=set)
    is_complete: bool = False


class ControlFlowAnalyzer:
    """Unified analyzer combining basic and enhanced features with function boundary detection."""

    # Function boundary indicators
    FUNCTION_START_INDICATORS = {
        "FUNCTION",
        "SUBROUTINE",
        "EVENT",
        "METHOD",
        "CONSTRUCTOR",
        "DESTRUCTOR",
        "ENTRY",
        "PROC",
        "PROCEDURE",
    }

    FUNCTION_END_INDICATORS = {
        "RETURN",
        "RET",
        "EXIT",
        "END_FUNCTION",
        "END_SUBROUTINE",
        "END_EVENT",
        "END_METHOD",
        "END_PROC",
        "ENDPROC",
    }

    # Control flow terminators
    CONDITIONAL_TERMINATORS = {
        "JUMPTRUE",
        "JUMPFALSE",
        "BRTRUE",
        "BRFALSE",
        "JZ",
        "JNZ",
        "JE",
        "JNE",
        "JL",
        "JG",
        "JLE",
        "JGE",
    }

    UNCONDITIONAL_TERMINATORS = {"JUMP", "JMP", "BR", "BRANCH", "GOTO"}

    def __init__(self) -> None:
        """Initialize the control flow analyzer."""
        self.function_boundaries = {}
        self.current_function = None
        self._reset_analysis_state()

    def _reset_analysis_state(self) -> None:
        """Reset internal analysis state."""
        self.function_boundaries = {}
        self.current_function = None

    def analyze(
        self,
        instructions: list[PCodeInstruction],
        use_function_boundaries: bool = True,
    ) -> list[ControlBlock]:
        """Analyze control flow and build control blocks.

        Args:
            instructions: List of P-code instructions
            use_function_boundaries: Whether to detect function boundaries

        Returns:
            List of control blocks representing the program structure
        """
        if not instructions:
            return []

        self._reset_analysis_state()

        # Detect function boundaries if requested
        if use_function_boundaries:
            self._detect_function_boundaries(instructions)

        # Build basic blocks
        basic_blocks = self._build_basic_blocks(instructions)

        # Identify control structures
        return self._identify_control_structures(basic_blocks)

    def _detect_function_boundaries(self, instructions: list[PCodeInstruction]) -> None:
        """Detect function boundaries in the instruction stream."""
        for _i, inst in enumerate(instructions):
            # Check for function start
            if inst.opcode_name in self.FUNCTION_START_INDICATORS:
                boundary = FunctionBoundary(name=inst.opcode_name)
                boundary.entry_points.add(inst.offset)
                self.current_function = inst.offset
                self.function_boundaries[inst.offset] = boundary

            # Check for function end
            elif inst.opcode_name in self.FUNCTION_END_INDICATORS:
                if (
                    self.current_function
                    and self.current_function in self.function_boundaries
                ):
                    boundary = self.function_boundaries[self.current_function]
                    boundary.end_addr = inst.offset
                    boundary.exit_points.add(inst.offset)
                    boundary.is_complete = True
                    self.current_function = None

            # Check for function calls (create implicit boundaries)
            elif inst.opcode_name in ["CALL", "CALLFUNC", "INVOKE"]:
                if inst.operands and isinstance(inst.operands[0], int):
                    target = inst.operands[0]
                    if target not in self.function_boundaries:
                        self.function_boundaries[target] = FunctionBoundary()
                    self.function_boundaries[target].entry_points.add(target)

    def _build_basic_blocks(
        self, instructions: list[PCodeInstruction]
    ) -> list[ControlBlock]:
        """Build basic blocks from instructions."""
        if not instructions:
            return []

        blocks = []
        current_block = []
        block_start = instructions[0].offset

        for i, inst in enumerate(instructions):
            # Add to current block
            current_block.append(inst)

            # Check if this ends a basic block
            is_terminator = (
                inst.opcode_name in self.CONDITIONAL_TERMINATORS
                or inst.opcode_name in self.UNCONDITIONAL_TERMINATORS
                or inst.opcode_name in self.FUNCTION_END_INDICATORS
            )

            # Check if next instruction is a jump target
            is_before_target = False
            if i + 1 < len(instructions):
                next_addr = instructions[i + 1].offset
                is_before_target = self._is_jump_target(instructions, next_addr)

            # End block if necessary
            if is_terminator or is_before_target or i == len(instructions) - 1:
                if current_block:
                    block = ControlBlock(
                        type=BlockType.BASIC,
                        start_addr=block_start,
                        end_addr=inst.offset,
                        instructions=current_block.copy(),
                    )
                    blocks.append(block)
                    current_block = []
                    if i + 1 < len(instructions):
                        block_start = instructions[i + 1].offset

        return blocks

    def _is_jump_target(
        self, instructions: list[PCodeInstruction], address: int
    ) -> bool:
        """Check if an address is a jump target."""
        for inst in instructions:
            if (
                inst.opcode_name
                in self.CONDITIONAL_TERMINATORS | self.UNCONDITIONAL_TERMINATORS
            ):
                if inst.operands and inst.operands[0] == address:
                    return True
        return False

    def _identify_control_structures(
        self, blocks: list[ControlBlock]
    ) -> list[ControlBlock]:
        """Identify high-level control structures from basic blocks."""
        if not blocks:
            return []

        result = []
        processed = set()
        i = 0

        while i < len(blocks):
            if i in processed:
                i += 1
                continue

            # Try to match control structures in priority order
            matched = False

            # Try for loop
            for_block = self._try_match_for_loop(blocks, i, processed)
            if for_block:
                result.append(for_block)
                matched = True
                # Skip to after the loop
                i = self._find_next_unprocessed(blocks, i, processed)
                continue

            # Try while loop
            while_block = self._try_match_while_loop(blocks, i, processed)
            if while_block:
                result.append(while_block)
                matched = True
                i = self._find_next_unprocessed(blocks, i, processed)
                continue

            # Try do-while loop
            do_while_block = self._try_match_do_while(blocks, i, processed)
            if do_while_block:
                result.append(do_while_block)
                matched = True
                i = self._find_next_unprocessed(blocks, i, processed)
                continue

            # Try if-then-else
            if_block = self._try_match_if_else(blocks, i, processed)
            if if_block:
                result.append(if_block)
                matched = True
                i = self._find_next_unprocessed(blocks, i, processed)
                continue

            # Try choose-case
            choose_block = self._try_match_choose_case(blocks, i, processed)
            if choose_block:
                result.append(choose_block)
                matched = True
                i = self._find_next_unprocessed(blocks, i, processed)
                continue

            # Try try-catch-finally
            try_block = self._try_match_try_catch(blocks, i, processed)
            if try_block:
                result.append(try_block)
                matched = True
                i = self._find_next_unprocessed(blocks, i, processed)
                continue

            # No pattern matched, add as basic block
            if not matched:
                result.append(blocks[i])
                processed.add(i)
                i += 1

        return result

    def _find_next_unprocessed(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> int:
        """Find the next unprocessed block index."""
        idx = start_idx + 1
        while idx < len(blocks) and idx in processed:
            idx += 1
        return idx

    def _get_jump_target_address(self, inst: PCodeInstruction) -> int | None:
        """Extract jump target address from instruction."""
        if inst.operands and len(inst.operands) > 0:
            target = inst.operands[0]
            if isinstance(target, int):
                return target
        return None

    def _try_match_if_else(
        self,
        blocks: list[ControlBlock],
        start_idx: int,
        processed: set[int],
    ) -> ControlBlock | None:
        """Try to match an if-then-else pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        # Check if block ends with conditional jump
        last_inst = block.instructions[-1]
        if last_inst.opcode_name not in self.CONDITIONAL_TERMINATORS:
            return None

        jump_target = self._get_jump_target_address(last_inst)
        if jump_target is None:
            return None

        # Find the target block index
        target_idx = self._find_block_by_address(blocks, jump_target)
        if target_idx is None:
            return None

        # Create if block
        if_block = ControlBlock(
            type=BlockType.IF,
            start_addr=block.start_addr,
            end_addr=block.end_addr,
            instructions=block.instructions[:-1],  # Exclude jump
            metadata={"condition": self._extract_condition(block)},
        )

        processed.add(start_idx)

        # Collect then branch
        then_blocks = []
        current_idx = start_idx + 1
        while current_idx < target_idx and current_idx not in processed:
            then_blocks.append(blocks[current_idx])
            processed.add(current_idx)
            current_idx += 1

        if then_blocks:
            if_block.then_block = self._merge_blocks(then_blocks, BlockType.BASIC)

        # Check for else branch
        if target_idx < len(blocks) - 1:
            # Look for unconditional jump at end of then branch
            if then_blocks and then_blocks[-1].instructions:
                last_then_inst = then_blocks[-1].instructions[-1]
                if last_then_inst.opcode_name in self.UNCONDITIONAL_TERMINATORS:
                    else_jump = self._get_jump_target_address(last_then_inst)
                    if else_jump:
                        else_end_idx = self._find_block_by_address(blocks, else_jump)
                        if else_end_idx and else_end_idx > target_idx:
                            # Collect else blocks
                            else_blocks = []
                            current_idx = target_idx
                            while (
                                current_idx < else_end_idx
                                and current_idx not in processed
                            ):
                                else_blocks.append(blocks[current_idx])
                                processed.add(current_idx)
                                current_idx += 1

                            if else_blocks:
                                if_block.else_block = self._merge_blocks(
                                    else_blocks, BlockType.BASIC
                                )

        return if_block

    def _try_match_while_loop(
        self,
        blocks: list[ControlBlock],
        start_idx: int,
        processed: set[int],
    ) -> ControlBlock | None:
        """Try to match a while loop pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        # While loop: condition check with forward conditional jump
        last_inst = block.instructions[-1]
        if last_inst.opcode_name not in self.CONDITIONAL_TERMINATORS:
            return None

        exit_target = self._get_jump_target_address(last_inst)
        if exit_target is None:
            return None

        # Find exit block
        exit_idx = self._find_block_by_address(blocks, exit_target)
        if exit_idx is None or exit_idx <= start_idx:
            return None

        # Look for backward jump to condition
        for check_idx in range(start_idx + 1, exit_idx):
            if check_idx >= len(blocks):
                break
            check_block = blocks[check_idx]
            if check_block.instructions:
                last = check_block.instructions[-1]
                if last.opcode_name in self.UNCONDITIONAL_TERMINATORS:
                    jump_back = self._get_jump_target_address(last)
                    if jump_back == block.start_addr:
                        # Found while loop
                        while_block = ControlBlock(
                            type=BlockType.WHILE,
                            start_addr=block.start_addr,
                            end_addr=check_block.end_addr,
                            metadata={"condition": self._extract_condition(block)},
                        )

                        # Mark blocks as processed
                        for idx in range(start_idx, check_idx + 1):
                            processed.add(idx)

                        # Collect body blocks
                        body_blocks = []
                        for idx in range(start_idx + 1, check_idx + 1):
                            body_blocks.append(blocks[idx])

                        if body_blocks:
                            while_block.body = self._merge_blocks(
                                body_blocks, BlockType.BASIC
                            )

                        return while_block

        return None

    def _try_match_for_loop(
        self,
        blocks: list[ControlBlock],
        start_idx: int,
        processed: set[int],
    ) -> ControlBlock | None:
        """Try to match a for loop pattern."""
        if start_idx >= len(blocks) - 2 or start_idx in processed:
            return None

        # For loop pattern:
        # 1. Initialization (assignment)
        # 2. Condition check (comparison + conditional jump)
        # 3. Body
        # 4. Increment (assignment)
        # 5. Jump back to condition

        init_block = blocks[start_idx]
        if not self._has_assignment(init_block):
            return None

        # Check condition block
        if start_idx + 1 >= len(blocks):
            return None
        cond_block = blocks[start_idx + 1]
        if not cond_block.instructions:
            return None

        last_cond = cond_block.instructions[-1]
        if last_cond.opcode_name not in self.CONDITIONAL_TERMINATORS:
            return None

        exit_target = self._get_jump_target_address(last_cond)
        if exit_target is None:
            return None

        # Look for increment and back jump
        for inc_idx in range(start_idx + 2, min(start_idx + 10, len(blocks))):
            inc_block = blocks[inc_idx]
            if not inc_block.instructions:
                continue

            # Check for increment pattern and backward jump
            if (
                self._has_assignment(inc_block)
                and inc_block.instructions[-1].opcode_name
                in self.UNCONDITIONAL_TERMINATORS
            ):
                jump_target = self._get_jump_target_address(inc_block.instructions[-1])
                if jump_target == cond_block.start_addr:
                    # Found for loop
                    for_block = ControlBlock(
                        type=BlockType.FOR,
                        start_addr=init_block.start_addr,
                        end_addr=inc_block.end_addr,
                        metadata={
                            "init": self._extract_assignment(init_block),
                            "condition": self._extract_condition(cond_block),
                            "increment": self._extract_assignment(inc_block),
                        },
                    )

                    # Collect loop body
                    body_instructions = []
                    for idx in range(start_idx + 2, inc_idx):
                        body_instructions.extend(blocks[idx].instructions)
                        processed.add(idx)

                    # Mark all blocks as processed
                    for idx in range(start_idx, inc_idx + 1):
                        processed.add(idx)

                    if body_instructions:
                        for_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].offset,
                            end_addr=body_instructions[-1].offset,
                            instructions=body_instructions,
                        )

                    return for_block

        return None

    def _try_match_do_while(
        self,
        blocks: list[ControlBlock],
        start_idx: int,
        processed: set[int],
    ) -> ControlBlock | None:
        """Try to match a do-while loop pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        # Do-while: body followed by condition with backward jump
        # Look ahead for conditional jump back to start
        for check_idx in range(start_idx + 1, min(start_idx + 10, len(blocks))):
            if check_idx >= len(blocks):
                break

            check_block = blocks[check_idx]
            if not check_block.instructions:
                continue

            last = check_block.instructions[-1]
            if last.opcode_name in self.CONDITIONAL_TERMINATORS:
                jump_target = self._get_jump_target_address(last)
                if jump_target == blocks[start_idx].start_addr:
                    # Found do-while loop
                    do_while_block = ControlBlock(
                        type=BlockType.DO_WHILE,
                        start_addr=blocks[start_idx].start_addr,
                        end_addr=check_block.end_addr,
                        metadata={"condition": self._extract_condition(check_block)},
                    )

                    # Mark blocks as processed
                    for idx in range(start_idx, check_idx + 1):
                        processed.add(idx)

                    # Collect body blocks (excluding condition)
                    body_blocks = []
                    for idx in range(start_idx, check_idx):
                        body_blocks.append(blocks[idx])

                    if body_blocks:
                        do_while_block.body = self._merge_blocks(
                            body_blocks, BlockType.BASIC
                        )

                    return do_while_block

        return None

    def _try_match_choose_case(
        self,
        blocks: list[ControlBlock],
        start_idx: int,
        processed: set[int],
    ) -> ControlBlock | None:
        """Try to match a choose-case (switch) pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        # Choose-case pattern:
        # - Value pushed on stack
        # - DUP (duplicate for comparison)
        # - Push case value
        # - EQ/NE comparison
        # - Conditional jump
        # This pattern repeats for each case

        # Check if this block ends with a comparison and jump
        if len(block.instructions) < 2:
            return None

        last_inst = block.instructions[-1]
        if last_inst.opcode_name not in self.CONDITIONAL_TERMINATORS:
            return None

        # Look for comparison before jump
        comparison_found = False
        for i in range(len(block.instructions) - 2, -1, -1):
            inst = block.instructions[i]
            if inst.opcode_name in ["EQ", "NE", "CMP"]:
                comparison_found = True
                break

        if not comparison_found:
            return None

        # Try to identify case structure
        cases = []
        default_case = None
        current_idx = start_idx
        end_addr = None

        # Process case blocks
        while (
            current_idx < len(blocks) and len(cases) < 20
        ):  # Limit to prevent infinite loop
            if current_idx in processed:
                current_idx += 1
                continue

            curr_block = blocks[current_idx]
            if not curr_block.instructions:
                current_idx += 1
                continue

            # Check if this is a case block
            last = curr_block.instructions[-1]

            # Case blocks typically end with JUMP to end of switch
            if last.opcode_name in self.UNCONDITIONAL_TERMINATORS:
                jump_target = self._get_jump_target_address(last)
                if jump_target:
                    case_block = {
                        "start_idx": current_idx,
                        "block": curr_block,
                        "jump_target": jump_target,
                    }
                    cases.append(case_block)
                    processed.add(current_idx)

                    # Track the furthest jump target as potential end
                    if end_addr is None or jump_target > end_addr:
                        end_addr = jump_target

            elif last.opcode_name not in self.CONDITIONAL_TERMINATORS:
                # Could be default case or end of switch
                if cases and end_addr:
                    if curr_block.start_addr >= end_addr:
                        break
                    # Otherwise might be default case
                    default_case = curr_block
                    processed.add(current_idx)

            current_idx += 1

        # Need at least 2 cases to consider it a switch
        if len(cases) < 2:
            # Unmark processed blocks
            for case in cases:
                processed.discard(case["start_idx"])
            return None

        # Create choose-case block
        choose_block = ControlBlock(
            type=BlockType.CHOOSE_CASE,
            start_addr=blocks[start_idx].start_addr,
            end_addr=end_addr or blocks[current_idx - 1].end_addr,
            metadata={
                "expression": self._extract_switch_expression(blocks[start_idx]),
                "case_count": len(cases),
            },
        )

        # Add case blocks
        choose_block.cases = []
        for i, case_info in enumerate(cases):
            case_block = ControlBlock(
                type=BlockType.CASE,
                start_addr=case_info["block"].start_addr,
                end_addr=case_info["block"].end_addr,
                instructions=case_info["block"].instructions[:-1],  # Exclude jump
                metadata={"case_value": f"case_{i}"},
            )
            choose_block.cases.append(case_block)

        # Add default case if found
        if default_case:
            default_block = ControlBlock(
                type=BlockType.CASE,
                start_addr=default_case.start_addr,
                end_addr=default_case.end_addr,
                instructions=default_case.instructions,
                metadata={"is_default": True},
            )
            choose_block.cases.append(default_block)

        return choose_block

    def _try_match_try_catch(
        self,
        blocks: list[ControlBlock],
        start_idx: int,
        processed: set[int],
    ) -> ControlBlock | None:
        """Try to match a try-catch-finally pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        # Look for exception handling setup
        # PowerBuilder uses specific opcodes for exception handling
        exception_ops = {"TRY", "CATCH", "FINALLY", "ENDTRY", "THROW", "EXCEPT"}

        # Check if this block has exception setup
        has_try = any(inst.opcode_name in exception_ops for inst in block.instructions)
        if not has_try:
            return None

        # Find the extent of the try-catch-finally block
        try_block = ControlBlock(
            type=BlockType.TRY,
            start_addr=block.start_addr,
            end_addr=block.end_addr,
        )

        current_idx = start_idx
        in_try = True
        in_catch = False
        in_finally = False

        try_blocks = []
        catch_blocks = []
        finally_blocks = []

        while current_idx < len(blocks):
            if current_idx in processed:
                current_idx += 1
                continue

            curr_block = blocks[current_idx]
            processed.add(current_idx)

            # Check for section markers
            for inst in curr_block.instructions:
                if inst.opcode_name == "CATCH":
                    in_try = False
                    in_catch = True
                    in_finally = False
                elif inst.opcode_name == "FINALLY":
                    in_try = False
                    in_catch = False
                    in_finally = True
                elif inst.opcode_name == "ENDTRY":
                    # End of try-catch-finally
                    try_block.end_addr = inst.offset

                    # Assign collected blocks
                    if try_blocks:
                        try_block.try_block = self._merge_blocks(
                            try_blocks, BlockType.BASIC
                        )
                    if catch_blocks:
                        try_block.catch_blocks = [
                            self._merge_blocks(catch_blocks, BlockType.BASIC)
                        ]
                    if finally_blocks:
                        try_block.finally_block = self._merge_blocks(
                            finally_blocks, BlockType.BASIC
                        )

                    return try_block

            # Collect blocks into appropriate sections
            if in_try:
                try_blocks.append(curr_block)
            elif in_catch:
                catch_blocks.append(curr_block)
            elif in_finally:
                finally_blocks.append(curr_block)

            current_idx += 1

        # If we didn't find ENDTRY, still return what we have
        if try_blocks or catch_blocks or finally_blocks:
            if try_blocks:
                try_block.try_block = self._merge_blocks(try_blocks, BlockType.BASIC)
            if catch_blocks:
                try_block.catch_blocks = [
                    self._merge_blocks(catch_blocks, BlockType.BASIC)
                ]
            if finally_blocks:
                try_block.finally_block = self._merge_blocks(
                    finally_blocks, BlockType.BASIC
                )
            return try_block

        # Unmark processed if we didn't find a complete structure
        for idx in range(start_idx, current_idx):
            processed.discard(idx)

        return None

    def _merge_blocks(
        self, blocks: list[ControlBlock], block_type: BlockType
    ) -> ControlBlock:
        """Merge multiple blocks into a single block."""
        if not blocks:
            return ControlBlock(type=block_type)

        instructions = []
        for block in blocks:
            instructions.extend(block.instructions)

        return ControlBlock(
            type=block_type,
            start_addr=blocks[0].start_addr,
            end_addr=blocks[-1].end_addr,
            instructions=instructions,
        )

    def _find_block_by_address(
        self,
        blocks: list[ControlBlock],
        address: int,
    ) -> int | None:
        """Find the index of the block containing the given address."""
        for i, block in enumerate(blocks):
            # Check if address is within block range
            if block.start_addr <= address <= block.end_addr:
                return i
            # Also check if address is the start of the block
            if block.start_addr == address:
                return i
        return None

    def _extract_condition(self, block: ControlBlock) -> str:
        """Extract condition expression from block."""
        if not block.instructions or len(block.instructions) < 2:
            return "unknown_condition"

        # Work backwards from the jump to find the condition
        comparison_ops = {"EQ", "NE", "LT", "GT", "LE", "GE", "CMP"}

        # Track the expression components
        left_operand = None
        right_operand = None
        operator = None

        # Scan backwards from jump
        for i in range(len(block.instructions) - 2, -1, -1):
            inst = block.instructions[i]

            if inst.opcode_name in comparison_ops:
                operator = {
                    "EQ": "=",
                    "NE": "<>",
                    "LT": "<",
                    "GT": ">",
                    "LE": "<=",
                    "GE": ">=",
                    "CMP": "=",
                }.get(inst.opcode_name, inst.opcode_name)

                # Look for operands before comparison
                if i > 0:
                    prev_inst = block.instructions[i - 1]
                    if prev_inst.opcode_name == "PUSHVAR" and prev_inst.operands:
                        right_operand = f"var_{prev_inst.operands[0]}"
                    elif prev_inst.opcode_name == "PUSHCONST" and prev_inst.operands:
                        right_operand = str(prev_inst.operands[0])

                    if i > 1:
                        prev_inst2 = block.instructions[i - 2]
                        if prev_inst2.opcode_name == "PUSHVAR" and prev_inst2.operands:
                            left_operand = f"var_{prev_inst2.operands[0]}"
                        elif (
                            prev_inst2.opcode_name == "PUSHCONST"
                            and prev_inst2.operands
                        ):
                            left_operand = str(prev_inst2.operands[0])

                break

            # Check for boolean test (just variable on stack)
            if inst.opcode_name == "PUSHVAR" and inst.operands:
                var_name = f"var_{inst.operands[0]}"
                # Check if next instruction is the jump
                if i == len(block.instructions) - 2:
                    return var_name

            # Check for NOT operation
            elif inst.opcode_name == "NOT":
                if i > 0:
                    prev_inst = block.instructions[i - 1]
                    if prev_inst.opcode_name == "PUSHVAR" and prev_inst.operands:
                        return f"NOT var_{prev_inst.operands[0]}"

        # Build the condition string
        if operator and left_operand and right_operand:
            return f"{left_operand} {operator} {right_operand}"
        if operator and right_operand:
            return f"value {operator} {right_operand}"

        # Fallback - check jump type for hints
        jump_inst = block.instructions[-1]
        if jump_inst.opcode_name in ["JUMPTRUE", "BRTRUE"]:
            return "condition = true"
        if jump_inst.opcode_name in ["JUMPFALSE", "BRFALSE"]:
            return "condition = false"

        return "condition"

    def _has_assignment(self, block: ControlBlock) -> bool:
        """Check if block contains assignment operations."""
        assignment_ops = {"STORE", "POPVAR", "ASSIGN", "MOV", "SETVAR"}
        return any(inst.opcode_name in assignment_ops for inst in block.instructions)

    def _extract_assignment(self, block: ControlBlock) -> str:
        """Extract assignment expression from block."""
        assignment_ops = {"STORE", "POPVAR", "ASSIGN", "MOV", "SETVAR"}

        # Scan for assignment operations
        for i, inst in enumerate(block.instructions):
            if inst.opcode_name not in assignment_ops:
                continue

            if inst.operands:
                var_name = f"var_{inst.operands[0]}"

                # Look backwards for the value being assigned
                value_expr = None

                if i > 0:
                    prev_inst = block.instructions[i - 1]

                    # Direct value assignment
                    if prev_inst.opcode_name == "PUSHCONST" and prev_inst.operands:
                        value = prev_inst.operands[0]
                        if isinstance(value, str):
                            value_expr = f'"{value}"'
                        else:
                            value_expr = str(value)

                    elif prev_inst.opcode_name == "PUSHVAR" and prev_inst.operands:
                        value_expr = f"var_{prev_inst.operands[0]}"

                    # Arithmetic operation
                    elif prev_inst.opcode_name in {"ADD", "SUB", "MUL", "DIV", "MOD"}:
                        op_map = {
                            "ADD": "+",
                            "SUB": "-",
                            "MUL": "*",
                            "DIV": "/",
                            "MOD": "mod",
                        }
                        op = op_map.get(prev_inst.opcode_name, prev_inst.opcode_name)

                        # Look for operands
                        if i > 2:
                            op1 = block.instructions[i - 3]
                            op2 = block.instructions[i - 2]

                            left = self._extract_operand(op1)
                            right = self._extract_operand(op2)

                            if left and right:
                                value_expr = f"{left} {op} {right}"

                if value_expr:
                    return f"{var_name} = {value_expr}"
                return f"{var_name} = value"

        return "assignment"

    def _extract_operand(self, inst: PCodeInstruction) -> str | None:
        """Extract operand value from instruction."""
        if inst.opcode_name == "PUSHVAR" and inst.operands:
            return f"var_{inst.operands[0]}"
        if inst.opcode_name == "PUSHCONST" and inst.operands:
            value = inst.operands[0]
            if isinstance(value, str):
                return f'"{value}"'
            return str(value)
        return None

    def _extract_switch_expression(self, block: ControlBlock) -> str:
        """Extract the expression being switched on."""
        # Look for the value being duplicated and compared
        for inst in block.instructions:
            if inst.opcode_name == "PUSHVAR" and inst.operands:
                return f"var_{inst.operands[0]}"
            if inst.opcode_name == "PUSHCONST" and inst.operands:
                value = inst.operands[0]
                if isinstance(value, str):
                    return f'"{value}"'
                return str(value)

        return "switch_expression"
