"""Enhanced P-code detection for PowerBuilder objects.

This module provides improved P-code detection that understands
PowerBuilder object structures better.
"""

import logging
import struct
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class EnhancedPCodeDetector:
    """Enhanced P-code detector for PowerBuilder objects."""
    
    @classmethod
    def find_pcode_in_function(cls, data: bytes) -> Tuple[int, int]:
        """Find P-code in a PowerBuilder function object.
        
        PowerBuilder function format:
        1. Header/metadata
        2. Optional source code
        3. P-code section
        
        Args:
            data: Raw function data (from DAT blocks)
            
        Returns:
            Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        if len(data) < 16:
            return -1, 0
        
        # Strategy 1: Look for P-code header patterns
        # P-code often starts with specific patterns after metadata
        
        # Common P-code start patterns in functions
        PCODE_PATTERNS = [
            # Pattern: length prefix followed by instruction bytes
            b'\x00\x00\x00\x00',  # Null header
            b'\x04\x00',          # JUMP instruction (0x04)
            b'\x00\x00',          # RETURN at start (0x00)
            b'\x05\x00',          # DBSTART (0x05)
            b'\x29\x00',          # GLOBFUNCCALL (0x29)
            b'\x2C\x00',          # DOTFUNCCALL (0x2C)
        ]
        
        # Scan for P-code start
        pcode_start = -1
        for i in range(0, min(len(data) - 4, 1024)):  # Limit scan to first 1KB
            # Check if we have a potential P-code start
            
            # Method 1: Look for sequences of valid opcodes
            if cls._looks_like_pcode(data[i:i+20]):
                logger.debug(f"Found P-code by opcode pattern at offset {i}")
                pcode_start = i
                break
            
            # Method 2: Look for specific patterns
            for pattern in PCODE_PATTERNS:
                if data[i:i+len(pattern)] == pattern:
                    # Verify it's actually P-code by checking surrounding bytes
                    if cls._verify_pcode_context(data, i):
                        logger.debug(f"Found P-code by pattern {pattern.hex()} at offset {i}")
                        pcode_start = i
                        break
            
            if pcode_start >= 0:
                break
        
        # Strategy 2: Look for transition from text to binary
        if pcode_start < 0:
            text_end = cls._find_text_to_binary_transition(data)
            if text_end > 0:
                logger.debug(f"Found P-code after text transition at offset {text_end}")
                pcode_start = text_end
        
        if pcode_start < 0:
            logger.warning("Could not find P-code in function data")
            return -1, 0
        
        # Now find the end of executable P-code
        # Look for patterns that indicate end of code:
        # - Multiple RETURNs in a row
        # - Long sequences of 0x00 or 0xFF
        # - Invalid opcode sequences
        pcode_end = cls._find_pcode_end(data, pcode_start)
        
        return pcode_start, pcode_end - pcode_start
    
    @classmethod
    def _looks_like_pcode(cls, data: bytes) -> bool:
        """Check if data looks like P-code instructions."""
        if len(data) < 10:
            return False
        
        # P-code characteristics:
        # 1. Has valid opcodes (0x00-0xFF)
        # 2. Has reasonable instruction sequences
        # 3. Contains non-printable bytes
        
        # Count valid looking opcodes
        valid_opcodes = 0
        i = 0
        
        # Known valid opcodes (partial list)
        VALID_OPCODES = {
            0x00,  # RETURN
            0x01,  # STORE_RETURN_VAL
            0x02,  # JUMPTRUE
            0x03,  # JUMPFALSE
            0x04,  # JUMP
            0x05,  # DBSTART
            0x06,  # DBCOMMIT
            0x07,  # DBROLLBACK
            0x08,  # DBSTOP
            0x09,  # DBCLOSE
            0x0A,  # DBOPEN
            0x15,  # DBEXECUTEDYN
            0x29,  # GLOBFUNCCALL
            0x2C,  # DOTFUNCCALL
            0x32,  # PUSH_CONST_INT
            0x40,  # CNV_INT_TO_ULONG
            0xFF,  # DECR_LONG
        }
        
        while i < min(len(data), 10):
            if data[i] in VALID_OPCODES:
                valid_opcodes += 1
            i += 1
        
        # If we have several valid opcodes, it's likely P-code
        return valid_opcodes >= 3
    
    @classmethod
    def _verify_pcode_context(cls, data: bytes, offset: int) -> bool:
        """Verify that the context around offset looks like P-code."""
        # Check bytes before and after
        start = max(0, offset - 4)
        end = min(len(data), offset + 20)
        
        context = data[start:end]
        
        # Count non-printable bytes (P-code has many)
        non_printable = sum(1 for b in context if b < 32 or b > 126)
        
        # P-code should have significant non-printable content
        return non_printable > len(context) * 0.5
    
    @classmethod
    def _find_text_to_binary_transition(cls, data: bytes) -> int:
        """Find where text/metadata ends and binary P-code begins."""
        # Look for runs of printable ASCII followed by binary data
        
        in_text = True
        text_run = 0
        binary_run = 0
        
        for i in range(len(data)):
            if 32 <= data[i] <= 126 or data[i] in [9, 10, 13]:  # Printable or whitespace
                if in_text:
                    text_run += 1
                else:
                    # Transition from binary back to text
                    if binary_run < 4:
                        # Short binary run, probably still in text
                        in_text = True
                        text_run = 1
                        binary_run = 0
            else:
                # Non-printable
                if in_text and text_run > 20:
                    # We've had a good run of text, now hitting binary
                    in_text = False
                    binary_run = 1
                    
                    # Check if this looks like P-code start
                    if cls._looks_like_pcode(data[i:i+20]):
                        return i
                elif not in_text:
                    binary_run += 1
        
        return -1
    
    @classmethod
    def find_pcode_section(cls, data: bytes, object_type: str = 'function') -> Tuple[int, int]:
        """Main entry point for P-code detection.
        
        Args:
            data: Raw object data
            object_type: Type of object (function, window, etc.)
            
        Returns:
            Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        if object_type == 'function':
            return cls.find_pcode_in_function(data)
        else:
            # For other types, fall back to original detector
            from .pcode_detector import PCodeDetector
            return PCodeDetector.find_pcode_section(data)
    
    @classmethod
    def _find_pcode_end(cls, data: bytes, start_offset: int) -> int:
        """Find the end of executable P-code.
        
        Args:
            data: Full data buffer
            start_offset: Where P-code starts
            
        Returns:
            Offset where P-code ends
        """
        # Start scanning from P-code start
        i = start_offset
        consecutive_returns = 0
        consecutive_nulls = 0
        consecutive_ff = 0
        last_valid_offset = start_offset
        
        while i < len(data):
            opcode = data[i] if i < len(data) else 0
            
            # Check for multiple RETURNs
            if opcode == 0x00:  # RETURN
                consecutive_returns += 1
                if consecutive_returns >= 3:
                    # Three or more RETURNs in a row - likely end of code
                    logger.debug(f"Found {consecutive_returns} consecutive RETURNs at {i:04X}")
                    return last_valid_offset + 1
            else:
                if consecutive_returns > 0:
                    # Reset counter but remember we had RETURNs
                    last_valid_offset = i - 1
                consecutive_returns = 0
            
            # Check for padding patterns
            if opcode == 0x00:
                consecutive_nulls += 1
            else:
                consecutive_nulls = 0
                
            if opcode == 0xFF:
                consecutive_ff += 1
            else:
                consecutive_ff = 0
            
            # If we see long runs of padding, we're past code
            if consecutive_nulls >= 8 or consecutive_ff >= 8:
                logger.debug(f"Found padding at {i:04X}")
                return last_valid_offset + 1
            
            # Try to decode instruction to advance properly
            # This is a simplified check - just advance by 1 for now
            # In a real implementation, we'd decode the full instruction
            i += 1
            
            # Update last valid position if this looks like real code
            if opcode != 0x00 and opcode != 0xFF:
                last_valid_offset = i
        
        # If we reached end of data, return full length
        return len(data)