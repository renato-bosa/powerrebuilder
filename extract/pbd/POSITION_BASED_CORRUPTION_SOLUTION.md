# PowerBuilder Position-Based Corruption Solution

## Key Insight

The PowerBuilder PBD extraction corruption is **POSITION-BASED**, not a character substitution cipher.

### What's Actually Happening

1. **Binary Format Misalignment**: PowerBuilder uses a proprietary binary format with compression/encoding at specific byte positions
2. **Position-Based Encoding**: Certain byte positions in strings are encoded differently in the binary format
3. **Asterisk Manifestation**: When these positions are read incorrectly, they appear as asterisks (0x2A)

### Evidence

Looking at the corruption patterns:
- `address` → `a*dress` (asterisk at position 2)
- `date` → `*ate` (asterisk at position 1)
- `COLUMN` → `COL*MN` (asterisk at position 4)
- `treatment` → `trea*ment` (asterisk at position 5)

The asterisk position varies - it's not about which character gets replaced, but which **position** in the string is corrupted.

## The Solution

### Domain Dictionary Approach

Since we can't fully reverse-engineer PowerBuilder's binary format, we use a **domain-specific dictionary** to intelligently fix corruptions:

```python
# For each corrupted word like "a*dress"
# Try each possible character: "aadress", "abdress", "acdress", "address"...
# Check which one exists in our PowerBuilder/SQL domain dictionary
# "address" is found → fixed!
```

### Implementation

The updated `powerbuilder_decoder.py` now:

1. **Detects corruption patterns** (words with asterisks)
2. **Uses a domain dictionary** of PowerBuilder/SQL terms
3. **Intelligently fixes corruptions** by finding valid words
4. **Learns from clean files** to expand the dictionary
5. **Caches successful fixes** for performance

### Usage

```python
from extract.pbd.utils.powerbuilder_decoder import decode_powerbuilder_text

# Decode corrupted data
data = corrupted_text.encode('latin1')
fixed_text = decode_powerbuilder_text(data)

# Learn from clean files to improve accuracy
from extract.pbd.utils.powerbuilder_decoder import learn_from_clean_file
learn_from_clean_file('/path/to/clean/file.sql')

# Add custom domain terms
from extract.pbd.utils.powerbuilder_decoder import add_to_dictionary
add_to_dictionary(['mycustomtable', 'specialfield'])
```

## Advantages of This Approach

1. **No need to fully reverse-engineer** PowerBuilder's binary format
2. **High accuracy** for domain-specific terms
3. **Expandable** - can learn from your codebase
4. **Performance** - caches successful fixes
5. **Practical** - solves the problem without perfect knowledge

## Building Your Domain Dictionary

1. **Start with built-in terms** (SQL keywords, PowerBuilder functions)
2. **Scan your clean codebase** to extract identifiers
3. **Extract from database schema** (table/column names)
4. **Learn from successfully decoded files**
5. **Add project-specific terms** as needed

## Future Improvements

1. **Pattern Analysis**: Analyze which positions get corrupted most frequently
2. **Context-Aware Fixing**: Use surrounding SQL context for better guesses
3. **Confidence Scoring**: Rate fixes based on context and frequency
4. **Binary Format Research**: Continue investigating the actual encoding scheme

## Conclusion

By understanding that the corruption is position-based rather than character-based, we've developed a practical solution that:
- Fixes most corruptions accurately
- Doesn't require complete format reverse-engineering
- Can be customized for your specific domain
- Improves over time as it learns

The key was recognizing the true nature of the problem and applying a domain-specific solution rather than trying to decode an unknown cipher.