"""PowerBuilder-specific text decoder for handling position-based binary corruption.

This module handles PowerBuilder's binary format where certain byte positions
get corrupted and appear as asterisks (0x2A) when the binary data is misread.

Key insight: The corruption is POSITION-BASED, not character-mapping based.
When PowerBuilder's binary format is read incorrectly, certain byte positions
show up as asterisks, and we need to use a domain dictionary to fix them.

Examples of corruption:
  - "address" -> "a*dress" (position 2)
  - "date" -> "*ate" (position 1) 
  - "COLUMN" -> "COL*MN" (position 4)
  - "treatment" -> "trea*ment" (position 5)
"""

import logging
import re
import json
from typing import Dict, Set, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# PowerBuilder control byte that appears as asterisk when corrupted
PB_CONTROL_BYTE = 0x2A  # '*' character

# Domain dictionary for PowerBuilder/SQL terms
PB_DOMAIN_DICTIONARY: Set[str] = {
    # SQL Keywords
    'select', 'from', 'where', 'table', 'column', 'insert', 'update', 
    'delete', 'join', 'inner', 'outer', 'left', 'right', 'order', 'group',
    'having', 'between', 'exists', 'distinct', 'logic', 'and', 'or',
    'create', 'alter', 'drop', 'index', 'primary', 'foreign', 'key',
    'version', 'compute', 'retrieval', 'arguments', 'sort', 'filter',
    
    # PowerBuilder terms
    'datawindow', 'dataobject', 'retrieve', 'accepttext', 'rowcount',
    'insertrow', 'deleterow', 'getitem', 'setitem', 'describe', 'modify',
    'powerbuilder', 'transaction', 'sqlca', 'sqlcode', 'sqlerrtext',
    'pbselect', 'userobject', 'window', 'menu', 'function', 'event',
    'structure', 'global', 'instance', 'shared', 'private', 'public',
    'protected', 'systemfunctions', 'systemerror', 'open', 'close',
    
    # Common business terms  
    'address', 'customer', 'employee', 'operator', 'treatment', 'billing',
    'payment', 'invoice', 'product', 'clinic', 'person', 'patient',
    'amount', 'quantity', 'description', 'status', 'date', 'time',
    'created', 'updated', 'modified', 'deleted', 'active', 'valid',
    
    # Medical/Dental specific terms
    'dentist', 'doctor', 'appointment', 'medicare', 'insurer', 'insurance',
    'reminder', 'quotepayment', 'treatmentplan', 'treatmentbill', 'payee',
    'supplier', 'referral', 'charts', 'consultation', 'consult', 'diagnosis',
    'procedure', 'medication', 'prescription', 'health', 'medical', 'dental',
    'practitioner', 'provider', 'claim', 'benefit', 'rebate', 'receipt',
    
    # Financial/Accounting terms
    'deposit', 'credit', 'debit', 'balance', 'transaction', 'account',
    'ledger', 'journal', 'voucher', 'cheque', 'bank', 'accounting',
    'gst', 'tax', 'discount', 'refund', 'outstanding', 'overdue',
    'statement', 'reconciliation', 'audit', 'budget', 'expense', 'revenue',
    
    # Common column name components
    'id', 'name', 'code', 'type', 'flag', 'number', 'count', 'total',
    'first', 'last', 'middle', 'phone', 'email', 'street', 'city',
    'state', 'zip', 'country', 'comment', 'note', 'memo', 'text',
    'surname', 'firstname', 'lastname', 'middlename', 'title', 'gender',
    'birthdate', 'age', 'contact', 'mobile', 'fax', 'website', 'abn',
    'postcode', 'suburb', 'locality', 'region', 'addresstype', 'addressid',
    'datetime', 'timestamp', 'expiry', 'expdate', 'startdate', 'enddate',
    'filename', 'filepath', 'attachment', 'document', 'image', 'photo',
    'tag', 'category', 'group', 'level', 'priority', 'sequence', 'order'
}

# Add uppercase variants to dictionary
PB_DOMAIN_DICTIONARY.update({word.upper() for word in list(PB_DOMAIN_DICTIONARY)})

# Cache for successful fixes
_corruption_fix_cache: Dict[str, str] = {}


def _apply_pattern_specific_fixes(text: str) -> str:
    """Apply pattern-specific fixes for known edge cases.
    
    This handles specific corruption patterns that follow predictable rules
    rather than requiring dictionary lookup.
    
    Args:
        text: Text with potential corruption patterns
        
    Returns:
        Text with pattern-specific fixes applied
    """
    # Fix "NA *E=" pattern (should be "NAME=")
    text = re.sub(r'\bNA\s*\*\s*E=', 'NAME=', text)
    
    # Fix "COLUMN(NA *E=" pattern
    text = re.sub(r'COLUMN\s*\(\s*NA\s*\*\s*E=', 'COLUMN(NAME=', text)
    
    # Fix "WHERE(*EXP" pattern (should be "WHERE(EXP")
    text = re.sub(r'WHERE\s*\(\s*\*\s*EXP', 'WHERE(EXP', text)
    
    # Fix other parenthesis-asterisk patterns
    text = re.sub(r'\(\s*\*\s*([A-Z])', r'(\1', text)  # (*WORD -> (WORD
    
    # Fix common SQL keyword patterns
    patterns = [
        (r'\bCOL\s*\*\s*MN\b', 'COLUMN'),
        (r'\bCOL\*LMN\b', 'COLUMN'),
        (r'\bLOG\s*\*\s*C\b', 'LOGIC'),
        (r'\bTAB\s*\*\s*E\b', 'TABLE'),
        (r'\bSEL\s*\*\s*CT\b', 'SELECT'),
        (r'\bWH\s*\*\s*RE\b', 'WHERE'),
        (r'\bFR\s*\*\s*M\b', 'FROM'),
        (r'\bUPD\s*\*\s*TE\b', 'UPDATE'),
        (r'\bINS\s*\*\s*RT\b', 'INSERT'),
        (r'\bDEL\s*\*\s*TE\b', 'DELETE'),
        (r'\bCRE\s*\*\s*TE\b', 'CREATE'),
        (r'\bALT\s*\*\s*R\b', 'ALTER'),
        (r'\bDR\s*\*\s*P\b', 'DROP'),
        (r'\bPRIM\s*\*\s*RY\b', 'PRIMARY'),
        (r'\bFORE\s*\*\s*GN\b', 'FOREIGN'),
        (r'\bDAT\s*\*\s*BASE\b', 'DATABASE'),
        (r'\bTRANS\s*\*\s*CTION\b', 'TRANSACTION'),
    ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Fix patterns where asterisk appears at specific positions in common words
    # These are based on observed patterns in the data
    specific_fixes = [
        # Address-specific patterns (must come first to handle all variations)
        # These handle cases where letters are missing without asterisks
        (r'\baddess_id\b', 'address_id'),  # Missing 'r' in address_id
        (r'\.addess_id\b', '.address_id'),  # table.addess_id -> table.address_id
        (r'\baddess\b', 'address'),  # Missing 'r'
        (r'\.addess\b', '.address'),  # .addess -> .address
        (r'"addess', '"address'),  # "addess -> "address
        (r'"\s+ddress\.', '"address.'),  # " ddress. -> "address.
        (r'"\s+ddress\b', '"address'),  # " ddress -> "address
        (r'\s+ddress\.', ' address.'),  # Missing 'a' at start with dot
        (r'"\s*ddress\.', '"address.'),  # "ddress. -> "address. (no space)
        (r'\s+ddress\b', ' address'),  # Missing 'a' at start
        (r'\btrea\*ment\b', 'treatment'),
        (r'\boper\*tor\b', 'operator'),
        (r'\bupd\*te\b', 'update'),
        (r'\bbill\*ng\b', 'billing'),
        (r'\bclin\*c\b', 'clinic'),
        (r'\bpati\*nt\b', 'patient'),
        (r'\bpers\*n\b', 'person'),
        (r'\bamou\*t\b', 'amount'),
        (r'\bpaym\*nt\b', 'payment'),
        (r'\binvo\*ce\b', 'invoice'),
        (r'\bsuppl\*er\b', 'supplier'),
        (r'\brefe\*ral\b', 'referral'),
        (r'\bappo\*ntment\b', 'appointment'),
        (r'\binsur\*r\b', 'insurer'),
        (r'\bmedic\*re\b', 'medicare'),
        (r'\bdenti\*t\b', 'dentist'),
        (r'\bdoct\*r\b', 'doctor'),
    ]
    
    for pattern, replacement in specific_fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Additional fixes for patterns inside quoted strings
    # Fix "address.addess_id" -> "address.address_id"
    text = re.sub(r'(address\.)addess(_id)', r'\1address\2', text, flags=re.IGNORECASE)
    
    # Fix quoted patterns with missing first letter: " ddress." -> "address."
    text = re.sub(r'(["\']\s*)ddress\.', r'\1address.', text, flags=re.IGNORECASE)
    
    # Fix any remaining "addess" patterns
    text = re.sub(r'addess', 'address', text, flags=re.IGNORECASE)
    
    # Fix unclosed quotes followed by asterisk (e.g., "person.doctor_name *)
    text = re.sub(r'("\w+\.\w+)\s*\*\s*\)', r'\1")', text)
    
    # Fix missing closing parenthesis after quoted string with asterisk
    text = re.sub(r'("\w+\.\w+_\w+)"\s*\*\s*COLUMN', r'\1") COLUMN', text)
    
    return text


def _fix_corrupted_word(before: str, after: str) -> Optional[str]:
    """
    Fix a corrupted word using context-aware pattern matching.
    
    This function uses both sides of the asterisk to determine the most
    likely word from the dictionary.
    
    Args:
        before: Part of word before the asterisk
        after: Part of word after the asterisk
        
    Returns:
        Fixed word if found in dictionary, None otherwise
    """
    corrupted = f"{before}*{after}"
    
    # Check cache first
    if corrupted in _corruption_fix_cache:
        return _corruption_fix_cache[corrupted]
    
    best_match = None
    best_score = 0
    
    # Create a pattern that matches words starting with 'before' and ending with 'after'
    # This is much smarter than trying every character
    pattern_lower = f"{before.lower()}.*{after.lower()}"
    pattern_length = len(before) + 1 + len(after)  # Expected length with one missing char
    
    # Handle edge cases
    if not before and after:
        # Pattern like "*dress"
        pattern_length = 1 + len(after)
    elif before and not after:
        # Pattern like "addr*"
        pattern_length = len(before) + 1
    else:
        # Normal case
        pattern_length = len(before) + 1 + len(after)
    
    # Search dictionary for matches
    for word in PB_DOMAIN_DICTIONARY:
        word_lower = word.lower()
        
        # Check if word matches the pattern
        matches = False
        if before and after:
            matches = (word_lower.startswith(before.lower()) and 
                      word_lower.endswith(after.lower()) and
                      len(before) + len(after) < len(word_lower))
        elif before and not after:
            matches = word_lower.startswith(before.lower()) and len(word_lower) > len(before)
        elif not before and after:
            matches = word_lower.endswith(after.lower()) and len(word_lower) > len(after)
            
        if matches:
            
            # Calculate how well it matches
            score = 0
            
            # Exact length match (only one character missing) gets highest score
            if len(word_lower) == pattern_length:
                score += 100
            else:
                # Penalize for length difference
                score += 50 - abs(len(word_lower) - pattern_length) * 10
            
            # Case match bonus - prefer exact case matches
            if before and word.startswith(before):
                score += 30  # Exact case match on prefix
            elif before and word.lower().startswith(before.lower()):
                score += 10  # Case-insensitive match
                
            if after and word.endswith(after):
                score += 30  # Exact case match on suffix  
            elif after and word.lower().endswith(after.lower()):
                score += 10  # Case-insensitive match
            
            # Common word bonus
            common_words = {'address', 'column', 'table', 'update', 'create', 'select', 
                          'treatment', 'billing', 'person', 'clinic', 'operator'}
            if word_lower in common_words:
                score += 30
            
            # Check if only one character is different in the expected position
            if len(word) == pattern_length:
                # This is likely our match - verify it's only one char different
                expected_prefix_len = len(before)
                if (word[:expected_prefix_len].lower() == before.lower() and
                    word[expected_prefix_len + 1:].lower() == after.lower()):
                    score += 50  # Strong match!
            
            if score > best_score:
                best_score = score
                best_match = word
                
                # Preserve original case pattern if possible
                # Check if the original pattern is all lowercase
                all_lower = (before.islower() if before else True) and (after.islower() if after else True)
                # Check if the original pattern is all uppercase
                all_upper = (before.isupper() if before else True) and (after.isupper() if after else True)
                
                if all_lower and word.isupper():
                    best_match = word.lower()
                elif all_upper and word.islower():
                    best_match = word.upper()
                # Otherwise keep the dictionary case
    
    # If no match found, try single character replacement
    if not best_match and len(before) + len(after) + 1 < 30:  # Reasonable word length
        for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_':
            candidate = f"{before}{char}{after}"
            if candidate.lower() in PB_DOMAIN_DICTIONARY:
                best_match = candidate
                break
    
    if best_match:
        _corruption_fix_cache[corrupted] = best_match
        logger.debug(f"Fixed '{corrupted}' -> '{best_match}' (score: {best_score})")
    
    return best_match


def decode_powerbuilder_text(data: bytes, encoding: str = "latin1") -> str:
    """Decode PowerBuilder text with position-based corruption fixing.
    
    This function handles PowerBuilder's binary format where certain byte
    positions appear as asterisks (0x2A) when the data is misread.
    
    Args:
        data: The raw bytes to decode
        encoding: The base encoding to use (default: latin1)
        
    Returns:
        The decoded and fixed text string
    """
    if not data:
        return ""
    
    # First decode the bytes to text
    try:
        if encoding == "utf-16-le":
            text = data.decode("utf-16-le", errors='replace')
        else:
            text = data.decode(encoding, errors='replace')
    except Exception as e:
        logger.warning(f"Decode error with {encoding}: {e}, falling back to latin1")
        text = data.decode("latin1", errors='replace')
    
    # Apply pattern-specific fixes for known edge cases
    # This must run even if there are no asterisks, as some patterns don't have asterisks
    text = _apply_pattern_specific_fixes(text)
    
    # Check if text contains asterisk-based corruption patterns
    if '*' not in text:
        return text
    
    # Fix position-based corruption using domain dictionary
    def fix_corrupted_match(match):
        before = match.group(1)
        after = match.group(2)
        
        fixed = _fix_corrupted_word(before, after)
        if fixed:
            return fixed
        else:
            # No fix found, return original
            return match.group(0)
    
    # Apply fixes to all corrupted words
    fixed_text = re.sub(r'\b(\w*)\*(\w*)\b', fix_corrupted_match, text)
    
    # Count remaining corruptions
    remaining = len(re.findall(r'\b\w*\*\w*\b', fixed_text))
    if remaining > 0:
        logger.debug(f"PowerBuilder decoder: {remaining} corruptions could not be fixed")
    
    return fixed_text


def decode_with_fallback(data: bytes, is_unicode: bool) -> str:
    """Decode PowerBuilder data with appropriate encoding and fallback.
    
    Args:
        data: The raw bytes to decode
        is_unicode: Whether the file is in Unicode format
        
    Returns:
        The decoded text string
    """
    if is_unicode:
        return decode_powerbuilder_text(data, encoding="utf-16-le")
    else:
        return decode_powerbuilder_text(data, encoding="latin1")


def analyze_corruption_patterns(data: bytes) -> Dict[str, any]:
    """Analyze corruption patterns in PowerBuilder data.
    
    This helps understand the position-based corruption pattern.
    
    Args:
        data: The raw bytes to analyze
        
    Returns:
        Dictionary with analysis results
    """
    text = data.decode('latin1', errors='replace')
    
    corruption_positions = []
    corrupted_words = []
    
    # Find all corruption patterns
    for match in re.finditer(r'\b(\w*)\*(\w*)\b', text):
        before = match.group(1)
        after = match.group(2)
        position = len(before) + 1  # Position of asterisk in the word
        
        corruption_positions.append(position)
        corrupted_words.append({
            'word': f"{before}*{after}",
            'position': position,
            'byte_offset': match.start() + len(before),
            'fixed': _fix_corrupted_word(before, after)
        })
    
    # Analyze position frequency
    position_freq = {}
    for pos in corruption_positions:
        position_freq[pos] = position_freq.get(pos, 0) + 1
    
    return {
        'total_corruptions': len(corrupted_words),
        'position_frequency': position_freq,
        'examples': corrupted_words[:10],
        'asterisk_count': data.count(PB_CONTROL_BYTE)
    }


def add_to_dictionary(words: List[str]):
    """Add new words to the PowerBuilder domain dictionary.
    
    Args:
        words: List of words to add to the dictionary
    """
    global PB_DOMAIN_DICTIONARY
    
    for word in words:
        if word and len(word) > 2:
            PB_DOMAIN_DICTIONARY.add(word.lower())
            PB_DOMAIN_DICTIONARY.add(word.upper())
    
    logger.info(f"Added {len(words)} words to dictionary")


def learn_from_clean_file(file_path: str) -> int:
    """Learn new vocabulary from a clean PowerBuilder/SQL file.
    
    Args:
        file_path: Path to a clean file to learn from
        
    Returns:
        Number of new words added
    """
    new_words = set()
    
    try:
        with open(file_path, 'r', encoding='latin1') as f:
            content = f.read()
        
        # Extract all identifiers
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        
        # Extract from SQL contexts
        # Column names in SELECT
        columns = re.findall(r'SELECT\s+.*?(\w+)', content, re.IGNORECASE)
        # Table names
        tables = re.findall(r'FROM\s+(\w+)', content, re.IGNORECASE)
        tables += re.findall(r'JOIN\s+(\w+)', content, re.IGNORECASE)
        
        all_words = words + columns + tables
        
        for word in all_words:
            if len(word) > 2 and word.lower() not in PB_DOMAIN_DICTIONARY:
                new_words.add(word)
        
        # Add to dictionary
        add_to_dictionary(list(new_words))
        
    except Exception as e:
        logger.error(f"Error learning from file {file_path}: {e}")
    
    return len(new_words)


def save_dictionary(file_path: str):
    """Save the current dictionary to a JSON file.
    
    Args:
        file_path: Path to save the dictionary
    """
    data = {
        'words': sorted(list(PB_DOMAIN_DICTIONARY)),
        'version': '2.0',
        'type': 'powerbuilder_domain_dictionary',
        'count': len(PB_DOMAIN_DICTIONARY)
    }
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved dictionary with {len(PB_DOMAIN_DICTIONARY)} words to {file_path}")


def load_dictionary(file_path: str):
    """Load additional words from a JSON dictionary file.
    
    Args:
        file_path: Path to the dictionary file
    """
    global PB_DOMAIN_DICTIONARY
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        words = data.get('words', [])
        add_to_dictionary(words)
        
        logger.info(f"Loaded {len(words)} words from {file_path}")
        
    except Exception as e:
        logger.error(f"Error loading dictionary from {file_path}: {e}")