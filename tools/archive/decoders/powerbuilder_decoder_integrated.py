"""
Integrated PowerBuilder decoder that handles position-based binary format corruption.

This decoder understands that PowerBuilder's binary format causes corruption at
specific byte positions when misread, not through character substitution.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional, Union
from collections import defaultdict

logger = logging.getLogger(__name__)

# PowerBuilder control byte that appears as asterisk
PB_CONTROL_BYTE = 0x2A  # '*' character


class PowerBuilderBinaryDecoder:
    """
    Handles PowerBuilder's binary format decoding with position-aware corruption fixing.
    
    The key insight: PowerBuilder uses position-based encoding where certain byte
    positions get encoded differently, appearing as asterisks when misread.
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        self.domain_dictionary = self._initialize_dictionary(dictionary_path)
        self.corruption_cache = {}  # Cache successful fixes
        
    def _initialize_dictionary(self, dict_path: Optional[str]) -> Set[str]:
        """Initialize with PowerBuilder/SQL domain dictionary."""
        base_dict = {
            # SQL Keywords (uppercase and lowercase variants)
            'select', 'from', 'where', 'table', 'column', 'insert', 'update', 
            'delete', 'join', 'inner', 'outer', 'left', 'right', 'order', 'group',
            'having', 'between', 'exists', 'distinct', 'logic', 'and', 'or',
            
            # PowerBuilder specific
            'datawindow', 'dataobject', 'retrieve', 'accepttext', 'rowcount',
            'insertrow', 'deleterow', 'getitem', 'setitem', 'describe', 'modify',
            
            # Common business domain terms  
            'address', 'customer', 'employee', 'operator', 'treatment', 'billing',
            'transaction', 'payment', 'invoice', 'product', 'clinic', 'person',
            'amount', 'quantity', 'description', 'status', 'date', 'time',
            
            # Common prefixes/suffixes
            'id', 'name', 'code', 'type', 'flag', 'created', 'updated', 'modified'
        }
        
        # Add uppercase variants
        base_dict.update({word.upper() for word in base_dict})
        
        # Load custom dictionary if provided
        if dict_path and Path(dict_path).exists():
            try:
                with open(dict_path, 'r') as f:
                    custom_dict = json.load(f)
                    base_dict.update(custom_dict.get('words', []))
            except Exception as e:
                logger.warning(f"Could not load custom dictionary: {e}")
        
        return base_dict
    
    def detect_corruption_pattern(self, data: bytes) -> bool:
        """
        Detect if data contains PowerBuilder position-based corruption.
        
        Looks for patterns like:
        - Asterisks within words (not at boundaries)
        - Known corruption signatures
        """
        # Quick check for control byte
        if PB_CONTROL_BYTE not in data:
            return False
        
        # Convert section to text for pattern matching
        try:
            sample = data[:1000].decode('latin-1', errors='ignore')
            
            # Look for corruption patterns
            patterns = [
                r'\b\w+\*\w+\b',  # Words with asterisk in middle
                r'COL\*[A-Z]MN',  # Specific COLUMN corruption
                r'LOG\*C',        # LOGIC corruption
                r'[a-z]\*[A-Z]',  # Lowercase-asterisk-uppercase pattern
            ]
            
            for pattern in patterns:
                if re.search(pattern, sample):
                    return True
                    
        except:
            pass
        
        return False
    
    def fix_corruption_with_dictionary(self, text: str) -> str:
        """
        Fix position-based corruption using domain dictionary.
        
        This is the main fixing algorithm that understands the corruption
        is positional, not character-mapping based.
        """
        if text in self.corruption_cache:
            return self.corruption_cache[text]
        
        def replace_corrupted_word(match):
            before = match.group(1)
            after = match.group(2)
            corrupted = f"{before}*{after}"
            
            # Check cache first
            if corrupted in self.corruption_cache:
                return self.corruption_cache[corrupted]
            
            # Try each possible character
            best_match = None
            best_score = 0
            
            # First, try exact dictionary matches
            for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_':
                candidate = f"{before}{char}{after}"
                
                # Check both cases
                if candidate.lower() in self.domain_dictionary:
                    score = 100
                    
                    # Boost score for exact case match
                    if candidate in self.domain_dictionary:
                        score += 20
                    
                    # Special cases based on patterns
                    if before.upper() == 'COL' and after.upper() == 'MN' and char.upper() == 'U':
                        score += 50  # COLUMN is very common
                    elif before.upper() == 'LOG' and after.upper() == 'C' and char.upper() == 'I':
                        score += 50  # LOGIC is very common
                    
                    if score > best_score:
                        best_score = score
                        best_match = candidate
            
            # Apply known fixes for common patterns
            if not best_match:
                known_fixes = {
                    'COL*MN': 'COLUMN',
                    'LOG*C': 'LOGIC',
                    'TAB*E': 'TABLE',
                    'SEL*CT': 'SELECT',
                    'WH*RE': 'WHERE',
                    'FR*M': 'FROM',
                    'UPD*TE': 'UPDATE',
                    'INS*RT': 'INSERT',
                    'DEL*TE': 'DELETE',
                }
                
                upper_corrupted = corrupted.upper()
                if upper_corrupted in known_fixes:
                    best_match = known_fixes[upper_corrupted]
                    # Preserve original case pattern
                    if before and before[0].islower():
                        best_match = best_match.lower()
            
            if best_match:
                # Cache the result
                self.corruption_cache[corrupted] = best_match
                return best_match
            
            # No match found, return original
            return match.group(0)
        
        # Apply fixes to all corrupted words
        fixed = re.sub(r'\b(\w*)\*(\w*)\b', replace_corrupted_word, text)
        
        # Cache if the whole text is small enough
        if len(text) < 1000:
            self.corruption_cache[text] = fixed
        
        return fixed
    
    def decode_binary_data(self, data: bytes, is_unicode: bool = False) -> str:
        """
        Main decoding function that handles PowerBuilder binary data.
        
        Args:
            data: Raw binary data from PowerBuilder file
            is_unicode: Whether the data is in Unicode format
            
        Returns:
            Decoded and fixed text
        """
        if not data:
            return ""
        
        # Step 1: Detect if this is corrupted PowerBuilder data
        has_corruption = self.detect_corruption_pattern(data)
        
        # Step 2: Decode to text
        if is_unicode:
            try:
                text = data.decode('utf-16-le', errors='replace')
            except:
                text = data.decode('latin-1', errors='replace')
        else:
            text = data.decode('latin-1', errors='replace')
        
        # Step 3: Fix corruption if detected
        if has_corruption or '*' in text:
            text = self.fix_corruption_with_dictionary(text)
            
            # Log statistics
            remaining_corruptions = len(re.findall(r'\b\w*\*\w*\b', text))
            if remaining_corruptions > 0:
                logger.debug(f"Unable to fix {remaining_corruptions} corrupted words")
        
        return text
    
    def process_dat_blocks(self, data_blocks: List) -> str:
        """
        Process a list of DAT blocks and decode their content.
        
        This handles the case where corruption might span across blocks.
        """
        # Concatenate all block data
        combined_data = b''
        is_unicode = False
        
        for block in data_blocks:
            combined_data += block.data
            if block.is_unicode_data_block_header:
                is_unicode = True
        
        # Decode the combined data
        return self.decode_binary_data(combined_data, is_unicode)
    
    def add_to_dictionary(self, words: Union[str, List[str]]):
        """Add new words to the domain dictionary."""
        if isinstance(words, str):
            words = [words]
        
        for word in words:
            self.domain_dictionary.add(word.lower())
            self.domain_dictionary.add(word.upper())
    
    def learn_from_file(self, file_path: str) -> int:
        """Learn new vocabulary from a clean file."""
        new_words = set()
        
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            # Extract all identifiers
            words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
            
            for word in words:
                if len(word) > 2 and word.lower() not in self.domain_dictionary:
                    new_words.add(word.lower())
                    new_words.add(word.upper())
            
            self.domain_dictionary.update(new_words)
            
        except Exception as e:
            logger.error(f"Error learning from file {file_path}: {e}")
        
        return len(new_words)


# Global decoder instance for convenience
_global_decoder = None

def get_decoder(dictionary_path: Optional[str] = None) -> PowerBuilderBinaryDecoder:
    """Get or create the global decoder instance."""
    global _global_decoder
    if _global_decoder is None:
        _global_decoder = PowerBuilderBinaryDecoder(dictionary_path)
    return _global_decoder


def decode_powerbuilder_text(data: bytes, encoding: str = "latin1") -> str:
    """
    Compatibility function that matches the original interface.
    
    This is the main entry point for the rest of the codebase.
    """
    decoder = get_decoder()
    return decoder.decode_binary_data(data, is_unicode=(encoding == "utf-16-le"))


def decode_with_fallback(data: bytes, is_unicode: bool) -> str:
    """
    Compatibility function for existing codebase.
    
    Decode PowerBuilder data with appropriate encoding and corruption fixing.
    """
    decoder = get_decoder()
    return decoder.decode_binary_data(data, is_unicode)


# Analysis functions for debugging
def analyze_corruption_patterns(file_path: str) -> Dict:
    """Analyze a file to understand its corruption patterns."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    decoder = get_decoder()
    
    # Find all corruption positions
    text = data.decode('latin-1', errors='replace')
    
    patterns = []
    for match in re.finditer(r'\b(\w*)\*(\w*)\b', text):
        before = match.group(1)
        after = match.group(2)
        position = len(before) + 1
        
        patterns.append({
            'word': f"{before}*{after}",
            'position': position,
            'byte_offset': match.start() + len(before),
            'context': text[max(0, match.start()-20):match.end()+20]
        })
    
    # Analyze position distribution
    position_freq = defaultdict(int)
    for p in patterns:
        position_freq[p['position']] += 1
    
    return {
        'total_corruptions': len(patterns),
        'position_frequency': dict(position_freq),
        'examples': patterns[:10]
    }