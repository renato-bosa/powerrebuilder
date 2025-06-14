#!/usr/bin/env python3
"""Debug test to understand what's happening in the decompilation pipeline."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_decompilation_steps() -> None:
    """Test each step of the decompilation process."""
    # Set up detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Find a test file
    test_file = Path("output/extracted/dcm_login.pbd/dcm_login.pbd/f_get_username.fun")
    if not test_file.exists():
        return

    # Step 1: Read the file
    with open(test_file, "rb") as f:
        data = f.read()

    # Step 2: Parse the object
    from decompile.analysis.object_parser import ObjectParser

    object_name = test_file.stem
    pb_object = ObjectParser.parse_object(data, object_name)

    if not pb_object:
        return

    if not pb_object.pcode_data:
        return

    # Step 3: Decode P-code
    from decompile.core.pcode_decoder import PCodeDecoderV2
    from extract.pbd.utils.version_detector import PowerBuilderVersion

    version = PowerBuilderVersion(10, 5, True)
    decoder = PCodeDecoderV2(version)

    decoded_obj = decoder.decode_pcode_section(
        pb_object.pcode_data,
        test_file.name,
        None,
    )

    for _i, inst in enumerate(decoded_obj.instructions[:10]):
        inst.opcode if isinstance(inst.opcode, int) else int.from_bytes(
            inst.opcode, "little"
        )
    if len(decoded_obj.instructions) > 10:
        pass

    # Step 4: Analyze control flow
    from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer

    cf_analyzer = ControlFlowAnalyzer()
    control_blocks = cf_analyzer.analyze(decoded_obj.instructions)

    for _i, block in enumerate(control_blocks[:5]):
        pass

    # Step 5: Reconstruct expressions
    from decompile.core.expression_reconstructor import ExpressionReconstructor

    emulator = ExpressionReconstructor()
    for block in control_blocks[:1]:  # Just test first block
        try:
            emulator.emulate_block(block)

            # Check if expressions were added
            for _j, inst in enumerate(block.instructions[:5]):
                if hasattr(inst, "expression") and inst.expression:
                    pass
                else:
                    pass

        except Exception:
            pass

    # Step 6: Format output
    from decompile.core.output_formatter import OutputFormatter

    formatter = OutputFormatter()
    output_lines = formatter.format_object(
        decoded_obj,
        control_blocks,
        str(test_file),
    )

    for _line in output_lines[:20]:
        pass


if __name__ == "__main__":
    test_decompilation_steps()
