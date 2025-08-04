#!/usr/bin/env python3
"""CPU profiling script using pyinstrument."""

import sys
from pathlib import Path
from pyinstrument import Profiler

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.utils.strings import camel_to_snake, snake_to_camel
from src.common.utils.collections import chunk_list, filter_dict


def profile_string_operations():
    """Profile string conversion operations."""
    test_strings = [
        "SimpleTestCase",
        "HTTPSConnectionPoolManager",
        "XMLParserWithUTF8Support",
        "CamelCaseStringWithNumbers123",
        "veryLongCamelCaseStringWithManyWordsAndNumbers2024Version",
    ] * 1000
    
    # Profile camel to snake conversions
    for s in test_strings:
        camel_to_snake(s)
    
    # Profile snake to camel conversions
    snake_strings = [camel_to_snake(s) for s in test_strings[:100]]
    for s in snake_strings * 50:
        snake_to_camel(s)


def profile_collection_operations():
    """Profile collection operations."""
    # Large list operations
    large_list = list(range(100000))
    chunks = chunk_list(large_list, 100)
    
    # Large dict operations
    large_dict = {f"key_{i}": i for i in range(10000)}
    keys_to_filter = [f"key_{i}" for i in range(0, 10000, 5)]
    filtered = filter_dict(large_dict, keys_to_filter)
    
    # Nested operations
    for _ in range(10):
        chunked = chunk_list(list(range(1000)), 10)
        for chunk in chunked:
            small_dict = {str(i): i for i in chunk}
            filter_dict(small_dict, [str(i) for i in chunk[::2]])


def main():
    """Run profiling and display results."""
    profiler = Profiler()
    
    print("Starting CPU profiling...")
    profiler.start()
    
    # Run operations to profile
    profile_string_operations()
    profile_collection_operations()
    
    profiler.stop()
    
    print("\nProfiler Results:")
    print("-" * 80)
    print(profiler.output_text(unicode=True, show_all=True))
    
    # Save HTML report
    html_report = Path("cpu_profile_report.html")
    with open(html_report, "w") as f:
        f.write(profiler.output_html())
    print(f"\nDetailed HTML report saved to: {html_report}")


if __name__ == "__main__":
    main()