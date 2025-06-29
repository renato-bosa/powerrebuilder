#!/usr/bin/env python3
"""Add learned words to the PowerBuilder decoder dictionary."""

import json

# Load the learned vocabulary
with open('learned_vocabulary.json', 'r') as f:
    data = json.load(f)

new_words = data['new_words']

# Import and update the dictionary
import sys
sys.path.insert(0, '.')
from src.extract.utils.encoding import add_to_dictionary

# Add all learned words
add_to_dictionary(new_words)

print(f"Added {len(new_words)} new words to the PowerBuilder dictionary")

# Show some examples
print("\nSome of the added words:")
for word in sorted(new_words)[:20]:
    print(f"  - {word}")
if len(new_words) > 20:
    print(f"  ... and {len(new_words) - 20} more")