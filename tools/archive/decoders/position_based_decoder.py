#!/usr/bin/env python3
"""
Position-based PowerBuilder decoder that understands the corruption is positional,
not character-mapping based. Combined with domain dictionary for intelligent fixing.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class PositionBasedPBDecoder:
    """Decoder that understands PowerBuilder's position-based encoding corruption."""
    
    def __init__(self, dictionary_path: Optional[str] = None):
        self.domain_dictionary = self._load_or_create_dictionary(dictionary_path)
        self.corruption_patterns = defaultdict(list)
        self.position_stats = defaultdict(Counter)
        
    def _load_or_create_dictionary(self, dict_path: Optional[str]) -> Set[str]:
        """Load existing dictionary or create with PowerBuilder/SQL basics."""
        if dict_path and Path(dict_path).exists():
            with open(dict_path, 'r') as f:
                data = json.load(f)
                return set(data.get('words', []))
        
        # Start with core PowerBuilder/SQL terms
        return {
            # SQL keywords
            'select', 'from', 'where', 'insert', 'update', 'delete', 'table',
            'column', 'join', 'inner', 'outer', 'left', 'right', 'order',
            'group', 'having', 'distinct', 'between', 'exists', 'union',
            
            # PowerBuilder terms
            'datawindow', 'retrieve', 'accepttext', 'insertrow', 'deleterow',
            'rowcount', 'setitem', 'getitem', 'describe', 'modify', 'create',
            
            # Common business terms
            'address', 'customer', 'employee', 'transaction', 'treatment',
            'payment', 'invoice', 'product', 'inventory', 'department',
            'description', 'amount', 'quantity', 'status', 'operator',
            
            # Common column name parts
            'id', 'name', 'date', 'time', 'code', 'type', 'flag', 'number',
            'created', 'updated', 'modified', 'deleted', 'active', 'valid'
        }
    
    def analyze_corruption_positions(self, text: str) -> Dict[str, List[int]]:
        """Analyze where asterisks appear in the text to understand the pattern."""
        analysis = {
            'asterisk_positions': [],
            'word_lengths': [],
            'patterns': []
        }
        
        # Find all words with asterisks
        pattern = re.compile(r'\b(\w*)\*(\w*)\b')
        for match in pattern.finditer(text):
            before = match.group(1)
            after = match.group(2)
            full_match = match.group(0)
            
            # Position of asterisk within the word
            asterisk_pos = len(before) + 1  # 1-indexed
            word_length = len(before) + 1 + len(after)  # Assuming 1 char missing
            
            analysis['asterisk_positions'].append(asterisk_pos)
            analysis['word_lengths'].append(word_length)
            analysis['patterns'].append({
                'match': full_match,
                'position': asterisk_pos,
                'estimated_length': word_length,
                'context': text[max(0, match.start()-20):match.end()+20]
            })
            
            # Track position statistics
            self.position_stats[word_length][asterisk_pos] += 1
        
        return analysis
    
    def decode_with_dictionary(self, text: str, use_context: bool = True) -> Tuple[str, List[Dict]]:
        """
        Decode corrupted text using domain dictionary and context.
        
        Returns:
            Tuple of (decoded_text, list_of_fixes_applied)
        """
        fixes_applied = []
        
        def find_best_match(match):
            before = match.group(1)
            after = match.group(2)
            pattern = f"{before}*{after}"
            
            # Get context if requested
            context = ""
            if use_context:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].lower()
            
            candidates = []
            
            # Try each possible character
            for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_':
                candidate = f"{before}{char}{after}"
                candidate_lower = candidate.lower()
                
                # Check if it's in dictionary
                if candidate_lower in self.domain_dictionary:
                    score = 100  # Base score for dictionary match
                    
                    # Boost score if it appears in context
                    if use_context and candidate_lower in context:
                        score += 50
                    
                    # Common patterns get higher scores
                    if candidate_lower in ['address', 'update', 'column', 'date']:
                        score += 25
                    
                    candidates.append((candidate, score, char))
            
            # If no dictionary matches, try context-based heuristics
            if not candidates and before and after:
                # Check for SQL keywords
                if before.upper() == 'COL' and after.upper() == 'MN':
                    candidates.append(('COLUMN', 75, 'U'))
                elif before.upper() == 'LOG' and after.upper() == 'C':
                    candidates.append(('LOGIC', 75, 'I'))
            
            if candidates:
                # Sort by score and take the best match
                candidates.sort(key=lambda x: x[1], reverse=True)
                best_match, score, char = candidates[0]
                
                fixes_applied.append({
                    'original': pattern,
                    'fixed': best_match,
                    'character': char,
                    'position': len(before) + 1,
                    'confidence': score,
                    'location': match.start()
                })
                
                # Return the fixed word maintaining original case
                if before and before[0].isupper():
                    return best_match
                else:
                    return best_match.lower() if best_match.isupper() else best_match
            
            # No match found, return original
            fixes_applied.append({
                'original': pattern,
                'fixed': pattern,
                'character': '*',
                'position': len(before) + 1,
                'confidence': 0,
                'location': match.start()
            })
            
            return match.group(0)
        
        # Apply fixes
        fixed_text = re.sub(r'\b(\w*)\*(\w*)\b', find_best_match, text)
        
        return fixed_text, fixes_applied
    
    def learn_from_clean_files(self, file_paths: List[str]) -> Set[str]:
        """Extract vocabulary from known-good files to enhance dictionary."""
        new_words = set()
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                
                # Extract all identifiers
                identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
                
                # Extract from SQL contexts
                # Column names
                columns = re.findall(r'(?:SELECT|select)\s+(\w+)', content)
                columns += re.findall(r'(\w+)\s*=\s*["\']', content)
                
                # Table names  
                tables = re.findall(r'(?:FROM|from)\s+(\w+)', content)
                tables += re.findall(r'(?:JOIN|join)\s+(\w+)', content)
                
                # Add all to word set
                for word in identifiers + columns + tables:
                    word_lower = word.lower()
                    if len(word_lower) > 2 and self._is_valid_word(word_lower):
                        new_words.add(word_lower)
                        
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
        
        # Add to dictionary
        self.domain_dictionary.update(new_words)
        logger.info(f"Learned {len(new_words)} new words from clean files")
        
        return new_words
    
    def _is_valid_word(self, word: str) -> bool:
        """Check if a word is valid for the dictionary."""
        # Skip if too short or too long
        if len(word) < 3 or len(word) > 50:
            return False
        
        # Skip if all numbers
        if word.isdigit():
            return False
        
        # Skip if starts/ends with underscore (unless it's a valid pattern)
        if word.startswith('__') or word.endswith('__'):
            return False
        
        return True
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a file for corruption patterns."""
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        
        analysis = self.analyze_corruption_positions(content)
        
        # Add position frequency analysis
        if self.position_stats:
            analysis['position_frequency'] = {}
            for word_len, positions in self.position_stats.items():
                analysis['position_frequency'][word_len] = dict(positions.most_common())
        
        return analysis
    
    def save_dictionary(self, path: str):
        """Save the domain dictionary to a file."""
        data = {
            'words': sorted(list(self.domain_dictionary)),
            'version': '2.0',
            'count': len(self.domain_dictionary),
            'position_stats': {
                str(k): dict(v) for k, v in self.position_stats.items()
            }
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved dictionary with {len(self.domain_dictionary)} words to {path}")
    
    def decode_powerbuilder_data(self, data: bytes, encoding: str = 'latin-1') -> str:
        """
        Main decoding function that handles binary PowerBuilder data.
        
        This understands that the corruption is positional, not character-based.
        """
        # First, try to decode as text
        try:
            text = data.decode(encoding, errors='replace')
        except:
            text = data.decode('latin-1', errors='replace')
        
        # Check if there are corruption patterns
        if '*' not in text:
            return text
        
        # Analyze the corruption pattern
        analysis = self.analyze_corruption_positions(text)
        
        # Check if there's a consistent position pattern
        if analysis['asterisk_positions']:
            positions = analysis['asterisk_positions']
            # Log the pattern for debugging
            logger.debug(f"Asterisk positions: {positions}")
            logger.debug(f"Word lengths: {analysis['word_lengths']}")
        
        # Apply dictionary-based fixing
        fixed_text, fixes = self.decode_with_dictionary(text, use_context=True)
        
        # Log fixes applied
        if fixes:
            logger.info(f"Applied {len(fixes)} fixes")
            for fix in fixes[:5]:  # Log first 5
                if fix['confidence'] > 0:
                    logger.debug(f"Fixed '{fix['original']}' -> '{fix['fixed']}' (confidence: {fix['confidence']})")
        
        return fixed_text


# Convenience function for direct use
def decode_with_position_awareness(data: bytes, dictionary_path: Optional[str] = None) -> str:
    """
    Decode PowerBuilder data understanding position-based corruption.
    
    Args:
        data: Raw bytes from PowerBuilder file
        dictionary_path: Optional path to domain dictionary
    
    Returns:
        Decoded and fixed text
    """
    decoder = PositionBasedPBDecoder(dictionary_path)
    return decoder.decode_powerbuilder_data(data)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        decoder = PositionBasedPBDecoder()
        
        # Analyze file
        analysis = decoder.analyze_file(sys.argv[1])
        
        print("Corruption Analysis:")
        print(f"Found {len(analysis['patterns'])} corruption patterns")
        
        if analysis['position_frequency']:
            print("\nPosition frequency by word length:")
            for length, positions in sorted(analysis['position_frequency'].items()):
                print(f"  Words of length {length}:")
                for pos, count in sorted(positions.items()):
                    print(f"    Position {pos}: {count} times")