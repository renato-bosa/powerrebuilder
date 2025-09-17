#!/usr/bin/env python3
"""Final test of all corruption patterns including edge cases."""

import sys

sys.path.insert(0, ".")

from src.extract.utils.encoding import decode_powerbuilder_text

# Comprehensive test cases including all edge cases
test_cases = [
    # Original corruption patterns
    ("add*ess", "address"),
    ("COL*MN", "COLUMN"),
    ("trea*ment", "treatment"),
    ("NA *E=", "NAME="),
    # Edge case: parenthesis-asterisk
    ("WHERE(*EXP1", "WHERE(EXP1"),
    ("TABLE(*NAME", "TABLE(NAME"),
    # Edge case: missing letters without asterisk
    ("address.addess_id", "address.address_id"),
    (" ddress.create_datetime", " address.create_datetime"),
    ('"addess"', '"address"'),
    ('" ddress.field"', '"address.field"'),
    # Complex real-world patterns
    ('COLUMN(NA *E="person.medicare_number")', 'COLUMN(NAME="person.medicare_number")'),
    ('COLUMN(NAME="address.addess_id")', 'COLUMN(NAME="address.address_id")'),
    (
        'COLUMN(NAME=" ddress.create_datetime")',
        'COLUMN(NAME="address.create_datetime")',
    ),
    ('WHERE(*EXP1 ="tax_type.tax_type_id"', 'WHERE(EXP1 ="tax_type.tax_type_id"'),
    # Mixed patterns
    ("SELECT add*ess.addess_id FROM TAB*E", "SELECT address.address_id FROM TABLE"),
    (
        'UPDATE cli*ic SET address = "123 ddress street"',
        'UPDATE clinic SET address = "123 address street"',
    ),
]


success_count = 0
for corrupted, expected in test_cases:
    data = corrupted.encode("latin1")
    result = decode_powerbuilder_text(data)

    status = "✓" if result == expected else "✗"
    if result == expected:
        success_count += 1
    else:
        pass


if success_count == len(test_cases):
    pass
