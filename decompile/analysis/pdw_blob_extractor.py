"""PDW Binary Blob Extractor.

This module extracts binary blob data (images, PDFs, etc.) from compiled PowerBuilder DataWindow files.
It identifies and extracts embedded binary content that may be stored in PDW files.
"""

import logging
import struct
from typing import Any
from dataclasses import dataclass
from enum import Enum
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET

logger = logging.getLogger(__name__)


class BlobType(Enum):
    """Known blob types based on magic bytes."""
    JPEG = (b'\xFF\xD8\xFF', 'jpg')
    PNG = (b'\x89PNG\r\n\x1a\n', 'png')
    GIF = (b'GIF87a', 'gif')
    GIF89 = (b'GIF89a', 'gif')
    BMP = (b'BM', 'bmp')
    PDF = (b'%PDF', 'pdf')
    TIFF = (b'II*\x00', 'tiff')  # Little-endian
    TIFF_BE = (b'MM\x00*', 'tiff')  # Big-endian
    ICO = (b'\x00\x00\x01\x00', 'ico')
    ZIP = (b'PK\x03\x04', 'zip')
    OLE = (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', 'ole')  # OLE/Office docs
    UNKNOWN = (b'', 'bin')


@dataclass
class ExtractedBlob:
    """Represents an extracted binary blob."""
    offset: int
    size: int
    blob_type: BlobType
    data: bytes
    metadata: dict[str, Any] = None
    
    def __post_init__(self) -> None:
        
    
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def extension(self) -> str:

        
        """Get file extension for this blob type."""
        return self.blob_type.value[1]
    
    @property
    def magic_bytes(self) -> bytes:

        
        """Get magic bytes for this blob type."""
        return self.blob_type.value[0]


class PDWBlobExtractor:
    """Extract binary blob data from PDW files."""
    
    # Maximum reasonable blob size (100MB)
    MAX_BLOB_SIZE = 100 * 1024 * 1024
    
    # Minimum blob size to consider (1KB)
    MIN_BLOB_SIZE = 1024
    
    @classmethod
    def extract_blobs(cls, data: bytes, object_name: str = "") -> list[ExtractedBlob]:

        
        """Extract all binary blobs from PDW data.
        
        Args:
            data: Raw PDW file data
            object_name: Name of the DataWindow object for logging
            
        Returns:
            List of extracted blobs
        """
        logger.info(f"Extracting binary blobs from PDW file: {object_name}")
        
        blobs = []
        
        # Strategy 1: Look for known magic bytes
        magic_blobs = cls._extract_by_magic_bytes(data)
        blobs.extend(magic_blobs)
        
        # Strategy 2: Look for binary data regions with size headers
        size_blobs = cls._extract_by_size_headers(data)
        blobs.extend(size_blobs)
        
        # Strategy 3: Look for OLE embedded objects
        ole_blobs = cls._extract_ole_objects(data)
        blobs.extend(ole_blobs)
        
        # Remove duplicates (same offset)
        unique_blobs = cls._deduplicate_blobs(blobs)
        
        logger.info(f"Extracted {len(unique_blobs)} unique blobs from {object_name}")
        return unique_blobs
    
    @classmethod
    def _extract_by_magic_bytes(cls, data: bytes) -> list[ExtractedBlob]:

        
        """Extract blobs by searching for known file magic bytes."""
        blobs = []
        
        for blob_type in BlobType:
            if blob_type == BlobType.UNKNOWN:
                continue
                
            magic = blob_type.value[0]
            if not magic:
                continue
            
            # Search for all occurrences of magic bytes
            offset = 0
            while offset < len(data):
                idx = data.find(magic, offset)
                if idx == -1:
                    break
                
                # Try to determine blob size
                blob_size = cls._determine_blob_size(data, idx, blob_type)
                
                if blob_size and cls.MIN_BLOB_SIZE <= blob_size <= cls.MAX_BLOB_SIZE:
                    # Extract the blob data
                    blob_data = data[idx:idx + blob_size]
                    
                    # Verify it's a valid blob
                    if cls._verify_blob(blob_data, blob_type):
                        blob = ExtractedBlob(
                            offset=idx, size=blob_size, blob_type=blob_type, data=blob_data, metadata={'method': 'magic_bytes'}
                        )
                        blobs.append(blob)
                        logger.debug(f"Found {blob_type.name} blob at offset 0x{idx:08X}, size: {blob_size}")
                
                offset = idx + 1
        
        return blobs
    
    @classmethod
    def _extract_by_size_headers(cls, data: bytes) -> list[ExtractedBlob]:

        
        """Extract blobs that have size headers (common in PDW format)."""
        blobs = []
        
        # Look for patterns like: [4-byte size][blob data]
        # Common at specific offsets in PDW files
        possible_offsets = [
            0x1000, # Common blob start offset
            0x2000, 0x4000, 0x8000, ]
        
        # Also scan for size patterns throughout the file
        offset = 0x100  # Skip header
        while offset < len(data) - 8:
            # Try reading as little-endian 32-bit size
            try:
                size = struct.unpack('<I', data[offset:offset+4])[0]
                
                # Check if size is reasonable and data is available
                if cls.MIN_BLOB_SIZE <= size <= cls.MAX_BLOB_SIZE and offset + 4 + size <= len(data):
                    # Look for blob data after size
                    blob_start = offset + 4
                    blob_data = data[blob_start:blob_start + size]
                    
                    # Try to identify blob type
                    blob_type = cls._identify_blob_type(blob_data)
                    
                    if blob_type != BlobType.UNKNOWN:
                        blob = ExtractedBlob(
                            offset=blob_start, size=size, blob_type=blob_type, data=blob_data, metadata={
                                'method': 'size_header', 'size_offset': offset
                            }
                        )
                        blobs.append(blob)
                        logger.debug(f"Found {blob_type.name} blob with size header at 0x{offset:08X}, size: {size}")
                        offset = blob_start + size  # Skip past this blob
                        continue
            except struct.error:
                pass
            
            offset += 4  # Move to next potential size header
        
        return blobs
    
    @classmethod
    def _extract_ole_objects(cls, data: bytes) -> list[ExtractedBlob]:

        
        """Extract OLE embedded objects."""
        blobs = []
        
        # OLE objects have a specific header
        ole_header = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
        
        offset = 0
        while offset < len(data):
            idx = data.find(ole_header, offset)
            if idx == -1:
                break
            
            # OLE files have their size information in the header
            if idx + 512 <= len(data):  # OLE header is at least 512 bytes
                # Try to parse OLE header to get size
                ole_size = cls._parse_ole_size(data[idx:])
                
                if ole_size and cls.MIN_BLOB_SIZE <= ole_size <= cls.MAX_BLOB_SIZE:
                    blob_data = data[idx:idx + ole_size]
                    
                    blob = ExtractedBlob(
                        offset=idx, size=ole_size, blob_type=BlobType.OLE, data=blob_data, metadata={
                            'method': 'ole_object', 'ole_type': cls._identify_ole_type(blob_data)
                        }
                    )
                    blobs.append(blob)
                    logger.debug(f"Found OLE object at offset 0x{idx:08X}, size: {ole_size}")
            
            offset = idx + 1
        
        return blobs
    
    @classmethod
    def _determine_blob_size(cls, data: bytes, offset: int, blob_type: BlobType) -> int | None:

        
        """Determine the size of a blob based on its type and content."""
        remaining = len(data) - offset
        
        if blob_type in [BlobType.JPEG, BlobType.PNG, BlobType.GIF, BlobType.GIF89]:
            # These formats have end markers we can search for
            if blob_type == BlobType.JPEG:
                # JPEG ends with FFD9
                end_marker = b'\xFF\xD9'
                end_idx = data.find(end_marker, offset + 2)
                if end_idx != -1:
                    return end_idx + 2 - offset
            
            elif blob_type == BlobType.PNG:
                # PNG ends with IEND chunk
                end_marker = b'IEND\xAE\x42\x60\x82'
                end_idx = data.find(end_marker, offset + 8)
                if end_idx != -1:
                    return end_idx + 8 - offset
            
            elif blob_type in [BlobType.GIF, BlobType.GIF89]:
                # GIF ends with 3B
                end_marker = b'\x00\x3B'
                end_idx = data.find(end_marker, offset + 6)
                if end_idx != -1:
                    return end_idx + 2 - offset
        
        elif blob_type == BlobType.BMP:
            # BMP has size in header
            if remaining >= 18:
                try:
                    file_size = struct.unpack('<I', data[offset+2:offset+6])[0]
                    if 0 < file_size <= remaining:
                        return file_size
                except struct.error:
                    pass
        
        elif blob_type == BlobType.PDF:
            # PDF ends with %%EOF
            end_marker = b'%%EOF'
            end_idx = data.find(end_marker, offset + 4)
            if end_idx != -1:
                # Include some padding after %%EOF
                return end_idx + len(end_marker) + 10 - offset
        
        # Default: scan for next magic bytes or null region
        return cls._scan_for_blob_end(data, offset)
    
    @classmethod
    def _scan_for_blob_end(cls, data: bytes, offset: int) -> int | None:

        
        """Scan for the likely end of a blob by looking for patterns."""
        # Look for regions of nulls or other magic bytes
        scan_offset = offset + cls.MIN_BLOB_SIZE
        
        while scan_offset < min(offset + cls.MAX_BLOB_SIZE, len(data)):
            # Check for null region (likely padding between blobs)
            if data[scan_offset:scan_offset+16] == b'\x00' * 16:
                return scan_offset - offset
            
            # Check for other magic bytes
            for blob_type in BlobType:
                if blob_type != BlobType.UNKNOWN:
                    magic = blob_type.value[0]
                    if magic and data[scan_offset:scan_offset+len(magic)] == magic:
                        return scan_offset - offset
            
            scan_offset += 1
        
        return None
    
    @classmethod
    def _verify_blob(cls, data: bytes, blob_type: BlobType) -> bool:

        
        """Verify that extracted data is a valid blob of the given type."""
        if len(data) < cls.MIN_BLOB_SIZE:
            return False
        
        # Basic verification - check magic bytes still match
        magic = blob_type.value[0]
        if not data.startswith(magic):
            return False
        
        # Type-specific verification
        if blob_type == BlobType.JPEG:
            # JPEG should have JFIF or Exif marker
            return b'JFIF' in data[:20] or b'Exif' in data[:20]
        
        elif blob_type == BlobType.PNG:
            # PNG should have IHDR chunk
            return b'IHDR' in data[:20]
        
        elif blob_type == BlobType.PDF:
            # PDF should have version like %PDF-1.x
            return data[:8].startswith(b'%PDF-')
        
        # For other types, basic magic byte check is sufficient
        return True
    
    @classmethod
    def _identify_blob_type(cls, data: bytes) -> BlobType:

        
        """Identify blob type from data content."""
        if not data:
            return BlobType.UNKNOWN
        
        # Check each known type
        for blob_type in BlobType:
            if blob_type == BlobType.UNKNOWN:
                continue
            
            magic = blob_type.value[0]
            if magic and data.startswith(magic):
                return blob_type
        
        return BlobType.UNKNOWN
    
    @classmethod
    def _parse_ole_size(cls, data: bytes) -> int | None:

        
        """Parse OLE header to determine object size."""
        if len(data) < 512:
            return None
        
        try:
            # OLE files use FAT-like structure
            # This is simplified - real OLE parsing is complex
            # For now, scan for end of OLE data
            ole_end_patterns = [
                b'\x00' * 512, # Large null region
                b'Microsoft', # Often followed by padding
            ]
            
            for pattern in ole_end_patterns:
                idx = data.find(pattern, 512)
                if idx != -1:
                    return idx
            
            # Default to a reasonable size
            return min(len(data), 1024 * 1024)  # Max 1MB for OLE
            
        except Exception:
            return None
    
    @classmethod
    def _identify_ole_type(cls, data: bytes) -> str:

        
        """Identify the type of OLE object."""
        if b'Microsoft Office Word' in data:
            return 'Word Document'
        elif b'Microsoft Office Excel' in data or b'Microsoft Excel' in data:
            return 'Excel Spreadsheet'
        elif b'PowerPoint' in data:
            return 'PowerPoint Presentation'
        elif b'Visio' in data:
            return 'Visio Drawing'
        else:
            return 'Generic OLE Object'
    
    @classmethod
    def _deduplicate_blobs(cls, blobs: list[ExtractedBlob]) -> list[ExtractedBlob]:

        
        """Remove duplicate blobs (same offset)."""
        seen_offsets = set()
        unique_blobs = []
        
        # Sort by offset and size (prefer larger blobs)
        sorted_blobs = sorted(blobs, key=lambda b: (b.offset, -b.size))
        
        for blob in sorted_blobs:
            if blob.offset not in seen_offsets:
                seen_offsets.add(blob.offset)
                unique_blobs.append(blob)
        
        return sorted(unique_blobs, key=lambda b: b.offset)
    
    @classmethod
    def save_blobs(cls, blobs: list[ExtractedBlob], output_dir: str, object_name: str = "blob") -> dict[str, str]:

        
        """Save extracted blobs to files.
        
        Args:
            blobs: List of extracted blobs
            output_dir: Directory to save blob files
            object_name: Base name for blob files
            
        Returns:
            Dictionary mapping blob index to saved file path
        """
        import os
        
        saved_files = {}
        os.makedirs(output_dir, exist_ok=True)
        
        for i, blob in enumerate(blobs):
            filename = f"{object_name}_blob_{i:03d}.{blob.extension}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(blob.data)
            
            saved_files[i] = filepath
            logger.info(f"Saved {blob.blob_type.name} blob to {filepath} ({blob.size} bytes)")
        
        return saved_files