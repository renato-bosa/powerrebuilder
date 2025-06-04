"""Enhanced control flow analyzer for PowerBuilder P-code.

This module provides improved control flow analysis with better jump target
calculation and pattern recognition.
"""

import logging
from collections import defaultdict

from ..analysis.control_flow_analyzer import BlockType, ControlBlock
from .pcode_decoder import PCodeInstruction

logger = logging.getLogger(__name__)


class EnhancedControlFlowAnalyzer:
    """Enhanced analyzer with improved jump handling and pattern recognition."""

    def __init__(self):
        """Initialize the enhanced analyzer."""
        self.blocks: list[ControlBlock] = []
        self.labels: dict[int, str] = {}
        self.jump_targets: set[int] = set()
        self.address_to_instruction: dict[int, PCodeInstruction] = {}
        self.block_graph: dict[int, list[int]] = defaultdict(list)  # CFG edges

    def analyze(self, instructions: list[PCodeInstruction]) -> list[ControlBlock]:
        """Analyze instructions with enhanced control flow detection.
        
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
        structured_blocks = self._structure_control_flow(basic_blocks)

        return structured_blocks

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
        jump_opcodes = {
            'JUMP', 'JUMPTRUE', 'JUMPFALSE', 'JMP',
            'BRFALSE', 'BRTRUE', 'JZ', 'JNZ',
            'JUMPIF', 'JUMPIFNOT',
        }

        if inst.opcode_name not in jump_opcodes:
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
            inst_length += len(inst.operands)

        # For two-byte opcodes
        if inst.opcode_value and inst.opcode_value > 0xFF:
            inst_length += 1

        # Calculate target
        if offset < 0:
            # Backward jump - offset is negative
            target = inst.address + inst_length + offset
        else:
            # Forward jump
            target = inst.address + inst_length + offset

        # Validate target is within code bounds
        if target < 0:
            logger.warning(f"Jump target {target:04X} is negative, adjusting to 0")
            target = 0

        return target

    def _split_basic_blocks(self, instructions: list[PCodeInstruction]) -> list[ControlBlock]:
        """Split instructions into basic blocks with improved boundaries."""
        blocks = []
        current_block = None

        # Mark block boundaries
        block_starts = {0}  # First instruction always starts a block

        # Add jump targets as block starts
        block_starts.update(self.jump_targets)

        # Add instructions after jumps as block starts
        for i, inst in enumerate(instructions):
            if self._is_terminator(inst) and i + 1 < len(instructions):
                block_starts.add(instructions[i + 1].address)

        # Create blocks
        current_block_insts = []
        start_addr = 0

        for inst in instructions:
            if inst.address in block_starts and current_block_insts:
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
        # Unconditional jumps and control transfers
        unconditional_terminators = {
            'JUMP', 'JMP', 'HALT', 'THROW', 'RETHROW', 'EXIT',
        }

        # Conditional jumps (block continues after)
        conditional_terminators = {
            'JUMPTRUE', 'JUMPFALSE', 'JZ', 'JNZ',
            'BRFALSE', 'BRTRUE', 'JUMPIF', 'JUMPIFNOT',
        }

        # RETURN only terminates if it's the last instruction or followed by dead code
        if inst.opcode_name == 'RETURN':
            # We'll handle RETURN specially - only treat as terminator
            # if there's no fall-through code after it
            return True  # For now, but we'll improve this

        return inst.opcode_name in unconditional_terminators or inst.opcode_name in conditional_terminators

    def _build_cfg(self, blocks: list[ControlBlock]) -> None:
        """Build control flow graph edges between blocks."""
        # Map start addresses to block indices
        addr_to_block = {block.start_addr: i for i, block in enumerate(blocks)}

        for i, block in enumerate(blocks):
            if not block.instructions:
                continue

            last_inst = block.instructions[-1]

            # Check if block falls through to next
            if not self._is_terminator(last_inst) and i + 1 < len(blocks):
                self.block_graph[i].append(i + 1)

            # Add jump edges
            elif last_inst.opcode_name in ['JUMP', 'JMP']:
                target = self._get_jump_target_address(last_inst)
                if target is not None and target in addr_to_block:
                    self.block_graph[i].append(addr_to_block[target])

            # Add conditional jump edges
            elif last_inst.opcode_name in ['JUMPTRUE', 'JUMPFALSE', 'BRFALSE', 'BRTRUE']:
                # Conditional jumps have two edges: target and fall-through
                target = self._get_jump_target_address(last_inst)
                if target is not None and target in addr_to_block:
                    self.block_graph[i].append(addr_to_block[target])

                # Fall through to next block
                if i + 1 < len(blocks):
                    self.block_graph[i].append(i + 1)

    def _structure_control_flow(self, basic_blocks: list[ControlBlock]) -> list[ControlBlock]:
        """Structure basic blocks into high-level control flow."""
        # Use a more sophisticated algorithm to detect patterns
        structured = []
        processed = set()

        for i, block in enumerate(basic_blocks):
            if i in processed:
                continue

            # Try to match control flow patterns
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

            # No pattern matched, keep as basic block
            structured.append(block)
            processed.add(i)

        return structured

    def _try_match_if(self, blocks: list[ControlBlock], start_idx: int,
                      processed: set[int]) -> ControlBlock | None:
        """Try to match an if-then-else pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        block = blocks[start_idx]
        if not block.instructions:
            return None

        last_inst = block.instructions[-1]

        # Check for conditional jump
        if last_inst.opcode_name not in ['JUMPFALSE', 'JUMPTRUE', 'BRFALSE', 'BRTRUE']:
            return None

        # Get jump target
        target_addr = self._get_jump_target_address(last_inst)
        if target_addr is None:
            return None

        # Find target block
        target_idx = self._find_block_by_address(blocks, target_addr)
        if target_idx is None:
            return None

        # Create if block
        if_block = ControlBlock(
            type=BlockType.IF,
            start_addr=block.start_addr,
            end_addr=block.end_addr,
            instructions=block.instructions[:-1],  # Exclude jump
            metadata={'condition': self._extract_condition(block)},
        )

        # Mark this block as processed
        processed.add(start_idx)

        # Collect then branch blocks
        then_blocks = []
        current_idx = start_idx + 1

        while current_idx < target_idx and current_idx < len(blocks):
            then_blocks.append(blocks[current_idx])
            processed.add(current_idx)
            current_idx += 1

        if then_blocks:
            # Merge then blocks
            then_instructions = []
            for b in then_blocks:
                then_instructions.extend(b.instructions)

            if_block.then_block = ControlBlock(
                type=BlockType.BASIC,
                start_addr=then_blocks[0].start_addr,
                end_addr=then_blocks[-1].end_addr,
                instructions=then_instructions,
            )

            # Check if then branch ends with unconditional jump (else branch)
            if (then_instructions and
                then_instructions[-1].opcode_name in ['JUMP', 'JMP']):

                else_target = self._get_jump_target_address(then_instructions[-1])
                if else_target and else_target > target_addr:
                    # We have an else branch
                    else_blocks = []
                    current_idx = target_idx

                    else_end_idx = self._find_block_by_address(blocks, else_target)
                    if else_end_idx:
                        while current_idx < else_end_idx:
                            else_blocks.append(blocks[current_idx])
                            processed.add(current_idx)
                            current_idx += 1

                        if else_blocks:
                            else_instructions = []
                            for b in else_blocks:
                                else_instructions.extend(b.instructions)

                            if_block.else_block = ControlBlock(
                                type=BlockType.BASIC,
                                start_addr=else_blocks[0].start_addr,
                                end_addr=else_blocks[-1].end_addr,
                                instructions=else_instructions,
                            )

                            # Update if block end
                            if_block.end_addr = else_target

        return if_block

    def _try_match_while(self, blocks: list[ControlBlock], start_idx: int,
                        processed: set[int]) -> ControlBlock | None:
        """Try to match a while loop pattern."""
        if start_idx >= len(blocks) or start_idx in processed:
            return None

        # Look for a backward jump that creates a loop
        for end_idx in range(start_idx + 1, len(blocks)):
            if end_idx in processed:
                continue

            end_block = blocks[end_idx]
            if not end_block.instructions:
                continue

            last_inst = end_block.instructions[-1]

            # Check for backward jump
            if last_inst.opcode_name in ['JUMP', 'JUMPTRUE', 'JMP']:
                target = self._get_jump_target_address(last_inst)

                if target and target <= blocks[start_idx].start_addr:
                    # Found a loop
                    loop_start_idx = self._find_block_by_address(blocks, target)
                    if loop_start_idx is None:
                        continue

                    # Create while block
                    while_block = ControlBlock(
                        type=BlockType.WHILE,
                        start_addr=blocks[loop_start_idx].start_addr,
                        end_addr=end_block.end_addr,
                        metadata={'condition': 'loop_condition'},
                    )

                    # Collect loop body
                    body_instructions = []
                    for idx in range(loop_start_idx, end_idx + 1):
                        if idx < len(blocks):
                            body_instructions.extend(blocks[idx].instructions)
                            processed.add(idx)

                    while_block.body = ControlBlock(
                        type=BlockType.BASIC,
                        start_addr=body_instructions[0].address if body_instructions else target,
                        end_addr=body_instructions[-1].address if body_instructions else target,
                        instructions=body_instructions,
                    )

                    return while_block

        return None

    def _try_match_for(self, blocks: list[ControlBlock], start_idx: int,
                      processed: set[int]) -> ControlBlock | None:
        """Try to match a for loop pattern."""
        # FOR loops typically have:
        # 1. Initialization block
        # 2. Condition check with forward jump
        # 3. Loop body
        # 4. Increment block
        # 5. Backward jump to condition

        if start_idx + 2 >= len(blocks):
            return None

        # Look for the pattern
        init_block = blocks[start_idx]
        if start_idx + 1 >= len(blocks):
            return None

        cond_block = blocks[start_idx + 1]

        # Check if condition block has conditional jump
        if (not cond_block.instructions or
            cond_block.instructions[-1].opcode_name not in ['JUMPFALSE', 'BRFALSE']):
            return None

        # Find the exit target
        exit_target = self._get_jump_target_address(cond_block.instructions[-1])
        if not exit_target:
            return None

        # Look for backward jump to condition
        for end_idx in range(start_idx + 2, min(start_idx + 20, len(blocks))):
            if end_idx >= len(blocks):
                break

            end_block = blocks[end_idx]
            if not end_block.instructions:
                continue

            last_inst = end_block.instructions[-1]

            if last_inst.opcode_name in ['JUMP', 'JMP']:
                back_target = self._get_jump_target_address(last_inst)

                if back_target == cond_block.start_addr:
                    # Found FOR loop pattern
                    for_block = ControlBlock(
                        type=BlockType.FOR,
                        start_addr=init_block.start_addr,
                        end_addr=exit_target,
                        metadata={
                            'init': 'initialization',
                            'condition': 'loop_condition',
                            'increment': 'increment',
                        },
                    )

                    # Mark blocks as processed
                    for idx in range(start_idx, end_idx + 1):
                        processed.add(idx)

                    # Collect loop body (between condition and increment)
                    body_instructions = []
                    for idx in range(start_idx + 2, end_idx):
                        if idx < len(blocks):
                            body_instructions.extend(blocks[idx].instructions)

                    if body_instructions:
                        for_block.body = ControlBlock(
                            type=BlockType.BASIC,
                            start_addr=body_instructions[0].address,
                            end_addr=body_instructions[-1].address,
                            instructions=body_instructions,
                        )

                    return for_block

        return None

    def _find_block_by_address(self, blocks: list[ControlBlock], address: int) -> int | None:
        """Find block index containing the given address."""
        for i, block in enumerate(blocks):
            if block.start_addr <= address <= block.end_addr:
                return i
            # Also check if address is the start of this block
            if block.start_addr == address:
                return i
        return None

    def _extract_condition(self, block: ControlBlock) -> str:
        """Extract condition from block instructions."""
        # This would analyze the stack operations before the jump
        # to reconstruct the actual condition
        # For now, return a placeholder
        return "condition_expression"
