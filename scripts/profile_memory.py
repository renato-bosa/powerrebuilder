#!/usr/bin/env python3
"""Memory profiling script using memray."""

import subprocess
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def memory_intensive_operations():
    """Perform memory-intensive operations to profile."""
    from src.common.utils.collections import chunk_list, filter_dict

    # Create large data structures
    print("Creating large data structures...")

    # Large list operations
    huge_list = list(range(1_000_000))
    chunks = chunk_list(huge_list, 1000)

    # Nested list comprehensions
    nested_data = [[i * j for j in range(100)] for i in range(10000)]

    # Large dictionary operations
    huge_dict = {f"key_{i}": f"value_{i}" * 100 for i in range(100_000)}

    # Keep references to some data
    filtered_dict = filter_dict(huge_dict, [f"key_{i}" for i in range(0, 100_000, 10)])

    # String concatenation (potentially inefficient)
    big_string = ""
    for i in range(10000):
        big_string += f"Line {i}\n"

    # Return some data to prevent optimization
    return len(chunks), len(filtered_dict), len(big_string)


def run_with_memray():
    """Run the memory profiling with memray."""
    print("Starting memory profiling with memray...")

    # Create output directory
    output_dir = Path("memory_profiles")
    output_dir.mkdir(exist_ok=True)

    # Run memray
    output_file = output_dir / "memory_profile.bin"

    # Run this script with memray
    cmd = [
        sys.executable,
        "-m",
        "memray",
        "run",
        "-o",
        str(output_file),
        __file__,
        "--execute",
    ]

    subprocess.run(cmd, check=False)

    # Generate reports
    print("\nGenerating memory reports...")

    # Generate flamegraph
    flamegraph_file = output_dir / "memory_flamegraph.html"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "memray",
            "flamegraph",
            str(output_file),
            "-o",
            str(flamegraph_file),
        ],
        check=False,
    )
    print(f"Flamegraph saved to: {flamegraph_file}")

    # Generate summary
    print("\nMemory Summary:")
    subprocess.run(
        [sys.executable, "-m", "memray", "summary", str(output_file)], check=False
    )

    # Generate stats
    stats_file = output_dir / "memory_stats.html"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "memray",
            "stats",
            str(output_file),
            "-o",
            str(stats_file),
        ],
        check=False,
    )
    print(f"\nDetailed stats saved to: {stats_file}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        # Execute the memory-intensive operations
        results = memory_intensive_operations()
        print(f"Operation results: {results}")
    else:
        # Run with memray
        run_with_memray()


if __name__ == "__main__":
    main()
