"""Enhanced entry parsing with robust error recovery and detailed logging.

This module provides improved entry parsing capabilities with:
- Better error recovery for corrupted entries
- Detailed hex dump logging for debugging
- Format version detection
- Recovery strategies for common corruption patterns
"""

import struct
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass

from extract.pbd.utils.binary_utils import binary_to_time
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET

if TYPE_CHECKING:
    from extract.pbd.structures.entry import PbEntryDefinition

logger = logging.getLogger(__name__)


@dataclass
class EntryParseResult:
    """Result of entry parsing attempt."""
    entry: 'PbEntryDefinition' | None
    error: str | None
    hex_dump: str | None
    recovery_attempted: bool = False
    partial_data: dict | None = None


class EnhancedEntryParser:
    """Enhanced entry parser with better error recovery."""
    
    # Known format variations
    FORMAT_VARIATIONS = {
        'standard_ascii': {
            'signature': b'ENT*', 'fixed_size': 24, 'name_offset': 22, 'name_size': 2
        }, 'standard_unicode': {
            'signature': b'E\x00N\x00T\x00*\x00', 'fixed_size': 48, 'name_offset': 44, 'name_size': 4
        }, 'mixed_mode': {
            'signature': b'ENT*', # ASCII sig with Unicode data
            'fixed_size': 28, 'version_encoding': 'utf-16-le'
        }
    }
    
    def __init__(self, enable_recovery: bool = True) -> None:

    
        """Initialize enhanced parser.
        
        Args:
            enable_recovery: Whether to attempt recovery strategies
        """
        self.enable_recovery = enable_recovery
        self.parse_attempts = 0
        self.recovered_entries = 0
    
    def parse_entry_with_recovery(self, data: bytes, offset: int = 0, context: str | None = None) -> EntryParseResult:

    
        
    
        """Parse entry with multiple recovery strategies.
        
        Args:
            data: Raw entry data
            offset: Offset within file (for logging)
            context: Additional context (e.g., "entry 37 in dcm_detailobjects.pbd")
            
        Returns:
            EntryParseResult with parsed entry or error details
        """
        self.parse_attempts += 1
        context_str = f" ({context})" if context else ""
        
        # Generate hex dump for debugging
        hex_dump = self._generate_hex_dump(data[:min(256, len(data))])
        
        # Try standard parsing first
        result = self._try_standard_parse(data, offset)
        if result.entry:
            logger.debug(f"Successfully parsed entry at offset {offset}{context_str}")
            return result
        
        # Log initial failure with hex dump
        logger.warning(
            f"Standard parse failed at offset {offset}{context_str}. "
            f"Error: {result.error}\nHex dump:\n{hex_dump}"
        )
        
        if not self.enable_recovery:
            return EntryParseResult(None, result.error, hex_dump)
        
        # Try recovery strategies
        logger.info(f"Attempting recovery strategies for entry at offset {offset}{context_str}")
        
        # Strategy 1: Detect format variation
        detected_format = self._detect_format(data)
        if detected_format:
            logger.info(f"Detected format: {detected_format}")
            result = self._parse_with_format(data, detected_format, offset)
            if result.entry:
                self.recovered_entries += 1
                result.recovery_attempted = True
                logger.info(f"Recovery successful using format {detected_format}")
                return result
        
        # Strategy 2: Try partial extraction
        if len(data) >= 24:  # Minimum for any format
            partial_result = self._extract_partial_info(data, offset)
            if partial_result.partial_data:
                logger.info(
                    f"Partial extraction successful at offset {offset}{context_str}. "
                    f"Extracted: {partial_result.partial_data}"
                )
                return partial_result
        
        # Strategy 3: Scan for next valid entry
        next_entry_offset = self._find_next_entry_signature(data)
        if next_entry_offset > 0:
            logger.info(
                f"Found next valid entry signature at offset {offset + next_entry_offset}. "
                f"Current entry appears corrupted."
            )
            return EntryParseResult(
                None, f"Corrupted entry, next valid entry at +{next_entry_offset}", hex_dump, recovery_attempted=True
            )
        
        # All strategies failed
        return EntryParseResult(
            None, "All recovery strategies failed", hex_dump, recovery_attempted=True
        )
    
    def _try_standard_parse(self, data: bytes, offset: int) -> EntryParseResult:

    
        
    
        """Try standard entry parsing."""
        try:
            # Check for Unicode signature
            if data.startswith(b'E\x00N\x00T\x00*\x00'):
                return self._parse_unicode_entry(data, offset)
            elif data.startswith(b'ENT*'):
                # Could be ASCII or mixed mode
                if len(data) >= 12 and b'\x00' in data[4:12]:
                    return self._parse_mixed_mode_entry(data, offset)
                else:
                    return self._parse_ascii_entry(data, offset)
            else:
                return EntryParseResult(None, "No valid ENT* signature found", None)
        except Exception as e:
            return EntryParseResult(None, f"Parse exception: {str(e)}", None)
    
    def _parse_ascii_entry(self, data: bytes, offset: int) -> EntryParseResult:

    
        
    
        """Parse standard ASCII entry."""
        try:
            if len(data) < 24:
                return EntryParseResult(None, "Insufficient data for ASCII entry", None)
            
            # Parse fixed header
            sig, version, data_offset, data_size, timestamp, comment_len, name_len = struct.unpack(
                '<4s8sIIIHH', data[:24]
            )
            
            # Validate
            if sig != b'ENT*':
                return EntryParseResult(None, f"Invalid signature: {sig}", None)
            
            # Parse name
            name_start = 24 + comment_len
            if name_start + name_len > len(data):
                return EntryParseResult(
                    None, f"Name extends beyond data (need {name_start + name_len}, have {len(data)})", None
                )
            
            name_bytes = data[name_start:name_start + name_len]
            obj_name = name_bytes.decode('ascii', errors='replace').rstrip('\x00')
            
            # Convert version
            version_str = version.decode('ascii', errors='replace').rstrip('\x00')
            
            # Convert timestamp
            mod_time = binary_to_time(struct.pack('<I', timestamp))
            
            # Import locally to avoid circular dependency
            from extract.pbd.structures.entry import PbEntryDefinition
            entry = PbEntryDefinition(
                objectname=obj_name, version=version_str, offset=data_offset, objectsize=data_size, moddatetime=mod_time, commentlen=comment_len, objnamelen=name_len
            )
            
            return EntryParseResult(entry, None, None)
            
        except Exception as e:
            return EntryParseResult(None, f"ASCII parse error: {str(e)}", None)
    
    def _parse_unicode_entry(self, data: bytes, offset: int) -> EntryParseResult:

    
        
    
        """Parse Unicode entry."""
        try:
            if len(data) < 48:
                return EntryParseResult(None, "Insufficient data for Unicode entry", None)
            
            # Parse fixed header - note the 64-bit offset
            sig = data[:8]
            version = data[8:16]
            data_offset = struct.unpack('<Q', data[16:24])[0]  # 64-bit
            data_size = struct.unpack('<Q', data[24:32])[0]    # 64-bit
            timestamp = struct.unpack('<I', data[32:36])[0]
            comment_len = struct.unpack('<I', data[36:40])[0]
            zero_field = struct.unpack('<I', data[40:44])[0]
            name_len = struct.unpack('<I', data[44:48])[0]
            
            # Validate
            if sig != b'E\x00N\x00T\x00*\x00':
                return EntryParseResult(None, f"Invalid Unicode signature", None)
            
            # Parse name (Unicode)
            name_start = 48 + comment_len * 2  # Unicode chars
            name_bytes_len = name_len * 2
            
            if name_start + name_bytes_len > len(data):
                return EntryParseResult(
                    None, f"Unicode name extends beyond data (need {name_start + name_bytes_len}, have {len(data)})", None
                )
            
            name_bytes = data[name_start:name_start + name_bytes_len]
            obj_name = name_bytes.decode('utf-16-le', errors='replace').rstrip('\x00')
            
            # Convert version
            version_str = version.decode('utf-16-le', errors='replace').rstrip('\x00')
            
            # Convert timestamp
            mod_time = binary_to_time(struct.pack('<I', timestamp))
            
            # Import locally to avoid circular dependency
            from extract.pbd.structures.entry import PbEntryDefinition
            entry = PbEntryDefinition(
                objectname=obj_name, version=version_str, offset=data_offset, objectsize=data_size, moddatetime=mod_time, commentlen=comment_len, objnamelen=name_len
            )
            
            return EntryParseResult(entry, None, None)
            
        except Exception as e:
            return EntryParseResult(None, f"Unicode parse error: {str(e)}", None)
    
    def _parse_mixed_mode_entry(self, data: bytes, offset: int) -> EntryParseResult:

    
        
    
        """Parse mixed mode entry (ASCII sig, Unicode data)."""
        try:
            if len(data) < 28:
                return EntryParseResult(None, "Insufficient data for mixed mode entry", None)
            
            # Parse header
            sig = data[:4]
            version = data[4:12]  # Unicode version
            data_offset, data_size, timestamp, comment_len, name_len = struct.unpack(
                '<IIIHH', data[12:28]
            )
            
            # Validate
            if sig != b'ENT*':
                return EntryParseResult(None, f"Invalid signature", None)
            
            # Parse name (bytes already)
            name_start = 28 + comment_len
            if name_start + name_len > len(data):
                # Try partial extraction
                name_bytes = data[name_start:]
                obj_name = name_bytes.decode('utf-16-le', errors='replace').rstrip('\x00')
                logger.warning(f"Truncated name extracted: {obj_name}")
            else:
                name_bytes = data[name_start:name_start + name_len]
                obj_name = name_bytes.decode('utf-16-le', errors='replace').rstrip('\x00')
            
            # Convert version
            version_str = version.decode('utf-16-le', errors='replace').rstrip('\x00')
            
            # Convert timestamp
            mod_time = binary_to_time(struct.pack('<I', timestamp))
            
            # Import locally to avoid circular dependency
            from extract.pbd.structures.entry import PbEntryDefinition
            entry = PbEntryDefinition(
                objectname=obj_name, version=version_str, offset=data_offset, objectsize=data_size, moddatetime=mod_time, commentlen=comment_len, objnamelen=name_len // 2  # Convert to char count
            )
            
            return EntryParseResult(entry, None, None)
            
        except Exception as e:
            return EntryParseResult(None, f"Mixed mode parse error: {str(e)}", None)
    
    def _detect_format(self, data: bytes) -> str | None:

    
        
    
        """Detect entry format from data patterns."""
        if len(data) < 8:
            return None
        
        # Check Unicode signature
        if data[:8] == b'E\x00N\x00T\x00*\x00':
            return 'unicode'
        
        # Check ASCII signature
        if data[:4] == b'ENT*':
            # Check if version field has nulls (Unicode)
            if len(data) >= 12 and b'\x00' in data[4:12]:
                return 'mixed_mode'
            else:
                return 'ascii'
        
        # Check for offset patterns (entry might be misaligned)
        for i in range(min(16, len(data) - 8)):
            if data[i:i+4] == b'ENT*':
                logger.info(f"Found ENT* signature at offset {i}")
                return 'misaligned'
        
        return None
    
    def _extract_partial_info(self, data: bytes, offset: int) -> EntryParseResult:

    
        
    
        """Extract whatever information we can from corrupted entry."""
        partial = {}
        hex_dump = self._generate_hex_dump(data[:min(128, len(data))])
        
        try:
            # Look for patterns
            # Try to find object name (usually ends with .xxx extension)
            import re
            
            # Look for file extensions in various encodings
            ascii_match = re.search(rb'[\x20-\x7e]+\.(dwo|sru|srw|srd|srm|srf)', data)
            if ascii_match:
                partial['possible_name_ascii'] = ascii_match.group(0).decode('ascii', errors='replace')
            
            # Look for Unicode patterns
            unicode_match = re.search(rb'([\x20-\x7e]\x00)+\.([dws][wr][oum]\x00)', data)
            if unicode_match:
                try:
                    name = unicode_match.group(0).decode('utf-16-le', errors='replace')
                    partial['possible_name_unicode'] = name
                except Exception as e:
                    logger.debug("Exception caught: %s", e)
            
            # Try to extract any valid looking offsets/sizes
            if len(data) >= 24:
                # Try different offset positions
                for pos in [12, 16, 20]:
                    if pos + 4 <= len(data):
                        val = struct.unpack('<I', data[pos:pos+4])[0]
                        if 0 < val < 0x10000000:  # Reasonable file offset
                            partial[f'possible_offset_at_{pos}'] = val
            
            if partial:
                return EntryParseResult(
                    None, "Partial extraction successful", hex_dump, recovery_attempted=True, partial_data=partial
                )
            
        except Exception as e:
            logger.debug(f"Partial extraction error: {e}")
        
        return EntryParseResult(
            None, "No partial data could be extracted", hex_dump, recovery_attempted=True
        )
    
    def _find_next_entry_signature(self, data: bytes, start: int = 0) -> int:

    
        
    
        """Find the next valid entry signature."""
        # Look for both ASCII and Unicode signatures
        signatures = [b'ENT*', b'E\x00N\x00T\x00*\x00']
        
        min_offset = len(data)
        for sig in signatures:
            offset = data.find(sig, start)
            if offset >= 0 and offset < min_offset:
                min_offset = offset
        
        return min_offset if min_offset < len(data) else -1
    
    def _generate_hex_dump(self, data: bytes) -> str:

    
        
    
        """Generate formatted hex dump for debugging."""
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{i:08x}: {hex_part:<48} {ascii_part}")
        return '\n'.join(lines)
    
    def _parse_with_format(self, data: bytes, format_name: str, offset: int) -> EntryParseResult:

    
        
    
        """Parse entry with specific format."""
        if format_name == 'unicode':
            return self._parse_unicode_entry(data, offset)
        elif format_name == 'ascii':
            return self._parse_ascii_entry(data, offset)
        elif format_name == 'mixed_mode':
            return self._parse_mixed_mode_entry(data, offset)
        elif format_name == 'misaligned':
            # Find the actual start
            sig_offset = data.find(b'ENT*')
            if sig_offset >= 0:
                logger.info(f"Attempting parse from misaligned offset {sig_offset}")
                return self._try_standard_parse(data[sig_offset:], offset + sig_offset)
        
        return EntryParseResult(None, f"Unknown format: {format_name}", None)
    
    def get_statistics(self) -> dict:

    
        
    
        """Get parser statistics."""
        return {
            'parse_attempts': self.parse_attempts, 'recovered_entries': self.recovered_entries, 'recovery_rate': (self.recovered_entries / self.parse_attempts * 100) 
                            if self.parse_attempts > 0 else 0
        }