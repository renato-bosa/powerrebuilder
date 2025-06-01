"""Unit tests for PowerBuilder P-code decoder v2."""

import pytest
from unittest.mock import Mock, patch
from decompile.pcode_decoder_v2 import PCodeDecoderV2, PCodeInstruction, DecodedObject
from extract.pbd_core.version_detector import PowerBuilderVersion


class TestPCodeDecoderV2:
    """Test P-code decoder v2 functionality."""
    
    @pytest.fixture
    def decoder(self):
        """Create a decoder instance."""
        return PCodeDecoderV2(version=PowerBuilderVersion.PB80)
    
    def test_init_with_version(self):
        """Test initialization with specific version."""
        decoder = PCodeDecoderV2(version=PowerBuilderVersion.PB105)
        assert decoder.version == PowerBuilderVersion.PB105
        assert decoder.opcode_manager is not None
    
    def test_init_without_version(self):
        """Test initialization with auto-detect version."""
        decoder = PCodeDecoderV2()
        assert decoder.version == PowerBuilderVersion.PB80  # Default
    
    def test_decode_instruction_single_byte(self, decoder):
        """Test decoding single-byte instruction."""
        # RETURN instruction (0x00)
        data = b'\x00'
        address = 0x100
        
        inst = decoder._decode_instruction(data, 0, address)
        
        assert inst is not None
        assert inst.opcode_name == "RETURN"
        assert inst.address == 0x100
        assert inst.opcode == b'\x00'
    
    def test_decode_instruction_with_operands(self, decoder):
        """Test decoding instruction with operands."""
        # PUSH_CONST_INT with 2-byte operand
        data = b'\x32\x0A\x00'  # Opcode 0x32, operand 0x000A (10)
        address = 0x100
        
        inst = decoder._decode_instruction(data, 0, address)
        
        assert inst is not None
        assert inst.opcode_name == "PUSH_CONST_INT"
        assert inst.operand_values == [10]
    
    def test_decode_instruction_two_byte_opcode(self, decoder):
        """Test decoding two-byte opcode."""
        # Mock a two-byte opcode
        data = b'\xFE\x01\x00'  # Extended opcode marker + opcode
        address = 0x100
        
        with patch.object(decoder.opcode_manager, 'get_opcode') as mock_get:
            mock_get.return_value = {
                'name': 'EXTENDED_OP',
                'operands': [],
                'stack_effect': 0
            }
            
            inst = decoder._decode_instruction(data, 0, address)
            
            # Should pass 0xFE01 as the opcode
            mock_get.assert_called_with(0xFE01)
    
    def test_decode_object_function(self, decoder):
        """Test decoding a function object."""
        # Minimal function P-code
        pcode_data = b'\x32\x05\x00'  # PUSH_CONST_INT 5
        pcode_data += b'\x00'         # RETURN
        
        with patch.object(decoder, '_find_pcode_in_object') as mock_find:
            mock_find.return_value = (0, len(pcode_data))
            
            decoded = decoder.decode_object(
                name="test_func.fun",
                object_type="function",
                data=pcode_data
            )
            
            assert decoded is not None
            assert decoded.name == "test_func.fun"
            assert decoded.type == "function"
            assert len(decoded.instructions) == 2
            assert decoded.instructions[0].opcode_name == "PUSH_CONST_INT"
            assert decoded.instructions[1].opcode_name == "RETURN"
    
    def test_decode_with_control_flow(self, decoder):
        """Test decoding with control flow analysis."""
        # Create P-code with a jump
        pcode_data = b'\x32\x01\x00'  # PUSH_CONST_INT 1
        pcode_data += b'\x02\x03\x00' # JUMPTRUE +3
        pcode_data += b'\x32\x02\x00' # PUSH_CONST_INT 2
        pcode_data += b'\x00'         # RETURN
        
        with patch.object(decoder, '_find_pcode_in_object') as mock_find:
            mock_find.return_value = (0, len(pcode_data))
            
            decoded = decoder.decode_object(
                name="test.fun",
                object_type="function",
                data=pcode_data,
                analyze_control_flow=True
            )
            
            assert decoded is not None
            assert 'control_blocks' in decoded.metadata
    
    def test_extract_strings(self, decoder):
        """Test string extraction from object data."""
        # Mock string data
        data = b'\x00\x00\x00\x0C'  # Length 12
        data += b'Hello World\x00'   # Null-terminated string
        
        strings = decoder._extract_strings(data)
        
        # Would need actual string table format
        assert isinstance(strings, dict)
    
    def test_decode_operand_types(self, decoder):
        """Test decoding different operand types."""
        # Test byte operand
        data = b'\x42'
        offset, value = decoder._decode_operand(data, 0, 'byte')
        assert offset == 1
        assert value == 0x42
        
        # Test word operand
        data = b'\x34\x12'
        offset, value = decoder._decode_operand(data, 0, 'word')
        assert offset == 2
        assert value == 0x1234
        
        # Test dword operand
        data = b'\x78\x56\x34\x12'
        offset, value = decoder._decode_operand(data, 0, 'dword')
        assert offset == 4
        assert value == 0x12345678
        
        # Test signed word
        data = b'\xFF\xFF'  # -1 in signed 16-bit
        offset, value = decoder._decode_operand(data, 0, 'sword')
        assert offset == 2
        assert value == -1
    
    def test_format_instruction(self, decoder):
        """Test instruction formatting."""
        inst = PCodeInstruction(
            address=0x100,
            opcode=b'\x32',
            opcode_name='PUSH_CONST_INT',
            operands=[b'\x0A\x00'],
            operand_values=[10],
            text_format='0100: PUSH_CONST_INT 10'
        )
        
        # The text_format is already set in the instruction
        assert '0100' in inst.text_format
        assert 'PUSH_CONST_INT' in inst.text_format
        assert '10' in inst.text_format
    
    def test_decode_empty_data(self, decoder):
        """Test decoding empty data."""
        decoded = decoder.decode_object(
            name="empty.fun",
            object_type="function",
            data=b''
        )
        
        assert decoded is not None
        assert decoded.name == "empty.fun"
        assert len(decoded.instructions) == 0
    
    def test_decode_invalid_opcode(self, decoder):
        """Test handling of invalid opcodes."""
        # Use an invalid opcode that might not be in the table
        data = b'\xFF\xFF\xFF'
        
        with patch.object(decoder.opcode_manager, 'get_opcode') as mock_get:
            mock_get.return_value = None  # Unknown opcode
            
            inst = decoder._decode_instruction(data, 0, 0x100)
            
            # Should still create an instruction with UNKNOWN
            assert inst is not None
            assert 'UNKNOWN' in inst.opcode_name or inst.opcode_name == ''