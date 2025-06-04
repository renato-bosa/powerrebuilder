"""PowerBuilder 10.5 opcode table (Unicode version).

Generated from reference implementations.
This version includes Unicode support.
"""

# Import base opcodes from PB 8.0
from .pb80_0 import OPCODES as BASE_OPCODES

# PowerBuilder 10.5 uses the same opcodes as 8.0
# but with Unicode string handling
OPCODES = BASE_OPCODES.copy()

# Alias for the opcode manager
OPCODE_MAP_PB10_5 = OPCODES
