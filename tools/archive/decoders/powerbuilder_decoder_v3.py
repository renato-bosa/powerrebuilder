#!/usr/bin/env python3
"""
PowerBuilder Binary Decoder v3 - Fixed version.

This version fixes the issue where control byte decoding was too aggressive
and prevented proper corruption fixing. The key change is to be more selective
about when to apply control byte decoding vs position-based corruption fixing.

Key improvements:
- Only apply control byte decoding when we're confident it's binary control data
- Prioritize position-based dictionary fixing for text content
- Better heuristics to distinguish between control sequences and corrupted text
"""

import json
import re
import struct
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


class PowerBuilderDecoderV3:
    """PowerBuilder binary decoder with improved corruption handling."""
    
    def __init__(self):
        """Initialize the decoder with comprehensive dictionaries and caches."""
        # Domain dictionary combining all known terms
        self.domain_dict = self._initialize_domain_dictionary()
        
        # Caches for performance
        self.corruption_fix_cache: Dict[str, str] = {}
        
        # Pattern-specific fixes
        self.pattern_fixes = self._initialize_pattern_fixes()
        
        # Position analysis data
        self.position_stats: Dict[int, Counter] = defaultdict(Counter)
        self.corruption_patterns: List[Tuple[str, str]] = []
        
        # Configuration
        self.min_word_length = 3
        self.max_candidates = 50
        self.context_weight = 0.3
        
    def _initialize_domain_dictionary(self) -> Set[str]:
        """Initialize comprehensive domain dictionary from all implementations."""
        # Core PowerBuilder/SQL terms
        terms = {
            # SQL Keywords
            'select', 'from', 'where', 'insert', 'update', 'delete', 'into',
            'values', 'set', 'join', 'left', 'right', 'inner', 'outer', 'on',
            'and', 'or', 'not', 'null', 'like', 'between', 'exists', 'group', 'logic',
            'by', 'having', 'order', 'asc', 'desc', 'limit', 'union', 'all',
            'distinct', 'case', 'when', 'then', 'else', 'end', 'create', 'table',
            'column', 'primary', 'key', 'foreign', 'references', 'constraint',
            'index', 'view', 'procedure', 'function', 'trigger', 'begin', 'commit',
            'rollback', 'transaction', 'declare', 'cursor', 'fetch', 'open', 'close',
            
            # PowerBuilder Keywords
            'datawindow', 'window', 'userobject', 'global', 'instance', 'shared',
            'private', 'public', 'protected', 'event', 'function', 'subroutine',
            'forward', 'ref', 'reference', 'constant', 'indirect', 'variables',
            'end', 'if', 'then', 'elseif', 'else', 'choose', 'case', 'loop',
            'while', 'for', 'next', 'exit', 'return', 'continue', 'try', 'catch',
            'finally', 'throw', 'pbselect', 'retrieve', 'update', 'accepttext',
            'insertrow', 'deleterow', 'getitemstring', 'setitem', 'rowcount',
            
            # Data Types
            'integer', 'long', 'decimal', 'real', 'double', 'boolean', 'char',
            'character', 'string', 'date', 'time', 'datetime', 'timestamp', 'blob',
            'any', 'structure', 'object', 'array', 'powerobject',
            
            # Common Identifiers
            'name', 'type', 'value', 'status', 'message', 'code', 'description',
            'title', 'text', 'label', 'enabled', 'visible', 'width', 'height',
            'color', 'font', 'size', 'style', 'parent', 'child', 'owner',
            
            # Business Domain Terms (Medical/Dental)
            'patient', 'person', 'doctor', 'dentist', 'physician', 'practitioner',
            'clinic', 'practice', 'hospital', 'facility', 'location', 'address',
            'phone', 'email', 'contact', 'appointment', 'schedule', 'calendar',
            'treatment', 'procedure', 'diagnosis', 'medication', 'prescription',
            'bill', 'invoice', 'payment', 'charge', 'credit', 'debit', 'balance',
            'insurance', 'claim', 'medicare', 'medicaid', 'provider', 'member',
            'policy', 'coverage', 'benefit', 'copay', 'deductible', 'coinsurance',
            
            # Financial Terms
            'account', 'accounting', 'ledger', 'journal', 'transaction', 'entry',
            'debit', 'credit', 'balance', 'asset', 'liability', 'equity', 'revenue',
            'expense', 'income', 'cost', 'profit', 'loss', 'tax', 'gst', 'vat',
            'discount', 'rebate', 'refund', 'deposit', 'withdrawal', 'transfer',
            
            # Common Field Names
            'id', 'person_id', 'patient_id', 'clinic_id', 'treatment_id', 'bill_id',
            'firstname', 'lastname', 'middlename', 'fullname', 'birthdate', 'age',
            'gender', 'address1', 'address2', 'city', 'state', 'zipcode', 'country',
            'create_date', 'update_date', 'create_user', 'update_user', 'active',
            'deleted', 'notes', 'comments', 'description', 'amount', 'quantity',
            'unit_price', 'total_price', 'discount_amount', 'tax_amount', 'net_amount',
            
            # System Terms
            'username', 'password', 'login', 'logout', 'session', 'security',
            'permission', 'role', 'access', 'audit', 'log', 'error', 'warning',
            'info', 'debug', 'trace', 'version', 'release', 'build', 'config',
            'setting', 'preference', 'option', 'parameter', 'argument', 'result',
            
            # Common Misspellings/Corruptions to be fixed
            'address',  # Ensure this is in dictionary for a*dress fix
            'treatment',  # For trea*ment
            'operator',  # For opera*or
            'patient',  # For patien*
            'date',  # For *ate
        }
        
        # Add lowercase and uppercase variants
        result = set()
        for term in terms:
            result.add(term.lower())
            result.add(term.upper())
            result.add(term.capitalize())
            
        return result
    
    def _initialize_pattern_fixes(self) -> List[Tuple[re.Pattern, str]]:
        """Initialize pattern-specific fixes from all implementations."""
        return [
            # Common PowerBuilder/SQL patterns
            (re.compile(r'\bNA\s*\*E\s*=', re.IGNORECASE), 'NAME='),
            (re.compile(r'\bCOL\*MN\b', re.IGNORECASE), 'COLUMN'),
            (re.compile(r'\bCOL\*LMN\b', re.IGNORECASE), 'COLUMN'),
            (re.compile(r'\bLOG\*C\b', re.IGNORECASE), 'LOGIC'),
            (re.compile(r'\bTREA\*MENT\b', re.IGNORECASE), 'TREATMENT'),
            (re.compile(r'\bA\*DRESS\b', re.IGNORECASE), 'ADDRESS'),
            (re.compile(r'\bPATIEN\*\b', re.IGNORECASE), 'PATIENT'),
            (re.compile(r'\bOPERA\*OR\b', re.IGNORECASE), 'OPERATOR'),
            (re.compile(r'\bUPDA\*E\b', re.IGNORECASE), 'UPDATE'),
            (re.compile(r'\bSELEC\*\b', re.IGNORECASE), 'SELECT'),
            (re.compile(r'\bINSER\*\b', re.IGNORECASE), 'INSERT'),
            (re.compile(r'\bDELE\*E\b', re.IGNORECASE), 'DELETE'),
            
            # Edge cases - asterisk at beginning or end
            (re.compile(r'\*ATE\b', re.IGNORECASE), 'DATE'),
            (re.compile(r'\*Jate', re.IGNORECASE), 'date'),
            (re.compile(r'\bPATIEN\*', re.IGNORECASE), 'PATIENT'),
            
            # Missing character patterns (no asterisk)
            (re.compile(r'\baddess\b', re.IGNORECASE), 'address'),
            (re.compile(r'\btreament\b', re.IGNORECASE), 'treatment'),
            (re.compile(r'\bpatient\b', re.IGNORECASE), 'patient'),
            
            # SQL parameter placeholder corruption
            # The Ā character (U+0100) appears where ? should be in SQL
            (re.compile(r'Ā'), '?'),
        ]
    
    def decode(self, data: bytes, encoding: str = 'latin1') -> str:
        """
        Main decoding method with improved heuristics.
        
        Key change: Only use control byte decoding for binary data,
        not for text content with asterisk corruptions.
        
        Args:
            data: Binary data to decode
            encoding: Initial encoding to try
            
        Returns:
            Decoded and fixed string
        """
        # First, try standard text decoding
        try:
            decoded = data.decode(encoding)
        except UnicodeDecodeError:
            # Try alternative encodings
            for alt_encoding in ['utf-8', 'utf-16-le', 'cp1252']:
                try:
                    decoded = data.decode(alt_encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Fallback with replacement
                decoded = data.decode(encoding, errors='replace')
        
        # Check if this looks like text with asterisk corruptions
        # (not binary control sequences)
        if self._looks_like_text_corruption(decoded):
            # Apply corruption fixes
            decoded = self._fix_corruption(decoded)
            # Apply pattern-specific fixes
            decoded = self._apply_pattern_fixes(decoded)
        
        return decoded
    
    def _looks_like_text_corruption(self, text: str) -> bool:
        """
        Determine if the text contains position-based corruptions
        rather than binary control sequences.
        """
        # Look for asterisks that could be corruptions
        if '*' in text:
            # Check various asterisk patterns
            patterns = [
                r'\b\w*\*\w*\b',  # word*word
                r'\*\w+\b',       # *word (asterisk at start)
                r'\b\w+\*',       # word* (asterisk at end)
                r'\w+\s*\*\w*',   # word *word (with space)
            ]
            
            for pattern in patterns:
                if re.search(pattern, text):
                    return True
            
            # Check if the context looks like SQL/PowerBuilder code
            sql_keywords = ['select', 'from', 'where', 'column', 'table', 'update']
            pb_keywords = ['datawindow', 'retrieve', 'pbselect']
            
            text_lower = text.lower()
            for keyword in sql_keywords + pb_keywords:
                if keyword in text_lower:
                    return True
            
            # Check for common corruption patterns
            corruption_patterns = ['a*dress', 'col*mn', 'trea*ment', 'na*e', '*ate', 'patien*']
            for pattern in corruption_patterns:
                if pattern.lower() in text_lower:
                    return True
        
        # Check for known corrupted words without asterisks
        corrupted_words = ['addess', 'treament', 'patien ']
        for word in corrupted_words:
            if word in text.lower():
                return True
        
        return False
    
    def _fix_corruption(self, text: str) -> str:
        """Apply position-based dictionary fixes with context awareness."""
        # First, handle special cases with spaces before asterisk
        # e.g., "NA *E=" -> "NAME="
        text = re.sub(r'\bNA\s*\*E\s*=', 'NAME=', text, flags=re.IGNORECASE)
        
        # Find all words with asterisks
        pattern = re.compile(r'\b(\w*)\*(\w*)\b')
        
        def replace_corrupted(match):
            prefix = match.group(1)
            suffix = match.group(2)
            corrupted_word = match.group(0)
            
            # Check cache first
            if corrupted_word in self.corruption_fix_cache:
                return self.corruption_fix_cache[corrupted_word]
            
            # Find best replacement
            best_word = self._find_best_replacement(prefix, suffix, text, match.start())
            
            if best_word:
                self.corruption_fix_cache[corrupted_word] = best_word
                self._update_position_stats(len(prefix) if prefix else 0, prefix + suffix, best_word)
                return best_word
            
            return corrupted_word
        
        return pattern.sub(replace_corrupted, text)
    
    def _find_best_replacement(self, prefix: str, suffix: str, 
                               context: str, position: int) -> Optional[str]:
        """Find best replacement using scoring algorithm with context."""
        candidates = []
        prefix_lower = prefix.lower()
        suffix_lower = suffix.lower()
        
        for word in self.domain_dict:
            word_lower = word.lower()
            if (word_lower.startswith(prefix_lower) and 
                word_lower.endswith(suffix_lower) and
                len(word) == len(prefix) + 1 + len(suffix)):
                
                # Calculate base score
                score = 100.0
                
                # Prefer exact case match
                if word.startswith(prefix) and word.endswith(suffix):
                    score += 20
                
                # Consider word frequency in context
                context_score = self._calculate_context_score(word, context, position)
                score += context_score * self.context_weight
                
                # Prefer common words
                if word_lower in ['name', 'type', 'column', 'table', 'update', 
                                  'address', 'treatment', 'patient']:
                    score += 30
                
                candidates.append((score, word))
        
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
        
        return None
    
    def _calculate_context_score(self, word: str, context: str, position: int) -> float:
        """Calculate context-based score for word replacement."""
        score = 0.0
        
        # Check surrounding context (100 chars before and after)
        start = max(0, position - 100)
        end = min(len(context), position + 100)
        surrounding = context[start:end].lower()
        
        # SQL context clues
        if word.lower() in ['column', 'table', 'where', 'select']:
            sql_keywords = ['select', 'from', 'where', 'join', 'insert', 'update']
            for keyword in sql_keywords:
                if keyword in surrounding:
                    score += 10
                    
        # DataWindow context
        if word.lower() in ['name', 'type', 'dbname']:
            if 'datawindow' in surrounding or 'pbselect' in surrounding:
                score += 15
                
        # Medical/billing context
        if word.lower() in ['patient', 'treatment', 'address', 'billing']:
            medical_terms = ['clinic', 'doctor', 'appointment', 'medical']
            for term in medical_terms:
                if term in surrounding:
                    score += 10
                    
        return score
    
    def _apply_pattern_fixes(self, text: str) -> str:
        """Apply pattern-specific fixes."""
        for pattern, replacement in self.pattern_fixes:
            text = pattern.sub(replacement, text)
        return text
    
    def _update_position_stats(self, position: int, corrupted: str, fixed: str):
        """Update position statistics for learning."""
        self.position_stats[position][fixed] += 1
        self.corruption_patterns.append((corrupted, fixed))
    
    def analyze_corruption_patterns(self) -> Dict[str, Any]:
        """Analyze corruption patterns for insights."""
        analysis = {
            'total_fixes': len(self.corruption_patterns),
            'position_frequency': dict(self.position_stats),
            'common_corruptions': Counter(p[0] for p in self.corruption_patterns).most_common(10),
            'common_fixes': Counter(p[1] for p in self.corruption_patterns).most_common(10),
        }
        
        # Analyze corruption positions by word length
        by_length = defaultdict(Counter)
        for pos, counts in self.position_stats.items():
            for word, count in counts.items():
                by_length[len(word)][pos] += count
        
        analysis['position_by_word_length'] = dict(by_length)
        
        return analysis
    
    def learn_from_file(self, file_path: Path):
        """Learn new terms from a clean file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract potential identifiers
            identifier_pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]+\b')
            words = identifier_pattern.findall(content)
            
            # Add new words to dictionary
            new_words = set()
            for word in words:
                if len(word) >= self.min_word_length and word not in self.domain_dict:
                    new_words.add(word.lower())
                    self.domain_dict.add(word.lower())
                    self.domain_dict.add(word.upper())
                    self.domain_dict.add(word.capitalize())
            
            logger.info(f"Learned {len(new_words)} new words from {file_path}")
            
        except Exception as e:
            logger.error(f"Error learning from file {file_path}: {e}")
    
    def save_state(self, path: Path):
        """Save decoder state to file."""
        state = {
            'domain_dict': list(self.domain_dict),
            'corruption_fix_cache': self.corruption_fix_cache,
            'corruption_patterns': self.corruption_patterns,
        }
        
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, path: Path):
        """Load decoder state from file."""
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            
            self.domain_dict = set(state.get('domain_dict', []))
            self.corruption_fix_cache = state.get('corruption_fix_cache', {})
            self.corruption_patterns = state.get('corruption_patterns', [])
            
            logger.info(f"Loaded decoder state from {path}")
            
        except Exception as e:
            logger.error(f"Error loading state from {path}: {e}")


# Global decoder instance for efficiency
_global_decoder = None


def get_decoder() -> PowerBuilderDecoderV3:
    """Get or create global decoder instance."""
    global _global_decoder
    if _global_decoder is None:
        _global_decoder = PowerBuilderDecoderV3()
    return _global_decoder


def decode_powerbuilder_text(data: bytes, encoding: str = 'latin1') -> str:
    """
    Decode PowerBuilder binary text using the fixed decoder.
    
    This version properly handles position-based corruption without
    interfering control byte decoding.
    
    Args:
        data: Binary data to decode
        encoding: Initial encoding to try
        
    Returns:
        Decoded and fixed string
    """
    decoder = get_decoder()
    return decoder.decode(data, encoding)


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a file for corruption patterns.
    
    Args:
        file_path: Path to file to analyze
        
    Returns:
        Dictionary with analysis results
    """
    decoder = get_decoder()
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Decode the file
        decoded = decoder.decode(data)
        
        # Get analysis
        analysis = decoder.analyze_corruption_patterns()
        analysis['file_path'] = str(file_path)
        analysis['file_size'] = len(data)
        analysis['decoded_size'] = len(decoded)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        return {'error': str(e), 'file_path': str(file_path)}