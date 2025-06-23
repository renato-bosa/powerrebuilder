#!/usr/bin/env python3
"""
PowerBuilder Binary Decoder v4 - SQL Parameter Placeholder Fix.

This version specifically addresses the issue where SQL parameter placeholders
are being corrupted to the Ā character (U+0100, UTF-8: 0xC4 0x80).

In PowerBuilder SQL, parameter placeholders can be:
- ? (question mark) for positional parameters
- :name (colon followed by name) for named parameters

The corruption pattern shows Ā appearing where these placeholders should be,
suggesting that the binary encoding for parameter markers is being misinterpreted.
"""

import json
import re
import struct
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
import logging

from extract.pbd.utils.powerbuilder_decoder_v3 import PowerBuilderDecoderV3

logger = logging.getLogger(__name__)


class PowerBuilderDecoderV4(PowerBuilderDecoderV3):
    """PowerBuilder binary decoder with SQL parameter placeholder fixes."""
    
    def __init__(self):
        """Initialize the decoder with parameter placeholder handling."""
        super().__init__()
        
        # Add specific patterns for SQL parameter placeholder corruption
        self.parameter_patterns = [
            # The Ā character appearing in SQL WHERE clauses
            (re.compile(r'\bWHERE\s*\([^)]*Ā[^)]*\)', re.IGNORECASE), self._fix_where_clause_parameters),
            (re.compile(r'=\s*Ā\s*(?:\)|,|AND|OR)', re.IGNORECASE), self._fix_equals_parameter),
            (re.compile(r'VALUES\s*\([^)]*Ā[^)]*\)', re.IGNORECASE), self._fix_values_parameters),
            # Handle UNION queries with parameters - use a function to preserve the following text
            (re.compile(r'Ā(\s*(?:\)|,|\s+AND|\s+OR|\s+UNION))', re.IGNORECASE), r'?\1'),
        ]
    
    def decode(self, data: bytes, encoding: str = 'latin1') -> str:
        """
        Main decoding method with SQL parameter placeholder fixes.
        
        Args:
            data: Binary data to decode
            encoding: Initial encoding to try
            
        Returns:
            Decoded and fixed string
        """
        # First, use parent class decoding
        decoded = super().decode(data, encoding)
        
        # Then apply SQL parameter placeholder fixes
        decoded = self._fix_sql_parameters(decoded)
        
        return decoded
    
    def _fix_sql_parameters(self, text: str) -> str:
        """Fix SQL parameter placeholders corrupted to Ā."""
        # Quick check if we need to process
        if 'Ā' not in text:
            return text
        
        # Check if this looks like SQL
        if not self._looks_like_sql(text):
            return text
        
        # Apply parameter-specific fixes
        for pattern, replacement in self.parameter_patterns:
            if callable(replacement):
                text = pattern.sub(replacement, text)
            else:
                text = pattern.sub(replacement, text)
        
        # Generic replacement for remaining Ā in SQL context
        if self._is_sql_context(text):
            # Replace remaining Ā with ? (most common parameter placeholder)
            text = text.replace('Ā', '?')
        
        return text
    
    def _looks_like_sql(self, text: str) -> bool:
        """Check if the text appears to be SQL."""
        sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
            'VALUES', 'SET', 'JOIN', 'UNION', 'ORDER BY', 'GROUP BY',
            'PBSELECT', 'bill_payment', 'quotemp'  # Common in the examples
        ]
        
        text_upper = text.upper()
        keyword_count = sum(1 for keyword in sql_keywords if keyword in text_upper)
        
        return keyword_count >= 2
    
    def _is_sql_context(self, text: str) -> bool:
        """Determine if we're in SQL context (more strict than _looks_like_sql)."""
        # Must have SELECT or INSERT or UPDATE or DELETE
        text_upper = text.upper()
        main_sql_commands = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'PBSELECT']
        
        has_main_command = any(cmd in text_upper for cmd in main_sql_commands)
        
        # And must have WHERE or VALUES or FROM
        sql_clauses = ['WHERE', 'FROM', 'VALUES', 'SET']
        has_clause = any(clause in text_upper for clause in sql_clauses)
        
        return has_main_command and has_clause
    
    def _fix_where_clause_parameters(self, match) -> str:
        """Fix parameters in WHERE clauses."""
        where_clause = match.group(0)
        # Replace Ā with ? in WHERE clauses
        fixed = where_clause.replace('Ā', '?')
        return fixed
    
    def _fix_equals_parameter(self, match) -> str:
        """Fix parameters after equals signs."""
        equals_expr = match.group(0)
        # Replace Ā with ? after equals
        fixed = equals_expr.replace('Ā', '?')
        return fixed
    
    def _fix_values_parameters(self, match) -> str:
        """Fix parameters in VALUES clauses."""
        values_clause = match.group(0)
        # Replace Ā with ? in VALUES
        fixed = values_clause.replace('Ā', '?')
        return fixed
    
    def analyze_parameter_corruption(self, text: str) -> Dict[str, Any]:
        """Analyze parameter placeholder corruption patterns."""
        if 'Ā' not in text:
            return {'has_corruption': False}
        
        analysis = {
            'has_corruption': True,
            'total_corrupted_params': text.count('Ā'),
            'contexts': []
        }
        
        # Find contexts where Ā appears
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'Ā' in line:
                # Extract surrounding context
                start = max(0, line.find('Ā') - 20)
                end = min(len(line), line.find('Ā') + 20)
                context = line[start:end]
                
                analysis['contexts'].append({
                    'line': i + 1,
                    'context': context,
                    'full_line': line.strip()
                })
        
        return analysis


# Global decoder instance for efficiency
_global_decoder_v4 = None


def get_decoder() -> PowerBuilderDecoderV4:
    """Get or create global decoder instance."""
    global _global_decoder_v4
    if _global_decoder_v4 is None:
        _global_decoder_v4 = PowerBuilderDecoderV4()
    return _global_decoder_v4


def decode_powerbuilder_text(data: bytes, encoding: str = 'latin1') -> str:
    """
    Decode PowerBuilder binary text with SQL parameter fixes.
    
    Args:
        data: Binary data to decode
        encoding: Initial encoding to try
        
    Returns:
        Decoded and fixed string
    """
    decoder = get_decoder()
    return decoder.decode(data, encoding)


def fix_sql_file(file_path: Path) -> None:
    """
    Fix SQL parameter placeholders in a file.
    
    Args:
        file_path: Path to SQL file with corrupted parameters
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it needs fixing
        if 'Ā' not in content:
            logger.info(f"No parameter corruption found in {file_path}")
            return
        
        # Create decoder and analyze
        decoder = get_decoder()
        analysis = decoder.analyze_parameter_corruption(content)
        
        logger.info(f"Found {analysis['total_corrupted_params']} corrupted parameters in {file_path}")
        
        # Fix the content
        fixed_content = decoder._fix_sql_parameters(content)
        
        # Backup original file
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        file_path.rename(backup_path)
        
        # Write fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        logger.info(f"Fixed SQL parameters in {file_path}, backup saved as {backup_path}")
        
    except Exception as e:
        logger.error(f"Error fixing SQL file {file_path}: {e}")


def main():
    """Test the decoder with examples."""
    test_cases = [
        # Example from the extracted SQL
        "SELECT bill_payment.bill_id FROM bill_payment WHERE ( bill_payment.bill_id = Ā ) AND ( bill_payment.payment_type = Ā )",
        "INSERT INTO test_table VALUES (Ā, Ā, Ā)",
        "UPDATE person SET name = Ā WHERE id = Ā",
    ]
    
    decoder = get_decoder()
    
    for test in test_cases:
        print(f"\nOriginal: {test}")
        fixed = decoder._fix_sql_parameters(test)
        print(f"Fixed:    {fixed}")
        
        analysis = decoder.analyze_parameter_corruption(test)
        print(f"Analysis: {analysis}")


if __name__ == "__main__":
    main()