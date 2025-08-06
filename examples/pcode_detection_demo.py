#!/usr/bin/env python3
"""Demonstration of high-performance P-code detection algorithm.

This script shows how the new O(n) P-code detection algorithm works
and compares it with the original O(n²) implementation.
"""

import logging
import random
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

try:
    from src.decompile.pcode.detector import PCodeDetector
    from src.decompile.pcode.high_performance_detector import (
        HighPerformancePCodeDetector,
    )

    HAVE_HIGH_PERFORMANCE = True
except ImportError:
    logger.error(
        "Could not import high-performance detector. Make sure you're in the project root."
    )
    HAVE_HIGH_PERFORMANCE = False


def generate_test_data(size: int = 10000) -> bytes:
    """Generate realistic test data with P-code patterns.

    Args:
        size: Size of test data in bytes

    Returns:
        Test data with embedded P-code patterns
    """
    logger.info(f"Generating {size} bytes of test data...")

    data = bytearray(size)

    # Fill with random data initially
    for i in range(size):
        data[i] = random.randint(0, 255)

    # Add PowerBuilder export header
    export_header = b"HA$PBExportHeader$test_function.fun\n$PBExportComments$\n"
    if len(export_header) < size:
        data[: len(export_header)] = export_header

    # Inject realistic P-code patterns
    pcode_patterns = [
        # Common instruction sequences
        b"\x00\x00",  # RETURN
        b"\x04\x00",  # JUMP
        b"\x05\x00",  # DBSTART
        b"\x29\x00",  # GLOBFUNCCALL
        b"\x2c\x00",  # DOTFUNCCALL
        b"\x32\x00",  # PUSH_CONST_INT
        b"\x1e\x00",  # PUSH_LOCAL_VAR
        b"\x21\x00",  # PUSH_THIS
        # Multi-byte patterns
        b"\x32\x00\x00",  # PUSH_CONST_INT + RETURN
        b"\x2d\x00\x00",  # PUSH_PROPERTY + RETURN (getter)
        b"\x2e\x00\x00",  # POP_PROPERTY + RETURN (setter)
        b"\x21\x00\x27",  # PUSH_THIS + DOT
        # Complex sequences
        b"\x1e\x01\x32\x05\x00\x29\x02\x00",  # PUSH_LOCAL_VAR + PUSH_CONST_INT + GLOBFUNCCALL + RETURN
        b"\x21\x00\x27\x03\x2c\x01\x00",  # PUSH_THIS + DOT + DOTFUNCCALL + RETURN
    ]

    # Inject patterns at various locations (simulate real P-code)
    pattern_locations = []
    for i in range(len(export_header), size - 50, 200):  # Every ~200 bytes
        if i + 10 < size:
            pattern = random.choice(pcode_patterns)
            if i + len(pattern) < size:
                data[i : i + len(pattern)] = pattern
                pattern_locations.append((i, len(pattern), pattern))

    # Add some UTF-16 strings to test skipping
    utf16_strings = [
        "Hello World".encode("utf-16le"),
        "PowerBuilder".encode("utf-16le"),
        "Test Function".encode("utf-16le"),
    ]

    utf16_locations = []
    for i, utf16_str in enumerate(utf16_strings):
        offset = 1000 + i * 500
        if offset + len(utf16_str) < size:
            data[offset : offset + len(utf16_str)] = utf16_str
            utf16_locations.append((offset, len(utf16_str)))

    logger.info(
        f"Injected {len(pattern_locations)} P-code patterns and {len(utf16_locations)} UTF-16 strings"
    )

    return bytes(data), pattern_locations, utf16_locations


def benchmark_detection(
    data: bytes, pattern_locations: list[tuple[int, int, bytes]]
) -> None:
    """Benchmark both detection algorithms.

    Args:
        data: Test data
        pattern_locations: Known pattern locations for validation
    """
    if not HAVE_HIGH_PERFORMANCE:
        logger.error("High-performance detector not available for benchmarking")
        return

    logger.info("=" * 60)
    logger.info("PERFORMANCE BENCHMARK")
    logger.info("=" * 60)

    # Test high-performance detector
    logger.info("\nTesting High-Performance O(n) Algorithm:")
    logger.info("-" * 40)

    detector = HighPerformancePCodeDetector()
    start_time = time.time()

    # Find P-code sections
    sections = detector.detect_pcode_sections_fast(data)

    end_time = time.time()
    hp_time = end_time - start_time

    logger.info(f"Processing time: {hp_time * 1000:.2f} ms")
    logger.info(f"Throughput: {len(data) / hp_time / 1024 / 1024:.2f} MB/s")
    logger.info(f"Sections found: {len(sections)}")

    # Display found sections
    for i, (offset, length, confidence) in enumerate(sections):
        logger.info(
            f"  Section {i + 1}: offset=0x{offset:04x}, length={length}, confidence={confidence:.2f}"
        )

    # Test legacy detector for comparison
    logger.info("\nTesting Legacy O(n²) Algorithm:")
    logger.info("-" * 40)

    start_time = time.time()

    # Use legacy method directly
    legacy_sections = PCodeDetector._find_all_pcode_sections_legacy(data, "function")

    end_time = time.time()
    legacy_time = end_time - start_time

    logger.info(f"Processing time: {legacy_time * 1000:.2f} ms")
    logger.info(f"Throughput: {len(data) / legacy_time / 1024 / 1024:.2f} MB/s")
    logger.info(f"Sections found: {len(legacy_sections)}")

    # Performance comparison
    logger.info("\nPerformance Comparison:")
    logger.info("-" * 40)

    if legacy_time > 0:
        speedup = legacy_time / hp_time
        logger.info(f"Speed improvement: {speedup:.1f}x faster")
        logger.info(f"Time reduction: {(1 - hp_time / legacy_time) * 100:.1f}%")

    # Accuracy comparison
    logger.info("\nAccuracy Comparison:")
    logger.info("-" * 40)
    logger.info(f"High-performance sections: {len(sections)}")
    logger.info(f"Legacy sections: {len(legacy_sections)}")
    logger.info(f"Known patterns injected: {len(pattern_locations)}")

    # Memory usage estimation
    logger.info("\nMemory Usage:")
    logger.info("-" * 40)
    logger.info(f"High-performance: ~{detector.CHUNK_SIZE / 1024:.1f} KB (chunked)")
    logger.info(f"Legacy: ~{len(data) / 1024:.1f} KB (full buffer)")
    memory_reduction = (1 - detector.CHUNK_SIZE / len(data)) * 100
    logger.info(f"Memory reduction: {memory_reduction:.1f}%")


def demonstrate_pattern_detection(
    data: bytes, pattern_locations: list[tuple[int, int, bytes]]
) -> None:
    """Demonstrate pattern detection capabilities.

    Args:
        data: Test data
        pattern_locations: Known pattern locations
    """
    if not HAVE_HIGH_PERFORMANCE:
        logger.error("High-performance detector not available for demonstration")
        return

    logger.info("=" * 60)
    logger.info("PATTERN DETECTION DEMONSTRATION")
    logger.info("=" * 60)

    detector = HighPerformancePCodeDetector()

    # Test Boyer-Moore pattern matching
    logger.info("\nBoyer-Moore Pattern Matching:")
    logger.info("-" * 40)

    test_patterns = [b"\x00\x00", b"\x32\x00\x00", b"\x2d\x00\x00"]

    for pattern in test_patterns:
        matches = detector._boyer_moore_search(data, pattern)
        logger.info(f"Pattern {pattern.hex()}: {len(matches)} matches found")

        # Show first few matches
        for i, match in enumerate(matches[:3]):
            logger.info(f"  Match {i + 1}: offset 0x{match:04x}")

    # Test confidence calculation
    logger.info("\nConfidence Calculation:")
    logger.info("-" * 40)

    for offset, length, pattern in pattern_locations[:5]:  # Show first 5 patterns
        confidence = detector._calculate_window_confidence(data, offset, 32)
        logger.info(
            f"Pattern at 0x{offset:04x} ({pattern.hex()}): confidence {confidence:.2f}"
        )

    # Test heuristics
    logger.info("\nHeuristic Detection:")
    logger.info("-" * 40)

    # Test text boundary detection
    boundary = detector._find_text_boundary_heuristic(data)
    if boundary >= 0:
        logger.info(f"Text boundary detected at offset 0x{boundary:04x}")
    else:
        logger.info("No clear text boundary found")

    # Test UTF-16 detection
    utf16_regions = detector._detect_utf16_regions(data)
    logger.info(f"UTF-16 regions detected: {len(utf16_regions)}")
    for start, end in utf16_regions[:3]:  # Show first 3
        logger.info(
            f"  UTF-16 region: 0x{start:04x} - 0x{end:04x} ({end - start} bytes)"
        )


def demonstrate_caching(data: bytes) -> None:
    """Demonstrate confidence caching.

    Args:
        data: Test data
    """
    if not HAVE_HIGH_PERFORMANCE:
        logger.error("High-performance detector not available for caching demo")
        return

    logger.info("=" * 60)
    logger.info("CONFIDENCE CACHING DEMONSTRATION")
    logger.info("=" * 60)

    detector = HighPerformancePCodeDetector()

    # Test multiple confidence calculations at same offset
    test_offset = 500

    logger.info(f"\nTesting confidence caching at offset 0x{test_offset:04x}:")
    logger.info("-" * 50)

    # First calculation (not cached)
    start_time = time.time()
    confidence1 = detector._calculate_window_confidence(data, test_offset)
    end_time = time.time()
    time1 = end_time - start_time

    detector._cache_confidence(test_offset, confidence1)

    # Second calculation (cached)
    start_time = time.time()
    confidence2 = detector._get_cached_confidence(test_offset)
    end_time = time.time()
    time2 = end_time - start_time

    logger.info(f"First calculation: {confidence1:.2f} (time: {time1 * 1000:.3f} ms)")
    logger.info(f"Cached retrieval: {confidence2:.2f} (time: {time2 * 1000:.3f} ms)")

    if time1 > 0 and time2 > 0:
        speedup = time1 / time2
        logger.info(f"Cache speedup: {speedup:.1f}x faster")

    logger.info(f"Cache size: {len(detector._confidence_cache)} entries")


def main():
    """Main demonstration function."""
    logger.info("High-Performance P-code Detection Algorithm Demonstration")
    logger.info("=" * 80)

    if not HAVE_HIGH_PERFORMANCE:
        logger.error("Cannot run demonstration without high-performance detector")
        return

    # Generate test data
    test_data, pattern_locations, utf16_locations = generate_test_data(
        20000
    )  # 20KB test data

    # Run benchmarks
    benchmark_detection(test_data, pattern_locations)

    # Demonstrate pattern detection
    demonstrate_pattern_detection(test_data, pattern_locations)

    # Demonstrate caching
    demonstrate_caching(test_data)

    # Final summary
    logger.info("=" * 80)
    logger.info("DEMONSTRATION COMPLETE")
    logger.info("=" * 80)
    logger.info("Key benefits of the high-performance algorithm:")
    logger.info("• O(n) complexity instead of O(n²)")
    logger.info("• Boyer-Moore pattern matching for fast detection")
    logger.info("• Sliding window with cached confidence scores")
    logger.info("• Intelligent heuristics for quick navigation")
    logger.info("• Early termination for high-confidence results")
    logger.info("• Chunked processing for memory efficiency")
    logger.info("• Full backward compatibility with existing code")


if __name__ == "__main__":
    main()
