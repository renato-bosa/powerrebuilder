#!/usr/bin/env python3
"""Learn vocabulary from successfully extracted files to enhance the PowerBuilder decoder."""

import re
import glob
from pathlib import Path
from collections import Counter
import json

def extract_vocabulary_from_file(file_path):
    """Extract potential vocabulary words from a file."""
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        
        # Extract various types of identifiers
        words = set()
        
        # SQL column names (e.g., COLUMN(NAME="person.person_id"))
        column_names = re.findall(r'COLUMN\s*\(\s*NAME\s*=\s*"([^"]+)"', content, re.IGNORECASE)
        for col in column_names:
            # Split on dots to get table and column names
            parts = col.split('.')
            words.update(parts)
        
        # Table names (e.g., TABLE(NAME="person"))
        table_names = re.findall(r'TABLE\s*\(\s*NAME\s*=\s*"([^"]+)"', content, re.IGNORECASE)
        words.update(table_names)
        
        # General identifiers (alphanumeric + underscore)
        all_identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        
        # Filter to reasonable length and not all caps constants
        for word in all_identifiers:
            if 2 < len(word) < 50 and not (word.isupper() and '_' in word):
                words.add(word.lower())
        
        # Extract from WHERE clauses
        where_fields = re.findall(r'WHERE\s*\([^)]*?(\w+)\s*=', content, re.IGNORECASE)
        words.update(w.lower() for w in where_fields)
        
        # Extract from JOIN clauses
        join_fields = re.findall(r'JOIN\s*\([^)]*?"([^"]+)"', content, re.IGNORECASE)
        for field in join_fields:
            parts = field.split('.')
            words.update(p.lower() for p in parts)
        
        return words
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return set()

def main():
    """Learn vocabulary from all extracted files."""
    print("Learning vocabulary from extracted files...")
    print("=" * 50)
    
    # Find all extracted files
    patterns = ['data/output/current/extracted/**/*.srd', 'data/output/current/extracted/**/*.dwo']
    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern, recursive=True))
    
    print(f"Found {len(all_files)} files to analyze")
    
    # Collect vocabulary
    word_frequency = Counter()
    
    for file_path in all_files:
        words = extract_vocabulary_from_file(file_path)
        word_frequency.update(words)
    
    # Filter to words that appear at least twice
    common_words = {word for word, count in word_frequency.items() if count >= 2}
    
    print(f"\nExtracted {len(common_words)} unique words appearing 2+ times")
    
    # Load existing dictionary
    import sys
    sys.path.insert(0, '.')
    from extract.pbd.utils.powerbuilder_decoder import PB_DOMAIN_DICTIONARY
    
    # Find new words not in dictionary
    new_words = common_words - {w.lower() for w in PB_DOMAIN_DICTIONARY}
    
    print(f"Found {len(new_words)} new words not in current dictionary")
    
    # Show most common new words
    if new_words:
        print("\nMost common new words:")
        new_word_freq = {w: word_frequency[w] for w in new_words}
        sorted_new = sorted(new_word_freq.items(), key=lambda x: x[1], reverse=True)
        
        for word, freq in sorted_new[:30]:
            print(f"  {word}: {freq} occurrences")
    
    # Save new words for review
    output_data = {
        'new_words': sorted(list(new_words)),
        'word_frequency': {w: word_frequency[w] for w in sorted(new_words)},
        'total_files_analyzed': len(all_files),
        'total_unique_words': len(common_words)
    }
    
    with open('learned_vocabulary.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nSaved {len(new_words)} new words to learned_vocabulary.json")
    
    # Generate Python code to add to dictionary
    if new_words:
        print("\nPython code to add new words:")
        print("-" * 30)
        print("# New words learned from extraction")
        print("new_words = {")
        for i, word in enumerate(sorted(new_words)[:50]):  # First 50
            print(f"    '{word}',")
        if len(new_words) > 50:
            print(f"    # ... and {len(new_words) - 50} more")
        print("}")
        print("\n# Add to dictionary:")
        print("from extract.pbd.utils.powerbuilder_decoder import add_to_dictionary")
        print("add_to_dictionary(list(new_words))")

if __name__ == "__main__":
    main()