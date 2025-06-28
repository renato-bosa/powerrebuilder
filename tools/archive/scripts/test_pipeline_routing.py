#!/usr/bin/env python3
"""Test the pipeline file routing improvements."""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.utils.object_type_detector import ObjectTypeDetector
from common.pipeline.pipeline_coordinator import PipelineCoordinator


def test_file_classification():




    """Test that files are properly classified."""
    print("Testing file classification...")
    print("=" * 60)

    # Test file names
    test_files = [
        "w_main.srw",           # Source window
        "u_datawindow.sru",     # Source user object
        "d_customer.srd",       # Source DataWindow
        "d_order.dwo",          # Binary DataWindow
        "w_main.fun",           # P-code function
        "w_main.win",           # P-code window
        "m_menu.men",           # P-code menu
        "query.sql",            # SQL file
        "n_business.udo",       # P-code user object
    ]

    for file_name in test_files:
        should_decompile = ObjectTypeDetector.should_decompile(file_name)
        is_datawindow = ObjectTypeDetector.is_datawindow(file_name)
        suffix = Path(file_name).suffix

        print(f"\n{file_name}:")
        print(f"  Extension: {suffix}")
        print(f"  Should decompile: {should_decompile}")
        print(f"  Is DataWindow: {is_datawindow}")

        # Determine expected routing
        if suffix in [".srw", ".sru", ".srf", ".srm", ".srs", ".sra", ".srd"]:
            expected = "Parse (source)"
        elif suffix == ".dwo":
            expected = "Parse (binary DataWindow)"
        elif suffix == ".sql":
            expected = "Parse (SQL)"
        elif should_decompile:
            expected = "Decompile (P-code)"
        else:
            expected = "Unknown"

        print(f"  Expected routing: {expected}")

def test_pipeline_routing():




    """Test the actual pipeline routing with sample files."""
    print("\n\nTesting pipeline routing with sample files...")
    print("=" * 60)

    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        extracted_dir = output_dir / "extracted"

        input_dir.mkdir()
        output_dir.mkdir()
        extracted_dir.mkdir()

        # Create sample extracted files
        sample_files = {
            "w_main.srw": "// Source window",
            "d_customer.srd": "// Source DataWindow",
            "d_order.dwo": b"PDW\x00binary data",  # Binary content
            "w_main.fun": b"PCODE\x00binary",      # Binary content
            "query.sql": "SELECT * FROM customer",
        }

        for file_name, content in sample_files.items():
            file_path = extracted_dir / file_name
            if isinstance(content, bytes):
                file_path.write_bytes(content)
            else:
                file_path.write_text(content)

        # Initialize pipeline coordinator
        pipeline = PipelineCoordinator(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
        )

        # Manually set extracted_dir to our test directory
        pipeline.extracted_dir = extracted_dir

        # Run parse stage to test classification
        print("\nRunning parse stage classification...")
        parse_result = pipeline._run_parse_stage()

        print(f"\nParse stage results:")
        print(f"  Processed: {parse_result.get('processed', 0)}")
        print(f"  Successful: {parse_result.get('successful', 0)}")
        print(f"  Failed: {parse_result.get('failed', 0)}")

        if "file_classification" in parse_result:
            print(f"\nFile classification:")
            for category, count in parse_result["file_classification"].items():
                print(f"  {category}: {count}")

        # Check if binary files were stored
        if hasattr(pipeline, "_binary_files_for_decompile"):
            print(f"\nBinary files stored for decompile stage: {len(pipeline._binary_files_for_decompile)}")
            for f in pipeline._binary_files_for_decompile:
                print(f"  - {f.name}")

if __name__ == "__main__":
    test_file_classification()
    test_pipeline_routing()
