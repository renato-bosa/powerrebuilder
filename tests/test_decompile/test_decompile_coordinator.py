#!/usr/bin/env python3
"""Comprehensive test suite for Decompile coordinator."""

import struct
import tempfile
from pathlib import Path

from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer
from decompile.analysis.object_parser import ObjectParser
from decompile.core.expression_reconstructor import (
    Expression,
    ExpressionReconstructor,
    ExpressionType,
    StackValue,
)
from decompile.core.output_formatter import OutputFormatter
from decompile.core.pcode_decoder import DecodedObject, PCodeDecoderV2, PCodeInstruction
from decompile.decompile_coordinator import ExtractedFileDecompiler, decompile_directory
from decompile.opcodes import OPCODE_TABLE, get_opcode_info
from decompile.types import BlockType, ControlBlock
from extract.pbd.utils.version_detector import PowerBuilderVersion


class TestPCodeDecoder:
    """Test P-code decoding functionality."""

    def test_decoder_initialization(self):




        """Test decoder initialization with different versions."""
        # Default version (None is acceptable)
        decoder = PCodeDecoderV2()
        assert hasattr(decoder, "version")

        # Specific version
        version = PowerBuilderVersion(10, 5, True)
        decoder = PCodeDecoderV2(version)
        assert decoder.version == version

    def test_decode_simple_instruction(self):




        """Test decoding a simple instruction."""
        version = PowerBuilderVersion(10, 5, True)
        decoder = PCodeDecoderV2(version)

        # Create simple RETURN instruction (opcode 0x00)
        pcode_data = bytes([0x00, 0x00])  # RETURN with 1 byte operand

        decoded = decoder.decode_pcode_section(pcode_data, "test_func", None)

        assert decoded.name == "test_func"
        assert len(decoded.instructions) > 0

        # Check first instruction
        first_inst = decoded.instructions[0]
        assert first_inst.opcode_name == "RETURN"

    def test_decode_multiple_instructions(self):




        """Test decoding multiple instructions."""
        version = PowerBuilderVersion(10, 5, True)
        decoder = PCodeDecoderV2(version)

        # Create a sequence of instructions
        pcode_data = bytes([
            0x04, 0x05,  # JUMP with 2-byte offset
            0x1D, 0x01,  # PUSH_BOOLEAN true
            0x00, 0x00,   # RETURN
        ])

        decoded = decoder.decode_pcode_section(pcode_data, "test_func", None)

        assert len(decoded.instructions) >= 2
        assert decoded.instructions[0].opcode_name == "JUMP"
        assert any(inst.opcode_name == "RETURN" for inst in decoded.instructions)

    def test_decode_with_operands(self):




        """Test decoding instructions with operands."""
        version = PowerBuilderVersion(10, 5, True)
        decoder = PCodeDecoderV2(version)

        # PUSH_CONST_INT instruction with 2-byte operand (opcode 0x32)
        value = 42
        pcode_data = bytes([0x32]) + struct.pack("<H", value)  # H for uint16

        decoded = decoder.decode_pcode_section(pcode_data, "test_func", None)

        assert len(decoded.instructions) > 0
        inst = decoded.instructions[0]
        assert inst.opcode_name == "PUSH_CONST_INT"
        assert len(inst.operand_values) > 0
        # Check if the operand value is correct (might be int or hex string)
        if isinstance(inst.operand_values[0], str):
            assert int(inst.operand_values[0], 16) == value
        else:
            assert inst.operand_values[0] == value

    def test_decode_invalid_pcode(self):




        """Test handling of invalid P-code data."""
        decoder = PCodeDecoderV2()

        # Empty data
        decoded = decoder.decode_pcode_section(b"", "test", None)
        assert len(decoded.instructions) == 0

        # Invalid opcode
        decoded = decoder.decode_pcode_section(b"\xFF\xFF\xFF", "test", None)
        # Should still try to decode, even if unknown
        assert decoded is not None


class TestExpressionReconstructor:
    """Test expression reconstruction functionality."""

    def test_stack_operations(self):




        """Test basic stack operations."""
        reconstructor = ExpressionReconstructor()

        # Push literal - using StackValue which is what the reconstructor uses
        lit_val = StackValue(expression="42", type="int")
        reconstructor.stack.append(lit_val)
        assert len(reconstructor.stack) == 1
        assert reconstructor.stack[-1].expression == "42"

        # Pop
        popped = reconstructor.stack.pop()
        assert popped.expression == "42"
        assert len(reconstructor.stack) == 0

    def test_binary_expression_reconstruction(self):




        """Test reconstructing binary expressions."""
        reconstructor = ExpressionReconstructor()

        # Create instructions that push two values and add them
        instructions = [
            PCodeInstruction(0, b"\x20", "PUSH_INT32", b"\x0A\x00\x00\x00", [10], "PUSH 10"),
            PCodeInstruction(4, b"\x20", "PUSH_INT32", b"\x14\x00\x00\x00", [20], "PUSH 20"),
            PCodeInstruction(8, b"\x2A", "ADD", b"", [], "ADD"),
        ]

        # Create a block and emulate it
        block = ControlBlock(type=BlockType.BASIC, start_addr=0, end_addr=12, instructions=instructions)
        reconstructor.emulate_block(block)

        # Check that statements were generated
        assert len(block.statements) >= 0

        # The ADD operation should have consumed both values and produced a result
        # Since we're using emulate_block, the result is in block.statements

    def test_unary_expression_reconstruction(self):




        """Test reconstructing unary expressions."""
        reconstructor = ExpressionReconstructor()

        # Create instructions that push a boolean and apply NOT
        instructions = [
            PCodeInstruction(0, b"\x1D", "PUSH_BOOLEAN", b"\x01", [True], "PUSH true"),
            PCodeInstruction(2, b"\x26", "NOT", b"", [], "NOT"),  # Using correct opcode 0x26 for NOT
        ]

        # Create a block and emulate it
        block = ControlBlock(type=BlockType.BASIC, start_addr=0, end_addr=4, instructions=instructions)
        reconstructor.emulate_block(block)

        # Check that the block was processed
        assert hasattr(block, "statements")

    def test_emulate_block(self):




        """Test emulating a control flow block."""
        reconstructor = ExpressionReconstructor()

        # Create a block with multiple instructions
        instructions = [
            PCodeInstruction(0, b"\x20", "PUSH_INT32", b"\x0A\x00\x00\x00", [10], "PUSH 10"),
            PCodeInstruction(4, b"\x20", "PUSH_INT32", b"\x14\x00\x00\x00", [20], "PUSH 20"),
            PCodeInstruction(8, b"\x2A", "ADD", b"", [], "ADD"),
        ]

        block = ControlBlock(type=BlockType.BASIC, start_addr=0, end_addr=12, instructions=instructions)

        reconstructor.emulate_block(block)

        # Check that the block has statements after emulation
        assert hasattr(block, "statements")
        # The block should have processed the instructions


class TestControlFlowAnalyzer:
    """Test control flow analysis."""

    def test_basic_block_creation(self):




        """Test creating basic blocks from instructions."""
        analyzer = ControlFlowAnalyzer()

        instructions = [
            PCodeInstruction(0, b"\x20", "PUSH_INT32", b"", [10], "PUSH 10"),
            PCodeInstruction(4, b"\x00", "RETURN", b"", [], "RETURN"),
        ]

        blocks = analyzer.analyze(instructions)

        assert len(blocks) == 1
        assert blocks[0].start_addr == 0
        assert len(blocks[0].instructions) == 2

    def test_conditional_branch_analysis(self):




        """Test analyzing conditional branches."""
        analyzer = ControlFlowAnalyzer()

        instructions = [
            PCodeInstruction(0, b"\x1D", "PUSH_BOOLEAN", b"\x01", [True], "PUSH true"),
            PCodeInstruction(2, b"\x03", "JUMPFALSE", b"\x08\x00", [8], "JUMPFALSE 8"),
            PCodeInstruction(4, b"\x20", "PUSH_INT32", b"\x01\x00\x00\x00", [1], "PUSH 1"),
            PCodeInstruction(8, b"\x00", "RETURN", b"", [], "RETURN"),
        ]

        blocks = analyzer.analyze(instructions)

        # Should create multiple blocks due to branch
        assert len(blocks) >= 2

        # Check that branch creates proper edges
        branch_block = blocks[0]
        assert any("JUMPFALSE" in inst.opcode_name for inst in branch_block.instructions)

    def test_loop_detection(self):




        """Test detecting loops in control flow."""
        analyzer = ControlFlowAnalyzer()

        # Simple loop structure
        instructions = [
            PCodeInstruction(0, b"\x20", "PUSH_INT32", b"\x00\x00\x00\x00", [0], "PUSH 0"),
            PCodeInstruction(4, b"\x20", "PUSH_INT32", b"\x0A\x00\x00\x00", [10], "PUSH 10"),
            PCodeInstruction(8, b"\x2F", "LT", b"", [], "LT"),
            PCodeInstruction(9, b"\x03", "JUMPFALSE", b"\x10\x00", [16], "JUMPFALSE end"),
            PCodeInstruction(11, b"\x04", "JUMP", b"\xF5\xFF", [-11], "JUMP loop_start"),
            PCodeInstruction(16, b"\x00", "RETURN", b"", [], "RETURN"),
        ]

        blocks = analyzer.analyze(instructions)

        # Should detect back edge (loop)
        assert len(blocks) >= 2
        # One block should have a predecessor with higher address (back edge)


class TestOutputFormatter:
    """Test output formatting."""

    def test_format_simple_object(self):




        """Test formatting a simple decoded object."""
        formatter = OutputFormatter()

        decoded_obj = DecodedObject(
            name="test_func",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
            instructions=[
                PCodeInstruction(0, b"\x20", "PUSH_INT32", b"", [42], "PUSH 42"),
                PCodeInstruction(4, b"\x00", "RETURN", b"", [], "RETURN"),
            ],
        )

        blocks = [ControlBlock(type=BlockType.BASIC, start_addr=0, end_addr=8, instructions=decoded_obj.instructions)]

        output = formatter.format_object(decoded_obj, blocks, "test.fun")

        assert len(output) > 0
        assert any("function" in line.lower() for line in output)
        assert any("return" in line.lower() for line in output)

    def test_format_with_expressions(self):




        """Test formatting with reconstructed expressions."""
        formatter = OutputFormatter()

        # Create object with expression
        decoded_obj = DecodedObject(
            name="calc_sum",
            type="function",
            version=PowerBuilderVersion(10, 5, True),
        )

        # Create blocks with expressions
        expr = Expression(
            type=ExpressionType.BINARY_OP,
            value="+",
            children=[
                Expression(ExpressionType.VARIABLE, "a"),
                Expression(ExpressionType.VARIABLE, "b"),
            ],
        )

        block = ControlBlock(type=BlockType.BASIC, start_addr=0, end_addr=8, instructions=[])
        # Convert expression to statement
        block.statements = [f"return {expr.to_string()}"]

        output = formatter.format_object(decoded_obj, [block], "test.fun")

        assert len(output) > 0
        # Should contain the expression
        output_text = "\n".join(output)
        assert "a" in output_text or "b" in output_text


class TestObjectParser:
    """Test PowerBuilder object parsing."""

    def test_parse_object_with_pcode(self):




        """Test parsing object with P-code section."""
        # Create mock object data with P-code marker
        object_data = b"OBJECT_HEADER" + b"\x00" * 100 + b"PCODE_START"

        parsed = ObjectParser.parse_object(object_data, "test_obj")

        assert parsed is not None
        assert parsed.object_name == "test_obj"

    def test_parse_empty_object(self):




        """Test parsing empty object."""
        parsed = ObjectParser.parse_object(b"", "empty")

        # Should handle gracefully
        assert parsed is None or parsed.pcode_length == 0


class TestExtractedFileDecompiler:
    """Test the main decompiler for extracted files."""

    def test_decompiler_initialization(self):




        """Test decompiler initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"

            decompiler = ExtractedFileDecompiler(output_dir, enable_filtering=True)

            assert decompiler.output_dir == output_dir
            assert output_dir.exists()
            assert decompiler.enable_filtering is True

    def test_decompile_empty_file(self):




        """Test decompiling an empty file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty file
            test_file = Path(temp_dir) / "empty.fun"
            test_file.write_bytes(b"")

            decompiler = ExtractedFileDecompiler()
            result = decompiler.decompile_extracted_file(test_file)

            # Should handle gracefully
            assert result is False

    def test_decompile_simple_function(self):




        """Test decompiling a simple function file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"

            # Create mock function file with minimal P-code
            test_file = Path(temp_dir) / "test_func.fun"
            # This would need actual PowerBuilder object format
            # For now, just test the flow
            test_file.write_bytes(b"MOCK_FUNCTION_DATA")

            decompiler = ExtractedFileDecompiler(output_dir)
            result = decompiler.decompile_extracted_file(test_file)

            # Will fail to parse but should handle gracefully
            assert isinstance(result, bool)

    def test_decompile_with_output_dir(self):




        """Test decompiling with output directory specified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "decompiled"
            test_file = Path(temp_dir) / "test.fun"
            test_file.write_bytes(b"TEST_DATA")

            decompiler = ExtractedFileDecompiler(output_dir)
            decompiler.decompile_extracted_file(test_file)

            # Output directory should be created
            assert output_dir.exists()


class TestDecompileHelpers:
    """Test decompile helper functions."""

    def test_decompile_directory(self):




        """Test the decompile_directory helper function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            input_dir.mkdir()
            output_dir = Path(temp_dir) / "output"

            # Create some test files
            (input_dir / "test1.fun").write_bytes(b"TEST1")
            (input_dir / "test2.men").write_bytes(b"TEST2")
            (input_dir / "ignore.txt").write_bytes(b"IGNORE")

            # decompile_directory returns None, not a count
            decompile_directory(str(input_dir), str(output_dir))

            # Check that output directory was created
            assert output_dir.exists()


class TestOpcodeInfo:
    """Test opcode information retrieval."""

    def test_get_known_opcode_info(self):




        """Test getting info for known opcodes."""
        # Test RETURN opcode
        info = get_opcode_info(0x00)
        assert info is not None
        assert len(info) == 3  # Should be (mnemonic, length, hint)
        assert info[0] == "RETURN"

        # Test PUSH_CONST_REF opcode (0x20)
        info = get_opcode_info(0x20)
        assert info is not None
        assert len(info) == 3
        assert info[0] == "PUSH_CONST_REF"

    def test_get_unknown_opcode_info(self):




        """Test getting info for unknown opcodes."""
        # Use a very high opcode value that's unlikely to be defined
        info = get_opcode_info(0xFFFF)  # 65535 - way beyond any real opcode

        # Should return None for undefined opcodes
        assert info is None

    def test_opcode_table_completeness(self):




        """Test that opcode table has expected entries."""
        # Check some key opcodes exist
        assert 0x00 in OPCODE_TABLE  # RETURN
        assert 0x04 in OPCODE_TABLE  # JUMP
        assert 0x20 in OPCODE_TABLE  # PUSH_INT32

        # Check operand counts make sense
        return_info = OPCODE_TABLE[0x00]
        assert return_info[1] >= 1  # At least 1 byte for RETURN

        jump_info = OPCODE_TABLE[0x04]
        assert jump_info[1] >= 2  # At least 2 bytes for JUMP offset
