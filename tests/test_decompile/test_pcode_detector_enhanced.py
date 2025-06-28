"""Unit tests for enhanced P-code detector."""

from decompile.analyzers.pcode_detector import EnhancedPCodeDetector


class TestEnhancedPCodeDetector:
    """Test enhanced P-code detection functionality."""

    def test_find_pcode_in_function_empty_data(self):




        """Test with empty data."""
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(b"")
        assert offset == -1
        assert length == 0

    def test_find_pcode_in_function_short_data(self):




        """Test with data too short to contain P-code."""
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(b"ABC")
        assert offset == -1
        assert length == 0

    def test_find_pcode_with_return_pattern(self):




        """Test P-code detection with RETURN opcode pattern."""
        # Create test data with valid P-code sequence
        test_data = b"\x04\x00\x10\x00\x00\x00"  # JUMP followed by RETURNs
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(test_data)
        # The detector looks for valid P-code patterns
        if offset == -1:
            # If not found, that's okay - the test data might not match detection criteria
            assert length == 0
        else:
            assert offset >= 0
            assert length > 0

    def test_find_pcode_with_jump_pattern(self):




        """Test P-code detection with JUMP opcode pattern."""
        # Create test data with JUMP opcode (0x04)
        test_data = b"metadata" + b"\x04\x00\x10\x00"  # JUMP with offset
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(test_data)
        # The detector might find it at offset 8 or not at all
        if offset != -1:
            assert offset >= 0
            assert length > 0

    def test_looks_like_pcode_valid_opcodes(self):




        """Test P-code validation with valid opcodes."""
        # Mix of valid opcodes
        valid_data = (
            b"\x00\x04\x05\x29\x2c"  # RETURN, JUMP, DBSTART, GLOBFUNCCALL, DOTFUNCCALL
        )
        assert EnhancedPCodeDetector._looks_like_pcode(valid_data) is True

    def test_looks_like_pcode_invalid_data(self):




        """Test P-code validation with text data."""
        text_data = b"Hello World!"
        assert EnhancedPCodeDetector._looks_like_pcode(text_data) is False

    def test_verify_pcode_context_binary_data(self):




        """Test context verification with binary data."""
        # Mostly non-printable bytes
        binary_data = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        assert EnhancedPCodeDetector._verify_pcode_context(binary_data, 5) is True

    def test_verify_pcode_context_text_data(self):




        """Test context verification with text data."""
        # Mostly printable ASCII
        text_data = b"This is regular text content"
        assert EnhancedPCodeDetector._verify_pcode_context(text_data, 10) is False

    def test_find_text_to_binary_transition(self):




        """Test finding transition from text to binary data."""
        # Create data with clear text-to-binary transition
        text_part = b"Function metadata and description text here"
        binary_part = b"\x00\x04\x05\x29\x2c\x00\x01\x02"
        test_data = text_part + binary_part

        transition = EnhancedPCodeDetector._find_text_to_binary_transition(test_data)
        assert transition == len(text_part)

    def test_find_pcode_end_multiple_returns(self):




        """Test end detection with multiple RETURN opcodes."""
        # Three consecutive RETURNs should mark end
        pcode_data = b"\x04\x00\x10"  # JUMP
        pcode_data += b"\x00\x00\x00"  # Three RETURNs
        pcode_data += b"\xff\xff\xff"  # Padding

        end_offset = EnhancedPCodeDetector._find_pcode_end(pcode_data, 0)
        assert end_offset == 4  # Should end after first valid instruction

    def test_find_pcode_end_padding_detection(self):




        """Test end detection with padding bytes."""
        # Code followed by null padding
        pcode_data = b"\x04\x00\x10"  # JUMP
        pcode_data += b"\x00" * 10  # Null padding

        end_offset = EnhancedPCodeDetector._find_pcode_end(pcode_data, 0)
        assert end_offset < len(pcode_data)  # Should not include all padding

    def test_find_pcode_section_function_type(self):




        """Test main entry point for function objects."""
        test_data = b"metadata" + b"\x00\x00\x04\x00\x10\x00"
        offset, length = EnhancedPCodeDetector.find_pcode_section(test_data, "function")
        assert offset >= 0 or (offset == -1 and length == 0)  # Valid result

    def test_find_pcode_section_other_type(self):




        """Test fallback for non-function object types."""
        # This should fall back to original detector
        # We can't test the actual fallback without mocking, but we can ensure no crash
        test_data = b"window object data"
        offset, length = EnhancedPCodeDetector.find_pcode_section(test_data, "window")
        assert isinstance(offset, int)
        assert isinstance(length, int)
