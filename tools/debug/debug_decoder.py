#!/usr/bin/env python3
"""Debug the decoder to understand why upd*te returns UPDATE."""

import sys
sys.path.insert(0, '.')

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

from extract.pbd.utils.powerbuilder_decoder import decode_powerbuilder_text, _fix_corrupted_word

# Test specific case
test = "upd*te"
print(f"Testing: {test}")
print("-" * 30)

# Call the fix function directly
result = _fix_corrupted_word("upd", "te")
print(f"Result: {result}")

# Also test full decode
data = test.encode('latin1')
full_result = decode_powerbuilder_text(data)
print(f"Full decode result: {full_result}")