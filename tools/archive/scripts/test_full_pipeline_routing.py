#!/usr/bin/env python3
"""Test the full pipeline with improved file routing."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.pipeline.pipeline_coordinator import PipelineCoordinator

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

def test_pipeline_with_real_data():




    """Test the pipeline with real extracted data."""

    # Use the already extracted test data
    extracted_dir = Path("test_output/extracted/dcm_detailobjects.pbd/dcm_detailobjects.pbd")

    if not extracted_dir.exists():
        print(f"Extracted directory not found: {extracted_dir}")
        return

    # Count files by type
    all_files = list(extracted_dir.rglob("*"))
    files_by_ext = {}

    for f in all_files:
        if f.is_file():
            ext = f.suffix.lower()
            if ext not in files_by_ext:
                files_by_ext[ext] = []
            files_by_ext[ext].append(f.name)

    print("Files in extracted directory:")
    print("=" * 60)
    for ext, files in sorted(files_by_ext.items()):
        print(f"{ext}: {len(files)} files")
        if len(files) <= 5:
            for f in files:
                print(f"  - {f}")
        else:
            for f in files[:3]:
                print(f"  - {f}")
            print(f"  ... and {len(files) - 3} more")

    # Run parse stage only to test classification
    print("\n\nTesting parse stage classification...")
    print("=" * 60)

    pipeline = PipelineCoordinator(
        input_dir=str(extracted_dir.parent),
        output_dir="test_output_routing",
    )

    # Set the extracted directory
    pipeline.extracted_dir = extracted_dir

    # Run parse stage
    parse_result = pipeline._run_parse_stage()

    print(f"\nParse stage results:")
    print(f"  Processed: {parse_result.get('processed', 0)}")
    print(f"  Successful: {parse_result.get('successful', 0)}")
    print(f"  Failed: {parse_result.get('failed', 0)}")

    if "file_classification" in parse_result:
        print(f"\nFile classification:")
        for category, count in parse_result["file_classification"].items():
            print(f"  {category}: {count} files")

    # Show binary files that will go to decompile stage
    if hasattr(pipeline, "_binary_files_for_decompile"):
        binary_files = pipeline._binary_files_for_decompile
        print(f"\nBinary files for decompilation: {len(binary_files)}")

        # Group by extension
        binary_by_ext = {}
        for f in binary_files:
            ext = f.suffix.lower()
            if ext not in binary_by_ext:
                binary_by_ext[ext] = 0
            binary_by_ext[ext] += 1

        for ext, count in sorted(binary_by_ext.items()):
            print(f"  {ext}: {count} files")

if __name__ == "__main__":
    test_pipeline_with_real_data()
