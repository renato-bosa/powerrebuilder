#!/usr/bin/env python3
"""Simplified pipeline test focusing on working modules."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline_test_simplified.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Import modules that we know are working
# from decompile.generators.unified_decompiler import UnifiedDecompiler  # Module doesn't exist
from src.extract.pbd.extractors.base import extract_pbl


def test_extraction(pbd_path: Path, output_dir: Path) -> dict:








    """Test extraction of a PBD file."""
    result = {"status": "failed", "files": 0, "errors": []}

    try:
        extracted_dir = output_dir / "extracted" / pbd_path.stem
        extracted_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {pbd_path.name}...")
        extract_pbl(str(pbd_path), str(extracted_dir), show_progress=False)

        # Count extracted files
        extracted_files = list(extracted_dir.glob("*"))
        result["files"] = len(extracted_files)
        result["status"] = "success" if extracted_files else "empty"
        result["file_types"] = {}

        # Count file types
        for f in extracted_files:
            ext = f.suffix.lower()
            result["file_types"][ext] = result["file_types"].get(ext, 0) + 1

    except Exception as e:
        result["errors"].append(str(e))
        logger.exception(f"Extraction failed: {e}")

    return result


def test_decompilation(extracted_dir: Path, output_dir: Path) -> dict:








    """Test decompilation of extracted P-code files."""
    result = {"status": "failed", "files": 0, "errors": [], "samples": []}

    try:
        decompiler = UnifiedDecompiler()
        decompiled_dir = output_dir / "decompiled"
        decompiled_dir.mkdir(parents=True, exist_ok=True)

        # Find P-code files
        pcode_files = []
        for ext in [".fun", ".win", ".udo"]:
            pcode_files.extend(extracted_dir.glob(f"*{ext}"))

        logger.info(f"Found {len(pcode_files)} P-code files to decompile")

        # Decompile first few files
        for pcode_file in pcode_files[:3]:
            try:
                logger.info(f"Decompiling {pcode_file.name}...")
                decompiled = decompiler.decompile_file(pcode_file)

                # Save result
                output_file = decompiled_dir / f"{pcode_file.stem}.pb"
                output_file.write_text(decompiled)

                result["files"] += 1
                result["samples"].append(
                    {
                        "name": pcode_file.name,
                        "lines": len(decompiled.split("\n")),
                        "has_code": "function" in decompiled.lower()
                        or "type" in decompiled.lower(),
                    },
                )

            except Exception as e:
                result["errors"].append(f"{pcode_file.name}: {e!s}")

        result["status"] = "success" if result["files"] > 0 else "failed"

    except Exception as e:
        result["errors"].append(str(e))
        logger.exception(f"Decompilation setup failed: {e}")

    return result


def main() -> None:








    """Run simplified pipeline test."""
    logger.info("Starting simplified pipeline test")

    # Test configuration
    input_dir = Path("data/input/pbd_files")
    output_dir = Path(
        "output/pipeline_test_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test just one PBD file
    pbd_files = list(input_dir.glob("*.pbd"))[:1]

    if not pbd_files:
        logger.error("No PBD files found in input directory")
        return

    results = {
        "test_date": datetime.now().isoformat(),
        "pbd_files": [],
    }

    for pbd_path in pbd_files:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Testing: {pbd_path.name}")
        logger.info(f"{'=' * 60}")

        pbd_result = {
            "name": pbd_path.name,
            "size": pbd_path.stat().st_size,
            "extraction": {},
            "decompilation": {},
        }

        # Test extraction
        logger.info("\n--- EXTRACTION ---")
        extraction_result = test_extraction(pbd_path, output_dir)
        pbd_result["extraction"] = extraction_result

        if extraction_result["status"] == "success":
            logger.info(f"Extracted {extraction_result['files']} files")
            logger.info(f"File types: {extraction_result['file_types']}")

            # Test decompilation
            logger.info("\n--- DECOMPILATION ---")
            extracted_dir = output_dir / "extracted" / pbd_path.stem
            decompilation_result = test_decompilation(extracted_dir, output_dir)
            pbd_result["decompilation"] = decompilation_result

            if decompilation_result["status"] == "success":
                logger.info(f"Decompiled {decompilation_result['files']} files")
                for sample in decompilation_result["samples"]:
                    logger.info(
                        f"  - {sample['name']}: {sample['lines']} lines, has_code={sample['has_code']}",
                    )

        results["pbd_files"].append(pbd_result)

    # Save results
    report_path = output_dir / "test_results.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nResults saved to: {report_path}")

    # Print summary

    for pbd in results["pbd_files"]:
        if pbd["extraction"]["file_types"]:
            pass
        if pbd["decompilation"]["errors"]:
            pass


if __name__ == "__main__":
    main()
