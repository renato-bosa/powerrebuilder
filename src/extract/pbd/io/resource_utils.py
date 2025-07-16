"""Resource utility functions for PowerBuilder extraction."""

import logging
import struct
from typing import Any
# tuple is now a built-in type in Python 3.9+, no need to import from typing

logger = logging.getLogger(__name__)


def get_bmp_size(data: bytes) -> tuple[int, int] | None:
    """Extract dimensions from BMP data.

    Args:
        data: BMP file data

    Returns:
        Tuple of (width, height) or None if invalid
    """
    if len(data) < 26:
        return None

    # Check BMP signature
    if data[:2] != b'BM':
        return None

    try:
        # BMP header structure:
        # Offset 18: width (4 bytes, little-endian)
        # Offset 22: height (4 bytes, little-endian)
        width = struct.unpack('<I', data[18:22])[0]
        height = struct.unpack('<I', data[22:26])[0]

        # Validate dimensions
        if width > 0 and height > 0 and width < 10000 and height < 10000:
            return (width, height)
    except struct.error:
        pass

    return None


def get_ico_size(data: bytes) -> tuple[int, int] | None:
    """Extract dimensions from ICO data.

    Args:
        data: ICO file data

    Returns:
        Tuple of (width, height) or None if invalid
    """
    if len(data) < 22:
        return None

    try:
        # ICO header structure:
        # Offset 0-2: Reserved (always 0)
        # Offset 2-4: Type (1 for icon)
        # Offset 4-6: Number of images
        if struct.unpack('<HH', data[0:4]) != (0, 1):
            return None

        # Get first image dimensions
        # Icon directory entry starts at offset 6
        # Offset 6: Width (0 means 256)
        # Offset 7: Height (0 means 256)
        width = data[6]
        height = data[7]

        # 0 means 256 in ICO format
        if width == 0:
            width = 256
        if height == 0:
            height = 256

        return (width, height)
    except (struct.error, IndexError):
        pass

    return None


def get_image_format(data: bytes) -> str | None:
    """Detect image format from data.

    Args:
        data: Image file data

    Returns:
        Format string ('BMP', 'ICO', 'PNG', 'JPEG') or None
    """
    if len(data) < 4:
        return None

    # Check common image signatures
    if data[:2] == b'BM':
        return 'BMP'
    elif data[:4] == b'\x00\x00\x01\x00':
        return 'ICO'
    elif data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'PNG'
    elif data[:3] == b'\xff\xd8\xff':
        return 'JPEG'
    elif data[:4] == b'GIF8':
        return 'GIF'

    return None


def estimate_resource_size(data: bytes, resource_type: str) -> dict[str, Any]:
    """Estimate resource size and metadata.

    Args:
        data: Resource data
        resource_type: Type of resource

    Returns:
        Dictionary with size information
    """
    info = {
        'size': len(data),
        'type': resource_type
    }

    if resource_type == 'image':
        format_type = get_image_format(data)
        if format_type:
            info['format'] = format_type

            if format_type == 'BMP':
                dimensions = get_bmp_size(data)
                if dimensions:
                    info['width'], info['height'] = dimensions
            elif format_type == 'ICO':
                dimensions = get_ico_size(data)
                if dimensions:
                    info['width'], info['height'] = dimensions

    return info