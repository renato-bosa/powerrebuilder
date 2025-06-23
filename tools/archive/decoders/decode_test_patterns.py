#!/usr/bin/env python3
"""Analyze the test corruption patterns to determine the PowerBuilder encoding rules."""

# From test_corruption_patterns.txt, we have these examples:
patterns = [
    ("a*dress", "address"),      # * → d (but shows as *J in actual data)
    ("LOG*C", "LOGIC"),          # * → I (uppercase I)
    ("trea*ment", "treatment"),  # * → t
    ("COL*LMN", "COLUMN"),       # * → U (uppercase U)
    ("clinic_a*ddress", "clinic_address"),  # * → d
    ("person_address.* ddress_id", "person_address.address_id"),  # * → a
]

# From the actual corrupted data patterns mentioned:
actual_patterns = [
    (".*Jate", ".date"),         # *J → d
    ("COL*LMN", "COLUMN"),       # *L → U (uppercase!)
    ("a*Jress", "address"),      # *J → d
]

print("Analyzing PowerBuilder Encoding Patterns")
print("=" * 50)

print("\nFrom test file patterns:")
for corrupted, fixed in patterns:
    # Find what character is missing
    for i in range(len(corrupted)):
        if corrupted[i] == '*':
            if i < len(fixed):
                missing_char = fixed[i]
                # What comes after * in corrupted?
                next_char = corrupted[i+1] if i+1 < len(corrupted) else '?'
                print(f"'{corrupted}' → '{fixed}': *{next_char} represents '{missing_char}'")
            break

print("\nFrom actual data patterns:")
for corrupted, fixed in actual_patterns:
    # Find what character is missing
    for i in range(len(corrupted)):
        if corrupted[i] == '*':
            if i < len(fixed):
                missing_char = fixed[i]
                # What comes after * in corrupted?
                next_char = corrupted[i+1] if i+1 < len(corrupted) else '?'
                print(f"'{corrupted}' → '{fixed}': *{next_char} represents '{missing_char}'")
            break

# Now let's build the mapping
print("\n\nDerived Mapping Table:")
print("-" * 30)

# From the patterns, we can see:
mapping = {
    'J': 'd',  # *J → d (from .*Jate → .date, a*Jress → address)
    'L': 'U',  # *L → U (from COL*LMN → COLUMN) - NOTE: uppercase!
    'C': 'I',  # *C → I (from LOG*C → LOGIC) - NOTE: uppercase!
    'd': 'd',  # *d → d (from a*ddress → address)
    ' ': 'a',  # '* ' → a (from "person_address.* ddress_id")
    # We need the actual byte after * for "trea*ment" to know what maps to 't'
}

for key, value in sorted(mapping.items()):
    print(f"*{key} → '{value}'")

print("\n\nObservations:")
print("1. The encoding is NOT a simple ROT cipher")
print("2. Some mappings produce uppercase letters (L→U, C→I)")
print("3. Some mappings produce lowercase letters (J→d)")
print("4. The byte after * determines what character it represents")
print("5. This is likely a custom lookup table, not a mathematical transformation")

print("\n\nTo complete the mapping, we need to:")
print("1. Analyze actual PBD files with known content")
print("2. Look at the hex values of the bytes after 0x2A")
print("3. Build a complete lookup table based on observations")

# Let's also check ASCII values to see if there's a pattern
print("\n\nASCII Analysis:")
for char, replacement in mapping.items():
    if char != ' ':
        char_val = ord(char)
        repl_val = ord(replacement)
        diff = repl_val - char_val
        print(f"'{char}' ({char_val}) → '{replacement}' ({repl_val}), difference: {diff}")