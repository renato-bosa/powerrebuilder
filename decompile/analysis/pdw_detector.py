"""PDW (Compiled PowerBuilder DataWindow) format detection and information extraction."""

import logging
import struct
from typing import Any
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)

# Known PDW signatures
PDW_SIGNATURES = {
    b"PDW600": "PowerBuilder 6.0", b"PDW700": "PowerBuilder 7.0", b"PDW800": "PowerBuilder 8.0", b"PDW900": "PowerBuilder 9.0", b"PDW1000": "PowerBuilder 10.0", b"PDW1050": "PowerBuilder 10.5", b"PDW1100": "PowerBuilder 11.0", b"PDW1150": "PowerBuilder 11.5", b"PDW1200": "PowerBuilder 12.0", b"PDW1250": "PowerBuilder 12.5", b"PDW1260": "PowerBuilder 12.6", b"PDW1700": "PowerBuilder 17.0", b"PDW1900": "PowerBuilder 19.0", b"PDW2100": "PowerBuilder 21.0", b"PDW2200": "PowerBuilder 22.0", }

class PDWInfo:
    """Information about a compiled PDW file."""
    
    def __init__(self) -> None:
        
    
        self.version: str | None = None
        self.signature: bytes | None = None
        self.is_compiled: bool = False
        self.file_size: int = 0
        self.metadata: dict[str, Any] = {}

def detect_pdw_format(data: bytes, filename: str = "") -> PDWInfo:


    
    

    """Detect if data is a compiled PDW format DataWindow.
    
    Args:
        data: Raw binary data
        filename: Optional filename for logging
        
    Returns:
        PDWInfo object with detection results
    """
    info = PDWInfo()
    info.file_size = len(data)
    
    if len(data) < 8:
        return info
    
    # Check for PDW signatures
    header = data[:8]
    for sig, version in PDW_SIGNATURES.items():
        if header.startswith(sig):
            info.is_compiled = True
            info.signature = sig
            info.version = version
            logger.info(f"{filename} is a compiled PDW format ({version})")
            
            # Try to extract additional metadata
            _extract_pdw_metadata(data, info)
            return info
    
    # Check for older PDW formats that might not have clear signatures
    if header.startswith(b"PDW"):
        info.is_compiled = True
        info.signature = header[:7].rstrip(b'\x00')
        info.version = f"Unknown PDW version ({info.signature.decode('ascii', errors='ignore')})"
        logger.info(f"{filename} appears to be compiled PDW format (unknown version)")
        return info
    
    return info

def _extract_pdw_metadata(data: bytes, info: PDWInfo) -> None:


    

    """Extract metadata from PDW file if possible."""
    try:
        # PDW files typically have some structure we can parse
        # Offset 0x08-0x0B: Often contains a size/count field
        if len(data) >= 12:
            # Try to read what might be object count or size
            value1 = struct.unpack("<I", data[8:12])[0]
            if 0 < value1 < 100000:  # Reasonable bounds
                info.metadata["field_0x08"] = value1
        
        # Look for embedded strings (often object names)
        # PDW files sometimes contain the original DWO name
        pdw_idx = data.find(b"pdw")
        if pdw_idx > 0 and pdw_idx < 100:
            # There might be a name nearby
            info.metadata["has_pdw_marker"] = True
            
        # Check for common PowerBuilder strings
        pb_strings = [b"release", b"datawindow", b"column", b"table"]
        for pb_str in pb_strings:
            if pb_str in data:
                info.metadata[f"contains_{pb_str.decode()}"] = True
                
    except Exception as e:
        logger.debug(f"Error extracting PDW metadata: {e}")

def log_pdw_warning(filename: str, info: PDWInfo) -> None:


    

    """Log a warning about compiled PDW format."""
    msg = (
        f"{filename} is a compiled PowerBuilder DataWindow ({info.version}). "
        "While we can extract SQL, columns, and layout information, "
        "the complete source code cannot be fully reconstructed. "
        "Original .srd or .dwo source file would provide more complete information."
    )
    logger.info(msg)  # Changed to info since we can now extract useful data
    
    if info.metadata:
        logger.debug(f"PDW metadata for {filename}: {info.metadata}")

def can_extract_from_pdw(info: PDWInfo) -> bool:


    
    

    """Check if we can extract any useful information from PDW.
    
    We can now extract:
    - SQL queries
    - Column definitions with properties
    - Layout information (coordinates, sizes)
    - Display properties (fonts, colors, alignment)
    - DataWindow metadata
    """
    return info.is_compiled  # We can extract from compiled PDW files