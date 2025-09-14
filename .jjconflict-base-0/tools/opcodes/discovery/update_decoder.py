#!/usr/bin/env python3
"""Update the SIME Finch decoder to use verified opcodes from reference implementations."""

import shutil
from pathlib import Path


def update_decoder() -> None:
    """Update decoder to use verified opcodes."""
    # Backup current decoder
    decoder_path = Path("extract/pbd_core/decoder.py")
    if decoder_path.exists():
        backup_path = decoder_path.with_suffix(".py.backup")
        shutil.copy(decoder_path, backup_path)

    # Update opcode import in decoder
    if decoder_path.exists():
        with open(decoder_path) as f:
            content = f.read()

        # Replace opcode import
        old_import = "from .opcodes import OPCODES"
        new_import = "from src.decompile.opcodes_unified import OPCODES, get_opcode_name, get_opcode_length"

        if old_import in content:
            content = content.replace(old_import, new_import)

            # Update opcode access patterns
            content = content.replace(
                "OPCODES.get(opcode, {'name': f'UNKNOWN_{opcode:02X}', 'length': 1})",
                "OPCODES.get(opcode, type('', (), {'name': get_opcode_name(opcode), 'length': get_opcode_length(opcode)})())",
            )

            with open(decoder_path, "w") as f:
                f.write(content)
        else:
            pass

    # Create a test script
    test_path = Path("test_verified_decoder.py")
    with open(test_path, "w") as f:
        f.write('''#!/usr/bin/env python3
"""Test decoder with verified opcodes."""

from pathlib import Path
from src.decompile.pcode.decoder import decode_pcode
from src.extract.pbd_io.reader import PBDReader

def test_decoder() -> None:





    """Test the decoder with a sample PBD file."""
    # Find a test PBD file
    test_files = list(Path("data/input/pbd_files").glob("*.pbd"))
    if not test_files:
        print("No PBD files found in data/input/pbd_files/")
        return

    test_file = test_files[0]
    print(f"Testing with: {test_file}")

    # Extract and decode
    reader = PBDReader(str(test_file))
    objects = reader.read_objects()

    if objects:
        obj = objects[0]
        if hasattr(obj, 'pcode') and obj.pcode:
            print(f"\\nDecoding {obj.name}...")
            instructions = decode_pcode(obj.pcode)

            print(f"Decoded {len(instructions)} instructions:")
            for i, inst in enumerate(instructions[:
                10]):
                print(f"  {i:04d}: {inst}")

            if len(instructions) > 10:
                print(f"  ... and {len(instructions) - 10} more")

if __name__ == "__main__":
    test_decoder()
''')


if __name__ == "__main__":
    update_decoder()
