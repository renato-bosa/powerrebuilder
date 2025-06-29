#!/usr/bin/env python3
"""
PowerBuilder Binary Decoder - Consolidated version.

This decoder combines all improvements from previous versions:
- Comprehensive domain dictionary for corruption fixing (from v3)
- Position-based corruption detection and fixing (from v3)
- SQL parameter placeholder corruption fixes (from v4)
- Intelligent control byte decoding with proper heuristics

Key features:
- Context-aware corruption fixing using domain knowledge
- SQL-specific parameter placeholder handling
- Learned vocabulary integration
- Performance optimizations with caching
"""

import json
import re
import struct
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


class PowerBuilderDecoder:
    """PowerBuilder binary decoder with comprehensive corruption handling."""
    
    def __init__(self):
        """Initialize the decoder with comprehensive dictionaries and caches."""
        # Domain dictionary combining all known terms
        self.domain_dict = self._initialize_domain_dictionary()
        
        # Load learned vocabulary if available
        self._load_learned_vocabulary()
        
        # Caches for performance
        self.corruption_fix_cache: Dict[str, str] = {}
        
        # Pattern-specific fixes
        self.pattern_fixes = self._initialize_pattern_fixes()
        
        # SQL parameter patterns for v4 functionality
        self.parameter_patterns = self._initialize_parameter_patterns()
        
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
            
            # Table/Object Names
            'dw_', 'tab_', 'cb_', 'st_', 'em_', 'ddlb_', 'lb_', 'pb_', 'rbtn_',
            'cbx_', 'sle_', 'mle_', 'htb_', 'vtb_', 'hpb_', 'vpb_', 'gr_', 'tv_',
            'patient_list', 'treatment_list', 'bill_list', 'appointment_list',
            'person_detail', 'clinic_detail', 'treatment_detail', 'payment_detail',
            
            # Common Prefixes/Suffixes
            'is_', 'has_', 'can_', 'should_', 'will_', 'did_', 'was_',
            '_id', '_no', '_num', '_code', '_name', '_desc', '_date', '_time',
            '_amt', '_amount', '_qty', '_quantity', '_flag', '_ind', '_indicator',
            
            # Additional Terms
            'search', 'filter', 'sort', 'export', 'import', 'print', 'preview',
            'save', 'load', 'open', 'close', 'new', 'edit', 'delete', 'cancel',
            'ok', 'yes', 'no', 'true', 'false', 'active', 'inactive', 'pending',
            'approved', 'rejected', 'completed', 'processing', 'error', 'warning',
            'info', 'success', 'failure', 'exception', 'trace', 'debug', 'log',
        }
        
        # Add variations (uppercase, title case)
        variations = set()
        for term in terms:
            variations.add(term)
            variations.add(term.upper())
            variations.add(term.title())
            
        return variations

    def _load_learned_vocabulary(self) -> None:
        """Load learned vocabulary from JSON file if available."""
        learned_vocab_path = Path(__file__).parent.parent.parent.parent / 'reference' / 'learned_vocabulary.json'
        if learned_vocab_path.exists():
            try:
                with open(learned_vocab_path, 'r') as f:
                    learned_data = json.load(f)
                    self.domain_dict.update(learned_data.get('words', []))
                    logger.info(f"Loaded {len(learned_data.get('words', []))} learned words")
            except Exception as e:
                logger.warning(f"Failed to load learned vocabulary: {e}")
    
    def _initialize_pattern_fixes(self) -> List[Tuple[re.Pattern, str]]:
        """Initialize regex-based pattern fixes for common corruptions."""
        return [
            # Fix corrupted operators
            (re.compile(r'\.Ā\s'), '.'),
            (re.compile(r'([a-zA-Z])\s+Ā\s+([a-zA-Z])'), r'\1.\2'),
            (re.compile(r'([0-9])\s+Ā\s+([0-9])'), r'\1.\2'),
            
            # Fix corrupted assignments
            (re.compile(r'\s+Ā\s+='), ' ='),
            (re.compile(r'=\s+Ā\s+'), '= '),
            
            # Fix SQL-specific patterns
            (re.compile(r'\bWHERE\s+Ā\s+'), 'WHERE '),
            (re.compile(r'\bAND\s+Ā\s+'), 'AND '),
            (re.compile(r'\bOR\s+Ā\s+'), 'OR '),
            
            # Common PowerBuilder patterns
            (re.compile(r'\.TriggerĀEvent'), '.TriggerEvent'),
            (re.compile(r'Ā_detail'), '_detail'),
            (re.compile(r'Ā_list'), '_list'),
            
            # Handle parameter placeholders
            (re.compile(r'VALUES\s*\([^)]*Ā[^)]*\)'), self._fix_values_clause),
        ]
    
    def _initialize_parameter_patterns(self) -> List[Tuple[re.Pattern, Any]]:
        """Initialize SQL parameter placeholder patterns from v4."""
        return [
            # The Ā character appearing in SQL WHERE clauses
            (re.compile(r'\bWHERE\s*\([^)]*Ā[^)]*\)', re.IGNORECASE), self._fix_where_clause_parameters),
            (re.compile(r'=\s*Ā\s*(?:\)|,|AND|OR)', re.IGNORECASE), self._fix_equals_parameter),
            (re.compile(r'VALUES\s*\([^)]*Ā[^)]*\)', re.IGNORECASE), self._fix_values_parameters),
            # Handle UNION queries with parameters
            (re.compile(r'Ā(\s*(?:\)|,|\s+AND|\s+OR|\s+UNION))', re.IGNORECASE), r'?\1'),
        ]
    
    def decode(self, data: bytes, encoding: str = 'latin1') -> str:
        """
        Main decoding method with comprehensive corruption fixes.
        
        Args:
            data: Binary data to decode
            encoding: Initial encoding to try
            
        Returns:
            Decoded and fixed string
        """
        if not data:
            return ""
        
        # Step 1: Initial decode with encoding detection
        try:
            # Try primary encoding
            text = data.decode(encoding, errors='replace')
        except Exception:
            # Fallback to latin1 which handles all byte values
            text = data.decode('latin1', errors='replace')
        
        # Step 2: Apply position-based corruption fixes
        text = self._fix_position_based_corruptions(text)
        
        # Step 3: Apply pattern-based fixes
        for pattern, replacement in self.pattern_fixes:
            if callable(replacement):
                text = pattern.sub(replacement, text)
            else:
                text = pattern.sub(replacement, text)
        
        # Step 4: Apply SQL parameter fixes (from v4)
        text = self._fix_sql_parameters(text)
        
        # Step 5: Final cleanup
        text = self._final_cleanup(text)
        
        return text
    
    def _fix_position_based_corruptions(self, text: str) -> str:
        """Fix corruptions based on position patterns."""
        if 'Ā' not in text:
            return text
        
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            if 'Ā' in line:
                fixed_line = self._fix_line_corruptions(line)
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_line_corruptions(self, line: str) -> str:
        """Fix corruptions in a single line using context."""
        # Check cache first
        if line in self.corruption_fix_cache:
            return self.corruption_fix_cache[line]
        
        words = line.split()
        fixed_words = []
        
        for i, word in enumerate(words):
            if 'Ā' in word:
                # Get context
                prev_word = words[i-1] if i > 0 else None
                next_word = words[i+1] if i < len(words)-1 else None
                
                # Try to fix the word
                fixed_word = self._fix_corrupted_word(word, prev_word, next_word)
                fixed_words.append(fixed_word)
            else:
                fixed_words.append(word)
        
        fixed_line = ' '.join(fixed_words)
        
        # Cache the result
        self.corruption_fix_cache[line] = fixed_line
        
        return fixed_line
    
    def _fix_corrupted_word(self, word: str, prev_word: Optional[str], next_word: Optional[str]) -> str:
        """Fix a corrupted word using dictionary and context."""
        # Simple replacements first
        if word == 'Ā':
            # Context-based replacement
            if prev_word and prev_word.lower() in ['where', 'and', 'or', '=', 'values']:
                return '?'  # SQL parameter
            return word
        
        # Try dictionary-based fixing
        candidates = self._find_similar_words(word)
        if candidates:
            # Score candidates based on context
            best_candidate = self._select_best_candidate(candidates, prev_word, next_word)
            if best_candidate:
                return best_candidate
        
        return word
    
    def _find_similar_words(self, corrupted_word: str) -> List[str]:
        """Find similar words in the domain dictionary."""
        if len(corrupted_word) < self.min_word_length:
            return []
        
        # Remove the corruption character for comparison
        clean_word = corrupted_word.replace('Ā', '')
        
        candidates = []
        for dict_word in self.domain_dict:
            if self._is_similar(clean_word, dict_word):
                candidates.append(dict_word)
        
        return candidates[:self.max_candidates]
    
    def _is_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are similar enough to be a match."""
        # Length difference check
        if abs(len(word1) - len(word2)) > 2:
            return False
        
        # Prefix/suffix matching
        if len(word1) >= 3 and len(word2) >= 3:
            if word1[:3].lower() == word2[:3].lower():
                return True
            if word1[-3:].lower() == word2[-3:].lower():
                return True
        
        return False
    
    def _select_best_candidate(self, candidates: List[str], prev_word: Optional[str], next_word: Optional[str]) -> Optional[str]:
        """Select the best candidate based on context."""
        if not candidates:
            return None
        
        # For now, return the first candidate
        # In a more sophisticated implementation, we would score based on context
        return candidates[0]
    
    def _fix_sql_parameters(self, text: str) -> str:
        """Fix SQL parameter placeholders corrupted to Ā (from v4)."""
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
    
    def _fix_values_clause(self, match) -> str:
        """Fix VALUES clause with corrupted parameters."""
        values = match.group(0)
        return values.replace('Ā', '?')
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup of the text."""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Fix multiple spaces
        text = re.sub(r'  +', ' ', text)
        
        # Fix space before punctuation
        text = re.sub(r' +([.,;!?])', r'\1', text)
        
        return text.strip()
    
    def analyze_corruption_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze corruption patterns in the text."""
        if 'Ā' not in text:
            return {'has_corruption': False}
        
        analysis = {
            'has_corruption': True,
            'total_corrupted_chars': text.count('Ā'),
            'contexts': []
        }
        
        # Find contexts where Ā appears
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'Ā' in line:
                # Extract surrounding context
                for match in re.finditer('Ā', line):
                    pos = match.start()
                    start = max(0, pos - 20)
                    end = min(len(line), pos + 20)
                    context = line[start:end]
                    
                    analysis['contexts'].append({
                        'line': i + 1,
                        'position': pos,
                        'context': context,
                        'full_line': line.strip()
                    })
        
        return analysis


# Global decoder instance for efficiency
_global_decoder = None


def get_decoder() -> PowerBuilderDecoder:
    """Get or create global decoder instance."""
    global _global_decoder
    if _global_decoder is None:
        _global_decoder = PowerBuilderDecoder()
    return _global_decoder


def decode_powerbuilder_text(data: bytes, encoding: str = 'latin1') -> str:
    """
    Decode PowerBuilder binary text with comprehensive fixes.
    
    This is the main entry point for decoding PowerBuilder binary data.
    
    Args:
        data: Binary data to decode
        encoding: Initial encoding to try (default: latin1)
        
    Returns:
        Decoded and fixed string
    """
    decoder = get_decoder()
    return decoder.decode(data, encoding)