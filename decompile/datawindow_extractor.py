"""DataWindow syntax extractor following PbdViewer's approach."""

import struct
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class DataWindowExtractor:
    """Extract DataWindow syntax from binary .dwo objects."""
    
    @staticmethod
    def extract_syntax(data: bytes) -> Optional[str]:
        """Extract DataWindow syntax from binary data.
        
        Args:
            data: Raw binary data of the DataWindow object
            
        Returns:
            Extracted DataWindow syntax as string, or None if extraction fails
        """
        # Look for PBSELECT or other DataWindow markers in UTF-16
        markers = [
            b'P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00',  # PBSELECT
            b'r\x00e\x00l\x00e\x00a\x00s\x00e\x00',      # release
            b'd\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00',  # datawindow
        ]
        
        syntax_pos = -1
        for marker in markers:
            pos = data.find(marker)
            if pos >= 0:
                syntax_pos = pos
                logger.debug(f"Found DataWindow marker at offset 0x{pos:x}")
                break
        
        if syntax_pos < 0:
            logger.debug("No DataWindow syntax markers found")
            return None
        
        # Method 1: Look for length field before the syntax
        best_result = DataWindowExtractor._extract_with_length_field(data, syntax_pos)
        if best_result:
            return best_result
        
        # Method 2: Extract from marker to end of valid UTF-16 text
        return DataWindowExtractor._extract_to_end(data, syntax_pos)
    
    @staticmethod
    def _extract_with_length_field(data: bytes, syntax_pos: int) -> Optional[str]:
        """Try to extract using a length field before the syntax."""
        # Search backwards for a potential length field
        search_start = max(0, syntax_pos - 100)
        
        for offset in range(search_start, syntax_pos, 4):
            if offset + 4 > len(data):
                continue
                
            potential_length = struct.unpack('<I', data[offset:offset+4])[0]
            
            # Validate the length
            if potential_length < 20 or potential_length > len(data) - offset - 4:
                continue
            
            syntax_start = offset + 4
            syntax_end = syntax_start + potential_length
            
            # Check if this range includes our marker
            if syntax_start > syntax_pos or syntax_end < syntax_pos + 10:
                continue
            
            # Try to decode
            try:
                syntax_data = data[syntax_start:syntax_end]
                decoded = syntax_data.decode('utf-16-le', errors='strict')
                
                # Validate the decoded text
                if DataWindowExtractor._is_valid_datawindow_syntax(decoded):
                    logger.debug(f"Found valid syntax with length field at 0x{offset:x}")
                    return decoded.strip('\x00')
            except UnicodeDecodeError:
                continue
        
        return None
    
    @staticmethod
    def _extract_to_end(data: bytes, syntax_pos: int) -> Optional[str]:
        """Extract from syntax position to end of valid UTF-16 text."""
        # Start from the syntax position
        current_pos = syntax_pos
        
        # Find the end of the UTF-16 text
        while current_pos < len(data) - 2:
            # Check for double null (end of string)
            if data[current_pos:current_pos+4] == b'\x00\x00\x00\x00':
                break
            
            # Check if next two bytes can be decoded as UTF-16
            try:
                char = data[current_pos:current_pos+2].decode('utf-16-le', errors='strict')
                # Only accept printable characters and whitespace
                if ord(char) < 32 and char not in '\r\n\t':
                    break
                current_pos += 2
            except UnicodeDecodeError:
                break
        
        # Extract and decode
        try:
            syntax_data = data[syntax_pos:current_pos]
            decoded = syntax_data.decode('utf-16-le', errors='ignore')
            
            if DataWindowExtractor._is_valid_datawindow_syntax(decoded):
                return decoded.strip('\x00')
        except Exception as e:
            logger.debug(f"Failed to decode syntax: {e}")
        
        return None
    
    @staticmethod
    def _is_valid_datawindow_syntax(text: str) -> bool:
        """Check if the text looks like valid DataWindow syntax."""
        if not text or len(text) < 10:
            return False
        
        # Check for common DataWindow keywords
        keywords = ['PBSELECT', 'release', 'datawindow', 'TABLE', 'COLUMN']
        if not any(kw in text for kw in keywords):
            return False
        
        # Basic validation - should have balanced parentheses
        if text.count('(') != text.count(')'):
            # Allow for truncation at the end
            if text.count('(') - text.count(')') > 2:
                return False
        
        # Should not have too many non-ASCII characters (indicates corruption)
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if non_ascii > len(text) * 0.1:  # More than 10% non-ASCII
            return False
        
        return True


def extract_datawindow_from_pbd(data: bytes, object_name: str) -> Optional[str]:
    """Extract DataWindow syntax from PBD object data.
    
    Args:
        data: Raw bytes of the DataWindow object from PBD
        object_name: Name of the DataWindow object (for logging)
        
    Returns:
        DataWindow syntax as string, or None if not a DataWindow
    """
    # Check if this is a DataWindow (DAT* header)
    if not data.startswith(b'DAT*'):
        logger.debug(f"{object_name} does not have DAT* header")
        return None
    
    logger.info(f"Extracting DataWindow syntax from {object_name}")
    
    # Use the extractor
    syntax = DataWindowExtractor.extract_syntax(data)
    
    if syntax:
        logger.info(f"Successfully extracted {len(syntax)} characters from {object_name}")
    else:
        logger.warning(f"Failed to extract syntax from {object_name}")
    
    return syntax