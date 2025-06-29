#!/usr/bin/env python3
"""Fix escaped quotes in DataWindow and SQL grammar files."""

import re
from pathlib import Path

def fix_datawindow_grammar():
    """Add proper handling for escaped quotes in DataWindow grammar."""
    grammar_file = Path("parse/grammar/datawindow.lark")
    content = grammar_file.read_text()
    
    # Check if ESCAPED_STRING is already defined
    if 'ESCAPED_STRING:' not in content:
        # Add ESCAPED_STRING definition before the %import section
        new_content = content.replace(
            '%import common.ESCAPED_STRING',
            '''// Define ESCAPED_STRING to handle PowerBuilder escaping
ESCAPED_STRING: /"([^"\\\\]|\\\\.)*"/
              | /'([^'\\\\]|\\\\.)*'/
              | /~"([^"]|"")*~"/  // PowerBuilder style escaped quotes

// For backward compatibility
%import common.ESCAPED_STRING -> _OLD_ESCAPED_STRING'''
        )
        
        # Also update string_value to handle tilde-escaped strings
        new_content = new_content.replace(
            'string_value: quoted_string | IDENTIFIER',
            '''string_value: quoted_string | IDENTIFIER | TILDE_STRING

// PowerBuilder tilde-escaped strings
TILDE_STRING: /~"[^"]*"/'''
        )
        
        grammar_file.write_text(new_content)
        print(f"Fixed DataWindow grammar: {grammar_file}")
    else:
        print(f"DataWindow grammar already has ESCAPED_STRING defined")

def fix_sql_grammar():
    """Add proper handling for escaped quotes in SQL grammar."""
    grammar_file = Path("parse/grammar/sql.lark")
    content = grammar_file.read_text()
    
    # Check if we need to add ESCAPED_STRING definition
    if '%import' in content and 'ESCAPED_STRING' not in content:
        # Find where to add the definition (before %import or at the end)
        import_pos = content.find('%import')
        if import_pos > 0:
            # Add before first import
            new_content = (
                content[:import_pos] +
                '''// Define ESCAPED_STRING to handle PowerBuilder escaping
ESCAPED_STRING: /"([^"\\\\]|\\\\.)*"/
              | /'([^'\\\\]|\\\\.)*'/
              | /~"([^"]|"")*~"/  // PowerBuilder style escaped quotes

''' +
                content[import_pos:]
            )
        else:
            # Add at the end
            new_content = content + '''

// Define ESCAPED_STRING to handle PowerBuilder escaping
ESCAPED_STRING: /"([^"\\\\]|\\\\.)*"/
              | /'([^'\\\\]|\\\\.)*'/
              | /~"([^"]|"")*~"/  // PowerBuilder style escaped quotes
'''
        
        grammar_file.write_text(new_content)
        print(f"Fixed SQL grammar: {grammar_file}")
    else:
        print(f"SQL grammar already handles ESCAPED_STRING")

def fix_common_grammar():
    """Update common grammar to export ESCAPED_STRING if needed."""
    grammar_file = Path("parse/grammar/common_grammar.lark")
    content = grammar_file.read_text()
    
    # Check if ESCAPED_STRING is defined
    if 'ESCAPED_STRING' not in content:
        # Add it after STRING definition
        new_content = content.replace(
            'STRING   : /"[^"]*"/',
            '''STRING   : /"[^"]*"/
ESCAPED_STRING: /"([^"\\\\]|\\\\.)*"/
              | /'([^'\\\\]|\\\\.)*'/'''
        )
        
        grammar_file.write_text(new_content)
        print(f"Fixed common grammar: {grammar_file}")
    else:
        print(f"Common grammar already has ESCAPED_STRING")

if __name__ == "__main__":
    print("Fixing escaped quotes in grammar files...")
    fix_datawindow_grammar()
    fix_sql_grammar()
    fix_common_grammar()
    print("Done!")