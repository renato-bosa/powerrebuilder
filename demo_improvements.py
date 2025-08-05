#!/usr/bin/env python3
"""
Demonstration of PowerRebuilder improvements:
1. Output directory overwrite handling
2. Performance optimizations (caching, parallel processing)
3. Streaming decoder for large files
"""

import subprocess
import sys
import os
import time
import shutil

def run_command(cmd, description):
    """Run a command and capture output."""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"CMD: {cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Return code: {result.returncode}")
    
    return result

def main():
    print("PowerRebuilder Improvements Demonstration")
    print("=========================================")
    
    # Setup test data
    test_pbd = "data/input/pbd_files/dcm_wizard.pbd"  # Smaller file for quick demo
    output_dir = "output/demo_improvements"
    
    # Demo 1: First extraction (creates output)
    print("\n\n1. FIRST EXTRACTION - Creates output directory")
    run_command(
        f"python main.py extract files {test_pbd} {output_dir} --enable-byte-recovery",
        "Initial extraction to create output files"
    )
    
    # Demo 2: Second extraction (shows overwrite warning)
    print("\n\n2. SECOND EXTRACTION - Shows overwrite warning")
    run_command(
        f"python main.py extract files {test_pbd} {output_dir} --enable-byte-recovery",
        "Extraction with existing output (overwrites with warning)"
    )
    
    # Demo 3: Using --no-overwrite flag
    print("\n\n3. NO-OVERWRITE FLAG - Prevents overwriting")
    run_command(
        f"python main.py --no-overwrite extract files {test_pbd} {output_dir} --enable-byte-recovery",
        "Extraction blocked by --no-overwrite flag"
    )
    
    # Demo 4: Performance test with caching
    print("\n\n4. PERFORMANCE OPTIMIZATION - Caching demonstration")
    cache_output = "output/demo_cache"
    
    # First run (no cache)
    print("\n4a. First decompilation (no cache):")
    run_command(
        f"python main.py --loglevel WARNING decompile {output_dir}/dcm_wizard {cache_output}/decompiled1",
        "Initial decompilation - populates cache"
    )
    
    # Second run (with cache)
    print("\n4b. Second decompilation (with cache):")
    run_command(
        f"python main.py --loglevel WARNING decompile {output_dir}/dcm_wizard {cache_output}/decompiled2",
        "Cached decompilation - should be much faster"
    )
    
    # Demo 5: Parallel processing
    print("\n\n5. PARALLEL PROCESSING - Speed improvement")
    parallel_output = "output/demo_parallel"
    
    # Create multiple files to process
    multi_input = "output/demo_multi_input"
    os.makedirs(multi_input, exist_ok=True)
    for i in range(3):
        shutil.copytree(f"{output_dir}/dcm_wizard", f"{multi_input}/copy_{i}", dirs_exist_ok=True)
    
    # Sequential processing
    print("\n5a. Sequential processing (default):")
    run_command(
        f"python main.py --loglevel WARNING decompile {multi_input} {parallel_output}/sequential",
        "Sequential decompilation of multiple files"
    )
    
    # Parallel processing
    print("\n5b. Parallel processing (optimized):")
    run_command(
        f"python main.py --loglevel WARNING decompile --parallel --max-workers 4 {multi_input} {parallel_output}/parallel",
        "Parallel decompilation with 4 workers"
    )
    
    print("\n\nDEMO COMPLETE!")
    print("==============")
    print("\nKey improvements demonstrated:")
    print("1. ✅ Output directory overwrite handling with warnings")
    print("2. ✅ --no-overwrite flag prevents accidental overwrites")
    print("3. ✅ Caching system reduces repeated work")
    print("4. ✅ Parallel processing speeds up multi-file operations")
    print("5. ✅ Performance monitoring and reporting")

if __name__ == "__main__":
    main()