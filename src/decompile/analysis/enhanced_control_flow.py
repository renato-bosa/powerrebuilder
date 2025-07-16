"""Enhanced control flow analyzer with better function boundary detection.

This module provides improved handling of function boundaries to prevent
"Unexpected 'end function' without matching block start" errors.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from src.decompile.pcode.decoder import PCodeInstruction
from src.decompile.types import BlockType, ControlBlock

logger = logging.getLogger(__name__)


@dataclass
class FunctionBoundary:
    """Represents a function boundary in P-code."""
    start_addr: int
    end_addr: Optional[int] = None
    name: Optional[str] = None
    entry_points: Set[int] = field(default_factory=set)
    exit_points: Set[int] = field(default_factory=set)
    is_complete: bool = False


class EnhancedControlFlowAnalyzer:
    """Enhanced analyzer with better function boundary detection."""

    # Extended set of function start/end indicators
    FUNCTION_START_INDICATORS = {
        "FUNCTION", "SUBROUTINE", "EVENT", "METHOD", "CONSTRUCTOR", "DESTRUCTOR",
        "ENTRY", "PROC", "PROCEDURE"
    }
    
    FUNCTION_END_INDICATORS = {
        "RETURN", "RET", "EXIT", "END_FUNCTION", "END_SUBROUTINE", "END_EVENT",
        "END_METHOD", "END_PROC", "ENDPROC", "ENDFUNC"
    }

    # Control flow opcodes
    JUMP_OPCODES = {
        "JUMP", "JUMPTRUE", "JUMPFALSE", "JMP", "BRFALSE", "BRTRUE", 
        "JZ", "JNZ", "JUMPIF", "JUMPIFNOT", "BR", "BRA"
    }

    UNCONDITIONAL_TERMINATORS = {
        "JUMP", "JMP", "BR", "BRA", "HALT", "THROW", "RETHROW", 
        "EXIT", "RETURN", "RET"
    }

    CONDITIONAL_TERMINATORS = {
        "JUMPTRUE", "JUMPFALSE", "JZ", "JNZ", "BRFALSE", "BRTRUE", 
        "JUMPIF", "JUMPIFNOT", "BEQ", "BNE", "BLT", "BGT", "BLE", "BGE"
    }

    def __init__(self) -> None:
        """Initialize the enhanced analyzer."""
        self.blocks: List[ControlBlock] = []
        self.labels: Dict[int, str] = {}
        self.jump_targets: Set[int] = set()
        self.address_to_instruction: Dict[int, PCodeInstruction] = {}
        self.block_graph: Dict[int, List[int]] = defaultdict(list)
        self.function_boundaries: List[FunctionBoundary] = []
        self.current_function: Optional[FunctionBoundary] = None

    def analyze(self, instructions: List[PCodeInstruction]) -> List[ControlBlock]:
        """Analyze instructions with enhanced function boundary detection.

        Args:
            instructions: List of P-code instructions

        Returns:
            List of structured control flow blocks
        """
        if not instructions:
            return []

        # Build address mapping
        self._build_address_map(instructions)

        # First pass: identify function boundaries
        self._identify_function_boundaries(instructions)

        # Second pass: identify all jump targets
        self._identify_jump_targets(instructions)

        # Third pass: split into basic blocks at control flow boundaries
        basic_blocks = self._split_basic_blocks(instructions)

        # Build control flow graph
        self._build_cfg(basic_blocks)

        # Fourth pass: structure control flow with function awareness
        return self._structure_control_flow_with_functions(basic_blocks)

    def _build_address_map(self, instructions: List[PCodeInstruction]) -> None:
        """Build mapping from address to instruction."""
        for inst in instructions:
            self.address_to_instruction[inst.address] = inst

    def _identify_function_boundaries(self, instructions: List[PCodeInstruction]) -> None:
        """Identify function boundaries to prevent mismatched end errors."""
        self.function_boundaries = []
        self.current_function = None
        
        # Track return patterns
        consecutive_returns = 0
        max_consecutive_returns = 3  # Multiple returns often indicate function end
        
        for i, inst in enumerate(instructions):
            # Check for function start patterns
            if self._is_function_start(inst, i, instructions):
                # End current function if any
                if self.current_function and not self.current_function.is_complete:
                    self.current_function.end_addr = inst.address
                    self.current_function.is_complete = True
                    
                # Start new function
                self.current_function = FunctionBoundary(
                    start_addr=inst.address,
                    name=self._extract_function_name(inst)
                )
                self.function_boundaries.append(self.current_function)
                consecutive_returns = 0
                logger.debug("Function start detected at 0x%04X", inst.address)
                
            # Check for explicit function end
            elif inst.opcode_name in self.FUNCTION_END_INDICATORS:
                consecutive_returns += 1
                
                # Multiple returns in a row likely indicate function boundary
                if consecutive_returns >= max_consecutive_returns:
                    if self.current_function and not self.current_function.is_complete:
                        self.current_function.end_addr = inst.address
                        self.current_function.is_complete = True
                        logger.debug("Function end detected at 0x%04X (multiple returns)", inst.address)
                        self.current_function = None
                    consecutive_returns = 0
                    
            # Check for other function boundary indicators
            elif self._is_likely_function_boundary(inst, i, instructions):
                if self.current_function and not self.current_function.is_complete:
                    self.current_function.end_addr = inst.address
                    self.current_function.is_complete = True
                    logger.debug("Function boundary detected at 0x%04X", inst.address)
                consecutive_returns = 0
                
            else:
                # Reset consecutive return counter on non-return instruction
                if inst.opcode_name not in ["RETURN", "RET"]:
                    consecutive_returns = 0
        
        # Close last function if unclosed
        if self.current_function and not self.current_function.is_complete:
            self.current_function.end_addr = instructions[-1].address
            self.current_function.is_complete = True

    def _is_function_start(self, inst: PCodeInstruction, idx: int, 
                          instructions: List[PCodeInstruction]) -> bool:
        """Detect if instruction marks a function start."""
        # Check for explicit function start opcodes
        if any(start in inst.opcode_name for start in self.FUNCTION_START_INDICATORS):
            return True
            
        # Check for common function entry patterns
        # 1. Label followed by stack setup
        if idx < len(instructions) - 1:
            next_inst = instructions[idx + 1]
            if inst.address in self.jump_targets and "PUSH" in next_inst.opcode_name:
                return True
                
        # 2. After multiple consecutive returns
        if idx > 0:
            prev_inst = instructions[idx - 1]
            if prev_inst.opcode_name in ["RETURN", "RET"]:
                # Check if this is a jump target from elsewhere
                if inst.address in self.jump_targets:
                    return True
                    
        return False

    def _is_likely_function_boundary(self, inst: PCodeInstruction, idx: int,
                                   instructions: List[PCodeInstruction]) -> bool:
        """Detect likely function boundaries based on patterns."""
        # Check for unconditional jump to distant location
        if inst.opcode_name in ["JUMP", "JMP"]:
            target = self._get_jump_target_address(inst)
            if target and abs(target - inst.address) > 100:  # Large jump
                return True
                
        # Check for HALT or EXIT
        if inst.opcode_name in ["HALT", "EXIT"]:
            return True
            
        # Check for exception handling boundaries
        if inst.opcode_name in ["THROW", "RETHROW", "CATCH_EXCEPTION"]:
            return True
            
        return False

    def _extract_function_name(self, inst: PCodeInstruction) -> Optional[str]:
        """Extract function name from instruction if available."""
        # This would need to look at metadata or string tables
        # For now, return a generated name
        return f"func_{inst.address:04X}"

    def _identify_jump_targets(self, instructions: List[PCodeInstruction]) -> None:
        """Identify all jump targets."""
        for inst in instructions:
            target = self._get_jump_target_address(inst)
            if target is not None:
                self.jump_targets.add(target)
                self.labels[target] = f"L_{target:04X}"

    def _get_jump_target_address(self, inst: PCodeInstruction) -> Optional[int]:
        """Calculate jump target address from instruction."""
        if inst.opcode_name not in self.JUMP_OPCODES:
            return None

        if not inst.operand_values:
            return None

        # Handle different jump types
        if "relative" in inst.opcode_name.lower() or inst.opcode_name in ["JUMPTRUE", "JUMPFALSE"]:
            # Relative jump
            offset = inst.operand_values[0]
            return inst.address + offset + len(inst.opcode) + len(inst.operands)
        else:
            # Absolute jump
            return inst.operand_values[0]

    def _split_basic_blocks(self, instructions: List[PCodeInstruction]) -> List[ControlBlock]:
        """Split instructions into basic blocks with function awareness."""
        blocks = []
        current_block = []
        current_start = 0

        for i, inst in enumerate(instructions):
            # Start new block at:
            # 1. Jump targets
            # 2. After terminators
            # 3. Function boundaries
            should_split = (
                inst.address in self.jump_targets or
                (i > 0 and self._is_terminator(instructions[i-1])) or
                self._is_at_function_boundary(inst.address)
            )

            if should_split and current_block:
                # Save current block
                blocks.append(ControlBlock(
                    type=BlockType.BASIC,
                    start_addr=current_start,
                    end_addr=current_block[-1].address,
                    instructions=current_block.copy()
                ))
                current_block = []
                current_start = inst.address

            current_block.append(inst)

            # End block after terminator
            if self._is_terminator(inst):
                blocks.append(ControlBlock(
                    type=BlockType.BASIC,
                    start_addr=current_start,
                    end_addr=inst.address,
                    instructions=current_block.copy()
                ))
                current_block = []
                if i + 1 < len(instructions):
                    current_start = instructions[i + 1].address

        # Add final block
        if current_block:
            blocks.append(ControlBlock(
                type=BlockType.BASIC,
                start_addr=current_start,
                end_addr=current_block[-1].address,
                instructions=current_block.copy()
            ))

        return blocks

    def _is_at_function_boundary(self, address: int) -> bool:
        """Check if address is at a function boundary."""
        for func in self.function_boundaries:
            if address == func.start_addr or address == func.end_addr:
                return True
        return False

    def _is_terminator(self, inst: PCodeInstruction) -> bool:
        """Check if instruction terminates a basic block."""
        return (
            inst.opcode_name in self.UNCONDITIONAL_TERMINATORS or
            inst.opcode_name in self.CONDITIONAL_TERMINATORS
        )

    def _build_cfg(self, blocks: List[ControlBlock]) -> None:
        """Build control flow graph edges between blocks."""
        addr_to_block = {block.start_addr: i for i, block in enumerate(blocks)}

        for i, block in enumerate(blocks):
            if not block.instructions:
                continue

            last_inst = block.instructions[-1]

            # Check for unconditional jump
            if last_inst.opcode_name in self.UNCONDITIONAL_TERMINATORS:
                if last_inst.opcode_name not in ["RETURN", "RET", "HALT", "EXIT"]:
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
                    # Check if next block is in same function
                    if not self._crosses_function_boundary(block.end_addr, blocks[i + 1].start_addr):
                        self.block_graph[i].append(i + 1)

            # Check if block falls through to next
            elif not self._is_terminator(last_inst) and i + 1 < len(blocks):
                # Check function boundary
                if not self._crosses_function_boundary(block.end_addr, blocks[i + 1].start_addr):
                    self.block_graph[i].append(i + 1)

    def _crosses_function_boundary(self, from_addr: int, to_addr: int) -> bool:
        """Check if control flow would cross a function boundary."""
        for func in self.function_boundaries:
            if func.end_addr and from_addr <= func.end_addr < to_addr:
                return True
            if func.start_addr and from_addr < func.start_addr <= to_addr:
                return True
        return False

    def _structure_control_flow_with_functions(self, basic_blocks: List[ControlBlock]) -> List[ControlBlock]:
        """Structure control flow with function boundary awareness."""
        structured = []
        
        # Process each function separately
        for func in self.function_boundaries:
            # Get blocks belonging to this function
            func_blocks = [
                block for block in basic_blocks
                if func.start_addr <= block.start_addr <= (func.end_addr or float('inf'))
            ]
            
            if func_blocks:
                # Create function block
                func_block = ControlBlock(
                    type=BlockType.FUNCTION,
                    start_addr=func.start_addr,
                    end_addr=func.end_addr or func_blocks[-1].end_addr,
                    instructions=[],
                    statements=[],
                    metadata={"name": func.name}
                )
                
                # Structure blocks within function
                func_structured = self._structure_blocks_within_function(func_blocks)
                func_block.statements = func_structured
                
                structured.append(func_block)
        
        # Add any blocks not in functions
        func_addresses = {(f.start_addr, f.end_addr) for f in self.function_boundaries}
        orphan_blocks = [
            block for block in basic_blocks
            if not any(
                start <= block.start_addr <= (end or float('inf'))
                for start, end in func_addresses
            )
        ]
        
        if orphan_blocks:
            structured.extend(self._structure_blocks_within_function(orphan_blocks))
        
        return structured

    def _structure_blocks_within_function(self, blocks: List[ControlBlock]) -> List[ControlBlock]:
        """Structure blocks within a function boundary."""
        structured = []
        processed = set()
        
        for i, block in enumerate(blocks):
            if i in processed:
                continue
                
            # Try to match control flow patterns
            result = None
            
            # Try patterns in order
            patterns = [
                self._try_match_if,
                self._try_match_while,
                self._try_match_for,
                self._try_match_do_while,
                self._try_match_choose_case,
            ]
            
            for pattern_matcher in patterns:
                result = pattern_matcher(blocks, i, processed)
                if result:
                    structured.append(result)
                    break
            
            if not result:
                # No pattern matched, keep as basic block
                structured.append(block)
                processed.add(i)
        
        return structured

    def _try_match_if(self, blocks: List[ControlBlock], start_idx: int, 
                     processed: Set[int]) -> Optional[ControlBlock]:
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

        # Create if block
        if_block = ControlBlock(
            type=BlockType.IF,
            start_addr=block.start_addr,
            end_addr=block.end_addr,
            instructions=block.instructions[:-1],  # Exclude jump
            metadata={"condition": self._extract_condition(block)}
        )

        processed.add(start_idx)

        # Simplified if handling - just mark the pattern
        return if_block

    def _try_match_while(self, blocks: List[ControlBlock], start_idx: int,
                        processed: Set[int]) -> Optional[ControlBlock]:
        """Try to match a while loop pattern."""
        # Simplified implementation
        return None

    def _try_match_for(self, blocks: List[ControlBlock], start_idx: int,
                      processed: Set[int]) -> Optional[ControlBlock]:
        """Try to match a for loop pattern."""
        # Simplified implementation
        return None

    def _try_match_do_while(self, blocks: List[ControlBlock], start_idx: int,
                           processed: Set[int]) -> Optional[ControlBlock]:
        """Try to match a do-while loop pattern."""
        # Simplified implementation
        return None

    def _try_match_choose_case(self, blocks: List[ControlBlock], start_idx: int,
                              processed: Set[int]) -> Optional[ControlBlock]:
        """Try to match a choose-case pattern."""
        # Simplified implementation
        return None

    def _extract_condition(self, block: ControlBlock) -> str:
        """Extract condition from block instructions."""
        # Look for comparison operations before the jump
        for inst in reversed(block.instructions):
            if any(op in inst.opcode_name for op in ["EQ", "NE", "GT", "LT", "GE", "LE"]):
                return inst.opcode_name
        return "condition"