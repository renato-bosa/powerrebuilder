"""PowerBuilder PCode Structured Decompiler.

This module implements a structured decompiler for PowerBuilder PCode (bytecode),
converting it into human-readable pseudocode or Python code. It forms the third
major stage in the reverse engineering pipeline after parsing.

The decompilation process works through two main approaches:
1. Instruction-level analysis: Converting raw (addr, opcode, operand) tuples into
   indented pseudocode by analyzing control flow and block structure
2. Block-based structured decompilation: Building a hierarchical representation of
   code blocks with proper nesting and then generating code using Jinja2 templates

Key features:
- Jump target analysis to detect control flow
- Block stack management for nested structures (if/else, loops, try/catch)
- Transaction block handling (USING statements)
- Exception handling (TRY/CATCH/FINALLY)
- DataWindow operation support
- Template-based output generation for consistent formatting

The decompiler produces Python-like pseudocode that serves as an intermediate
representation for the code generation phase or for human analysis of the
original PowerBuilder application's logic.
"""

import logging
import re
from collections import namedtuple  # Added for PCodeInstruction and DecompiledCode
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

# Define data structures for PCode processing
PCodeInstruction = namedtuple("PCodeInstruction", ["address", "opcode", "operands", "line_number"])
DecompiledCode = namedtuple("DecompiledCode", ["file_path", "pseudocode", "original_pcode"])

# Parses `.fun` text → (addr, opcode, operand) tuples
# - Reads PCode disassembly lines into structured tuples
# - Prepares instruction lists for analysis


def disassemble_pcode(lines):
    """Parse lines of PCode disassembly into structured tuples.

    Args:
        lines (list of str): Lines of PCode disassembly.

    Returns:
        list of tuple: List of (address, opcode, operand) tuples.
    """
    instructions = []
    for line in lines:
        # Example parsing logic; adjust regex as needed for actual PCode format
        match = re.match(r"^(\w+):\s+(\w+)\s+(.*)$", line)
        if match:
            addr, opcode, operand = match.groups()
            instructions.append((addr, opcode, operand))
    return instructions

# Block-stack & jump analysis → indented pseudocode
# - Scans instruction lists to build a map of jump targets
# - Maintains a stack of open blocks (`if`, `else`, `while`, `for`, `try`, `catch`)
# - Emits properly indented Python-style pseudocode lines
# - Detects nested constructs and closes blocks at correct addresses


def analyze_instructions(instructions):
    """Analyze a list of instructions to produce indented pseudocode.

    Args:
        instructions (list of tuple): List of (address, opcode, operand) tuples.

    Returns:
        str: Indented pseudocode as a string.
    """
    pseudocode_lines = []
    block_stack = []
    jump_targets = {}
    exception_handlers = {}

    # First pass - build jump target and exception handler maps
    for addr, opcode, operand in instructions:
        if opcode == 'JUMP':
            jump_targets[addr] = operand
        elif opcode == 'TRY':
            exception_handlers[addr] = operand

    # Second pass - generate pseudocode
    for addr, opcode, operand in instructions:
        # Handle basic control flow
        if opcode == 'JUMP':
            jump_targets[addr] = operand
        elif opcode in {'IF', 'WHILE', 'FOR'}:
            block_stack.append(opcode)
            pseudocode_lines.append(f"{opcode.lower()} {operand}:")
        elif opcode == 'ELSE':
            pseudocode_lines.append("else:")
        elif opcode == 'END':
            if block_stack:
                block_stack.pop()
            pseudocode_lines.append("# end block")

        # Handle transactions
        elif opcode == 'USING':
            block_stack.append('TRANSACTION')
            pseudocode_lines.append(f"using {operand}:")

        # Handle exception blocks
        elif opcode == 'TRY':
            block_stack.append('TRY')
            pseudocode_lines.append("try:")
        elif opcode == 'CATCH':
            if block_stack and block_stack[-1] == 'TRY':
                block_stack[-1] = 'CATCH'
            pseudocode_lines.append(f"catch ({operand}):")
        elif opcode == 'FINALLY':
            if block_stack and block_stack[-1] in {'TRY', 'CATCH'}:
                block_stack[-1] = 'FINALLY'
            pseudocode_lines.append("finally:")

        # Handle DataWindow operations
        elif opcode == 'DW_RETRIEVE':
            pseudocode_lines.append(f"dw.retrieve({operand})")
        elif opcode == 'DW_UPDATE':
            pseudocode_lines.append(f"dw.update({operand})")

        else:
            pseudocode_lines.append(f"# {opcode} {operand}")

    return "\n".join(pseudocode_lines)


"""Structured decompiler for PowerBuilder code.

Converts PowerBuilder bytecode into structured Python code using templates.
"""


class Block:
    """Represents a code block in the decompiled output."""

    def __init__(self, type: str, opcode: str = "", operand: str = "") -> None:
        """Initialize block.

        Args:
            type: Block type (if, using, try, datawindow, other)
            opcode: Optional opcode for the block
            operand: Optional operand for the block
        """
        self.type = type
        self.opcode = opcode
        self.operand = operand
        self.operation = ""  # For DataWindow operations
        self.statements: list[str] = []
        self.else_statements: list[str] = []
        self.try_statements: list[str] = []
        self.catch_blocks: list[dict[str, Any]] = []
        self.finally_statements: list[str] = []


class StructuredDecompiler:
    """Decompiles PowerBuilder bytecode into structured Python code."""

    def __init__(self, template_dir: str | None = None) -> None:
        """Initialize decompiler.

        Args:
            template_dir: Optional directory containing templates
        """
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def decompile(self, bytecode: list[dict[str, str]]) -> str:
        """Decompile PowerBuilder bytecode to Python code.

        Args:
            bytecode: List of bytecode instructions

        Returns:
            Decompiled Python code
        """
        blocks: list[Block] = []
        current_block: Block | None = None

        for instr in bytecode:
            opcode = instr["opcode"]
            operand = instr.get("operand", "")

            if opcode in {"IF", "ELSEIF"}:
                if current_block and current_block.type == "if":
                    blocks.append(current_block)
                current_block = Block("if", opcode, operand)

            elif opcode == "ELSE":
                if current_block and current_block.type == "if":
                    current_block.else_statements = []

            elif opcode == "ENDIF":
                if current_block and current_block.type == "if":
                    blocks.append(current_block)
                current_block = None

            elif opcode == "USING":
                if current_block:
                    blocks.append(current_block)
                current_block = Block("using", operand=operand)

            elif opcode == "ENDUSING":
                if current_block and current_block.type == "using":
                    blocks.append(current_block)
                current_block = None

            elif opcode == "TRY":
                if current_block:
                    blocks.append(current_block)
                current_block = Block("try")

            elif opcode == "CATCH":
                if current_block and current_block.type == "try":
                    current_block.catch_blocks.append({
                        "operand": operand,
                        "statements": [],
                    })

            elif opcode == "FINALLY":
                if current_block and current_block.type == "try":
                    current_block.finally_statements = []

            elif opcode == "ENDTRY":
                if current_block and current_block.type == "try":
                    blocks.append(current_block)
                current_block = None

            elif opcode in {"RETRIEVE", "UPDATE"}:
                block = Block("datawindow")
                block.operation = opcode.lower()
                block.operand = operand
                blocks.append(block)

            else:
                block = Block("other", opcode, operand)
                blocks.append(block)

            # Add statement to current block
            if current_block:
                if opcode == "ELSE" and current_block.type == "if":
                    current_block.else_statements.append(f"{opcode} {operand}")
                elif current_block.type == "try":
                    if current_block.catch_blocks and not current_block.finally_statements:
                        # Add to the latest catch block
                        current_block.catch_blocks[-1]["statements"].append(f"{opcode} {operand}")
                    elif current_block.finally_statements:
                        current_block.finally_statements.append(f"{opcode} {operand}")
                    else:
                        current_block.try_statements.append(f"{opcode} {operand}")
                else:
                    current_block.statements.append(f"{opcode} {operand}")

        if current_block:
            blocks.append(current_block)

        # Render the blocks using templates
        output_code = []
        for block in blocks:
            template_name = f"block_{block.type}.py.j2"
            template = self.env.get_template(template_name)
            output_code.append(template.render(block=block))

        return "\n".join(output_code)


logger = logging.getLogger(__name__)

# Placeholder for PCode line format, adjust as needed
PCODE_LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]+):\s*([A-Z_0-9]+)(?:\s+(.*))?$")


def decompile_pcode_file(pcode_file_path: Path) -> DecompiledCode | None:
    if not pcode_file_path.is_file():
        logger.warning(f"PCode file not found: {pcode_file_path}")
        return None

    try:
        with open(pcode_file_path, encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading PCode file {pcode_file_path}: {e}")
        return None

    instructions = []
    labels = {}  # Store address of labels
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Simplistic check: if a line doesn't look like PCode, skip it.
        # This helps avoid crashing on non-PCode .fun files from primary extraction.
        if not PCODE_LINE_RE.match(line):
            # logger.debug(f"Skipping non-PCode line in {pcode_file_path}: {line}")
            continue

        match = PCODE_LINE_RE.match(line)  # Re-match to capture groups
        if match:
            addr_str, opcode, operands_str = match.groups()
            address = int(addr_str, 16)
            operands = [op.strip() for op in operands_str.split(',')] if operands_str else []

            # Example: crude label detection if opcode looks like a jump and operand is a hex address
            if opcode.startswith("J") and operands and operands[0].startswith("0x"):
                try:
                    target_addr = int(operands[0], 16)
                    if target_addr not in labels:
                        labels[target_addr] = f"L_{target_addr:04X}"
                except ValueError:
                    pass  # Operand not a valid hex address

            instructions.append(PCodeInstruction(address, opcode, operands, line_number=i + 1))
        # else: # Already handled by the continue above
            # logger.warning(f"PCode line does not match expected format '{PCODE_LINE_RE.pattern}': {line} in {pcode_file_path}")

    if not instructions:
        # logger.warning(f"No valid PCode instructions found in {pcode_file_path}")
        return None

    # This is a very basic structuring, real structuring would involve control flow graph, etc.
    # For now, just use labels for jumps.
    structured_code = []
    for inst in instructions:
        if inst.address in labels:
            structured_code.append(f"{labels[inst.address]}:")

        op_str = ", ".join(inst.operands)
        # If jump to a known label, use the label name
        if inst.opcode.startswith("J") and inst.operands and inst.operands[0].startswith("0x"):
            try:
                target_addr = int(inst.operands[0], 16)
                if target_addr in labels:
                    op_str = labels[target_addr]
                    if len(inst.operands) > 1:  # Keep other operands if any
                        op_str += ", " + ", ".join(inst.operands[1:])
            except ValueError:
                pass

        structured_code.append(f"  {inst.opcode} {op_str}")

    return DecompiledCode(
        file_path=str(pcode_file_path),
        # For now, pseudocode is just the slightly formatted instructions
        pseudocode="\n".join(structured_code),
        original_pcode="\n".join(lines),
    )


def decompile_directory(input_dir_base: str | Path, output_dir_decompile: str | Path) -> None:
    input_base_path = Path(input_dir_base)
    output_decompile_path = Path(output_dir_decompile)
    output_decompile_path.mkdir(parents=True, exist_ok=True)

    decompiled_count = 0
    failed_count = 0

    if not input_base_path.exists() or not input_base_path.is_dir():
        logger.info(f"Input directory for PCode not found: {input_base_path}. Cannot decompile.")
        logger.info(f"Decompilation complete. Decompiled: {decompiled_count}, Failed: {failed_count}")
        return

    logger.info(f"Searching for PBD-specific directories in: {input_base_path}")

    for pbd_dir in input_base_path.iterdir():  # Iterate through items in output/extracted/
        if pbd_dir.is_dir():  # Check if item is a directory (e.g., output/extracted/dcm_accounting.pbd/)
            logger.debug(f"Searching for .fun files in PBD directory: {pbd_dir.name}")
            for fun_file in pbd_dir.rglob('*.fun'):  # Search for .fun files
                if fun_file.is_file():
                    logger.debug(f"Attempting to decompile (from primary extraction): {fun_file}")

                    # Create corresponding output structure in output/decompiled/
                    # e.g. output/decompiled/dcm_accounting.pbd/object_decompiled.txt
                    relative_path_from_input_base = fun_file.relative_to(input_base_path)
                    output_sub_dir = output_decompile_path / relative_path_from_input_base.parent
                    output_sub_dir.mkdir(parents=True, exist_ok=True)

                    output_file_name = fun_file.stem + "_decompiled.txt"
                    output_file_path = output_sub_dir / output_file_name

                    decompiled_data = decompile_pcode_file(fun_file)
                    if decompiled_data:
                        try:
                            with open(output_file_path, 'w', encoding='utf-8') as f_out:
                                f_out.write(f"--- Original PCode from: {decompiled_data.file_path} ---\n")
                                f_out.write(decompiled_data.original_pcode)
                                f_out.write("\n\n--- Pseudocode ---\n")
                                f_out.write(decompiled_data.pseudocode)
                            logger.info(f"Successfully decompiled and saved to {output_file_path}")
                            decompiled_count += 1
                        except Exception as e:
                            logger.error(f"Error writing decompiled output for {fun_file} to {output_file_path}: {e}")
                            failed_count += 1
                    # else: No PCode found or other non-critical failure, already logged by decompile_pcode_file

    logger.info(f"Decompilation complete. Decompiled: {decompiled_count}, Failed: {failed_count}")


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) >= 3:
        # Direct file decompilation
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])
        
        logger.info(f"Decompiling {input_file} to {output_file}")
        
        decompiled = decompile_pcode_file(input_file)
        if decompiled:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"--- Original PCode from: {decompiled.file_path} ---\n")
                f.write(decompiled.original_pcode)
                f.write("\n\n--- Pseudocode ---\n")
                f.write(decompiled.pseudocode)
            logger.info(f"Successfully decompiled to {output_file}")
        else:
            logger.error(f"Failed to decompile {input_file}")
    elif len(sys.argv) == 2:
        # Directory mode
        input_dir = Path(sys.argv[1])
        output_dir = input_dir.parent / (input_dir.name + "_decompiled")
        decompile_directory(input_dir, output_dir)
    else:
        print("Usage:")
        print("  python decompile_structured.py <input_pcode_file> <output_file>")
        print("  python decompile_structured.py <input_directory>")
