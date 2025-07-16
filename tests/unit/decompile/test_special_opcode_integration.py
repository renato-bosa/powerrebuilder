#!/usr/bin/env python3
"""Integration test for special opcode formatting in expression reconstruction."""


from src.model.expressions.reconstructor import ExpressionReconstructor
from src.decompile.pcode.decoder import PCodeInstruction
from src.decompile.types import BlockType, ControlBlock


class TestSpecialOpcodeIntegration:
    """Test integration of special opcode formatting with expression reconstruction."""

    def test_database_operations_integration(self):




        """Test that database operations are formatted properly in reconstruction."""
        # Create a control block with database operations
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x100,
            end_addr=0x110,
            instructions=[
                PCodeInstruction(
                    address=0x100,
                    opcode=b"\x05",
                    opcode_name="DBSTART",
                    operands=b"",
                    operand_values=[],
                    text_format="DBSTART",
                ),
                PCodeInstruction(
                    address=0x101,
                    opcode=b"\x10",
                    opcode_name="DBSELECT",
                    operands=b"\x03\x01\x05",
                    operand_values=[3, 1, 5],  # 3 columns, cursor 1, sql string 5
                    text_format="DBSELECT 3, 1, 5",
                ),
                PCodeInstruction(
                    address=0x104,
                    opcode=b"\x0E",
                    opcode_name="DBFETCH",
                    operands=b"\x01",
                    operand_values=[1],
                    text_format="DBFETCH 1",
                ),
                PCodeInstruction(
                    address=0x105,
                    opcode=b"\x06",
                    opcode_name="DBCOMMIT",
                    operands=b"",
                    operand_values=[],
                    text_format="DBCOMMIT",
                ),
            ],
        )

        # Set up the reconstructor with string table
        reconstructor = ExpressionReconstructor()
        reconstructor.strings[5] = "SELECT id, name, amount FROM orders WHERE status = ?"
        # Update the special formatter's string table reference
        reconstructor.special_formatter.strings = reconstructor.strings

        # Emulate the block
        reconstructor.emulate_block(block)

        # Check the formatted statements
        assert len(block.statements) == 4
        assert block.statements[0] == "/* Start transaction */"
        assert block.statements[1] == "SELECT /* 3 columns */ SELECT id, name, amount FROM orders WHERE status = ?"
        assert block.statements[2] == "FETCH cursor_1 INTO :variables"
        assert block.statements[3] == "COMMIT"

    def test_control_flow_formatting(self):




        """Test that control flow operations are formatted properly."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x200,
            end_addr=0x210,
            instructions=[
                PCodeInstruction(
                    address=0x200,
                    opcode=b"\x02",
                    opcode_name="JUMPTRUE",
                    operands=b"\x50\x02",
                    operand_values=[0x250],
                    text_format="JUMPTRUE 0x250",
                ),
                PCodeInstruction(
                    address=0x201,
                    opcode=b"\x04",
                    opcode_name="JUMP",
                    operands=b"\x00\x03",
                    operand_values=[0x300],
                    text_format="JUMP 0x300",
                ),
            ],
        )

        reconstructor = ExpressionReconstructor()
        reconstructor.emulate_block(block)

        assert len(block.statements) == 2
        assert block.statements[0] == "if (condition) goto L_0250"
        assert block.statements[1] == "goto L_0300"

    def test_function_call_formatting(self):




        """Test that function calls are formatted properly."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x300,
            end_addr=0x310,
            instructions=[
                PCodeInstruction(
                    address=0x300,
                    opcode=b"\x29",
                    opcode_name="GLOBFUNCCALL",
                    operands=b"\x2A",
                    operand_values=[42],
                    text_format="GLOBFUNCCALL 42",
                ),
                PCodeInstruction(
                    address=0x301,
                    opcode=b"\x2B",
                    opcode_name="DLLFUNCCALL",
                    operands=b"\x37\x03",
                    operand_values=[55, 3],
                    text_format="DLLFUNCCALL 55, 3",
                ),
            ],
        )

        reconstructor = ExpressionReconstructor()
        reconstructor.methods[42] = "calculate_discount"
        reconstructor.methods[55] = "GetSystemTime"
        # Update the special formatter's function table reference
        reconstructor.special_formatter.functions = reconstructor.methods
        reconstructor.emulate_block(block)

        assert len(block.statements) == 2
        assert block.statements[0] == "calculate_discount() /* global function */"
        assert block.statements[1] == "GetSystemTime() /* 3 args */ /* external function */"

    def test_event_call_formatting(self):




        """Test that event calls are formatted properly."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x400,
            end_addr=0x410,
            instructions=[
                PCodeInstruction(
                    address=0x400,
                    opcode=b"\x13",
                    opcode_name="EVENTCALL",
                    operands=b"\x0A\x14",
                    operand_values=[10, 20],
                    text_format="EVENTCALL 10, 20",
                ),
            ],
        )

        reconstructor = ExpressionReconstructor()
        reconstructor.methods[10] = "ue_itemchanged"
        # Update the special formatter's function table reference
        reconstructor.special_formatter.functions = reconstructor.methods
        reconstructor.emulate_block(block)

        assert len(block.statements) == 1
        assert block.statements[0] == "TriggerEvent('ue_itemchanged')"

    def test_exception_handling_formatting(self):




        """Test that exception handling is formatted properly."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x500,
            end_addr=0x510,
            instructions=[
                PCodeInstruction(
                    address=0x500,
                    opcode=b"\xE5\x01",
                    opcode_name="PUSH_TRY",
                    operands=b"",
                    operand_values=[],
                    text_format="PUSH_TRY",
                ),
                PCodeInstruction(
                    address=0x501,
                    opcode=b"\xE7\x01",
                    opcode_name="CATCH_EXCEPTION",
                    operands=b"\x01",
                    operand_values=[1],
                    text_format="CATCH_EXCEPTION 1",
                ),
                PCodeInstruction(
                    address=0x502,
                    opcode=b"\xE8\x01",
                    opcode_name="THROW_EXCEPTION",
                    operands=b"",
                    operand_values=[],
                    text_format="THROW_EXCEPTION",
                ),
            ],
        )

        reconstructor = ExpressionReconstructor()
        reconstructor.emulate_block(block)

        assert len(block.statements) == 3
        assert block.statements[0] == "TRY"
        assert block.statements[1] == "CATCH (Exception_1 e)"
        assert block.statements[2] == "THROW"

    def test_array_operations_formatting(self):




        """Test that array operations are formatted properly."""
        block = ControlBlock(
            type=BlockType.BASIC,
            start_addr=0x600,
            end_addr=0x610,
            instructions=[
                PCodeInstruction(
                    address=0x600,
                    opcode=b"\x2E",
                    opcode_name="ARRAYLIST",
                    operands=b"\x05",
                    operand_values=[5],
                    text_format="ARRAYLIST 5",
                ),
                PCodeInstruction(
                    address=0x601,
                    opcode=b"\xB8\x01",
                    opcode_name="LOWERBOUND",
                    operands=b"",
                    operand_values=[],
                    text_format="LOWERBOUND",
                ),
                PCodeInstruction(
                    address=0x602,
                    opcode=b"\xB9\x01",
                    opcode_name="UPPERBOUND",
                    operands=b"",
                    operand_values=[],
                    text_format="UPPERBOUND",
                ),
            ],
        )

        reconstructor = ExpressionReconstructor()
        reconstructor.emulate_block(block)

        assert len(block.statements) == 3
        assert block.statements[0] == "/* Create array list with 5 elements */"
        assert block.statements[1] == "LowerBound(array, dimension)"
        assert block.statements[2] == "UpperBound(array, dimension)"
