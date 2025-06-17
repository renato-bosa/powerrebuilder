"""String resource extraction from PowerBuilder compiled objects.

This module provides functionality to extract string resources from P-code files,
including literal strings, property values, and string tables.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

logger = logging.getLogger(__name__)


class StringResourceExtractor:
    """Extracts string resources from PowerBuilder compiled objects."""
    
    # Minimum string length to consider (filters out noise)
    MIN_STRING_LENGTH = 3
    
    # Maximum string length (prevents memory issues with corrupted data)
    MAX_STRING_LENGTH = 10000
    
    # Common PowerBuilder string patterns
    STRING_PATTERNS = [
        # ASCII strings (printable characters)
        rb'[\x20-\x7E]{3,}',
        # Unicode strings (simplified pattern)
        rb'(?:[\x00][\x20-\x7E]){3,}',
        # Wide character strings
        rb'(?:[\x20-\x7E][\x00]){3,}',
    ]
    
    # Patterns to exclude (reduce false positives)
    EXCLUDE_PATTERNS = [
        # Binary sequences that look like strings
        re.compile(rb'^[\x00]+$'),  # All nulls
        re.compile(rb'^[\xFF]+$'),  # All 0xFF
        re.compile(rb'^(?:[\x00-\x1F])+$'),  # All control characters
    ]
    
    def __init__(self):
        """Initialize the string resource extractor."""
        self.extracted_strings: Dict[str, Set[str]] = {}
        
    def extract_strings_from_file(self, file_path: Path) -> List[str]:
        """Extract all string resources from a file.
        
        Args:
            file_path: Path to the file to extract strings from
            
        Returns:
            List of extracted strings
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                
            return self.extract_strings_from_data(data, str(file_path))
            
        except Exception as e:
            logger.error("Failed to extract strings from %s: %s", file_path, e)
            return []
            
    def extract_strings_from_data(self, data: bytes, source: str = "unknown") -> List[str]:
        """Extract strings from binary data.
        
        Args:
            data: Binary data to extract strings from
            source: Source identifier for logging
            
        Returns:
            List of extracted strings
        """
        strings = set()
        
        # Try each string pattern
        for pattern in self.STRING_PATTERNS:
            matches = re.findall(pattern, data)
            for match in matches:
                # Decode the match
                decoded = self._decode_string(match)
                if decoded and self._is_valid_string(decoded):
                    strings.add(decoded)
                    
        # Store results
        if strings:
            self.extracted_strings[source] = strings
            logger.info("Extracted %s strings from %s", len(strings), source)
            
        return sorted(strings)
        
    def _decode_string(self, data: bytes) -> Optional[str]:
        """Attempt to decode a string from binary data.
        
        Args:
            data: Binary data to decode
            
        Returns:
            Decoded string or None if decoding fails
        """
        # Try different encodings
        encodings = ['utf-8', 'utf-16-le', 'utf-16-be', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                # Remove null bytes for certain encodings
                if encoding in ['utf-8', 'ascii', 'cp1252']:
                    # Remove interleaved nulls (wide char to normal)
                    if b'\x00' in data[::2] or b'\x00' in data[1::2]:
                        data = data.replace(b'\x00', b'')
                        
                decoded = data.decode(encoding, errors='ignore').strip()
                
                # Check if decoding produced valid result
                if decoded and len(decoded) >= self.MIN_STRING_LENGTH:
                    return decoded
                    
            except Exception:
                continue
                
        return None
        
    def _is_valid_string(self, s: str) -> bool:
        """Check if a string is valid (not noise).
        
        Args:
            s: String to validate
            
        Returns:
            True if string is valid, False otherwise
        """
        # Length checks
        if len(s) < self.MIN_STRING_LENGTH or len(s) > self.MAX_STRING_LENGTH:
            return False
            
        # Must contain at least one letter
        if not any(c.isalpha() for c in s):
            return False
            
        # Check printable ratio
        printable_count = sum(1 for c in s if c.isprintable())
        if printable_count / len(s) < 0.9:
            return False
            
        # Exclude strings that are all the same character
        if len(set(s)) == 1:
            return False
            
        # Exclude hex strings
        if all(c in '0123456789ABCDEFabcdef' for c in s):
            return False
            
        return True
        
    def extract_property_strings(self, data: bytes) -> Dict[str, str]:
        """Extract property name/value pairs from binary data.
        
        Args:
            data: Binary data to analyze
            
        Returns:
            Dictionary of property name to value mappings
        """
        properties = {}
        
        # Look for common property patterns
        # Format: property_name=value or property_name="value"
        property_pattern = rb'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:"([^"]+)"|([^\r\n\s]+))'
        
        matches = re.finditer(property_pattern, data)
        for match in matches:
            try:
                name = match.group(1).decode('ascii', errors='ignore')
                # Get value from either quoted (group 2) or unquoted (group 3)
                value = match.group(2) or match.group(3)
                value = value.decode('utf-8', errors='ignore').strip()
                
                if name and value:
                    properties[name] = value
                    
            except Exception:
                continue
                
        return properties
        
    def extract_string_table(self, data: bytes) -> List[Tuple[int, str]]:
        """Extract string table entries from binary data.
        
        String tables often have format: [length][string data]
        
        Args:
            data: Binary data containing string table
            
        Returns:
            List of (index, string) tuples
        """
        strings = []
        offset = 0
        index = 0
        
        while offset < len(data) - 4:
            # Try different length encodings
            # 2-byte length (little endian)
            if offset + 2 < len(data):
                length = int.from_bytes(data[offset:offset+2], 'little')
                
                if 0 < length < 1000 and offset + 2 + length <= len(data):
                    string_data = data[offset+2:offset+2+length]
                    decoded = self._decode_string(string_data)
                    
                    if decoded and self._is_valid_string(decoded):
                        strings.append((index, decoded))
                        index += 1
                        offset += 2 + length
                        continue
                        
            # 4-byte length (little endian)
            if offset + 4 < len(data):
                length = int.from_bytes(data[offset:offset+4], 'little')
                
                if 0 < length < 10000 and offset + 4 + length <= len(data):
                    string_data = data[offset+4:offset+4+length]
                    decoded = self._decode_string(string_data)
                    
                    if decoded and self._is_valid_string(decoded):
                        strings.append((index, decoded))
                        index += 1
                        offset += 4 + length
                        continue
                        
            # No valid string found, move forward
            offset += 1
            
        return strings
        
    def generate_string_catalog(self) -> Dict[str, Any]:
        """Generate a catalog of all extracted strings.
        
        Returns:
            Dictionary containing string statistics and mappings
        """
        catalog = {
            'total_sources': len(self.extracted_strings),
            'total_unique_strings': len(set().union(*self.extracted_strings.values())),
            'sources': {},
            'common_strings': {},
            'string_index': {}
        }
        
        # Count string occurrences across sources
        string_counts = {}
        for source, strings in self.extracted_strings.items():
            catalog['sources'][source] = len(strings)
            for string in strings:
                if string not in string_counts:
                    string_counts[string] = []
                string_counts[string].append(source)
                
        # Find common strings (appear in multiple sources)
        for string, sources in string_counts.items():
            if len(sources) > 1:
                catalog['common_strings'][string] = sources
                
        # Create string index
        all_strings = sorted(set().union(*self.extracted_strings.values()))
        catalog['string_index'] = {i: s for i, s in enumerate(all_strings)}
        
        return catalog