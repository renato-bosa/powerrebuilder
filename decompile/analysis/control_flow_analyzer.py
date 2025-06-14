"""Unified control flow analyzer for PowerBuilder P-code.

This module combines the best features from both the basic and enhanced
control flow analyzers into a single, comprehensive implementation.
"""

import logging
from collections import defaultdict

from decompile.core.pcode_decoder import PCodeInstruction
from decompile.types import BlockType, ControlBlock

logger = logging.getLogger(__name__)


class ControlFlowAnalyzer:
    """Unified analyzer combining basic and enhanced features."""

    # Comprehensive set of jump opcodes
    JUMP_OPCODES = {
        "JUMP",
        "JUMPTRUE",
        "JUMPFALSE",
        "JMP",
        "BRFALSE",
        "BRTRUE",
        "JZ",
        "JNZ",
        "JUMPIF",
        "JUMPIFNOT",
        "BR",
        "BRA",
    }

    # Opcodes that unconditionally terminate a block
    UNCONDITIONAL_TERMINATORS = {
        "JUMP",
        "JMP",
        "BR",
        "BRA",
        "HALT",
        "THROW",
        "RETHROW",
        "EXIT",
        "RETURN",
        "RET",
    }

    # Opcodes that conditionally terminate a block
    CONDITIONAL_TERMINATORS = {
        "JUMPTRUE",
        "JUMPFALSE",
        "JZ",
        "JNZ",
        "BRFALSE",
        "BRTRUE",
        "JUMPIF",
        "JUMPIFNOT",
        "BEQ",
        "BNE",
        "BLT",
        "BGT",
        "BLE",
        "BGE",
    }

    def __init__(self) -> None:
        """Initialize the unified analyzer."""
        self.blocks: list[ControlBlock] = []
        self.labels: dict[int, str] = {}
        self.jump_targets: set[int] = set()
        self.address_to_instruction: dict[int, PCodeInstruction] = {}
        self.block_graph: dict[int, list[int]] = defaultdict(list)  # CFG edges

    def analyze(self, instructions: list[PCodeInstruction]) -> list[ControlBlock]:
        """Analyze instructions and return structured control flow blocks.

        Args:
            instructions: List of P-code instructions

        Returns:
            List of structured control flow blocks
        """
        if not instructions:
            return []

        # Build address mapping
        self._build_address_map(instructions)

        # First pass: identify all jump targets
        self._identify_jump_targets(instructions)

        # Second pass: split into basic blocks at control flow boundaries
        basic_blocks = self._split_basic_blocks(instructions)

        # Build control flow graph
        self._build_cfg(basic_blocks)

        # Third pass: identify and structure control flow patterns
        return self._structure_control_flow(basic_blocks)

    def _build_address_map(self, instructions: list[PCodeInstruction]) -> None:
        """Build mapping from address to instruction."""
        for inst in instructions:
            self.address_to_instruction[inst.address] = inst

    def _identify_jump_targets(self, instructions: list[PCodeInstruction]) -> None:
        """Identify all jump targets with improved calculation."""
        for inst in instructions:
            target = self._get_jump_target_address(inst)
            if target is not None:
                self.jump_targets.add(target)
                self.labels[target] = f"L_{target:04X}"
                logger.debug(f"Jump from {inst.address:04X} to {target:04X}")

    def _get_jump_target_address(self, inst: PCodeInstruction) -> int | None:
        """Calculate jump target address for an instruction.

        Returns:
            Target address or None if not a jump
        """
        if inst.opcode_name not in self.JUMP_OPCODES:
            return None

        if not inst.operand_values:
            return None

        # Get the offset value
        offset = inst.operand_values[0]
        if not isinstance(offset, int):
            return None

        # Calculate target address
        # The offset is typically relative to the instruction after the jump
        # Address + instruction_length + offset

        # Estimate instruction length (opcode + operands)
        inst_length = 1  # opcode byte
        if inst.operands:
            # Add operand bytes
            for operand in inst.operands:
                if isinstance(operand, int):
                    # Determine size based on value
                    if -128 <= operand <= 127:
                        inst_length += 1  # int8
                    elif -32768 <= operand <= 32767:
                        inst_length += 2  # int16
                    else:
                        inst_length += 4  # int32
                else:
                    inst_length += len(operand) if isinstance(operand, bytes) else 4

        # Target = current address + instruction length + offset
        return inst.address + inst_length + offset

    def _split_basic_blocks(
        self, instructions: list[PCodeInstruction]
    ) -> list[ControlBlock]:
        """Split instructions into basic blocks."""
        blocks = []
        current_block_insts = []
        start_addr = instructions[0].address if instructions else 0

        for i, inst in enumerate(instructions):
            # Check if this instruction is a jump target (starts new block)
            if inst.address in self.jump_targets and current_block_insts:
                # End current block
                block = ControlBlock(
                    type=BlockType.BASIC,
                    start_addr=start_addr,
                    end_addr=current_block_insts[-1].address,
                    instructions=current_block_insts,
                )
                blocks.append(block)

                # Start new block
                current_block_insts = [inst]
                start_addr = inst.address
            else:
                current_block_insts.append(inst)

            # Check if instruction terminates block
            if self._is_terminator(inst) and i < len(instructions) - 1:
                # End current block
                block = ControlBlock(
                    type=BlockType.BASIC,
                    start_addr=start_addr,
                    end_addr=inst.address,
                    instructions=current_block_insts,
                )
                blocks.append(block)

                # Start new block (if not at end)
                current_block_insts = []
                if i + 1 < len(instructions):
                    start_addr = instructions[i + 1].address

        # Add final block
        if current_block_insts:
            block = ControlBlock(
                type=BlockType.BASIC,
                start_addr=start_addr,
                end_addr=current_block_insts[-1].address,
                instructions=current_block_insts,
            )
            blocks.append(block)

        logger.debug(f"Created {len(blocks)} basic blocks")
        return blocks

    def _is_terminator(self, inst: PCodeInstruction) -> bool:
        """Check if instruction terminates a basic block."""
        return (
            inst.opcode_name in self.UNCONDITIONAL_TERMINATORS
            or inst.opcode_name in self.CONDITIONAL_TERMINATORS
        )

    def _build_cfg(self, blocks: list[ControlBlock]) -> None:
        """Build control flow graph edges between blocks."""
        # Map start addresses to block indices
        addr_to_block = {block.start_addr: i for i, block in enumerate(blocks)}

        for i, block in enumerate(blocks):
            if not block.instructions:
                continue

            last_inst = block.instructions[-1]

            # Check for unconditional jump
            if last_inst.opcode_name in ["JUMP", "JMP", "BR", "BRA"]:
                target = self._get_jump_target_address(last_inst)
                if target is not None and target in addr_to_block:
                    self.block_graph[i].append(addr_to_block[target])

            # Check for conditional jump
            elif last_inst.opcode_name in self.CONDITIONAL_TERMINATORS:
                # Conditional jumps have two edges: target and fall-through
                target = self._get_jump_target_address(last_inst)
                if target is not None and target in addr_to_block:
                    self.block_graph[i].append(addr_to_block[target])

                # Fall through to next block
                if i + 1 < len(blocks):
                    self.block_graph[i].append(i + 1)

            # Check if block falls through to next
            elif not self._is_terminator(last_inst) and i + 1 < len(blocks):
                self.block_graph[i].append(i + 1)

    def _structure_control_flow(
        self, basic_blocks: list[ControlBlock]
    ) -> list[ControlBlock]:
        """Structure basic blocks into high-level control flow."""
        structured = []
        processed = set()

        for i, block in enumerate(basic_blocks):
            if i in processed:
                continue

            # Try to match control flow patterns in order of complexity
            result = self._try_match_if(basic_blocks, i, processed)
            if result:
                structured.append(result)
                continue

            result = self._try_match_while(basic_blocks, i, processed)
            if result:
                structured.append(result)
                continue

            result = self._try_match_for(basic_blocks, i, processed)
            if result:
                structured.append(result)
                continue

            result = self._try_match_do_while(basic_blocks, i, processed)
            if result:
                structured.append(result)
                continue

            result = self._try_match_repeat_until(basic_blocks, i, processed)
            if result:
                structured.append(result)
                continue

            result = self._try_match_choose_case(basic_blocks, i, processed)
            if result:
                structured.append(result)
                continue

            # No pattern matched, keep as basic block
            structured.append(block)
            processed.add(i)

        return structured

    def _try_match_if(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> ControlBlock | None:
        """Try to match an if-then-else pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        last_inst = block.instructions[-1]

        # Check for conditional jump
        if last_inst.opcode_name not in self.CONDITIONAL_TERMINATORS:
            return None

        # Get jump target
        target_addr = self._get_jump_target_address(last_inst)
        if target_addr is None:
            return None

        # Find target block index
        target_idx = self._find_block_by_address(blocks, target_addr)
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

        # Mark blocks as processed
        processed.add(start_idx)

        # Collect then branch blocks
        then_instructions = []
        current_idx = start_idx + 1

        # For JUMPFALSE, the fall-through is the then branch
        # For JUMPTRUE, the jump target is the then branch
        if last_inst.opcode_name in ["JUMPFALSE", "BRFALSE"]:
            # Fall-through is then, jump is else/end
            while current_idx < target_idx and current_idx < len(blocks):
                then_instructions.extend(blocks[current_idx].instructions)
                processed.add(current_idx)
                current_idx += 1
        # JUMPTRUE case - need to handle differently
        # The jump target is the then branch
        elif target_idx > start_idx:
            for idx in range(target_idx, len(blocks)):
                # Look for where then branch ends
                if (
                    blocks[idx].instructions
                    and blocks[idx].instructions[-1].opcode_name == "JUMP"
                ):
                    break
                then_instructions.extend(blocks[idx].instructions)
                processed.add(idx)

        if then_instructions:
            if_block.then_block = ControlBlock(
                type=BlockType.BASIC,
                start_addr=then_instructions[0].address,
                end_addr=then_instructions[-1].address,
                instructions=then_instructions,
            )

        # Check for else branch
        if (
            if_block.then_block
            and if_block.then_block.instructions
            and if_block.then_block.instructions[-1].opcode_name in ["JUMP", "JMP"]
        ):
            else_jump_target = self._get_jump_target_address(
                if_block.then_block.instructions[-1]
            )
            if else_jump_target:
                else_start_idx = current_idx
                else_end_idx = self._find_block_by_address(blocks, else_jump_target)

                if else_end_idx and else_start_idx < else_end_idx:
                    else_instructions = []
                    for idx in range(else_start_idx, else_end_idx):
                        if idx < len(blocks):
                            else_instructions.extend(blocks[idx].instructions)
                            processed.add(idx)

                    if else_instructions:
                        if_block.else_block = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=else_instructions[0].address,
                            end_addr=else_instructions[-1].address,
                            instructions=else_instructions,
                        )

        # Update end address to encompass all branches
        end_addr = if_block.end_addr
        if if_block.then_block:
            end_addr = max(end_addr, if_block.then_block.end_addr)
        if if_block.else_block:
            end_addr = max(end_addr, if_block.else_block.end_addr)
        if_block.end_addr = end_addr

        return if_block

    def _try_match_while(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> ControlBlock | None:
        """Try to match a while loop pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        # Look for backward jump that creates a loop
        for i in range(start_idx + 1, len(blocks)):
            if i >= len(blocks) or i in processed:
                continue

            check_block = blocks[i]
            if not check_block.instructions:
                continue

            last_inst = check_block.instructions[-1]

            # Check for backward jump
            if last_inst.opcode_name in ["JUMP", "JMP", "JUMPTRUE", "BRTRUE"]:
                target = self._get_jump_target_address(last_inst)

                # Is it jumping back to our block or before?
                if target is not None and target <= blocks[start_idx].start_addr:
                    # Found a loop
                    while_block = ControlBlock(
                        type=BlockType.WHILE,
                        start_addr=target,
                        end_addr=check_block.end_addr,
                        metadata={
                            "condition": self._extract_condition(blocks[start_idx])
                        },
                    )

                    # Collect loop body
                    body_instructions = []
                    for idx in range(start_idx, i + 1):
                        if idx < len(blocks) and idx not in processed:
                            body_instructions.extend(blocks[idx].instructions)
                            processed.add(idx)

                    if body_instructions:
                        while_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].address,
                            end_addr=body_instructions[-1].address,
                            instructions=body_instructions,
                        )

                    return while_block

        return None

    def _try_match_for(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> ControlBlock | None:
        """Try to match a for loop pattern."""
        # FOR loops in PowerBuilder typically have:
        # 1. Initialization (assignment)
        # 2. Condition check (comparison + conditional jump)
        # 3. Body
        # 4. Increment (assignment)
        # 5. Jump back to condition

        if start_idx >= len(blocks) or start_idx in processed:
            return None

        # Look for initialization pattern
        init_block = blocks[start_idx]
        if not self._has_assignment(init_block):
            return None

        # Look for condition check in next block
        if start_idx + 1 >= len(blocks):
            return None

        cond_block = blocks[start_idx + 1]
        if not cond_block.instructions:
            return None

        # Should end with conditional jump
        if cond_block.instructions[-1].opcode_name not in self.CONDITIONAL_TERMINATORS:
            return None

        # Find the increment block (should have assignment and jump back)
        for inc_idx in range(start_idx + 2, min(start_idx + 10, len(blocks))):
            if inc_idx >= len(blocks) or inc_idx in processed:
                continue

            inc_block = blocks[inc_idx]
            if not inc_block.instructions:
                continue

            # Check for increment pattern and backward jump
            if self._has_assignment(inc_block) and inc_block.instructions[
                -1
            ].opcode_name in ["JUMP", "JMP"]:
                jump_target = self._get_jump_target_address(inc_block.instructions[-1])
                if jump_target == cond_block.start_addr:
                    # Found a for loop!
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

                    # Collect loop body (between condition and increment)
                    body_instructions = []
                    for idx in range(start_idx + 2, inc_idx):
                        if idx < len(blocks) and idx not in processed:
                            body_instructions.extend(blocks[idx].instructions)
                            processed.add(idx)

                    # Mark all blocks as processed
                    for idx in range(start_idx, inc_idx + 1):
                        processed.add(idx)

                    if body_instructions:
                        for_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].address,
                            end_addr=body_instructions[-1].address,
                            instructions=body_instructions,
                        )

                    return for_block

        return None

    def _try_match_do_while(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> ControlBlock | None:
        """Try to match a do-while loop pattern."""
        # DO WHILE has body first, then condition check with backward jump
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        # Look ahead for a conditional backward jump
        for end_idx in range(start_idx + 1, min(start_idx + 20, len(blocks))):
            if end_idx >= len(blocks) or end_idx in processed:
                continue

            end_block = blocks[end_idx]
            if not end_block.instructions:
                continue

            last_inst = end_block.instructions[-1]

            # Check for conditional backward jump
            if last_inst.opcode_name in ["JUMPTRUE", "BRTRUE"]:
                target = self._get_jump_target_address(last_inst)

                if target is not None and target == blocks[start_idx].start_addr:
                    # Found do-while loop
                    do_while_block = ControlBlock(
                        type=BlockType.DO_WHILE,
                        start_addr=blocks[start_idx].start_addr,
                        end_addr=end_block.end_addr,
                        metadata={"condition": self._extract_condition(end_block)},
                    )

                    # Collect loop body
                    body_instructions = []
                    for idx in range(start_idx, end_idx + 1):
                        if idx < len(blocks) and idx not in processed:
                            body_instructions.extend(blocks[idx].instructions)
                            processed.add(idx)

                    if body_instructions:
                        do_while_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].address,
                            end_addr=body_instructions[-1].address,
                            instructions=body_instructions,
                        )

                    return do_while_block

        return None

    def _try_match_repeat_until(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> ControlBlock | None:
        """Try to match a repeat-until loop pattern."""
        # REPEAT UNTIL is similar to DO WHILE but jumps on false condition
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        # Look ahead for a conditional backward jump (on false)
        for end_idx in range(start_idx + 1, min(start_idx + 20, len(blocks))):
            if end_idx >= len(blocks) or end_idx in processed:
                continue

            end_block = blocks[end_idx]
            if not end_block.instructions:
                continue

            last_inst = end_block.instructions[-1]

            # Check for conditional backward jump on false
            if last_inst.opcode_name in ["JUMPFALSE", "BRFALSE"]:
                target = self._get_jump_target_address(last_inst)

                if target is not None and target == blocks[start_idx].start_addr:
                    # Found repeat-until loop
                    repeat_block = ControlBlock(
                        type=BlockType.REPEAT_UNTIL,
                        start_addr=blocks[start_idx].start_addr,
                        end_addr=end_block.end_addr,
                        metadata={"condition": self._extract_condition(end_block)},
                    )

                    # Collect loop body
                    body_instructions = []
                    for idx in range(start_idx, end_idx + 1):
                        if idx < len(blocks) and idx not in processed:
                            body_instructions.extend(blocks[idx].instructions)
                            processed.add(idx)

                    if body_instructions:
                        repeat_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].address,
                            end_addr=body_instructions[-1].address,
                            instructions=body_instructions,
                        )

                    return repeat_block

        return None

    def _try_match_choose_case(
        self, blocks: list[ControlBlock], start_idx: int, processed: set[int]
    ) -> ControlBlock | None:
        """Try to match a choose-case (switch) pattern."""
        # CHOOSE CASE typically has:
        # 1. Value evaluation
        # 2. Series of comparisons and conditional jumps
        # 3. Case blocks
        # 4. Default case (optional)

        # This is complex and would need more sophisticated analysis
        # For now, return None
        return None

    def _find_block_by_address(
        self, blocks: list[ControlBlock], address: int
    ) -> int | None:
        """Find the index of the block containing the given address."""
        for i, block in enumerate(blocks):
            if block.start_addr <= address <= block.end_addr:
                return i
            # Also check if address is the start of the block
            if block.start_addr == address:
                return i
        return None

    def _extract_condition(self, block: ControlBlock) -> str:
        """Extract condition expression from block."""
        # This would analyze the instructions to reconstruct the condition
        # Look for comparison operations before the jump
        if len(block.instructions) >= 2:
            # Check for comparison opcodes
            comparison_ops = {"EQ", "NE", "LT", "GT", "LE", "GE", "CMP"}
            for inst in reversed(block.instructions[:-1]):
                if inst.opcode_name in comparison_ops:
                    return f"{inst.opcode_name}_condition"

        return "condition_expression"

    def _has_assignment(self, block: ControlBlock) -> bool:
        """Check if block contains assignment operations."""
        assignment_ops = {"STORE", "POPVAR", "ASSIGN", "MOV", "SETVAR"}
        return any(inst.opcode_name in assignment_ops for inst in block.instructions)

    def _extract_assignment(self, block: ControlBlock) -> str:
        """Extract assignment expression from block."""
        # Look for store/assignment operations
        for inst in block.instructions:
            if inst.opcode_name in {"STORE", "POPVAR", "ASSIGN", "SETVAR"}:
                if inst.operand_values:
                    return f"var_{inst.operand_values[0]} = expression"
        return "assignment"


# For backward compatibility, create an alias
UnifiedControlFlowAnalyzer = ControlFlowAnalyzer
