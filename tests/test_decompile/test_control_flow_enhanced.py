"""Unit tests for enhanced control flow analyzer."""

import pytest
from decompile.core.control_flow import EnhancedControlFlowAnalyzer
from decompile.analysis.control_flow_analyzer import ControlBlock, BlockType
from decompile.core.pcode_decoder import PCodeInstruction


def create_instruction(address, opcode, opcode_name, operands=None, operand_values=None):
    """Helper to create PCodeInstruction with proper text format."""
    if operands is None:
        operands = []
    if operand_values is None:
        operand_values = []
    
    # Create text format
    text_format = f"{address:04X}: {opcode_name}"
    if operand_values:
        text_format += f" {', '.join(str(v) for v in operand_values)}"
    
    return PCodeInstruction(
        address=address,
        opcode=opcode,
        opcode_name=opcode_name,
        operands=operands,
        operand_values=operand_values,
        text_format=text_format
    )


class TestEnhancedControlFlowAnalyzer:
    """Test enhanced control flow analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a fresh analyzer instance."""
        return EnhancedControlFlowAnalyzer()
    
    def test_analyze_empty_instructions(self, analyzer):
        """Test analysis with no instructions."""
        blocks = analyzer.analyze([])
        assert blocks == []
    
    def test_identify_jump_targets(self, analyzer):
        """Test jump target identification."""
        instructions = [
            create_instruction(0x100, b'\x04', 'JUMP', [b'\x10\x00'], [0x10]),
            create_instruction(0x103, b'\x02', 'JUMPTRUE', [b'\x20\x00'], [0x20]),
            create_instruction(0x106, b'\x00', 'RETURN', [], [])
        ]
        
        analyzer._build_address_map(instructions)
        analyzer._identify_jump_targets(instructions)
        
        # Should identify jump targets
        assert len(analyzer.jump_targets) >= 1
        assert len(analyzer.labels) >= 1
    
    def test_get_jump_target_address(self, analyzer):
        """Test jump target calculation."""
        # JUMP with offset 0x10
        inst = create_instruction(0x100, b'\x04\x00', 'JUMP', [b'\x10\x00'], [0x10])
        target = analyzer._get_jump_target_address(inst)
        
        # Target should be current address + instruction length + offset
        # 0x100 + 3 (estimated length) + 0x10 = 0x113
        assert target is not None
        assert target > inst.address
    
    def test_get_jump_target_backward(self, analyzer):
        """Test backward jump calculation."""
        # JUMP with negative offset
        inst = create_instruction(0x200, b'\x04\x00', 'JUMP', [b'\xF0\xFF'], [-16])
        target = analyzer._get_jump_target_address(inst)
        
        assert target is not None
        assert target < inst.address
    
    def test_split_basic_blocks(self, analyzer):
        """Test basic block splitting."""
        instructions = [
            create_instruction(0x100, b'\x32', 'PUSH_CONST_INT', [b'\x01\x00'], [1]),
            create_instruction(0x103, b'\x02', 'JUMPTRUE', [b'\x10\x00'], [0x10]),
            create_instruction(0x106, b'\x32', 'PUSH_CONST_INT', [b'\x02\x00'], [2]),
            create_instruction(0x109, b'\x00', 'RETURN', [], []),
            create_instruction(0x10A, b'\x32', 'PUSH_CONST_INT', [b'\x03\x00'], [3]),
            create_instruction(0x10D, b'\x00', 'RETURN', [], [])
        ]
        
        analyzer._build_address_map(instructions)
        analyzer._identify_jump_targets(instructions)
        blocks = analyzer._split_basic_blocks(instructions)
        
        # Should create multiple blocks due to jumps and returns
        assert len(blocks) >= 2
        assert all(isinstance(block, ControlBlock) for block in blocks)
    
    def test_is_terminator(self, analyzer):
        """Test terminator instruction detection."""
        # Unconditional terminators
        assert analyzer._is_terminator(create_instruction(0, b'', 'JUMP', [], []))
        assert analyzer._is_terminator(create_instruction(0, b'', 'HALT', [], []))
        assert analyzer._is_terminator(create_instruction(0, b'', 'RETURN', [], []))
        
        # Conditional terminators
        assert analyzer._is_terminator(create_instruction(0, b'', 'JUMPTRUE', [], []))
        assert analyzer._is_terminator(create_instruction(0, b'', 'JUMPFALSE', [], []))
        
        # Non-terminators
        assert not analyzer._is_terminator(create_instruction(0, b'', 'PUSH_CONST_INT', [], []))
        assert not analyzer._is_terminator(create_instruction(0, b'', 'ADD_INT', [], []))
    
    def test_build_cfg(self, analyzer):
        """Test control flow graph construction."""
        blocks = [
            ControlBlock(BlockType.BASIC, 0x100, 0x105, [
                create_instruction(0x100, b'', 'PUSH_CONST_INT', [], []),
                create_instruction(0x103, b'', 'JUMPTRUE', [], [0x200])
            ]),
            ControlBlock(BlockType.BASIC, 0x106, 0x109, [
                create_instruction(0x106, b'', 'PUSH_CONST_INT', [], []),
                create_instruction(0x109, b'', 'RETURN', [], [])
            ]),
            ControlBlock(BlockType.BASIC, 0x200, 0x203, [
                create_instruction(0x200, b'', 'PUSH_CONST_INT', [], []),
                create_instruction(0x203, b'', 'RETURN', [], [])
            ])
        ]
        
        analyzer._build_cfg(blocks)
        
        # First block should have edges to both successors (conditional jump)
        assert 0 in analyzer.block_graph
        assert len(analyzer.block_graph[0]) == 2  # Jump target and fall-through
    
    def test_try_match_if_pattern(self, analyzer):
        """Test if-then-else pattern matching."""
        # Create blocks representing an if statement
        blocks = [
            # If condition block
            ControlBlock(BlockType.BASIC, 0x100, 0x105, [
                create_instruction(0x100, b'', 'PUSH_CONST_INT', [], []),
                create_instruction(0x103, b'', 'JUMPFALSE', [], [0x200])
            ]),
            # Then block
            ControlBlock(BlockType.BASIC, 0x106, 0x109, [
                create_instruction(0x106, b'', 'PUSH_CONST_INT', [], [1]),
                create_instruction(0x109, b'', 'JUMP', [], [0x300])
            ]),
            # Else block
            ControlBlock(BlockType.BASIC, 0x200, 0x203, [
                create_instruction(0x200, b'', 'PUSH_CONST_INT', [], [2]),
            ]),
            # After if
            ControlBlock(BlockType.BASIC, 0x300, 0x303, [
                create_instruction(0x300, b'', 'RETURN', [], [])
            ])
        ]
        
        # Set up analyzer state
        analyzer._build_address_map([inst for block in blocks for inst in block.instructions])
        processed = set()
        
        # Try to match if pattern
        if_block = analyzer._try_match_if(blocks, 0, processed)
        
        assert if_block is not None
        assert if_block.type == BlockType.IF
        assert 0 in processed  # First block should be processed
    
    def test_try_match_while_pattern(self, analyzer):
        """Test while loop pattern matching."""
        # Create blocks representing a while loop
        blocks = [
            # Loop header
            ControlBlock(BlockType.BASIC, 0x100, 0x105, [
                create_instruction(0x100, b'', 'PUSH_CONST_INT', [], []),
                create_instruction(0x103, b'', 'JUMPFALSE', [], [0x300])
            ]),
            # Loop body
            ControlBlock(BlockType.BASIC, 0x106, 0x109, [
                create_instruction(0x106, b'', 'PUSH_CONST_INT', [], []),
            ]),
            # Jump back to header
            ControlBlock(BlockType.BASIC, 0x200, 0x203, [
                create_instruction(0x200, b'', 'JUMP', [], [0x100])  # Back to loop start
            ]),
            # After loop
            ControlBlock(BlockType.BASIC, 0x300, 0x303, [
                create_instruction(0x300, b'', 'RETURN', [], [])
            ])
        ]
        
        analyzer._build_address_map([inst for block in blocks for inst in block.instructions])
        processed = set()
        
        # Try to match while pattern
        while_block = analyzer._try_match_while(blocks, 0, processed)
        
        # Should detect the backward jump creating a loop
        assert while_block is not None or len(processed) > 0
    
    def test_find_block_by_address(self, analyzer):
        """Test finding blocks by address."""
        blocks = [
            ControlBlock(BlockType.BASIC, 0x100, 0x105, []),
            ControlBlock(BlockType.BASIC, 0x106, 0x109, []),
            ControlBlock(BlockType.BASIC, 0x200, 0x203, [])
        ]
        
        # Test exact start address
        assert analyzer._find_block_by_address(blocks, 0x100) == 0
        assert analyzer._find_block_by_address(blocks, 0x200) == 2
        
        # Test address within block
        assert analyzer._find_block_by_address(blocks, 0x103) == 0
        
        # Test address not in any block
        assert analyzer._find_block_by_address(blocks, 0x400) is None
    
    def test_structure_control_flow(self, analyzer):
        """Test overall control flow structuring."""
        instructions = [
            create_instruction(0x100, b'\x32', 'PUSH_CONST_INT', [b'\x01\x00'], [1]),
            create_instruction(0x103, b'\x02', 'JUMPTRUE', [b'\x10\x00'], [0x10]),
            create_instruction(0x106, b'\x32', 'PUSH_CONST_INT', [b'\x02\x00'], [2]),
            create_instruction(0x109, b'\x00', 'RETURN', [], [])
        ]
        
        blocks = analyzer.analyze(instructions)
        
        # Should produce structured blocks
        assert len(blocks) > 0
        assert all(isinstance(block, ControlBlock) for block in blocks)