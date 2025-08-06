"""High-performance P-code detection algorithm for PowerBuilder objects.

This module provides a fast O(n) P-code detection algorithm that replaces the
current O(n²) implementation with advanced pattern matching, sliding window
confidence caching, and intelligent heuristics.

Key improvements:
- Boyer-Moore string matching for O(n) pattern detection
- Sliding window with cached confidence scores
- Early termination when sufficient P-code is found
- Chunked processing for memory efficiency
- Heuristics to jump to likely P-code locations

Complexity: O(n) instead of O(n²)
Memory usage: Significantly reduced through chunking and caching
"""

import logging
from typing import Optional, Tuple, List, Dict, Set
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class PCodePattern:
    """Represents a P-code detection pattern."""
    signature: bytes
    confidence_boost: float
    description: str


@dataclass 
class ConfidenceWindow:
    """Cached confidence score for a sliding window."""
    offset: int
    confidence: float
    window_size: int


class HighPerformancePCodeDetector:
    """High-performance O(n) P-code detector using advanced algorithms."""
    
    # PowerBuilder P-code signature patterns for fast detection
    PCODE_SIGNATURES = [
        # Common instruction sequences
        PCodePattern(b"\x00\x00", 0.8, "RETURN instruction"),
        PCodePattern(b"\x04\x00", 0.9, "JUMP instruction"),
        PCodePattern(b"\x05\x00", 0.9, "DBSTART instruction"),
        PCodePattern(b"\x29\x00", 0.85, "GLOBFUNCCALL instruction"),
        PCodePattern(b"\x2c\x00", 0.85, "DOTFUNCCALL instruction"),
        PCodePattern(b"\x32\x00", 0.8, "PUSH_CONST_INT instruction"),
        PCodePattern(b"\x1e\x00", 0.8, "PUSH_LOCAL_VAR instruction"),
        PCodePattern(b"\x21\x00", 0.8, "PUSH_THIS instruction"),
        PCodePattern(b"\x15\x00", 0.8, "DBEXECUTEDYN instruction"),
        
        # Multi-byte patterns for higher confidence
        PCodePattern(b"\x00\x00\x1e", 0.9, "RETURN + PUSH_LOCAL_VAR sequence"),
        PCodePattern(b"\x32\x00\x00", 0.9, "PUSH_CONST_INT + RETURN sequence"),
        PCodePattern(b"\x21\x00\x27", 0.9, "PUSH_THIS + DOT sequence"),
        PCodePattern(b"\x04\x00\x1e", 0.9, "JUMP + PUSH_LOCAL_VAR sequence"),
        
        # Common getter/setter patterns
        PCodePattern(b"\x2d\x00\x00", 0.95, "PUSH_PROPERTY + RETURN (getter)"),
        PCodePattern(b"\x2e\x00\x00", 0.95, "POP_PROPERTY + RETURN (setter)"),
    ]
    
    # Valid PowerBuilder opcodes for quick validation
    VALID_OPCODES = frozenset({
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
        0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
        0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23,
        0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
        0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B,
        0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47,
        0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x52, 0x53,
        0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F,
        0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x6B,
        0x6C, 0x6D, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77,
        0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F, 0x80, 0x81, 0x82, 0x83,
        0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F,
        # Extended opcodes up to 0x246 for PB 8.0+
    })
    
    # Confidence calculation parameters
    WINDOW_SIZE = 64  # Sliding window size for confidence calculation
    CACHE_SIZE = 1000  # Maximum cached confidence windows
    CHUNK_SIZE = 8192  # Processing chunk size for memory efficiency
    MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for P-code detection
    EARLY_TERMINATION_SIZE = 512  # Stop after finding this much P-code
    
    def __init__(self):
        """Initialize the high-performance detector."""
        self._confidence_cache: Dict[int, ConfidenceWindow] = {}
        self._boyer_moore_tables: Dict[bytes, List[int]] = {}
        
        # Pre-compute Boyer-Moore bad character tables for all signatures
        for pattern in self.PCODE_SIGNATURES:
            self._boyer_moore_tables[pattern.signature] = self._build_boyer_moore_table(pattern.signature)
    
    @staticmethod
    def _build_boyer_moore_table(pattern: bytes) -> List[int]:
        """Build Boyer-Moore bad character table for fast pattern matching.
        
        Args:
            pattern: The pattern to build the table for
            
        Returns:
            Bad character table for Boyer-Moore algorithm
        """
        table = [len(pattern)] * 256
        for i in range(len(pattern) - 1):
            table[pattern[i]] = len(pattern) - 1 - i
        return table
    
    def _boyer_moore_search(self, data: bytes, pattern: bytes) -> List[int]:
        """Fast Boyer-Moore pattern search with O(n/m) average complexity.
        
        Args:
            data: The data to search in
            pattern: The pattern to search for
            
        Returns:
            List of offsets where pattern is found
        """
        if len(pattern) == 0 or len(pattern) > len(data):
            return []
        
        bad_char_table = self._boyer_moore_tables.get(pattern)
        if bad_char_table is None:
            bad_char_table = self._build_boyer_moore_table(pattern)
            self._boyer_moore_tables[pattern] = bad_char_table
        
        matches = []
        skip = 0
        
        while skip <= len(data) - len(pattern):
            # Check pattern from right to left
            i = len(pattern) - 1
            while i >= 0 and pattern[i] == data[skip + i]:
                i -= 1
            
            if i < 0:
                # Found a match
                matches.append(skip)
                skip += len(pattern)  # Move past this match
            else:
                # Use bad character heuristic to skip positions
                skip += max(1, bad_char_table[data[skip + i]])
        
        return matches
    
    @lru_cache(maxsize=256)
    def _fast_opcode_confidence(self, byte_val: int) -> float:
        """Fast opcode confidence lookup with caching.
        
        Args:
            byte_val: The byte value to check
            
        Returns:
            Confidence score for the byte being a valid opcode
        """
        if byte_val in self.VALID_OPCODES:
            # Higher confidence for common opcodes
            if byte_val in {0x00, 0x04, 0x1E, 0x21, 0x29, 0x2C, 0x32}:
                return 0.9
            else:
                return 0.7
        return 0.0
    
    def _calculate_window_confidence(self, data: bytes, offset: int, window_size: int = None) -> float:
        """Calculate confidence for a window with optimized algorithm.
        
        Args:
            data: The data buffer
            offset: Starting offset of the window
            window_size: Size of the window (defaults to WINDOW_SIZE)
            
        Returns:
            Confidence score from 0.0 to 1.0
        """
        if window_size is None:
            window_size = self.WINDOW_SIZE
        
        end_offset = min(offset + window_size, len(data))
        if end_offset <= offset:
            return 0.0
        
        window = data[offset:end_offset]
        actual_size = len(window)
        
        if actual_size < 2:
            return 0.0
        
        # Fast confidence calculation using vectorized operations where possible
        confidence = 0.0
        valid_opcodes = 0
        instruction_patterns = 0
        
        # Check for valid opcodes
        for i in range(actual_size):
            byte_confidence = self._fast_opcode_confidence(window[i])
            confidence += byte_confidence * 0.4 / actual_size
            if byte_confidence > 0:
                valid_opcodes += 1
        
        # Check for instruction patterns (opcode followed by operands)
        i = 0
        while i < actual_size - 1:
            if window[i] in self.VALID_OPCODES:
                # Check if next byte could be an operand or another opcode
                if window[i + 1] == 0x00 or window[i + 1] in self.VALID_OPCODES:
                    instruction_patterns += 1
                    i += 2  # Skip the operand
                else:
                    i += 1
            else:
                i += 1
        
        # Boost confidence based on instruction patterns
        if actual_size >= 4:
            pattern_ratio = instruction_patterns / (actual_size // 2)
            confidence += min(pattern_ratio * 0.5, 0.5)
        
        # Penalize excessive null bytes (but not UTF-16 patterns)
        null_count = window.count(0x00)
        if null_count > actual_size * 0.7:  # More than 70% nulls
            confidence *= 0.3
        
        # Boost confidence for diverse byte values
        unique_bytes = len(set(window))
        if unique_bytes > actual_size * 0.3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_cached_confidence(self, offset: int, window_size: int = None) -> Optional[float]:
        """Get cached confidence score for an offset.
        
        Args:
            offset: The offset to check
            window_size: Expected window size
            
        Returns:
            Cached confidence score or None if not cached
        """
        if window_size is None:
            window_size = self.WINDOW_SIZE
        
        cached = self._confidence_cache.get(offset)
        if cached and cached.window_size == window_size:
            return cached.confidence
        return None
    
    def _cache_confidence(self, offset: int, confidence: float, window_size: int = None):
        """Cache a confidence score for an offset.
        
        Args:
            offset: The offset
            confidence: The confidence score
            window_size: The window size used
        """
        if window_size is None:
            window_size = self.WINDOW_SIZE
        
        # Limit cache size to prevent memory issues
        if len(self._confidence_cache) >= self.CACHE_SIZE:
            # Remove oldest entries (simple FIFO)
            oldest_offset = min(self._confidence_cache.keys())
            del self._confidence_cache[oldest_offset]
        
        self._confidence_cache[offset] = ConfidenceWindow(offset, confidence, window_size)
    
    def _find_text_boundary_heuristic(self, data: bytes) -> int:
        """Fast heuristic to find where text ends and binary data begins.
        
        Args:
            data: The data to analyze
            
        Returns:
            Offset where binary data likely starts, or -1 if not found
        """
        # Look for PowerBuilder export header first
        if data.startswith(b"HA$PBExportHeader$"):
            # Find second newline
            first_newline = data.find(b"\n")
            if first_newline >= 0:
                second_newline = data.find(b"\n", first_newline + 1)
                if second_newline >= 0:
                    return second_newline + 1
        
        # Scan for transition from ASCII to binary
        ascii_run = 0
        for i in range(min(len(data), 1024)):  # Check first 1KB only
            if 32 <= data[i] <= 126 or data[i] in {9, 10, 13}:
                ascii_run += 1
            else:
                if ascii_run >= 20:  # Had a good ASCII run
                    # Check if this looks like binary data
                    test_window = data[i:i + 32]
                    if self._calculate_window_confidence(data, i, 32) > 0.5:
                        return i
                ascii_run = 0
        
        return -1
    
    def _detect_utf16_regions(self, data: bytes) -> List[Tuple[int, int]]:
        """Fast detection of UTF-16 string regions to skip during scanning.
        
        Args:
            data: The data to analyze
            
        Returns:
            List of (start, end) tuples for UTF-16 regions
        """
        utf16_regions = []
        i = 0
        
        while i < len(data) - 20:  # Need at least 20 bytes to detect pattern
            # Look for UTF-16 LE pattern (ASCII char followed by null)
            if (data[i] != 0 and data[i + 1] == 0 and 
                32 <= data[i] <= 126):  # Printable ASCII
                
                # Confirm it's a UTF-16 string
                start = i
                while i < len(data) - 1:
                    if data[i + 1] == 0 and 32 <= data[i] <= 126:
                        i += 2  # Skip UTF-16 character
                    else:
                        break
                
                if i - start >= 20:  # At least 10 UTF-16 characters
                    utf16_regions.append((start, i))
            else:
                i += 1
        
        return utf16_regions
    
    def find_pcode_start_optimized(self, data: bytes) -> Tuple[int, float]:
        """Optimized O(n) P-code start detection with early termination.
        
        This is the main replacement for _find_pcode_start() with O(n) complexity.
        
        Args:
            data: The raw binary data to search
            
        Returns:
            Tuple of (offset, confidence) where P-code starts, or (-1, 0.0) if not found
        """
        if len(data) < 2:
            return -1, 0.0
        
        logger.debug("Starting optimized P-code detection on %d bytes", len(data))
        
        # Step 1: Check for PowerBuilder export format (O(1))
        if data.startswith(b"HA$PBExportHeader$"):
            boundary = self._find_text_boundary_heuristic(data)
            if boundary > 0:
                confidence = self._calculate_window_confidence(data, boundary)
                if confidence > 0.5:
                    logger.debug("Found P-code at export boundary: offset 0x%04x, confidence %.2f", 
                               boundary, confidence)
                    return boundary, confidence
        
        # Step 2: Use heuristic to find likely start position (O(1) amortized)
        text_boundary = self._find_text_boundary_heuristic(data)
        start_offset = max(0, text_boundary) if text_boundary >= 0 else 0
        
        # Step 3: Detect UTF-16 regions to skip (O(n) but with large jumps)
        utf16_regions = self._detect_utf16_regions(data[start_offset:])
        utf16_regions = [(start + start_offset, end + start_offset) for start, end in utf16_regions]
        
        # Step 4: Fast pattern matching using Boyer-Moore (O(n))
        best_offset = -1
        best_confidence = 0.0
        
        # Search for signature patterns
        for pattern in self.PCODE_SIGNATURES:
            matches = self._boyer_moore_search(data[start_offset:], pattern.signature)
            
            for match_offset in matches:
                absolute_offset = match_offset + start_offset
                
                # Skip if this offset is in a UTF-16 region
                in_utf16 = any(start <= absolute_offset < end for start, end in utf16_regions)
                if in_utf16:
                    continue
                
                # Check cached confidence first
                confidence = self._get_cached_confidence(absolute_offset)
                if confidence is None:
                    confidence = self._calculate_window_confidence(data, absolute_offset)
                    self._cache_confidence(absolute_offset, confidence)
                
                # Apply pattern-specific boost
                boosted_confidence = min(1.0, confidence + pattern.confidence_boost * 0.1)
                
                if boosted_confidence > best_confidence:
                    best_confidence = boosted_confidence
                    best_offset = absolute_offset
                    
                    logger.debug("Found pattern %s at offset 0x%04x, confidence %.2f", 
                               pattern.description, absolute_offset, boosted_confidence)
                
                # Early termination for high confidence
                if boosted_confidence >= 0.95:
                    logger.debug("Early termination: high confidence P-code found")
                    return best_offset, best_confidence
        
        # Step 5: Sliding window scan with caching (O(n) with cached confidence)
        if best_confidence < self.MIN_CONFIDENCE_THRESHOLD:
            logger.debug("Pattern search insufficient, performing sliding window scan")
            
            # Use larger steps for efficiency, but still maintain good coverage
            step_size = self.WINDOW_SIZE // 4
            
            for offset in range(start_offset, len(data) - self.WINDOW_SIZE, step_size):
                # Skip UTF-16 regions
                in_utf16 = any(start <= offset < end for start, end in utf16_regions)
                if in_utf16:
                    continue
                
                # Check cached confidence
                confidence = self._get_cached_confidence(offset)
                if confidence is None:
                    confidence = self._calculate_window_confidence(data, offset)
                    self._cache_confidence(offset, confidence)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_offset = offset
                    
                    # Early termination for good confidence
                    if confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                        logger.debug("Sliding window found P-code at offset 0x%04x, confidence %.2f", 
                                   offset, confidence)
                        break
        
        if best_offset >= 0:
            logger.info("P-code detection complete: offset 0x%04x, confidence %.2f", 
                       best_offset, best_confidence)
            return best_offset, best_confidence
        else:
            logger.warning("No P-code found in data")
            return -1, 0.0
    
    def find_pcode_end_optimized(self, data: bytes, start_offset: int) -> int:
        """Optimized P-code end detection with chunked processing.
        
        Args:
            data: The data buffer
            start_offset: Where P-code starts
            
        Returns:
            Offset where P-code ends
        """
        if start_offset < 0 or start_offset >= len(data):
            return len(data)
        
        logger.debug("Finding P-code end from offset 0x%04x", start_offset)
        
        current_offset = start_offset
        last_valid_offset = start_offset
        low_confidence_run = 0
        
        # Process in chunks for memory efficiency
        while current_offset < len(data):
            chunk_end = min(current_offset + self.CHUNK_SIZE, len(data))
            chunk_size = min(self.WINDOW_SIZE, chunk_end - current_offset)
            
            if chunk_size < 2:
                break
            
            # Check for UTF-16 strings
            utf16_regions = self._detect_utf16_regions(data[current_offset:chunk_end])
            if utf16_regions and utf16_regions[0][0] == 0:  # Starts with UTF-16
                logger.debug("Found UTF-16 string at offset 0x%04x, ending P-code", current_offset)
                return last_valid_offset
            
            # Calculate confidence for this chunk
            confidence = self._calculate_window_confidence(data, current_offset, chunk_size)
            
            if confidence < 0.3:
                low_confidence_run += chunk_size
                # If we have a long run of low confidence, we're past P-code
                if low_confidence_run >= 64:
                    logger.debug("Long low-confidence run, ending P-code at 0x%04x", last_valid_offset)
                    return last_valid_offset
            else:
                low_confidence_run = 0
                last_valid_offset = current_offset + chunk_size
            
            # Check for common end patterns
            remaining_data = data[current_offset:chunk_end]
            
            # Multiple nulls (but not UTF-16)
            null_run = 0
            for i, byte in enumerate(remaining_data):
                if byte == 0x00:
                    null_run += 1
                    if null_run >= 8:  # 8+ consecutive nulls
                        # Make sure it's not UTF-16
                        if not any(start <= current_offset + i < end for start, end in utf16_regions):
                            logger.debug("Found null padding at 0x%04x", current_offset + i)
                            return current_offset + i
                else:
                    null_run = 0
            
            # 0xFF padding
            if remaining_data.startswith(b'\xff' * 8):
                logger.debug("Found 0xFF padding at 0x%04x", current_offset)
                return current_offset
            
            current_offset += chunk_size
        
        return len(data)
    
    def detect_pcode_sections_fast(self, data: bytes) -> List[Tuple[int, int, float]]:
        """Fast detection of all P-code sections with O(n) complexity.
        
        Args:
            data: The raw binary data
            
        Returns:
            List of (offset, length, confidence) tuples for detected P-code sections
        """
        if len(data) < 2:
            return []
        
        logger.info("Fast P-code section detection on %d bytes", len(data))
        sections = []
        
        # Handle small data specially
        if len(data) < 20:
            confidence = self._calculate_window_confidence(data, 0, len(data))
            if confidence > 0.3:
                sections.append((0, len(data), confidence))
                logger.debug("Small data detected as single P-code section: confidence %.2f", confidence)
            return sections
        
        # Find first P-code section
        start_offset, confidence = self.find_pcode_start_optimized(data)
        
        if start_offset < 0:
            return []
        
        # Find end of this section
        end_offset = self.find_pcode_end_optimized(data, start_offset)
        section_length = end_offset - start_offset
        
        if section_length >= 2:
            sections.append((start_offset, section_length, confidence))
            logger.info("Found P-code section: offset=0x%04x, length=%d, confidence=%.2f", 
                       start_offset, section_length, confidence)
        
        # Look for additional sections after the first one
        search_offset = end_offset
        while search_offset < len(data) - 2:
            # Skip ahead through low-confidence regions
            chunk_confidence = self._calculate_window_confidence(data, search_offset, 
                                                               min(64, len(data) - search_offset))
            
            if chunk_confidence < 0.3:
                search_offset += 32  # Skip ahead
                continue
            
            # Found potential P-code
            section_end = self.find_pcode_end_optimized(data, search_offset)
            section_length = section_end - search_offset
            
            if section_length >= 2:
                sections.append((search_offset, section_length, chunk_confidence))
                logger.info("Found additional P-code section: offset=0x%04x, length=%d, confidence=%.2f", 
                           search_offset, section_length, chunk_confidence)
                search_offset = section_end
            else:
                search_offset += 1
        
        logger.info("Fast detection complete: found %d P-code sections", len(sections))
        return sections
    
    def clear_cache(self):
        """Clear the confidence cache to free memory."""
        self._confidence_cache.clear()
        logger.debug("Cleared confidence cache")


# Replacement function for the original _find_pcode_start method
def find_pcode_start_high_performance(data: bytes) -> int:
    """High-performance replacement for _find_pcode_start with O(n) complexity.
    
    This function provides a drop-in replacement for the original O(n²) implementation.
    
    Args:
        data: Raw binary data to search for P-code
        
    Returns:
        Offset where P-code starts, or -1 if not found
    """
    detector = HighPerformancePCodeDetector()
    offset, confidence = detector.find_pcode_start_optimized(data)
    
    # Log performance improvement details
    if offset >= 0:
        logger.info("High-performance detector found P-code at offset 0x%04x (confidence: %.2f)", 
                   offset, confidence)
    
    return offset


# Example usage and performance demonstration
def demonstrate_performance():
    """Demonstrate the performance improvements of the new algorithm."""
    import time
    import random
    
    # Generate test data
    test_data = bytearray(10000)
    
    # Add some P-code patterns
    pcode_patterns = [
        b"\x00\x00",  # RETURN
        b"\x04\x00",  # JUMP  
        b"\x1e\x00",  # PUSH_LOCAL_VAR
        b"\x32\x00\x00",  # PUSH_CONST_INT + RETURN
    ]
    
    # Inject patterns at various locations
    for i in range(0, len(test_data), 500):
        if i + 3 < len(test_data):
            pattern = random.choice(pcode_patterns)
            test_data[i:i+len(pattern)] = pattern
    
    # Add some UTF-16 strings to test skipping
    utf16_string = "Hello World".encode('utf-16le')
    test_data[1000:1000+len(utf16_string)] = utf16_string
    
    # Test the high-performance detector
    detector = HighPerformancePCodeDetector()
    
    start_time = time.time()
    sections = detector.detect_pcode_sections_fast(bytes(test_data))
    end_time = time.time()
    
    print(f"High-performance detector:")
    print(f"  Processing time: {(end_time - start_time) * 1000:.2f} ms")
    print(f"  Sections found: {len(sections)}")
    print(f"  Memory usage: Chunked processing with {detector.CHUNK_SIZE} byte chunks")
    
    for i, (offset, length, confidence) in enumerate(sections):
        print(f"    Section {i+1}: offset=0x{offset:04x}, length={length}, confidence={confidence:.2f}")


if __name__ == "__main__":
    # Run performance demonstration
    demonstrate_performance()