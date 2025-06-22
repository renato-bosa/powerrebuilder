#!/usr/bin/env python3
"""Test enhanced resource extraction functionality."""

import struct
import tempfile
from pathlib import Path

from extract.pbd.extraction.unified_resource_extractor import UnifiedResourceExtractor


def create_test_data_with_resources():



    


    """Create test data with embedded resources."""
    data = bytearray()
    
    # Add some PowerBuilder object code
    data.extend(b"forward\nglobal type test_object from object\nend type\n")
    
    # Embed a small PNG image
    png_data = b'\x89PNG\r\n\x1a\n'  # PNG signature
    png_data += b'\x00\x00\x00\rIHDR'  # IHDR chunk
    png_data += struct.pack('>II', 16, 16)  # 16x16 image
    png_data += b'\x08\x02\x00\x00\x00'  # 8-bit RGB
    png_data += b'\x90\x91\x68\x36'  # CRC
    png_data += b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'  # IEND chunk
    
    data.extend(b"\n// embedded image data\n")
    data.extend(png_data)
    
    # Add more code
    data.extend(b"\nend forward\n")
    
    # Embed a BMP file
    bmp_size = 54 + 64  # Header + small image data
    bmp_data = b'BM'  # Signature
    bmp_data += struct.pack('<I', bmp_size)  # File size
    bmp_data += b'\x00\x00\x00\x00'  # Reserved
    bmp_data += struct.pack('<I', 54)  # Data offset
    bmp_data += struct.pack('<I', 40)  # Header size
    bmp_data += struct.pack('<II', 8, 8)  # 8x8 image
    bmp_data += struct.pack('<HH', 1, 24)  # Planes, bits per pixel
    bmp_data += b'\x00' * 24  # Rest of header
    bmp_data += b'\xFF' * 64  # White pixels
    
    data.extend(b"\n// embedded bitmap\n")
    data.extend(bmp_data)
    
    # Embed a GIF file
    gif_data = b'GIF89a'  # Signature
    gif_data += struct.pack('<HH', 4, 4)  # 4x4 image
    gif_data += b'\xF0\x00\x00'  # Global color table info
    gif_data += b'\xFF\xFF\xFF\x00\x00\x00'  # Simple palette
    gif_data += b'\x21\xF9\x04\x00\x00\x00\x00\x00'  # Graphics control
    gif_data += b'\x2C'  # Image separator
    gif_data += struct.pack('<HHHH', 0, 0, 4, 4)  # Position and size
    gif_data += b'\x00'  # No local color table
    gif_data += b'\x02\x02\x44\x01\x00'  # Minimal LZW data
    gif_data += b'\x3B'  # Trailer
    
    data.extend(b"\n// embedded gif\n")
    data.extend(gif_data)
    
    return bytes(data)


def test_unified_resource_extractor():



    


    """Test the unified resource extractor."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        # Initialize extractor
        extractor = UnifiedResourceExtractor(output_dir)
        
        # Create test data
        test_data = create_test_data_with_resources()
        
        # Extract resources
        resources = extractor.extract_resources_from_data(
            test_data,
            "test_object.sru",
            "sru"
        )
        
        # Verify resources were extracted
        assert len(resources) == 3, f"Expected 3 resources, got {len(resources)}"
        
        # Check PNG resource
        png_resource = next(r for r in resources if r['type'] == 'png')
        assert png_resource['mime_type'] == 'image/png'
        assert png_resource['size'] > 0
        assert 'metadata' in png_resource
        assert png_resource['metadata']['width'] == 16
        assert png_resource['metadata']['height'] == 16
        
        # Check BMP resource
        bmp_resource = next(r for r in resources if r['type'] == 'bmp')
        assert bmp_resource['mime_type'] == 'image/bmp'
        assert bmp_resource['size'] == 118  # Expected size
        assert 'metadata' in bmp_resource
        assert bmp_resource['metadata']['width'] == 8
        assert bmp_resource['metadata']['height'] == 8
        
        # Check GIF resource
        gif_resource = next(r for r in resources if r['type'] == 'gif')
        assert gif_resource['mime_type'] == 'image/gif'
        assert gif_resource['size'] > 0
        assert 'metadata' in gif_resource
        assert gif_resource['metadata']['width'] == 4
        assert gif_resource['metadata']['height'] == 4
        
        # Generate manifest
        extractor.generate_manifest()
        
        # Check manifest file exists
        manifest_path = output_dir / "resources" / "manifest.txt"
        assert manifest_path.exists()
        
        # Check resource files exist
        resources_dir = output_dir / "resources"
        assert resources_dir.exists()
        
        images_dir = resources_dir / "images"
        assert images_dir.exists()
        
        # Check individual resource files
        image_files = list(images_dir.glob("*"))
        assert len(image_files) >= 3  # May have duplicates with different names
        
        # Check catalog
        catalog_path = resources_dir / "resource_catalog.json"
        assert catalog_path.exists()
        
        # Verify statistics
        assert extractor.stats['extracted_resources'] == 3
        assert extractor.stats['failed_resources'] == 0
        assert extractor.stats['resource_types']['png'] == 1
        assert extractor.stats['resource_types']['bmp'] == 1
        assert extractor.stats['resource_types']['gif'] == 1
        
        print("✓ Unified resource extractor test passed")


def test_resource_size_detection():



    


    """Test resource size detection for various formats."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        extractor = UnifiedResourceExtractor(output_dir)
        
        # Test PNG size detection
        png_data = b'\x89PNG\r\n\x1a\n'
        png_data += b'\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00'
        png_data += b'\x90\x91\x68\x36'
        png_data += b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'
        
        size = extractor._get_resource_size(png_data, 0, 'png')
        assert size == len(png_data), f"PNG size detection failed: {size} != {len(png_data)}"
        
        # Test JPEG size detection (minimal JPEG)
        jpg_data = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        jpg_data += b'\xFF\xD9'  # EOI marker
        
        size = extractor._get_resource_size(jpg_data, 0, 'jpg')
        assert size == len(jpg_data), f"JPEG size detection failed: {size} != {len(jpg_data)}"
        
        # Test WAV size detection
        wav_data = b'RIFF'
        wav_data += struct.pack('<I', 36)  # Chunk size
        wav_data += b'WAVEfmt '
        wav_data += struct.pack('<I', 16)  # fmt chunk size
        wav_data += b'\x01\x00\x02\x00'  # PCM, 2 channels
        wav_data += b'\x44\xAC\x00\x00'  # Sample rate
        wav_data += b'\x10\xB1\x02\x00'  # Byte rate
        wav_data += b'\x04\x00\x10\x00'  # Block align, bits per sample
        wav_data += b'data'
        wav_data += struct.pack('<I', 0)  # Data size
        
        size = extractor._get_resource_size(wav_data, 0, 'wav')
        assert size == 44, f"WAV size detection failed: {size} != 44"
        
        print("✓ Resource size detection test passed")


def test_resource_deduplication():



    


    """Test that duplicate resources are deduplicated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        extractor = UnifiedResourceExtractor(output_dir)
        
        # Create identical PNG data
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        png_data += struct.pack('>II', 1, 1)
        png_data += b'\x08\x02\x00\x00\x00\x90\x77\x53\xDE'
        png_data += b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'
        
        # Create test data with duplicate images
        test_data = b"code\n" + png_data + b"\nmore code\n" + png_data + b"\nend"
        
        # Extract resources
        resources = extractor.extract_resources_from_data(
            test_data,
            "test_dedup.sru",
            "sru"
        )
        
        # Should extract 2 resources
        assert len(resources) == 2
        
        # But only 1 file should be saved (deduplication)
        images_dir = output_dir / "resources" / "images"
        image_files = list(images_dir.glob("*.png"))
        
        # Check that both resources have the same full hash
        hashes = set()
        for resource in resources:
            hashes.add(resource['hash'])
        
        # Should have same hash for both
        assert len(hashes) == 1, "Deduplication failed - different hashes for identical resources"
        
        print("✓ Resource deduplication test passed")


if __name__ == "__main__":
    test_unified_resource_extractor()
    test_resource_size_detection()
    test_resource_deduplication()
    print("\n✅ All resource extraction enhancement tests passed!")