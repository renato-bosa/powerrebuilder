#!/usr/bin/env python3
"""Benchmark the performance improvements from caching."""

import logging
import tempfile
import time
from pathlib import Path

from common.types import get_registered_type
from parse.base_parser import PowerBuilderBaseParser
from parse.library import LibraryManager

logger = logging.getLogger(__name__)

def benchmark_library_manager() -> None:








    """Benchmark LibraryManager with caching."""
    # Create test directory with dummy library files
    with tempfile.TemporaryDirectory() as tmpdir:
        lib_dir = Path(tmpdir)

        # Create test library files
        for i in range(100):
            (lib_dir / f"library{i}.pbl").touch()
            (lib_dir / f"module{i}.pbd").touch()

        manager = LibraryManager([lib_dir])

        # Warm up
        manager._find_library_file("library50")

        # Test without cache (first lookups)
        start = time.time()
        for i in range(50):
            manager._find_library_file(f"library{i}")
        time.time() - start

        # Test with cache (repeated lookups)
        start = time.time()
        for _ in range(10):  # 10x more lookups
            for i in range(50):
                manager._find_library_file(f"library{i}")
        time.time() - start


def benchmark_type_registry() -> None:








    """Benchmark type registry with caching."""
    # Skip if register_type not available
    try:
        # Register some types
        from model.ast.types import TypeRegistry

        registry = TypeRegistry()
        for i in range(100):
            registry._registry[f"CustomType{i}"] = {"id": i, "data": f"type_{i}"}

        # Benchmark lookups
        iterations = 10000

        # Without cache benefit (different types)
        start = time.time()
        for i in range(iterations):
            get_registered_type(f"CustomType{i % 100}")
        time.time() - start

        # With cache benefit (same types repeatedly)
        start = time.time()
        for i in range(iterations):
            get_registered_type(f"CustomType{i % 10}")  # Only 10 different types
        time.time() - start

    except Exception:
        logger.debug("Generic exception caught")
        pass


def benchmark_parser_registry() -> None:








    """Benchmark parser extension lookups."""
    extensions = ["srw", "sru", "srd", "srm", "srs", "srf", "srj"]
    iterations = 50000

    # Benchmark
    start = time.time()
    for i in range(iterations):
        PowerBuilderBaseParser.get_file_type(extensions[i % len(extensions)])
    time.time() - start


def main() -> None:








    """Run all benchmarks."""
    benchmark_library_manager()
    benchmark_type_registry()
    benchmark_parser_registry()


if __name__ == "__main__":
    main()
