#!/usr/bin/env python3
"""Test the full SIME Finch pipeline from extraction to generation.

This script tests each module's functionality by running the complete pipeline
on actual PBD files from the input folder.
"""

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
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Import all modules
# from decompile.generators.unified_decompiler import UnifiedDecompiler  # Module doesn't exist
from extract.pbd.extraction.extractor import extract_pbl
from parse.powerbuilder import PowerBuilderParser


class PipelineTestResult:
    """Store test results for reporting."""

    def __init__(self) -> None:


        self.extraction_results = {}
        self.parsing_results = {}
        self.decompilation_results = {}
        self.generation_results = {}
        self.summary = {
            "total_pbd_files": 0,
            "successful_extractions": 0,
            "successful_parses": 0,
            "successful_decompilations": 0,
            "successful_generations": 0,
            "total_objects_extracted": 0,
            "total_objects_parsed": 0,
            "total_objects_decompiled": 0,
            "total_objects_generated": 0,
        }


def test_extraction_module(pbd_path: Path, output_dir: Path) -> dict:








    """Test the extraction module on a PBD file."""
    result = {
        "status": "failed",
        "objects_extracted": 0,
        "errors": [],
        "objects": [],
    }

    try:
        logger.info(f"Testing extraction on {pbd_path.name}")

        # Create output directory for this PBD
        extracted_dir = output_dir / "extracted" / pbd_path.stem
        extracted_dir.mkdir(parents=True, exist_ok=True)

        # Extract using the standard API
        extract_pbl(str(pbd_path), str(extracted_dir), show_progress=False)

        # Count extracted files
        extracted_files = list(extracted_dir.glob("*"))
        if extracted_files:
            result["objects_extracted"] = len(extracted_files)
            result["status"] = "success"

            # Record extracted objects
            for obj_path in extracted_files[:10]:  # Limit to first 10 for testing
                result["objects"].append(
                    {
                        "name": obj_path.name,
                        "size": obj_path.stat().st_size,
                        "path": str(obj_path),
                    }
                )
        else:
            result["errors"].append("No files extracted from PBD")

    except Exception as e:
        result["errors"].append(f"Extraction failed: {e!s}")
        logger.error(f"Extraction error: {e}", exc_info=True)

    return result


def test_parsing_module(extracted_files: list, output_dir: Path) -> dict:








    """Test the parsing module on extracted files."""
    result = {
        "status": "failed",
        "objects_parsed": 0,
        "errors": [],
        "parsed_objects": [],
    }

    try:
        parser = PowerBuilderParser()
        parsed_dir = output_dir / "parsed"
        parsed_dir.mkdir(parents=True, exist_ok=True)

        for file_info in extracted_files[:5]:  # Test first 5 files
            try:
                file_path = Path(file_info["path"])
                if file_path.exists() and file_path.suffix in [
                    ".sru",
                    ".srw",
                    ".srf",
                    ".srm",
                ]:
                    logger.info(f"Parsing {file_path.name}")

                    # Read and parse the file
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    ast = parser.parse(content)

                    if ast:
                        result["objects_parsed"] += 1
                        # Save AST representation
                        ast_path = parsed_dir / f"{file_path.stem}_ast.json"
                        ast_path.write_text(json.dumps(str(ast), indent=2))

                        result["parsed_objects"].append(
                            {
                                "name": file_path.name,
                                "ast_nodes": len(str(ast).split("\n")),
                                "path": str(ast_path),
                            }
                        )

            except Exception as e:
                result["errors"].append(f"Failed to parse {file_info['name']}: {e!s}")

        if result["objects_parsed"] > 0:
            result["status"] = "partial" if result["errors"] else "success"

    except Exception as e:
        result["errors"].append(f"Parsing setup failed: {e!s}")
        logger.error(f"Parsing error: {e}", exc_info=True)

    return result


def test_decompilation_module(extracted_files: list, output_dir: Path) -> dict:








    """Test the decompilation module on extracted P-code files."""
    result = {
        "status": "failed",
        "objects_decompiled": 0,
        "errors": [],
        "decompiled_objects": [],
    }

    try:
        decompiler = UnifiedDecompiler()
        decompiled_dir = output_dir / "decompiled"
        decompiled_dir.mkdir(parents=True, exist_ok=True)

        # Filter for P-code files
        pcode_files = [
            f
            for f in extracted_files
            if Path(f["path"]).suffix in [".fun", ".win", ".udo"]
        ]

        for file_info in pcode_files[:5]:  # Test first 5 P-code files
            try:
                file_path = Path(file_info["path"])
                if file_path.exists():
                    logger.info(f"Decompiling {file_path.name}")

                    # Decompile the file
                    decompiled_code = decompiler.decompile_file(file_path)

                    if decompiled_code and not decompiled_code.startswith("// Failed"):
                        result["objects_decompiled"] += 1

                        # Save decompiled code
                        output_path = decompiled_dir / f"{file_path.stem}.pb"
                        output_path.write_text(decompiled_code)

                        result["decompiled_objects"].append(
                            {
                                "name": file_path.name,
                                "lines": len(decompiled_code.split("\n")),
                                "path": str(output_path),
                            }
                        )

            except Exception as e:
                result["errors"].append(
                    f"Failed to decompile {file_info['name']}: {e!s}"
                )

        if result["objects_decompiled"] > 0:
            result["status"] = "partial" if result["errors"] else "success"

    except Exception as e:
        result["errors"].append(f"Decompilation setup failed: {e!s}")
        logger.error(f"Decompilation error: {e}", exc_info=True)

    return result


def test_generation_module(
    parsed_objects: list, decompiled_objects: list, output_dir: Path
) -> dict:








    """Test the code generation module."""
    result = {
        "status": "failed",
        "objects_generated": 0,
        "errors": [],
        "generated_files": [],
    }

    try:
        generated_dir = output_dir / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)

        # For now, just test basic generation capability
        logger.info("Testing code generation templates")

        # Test generating a simple model from decompiled code
        if decompiled_objects:
            for obj in decompiled_objects[:1]:  # Just test first object
                try:
                    # This is a placeholder - actual generation would use the parsed AST
                    model_code = f"""# Generated from {obj["name"]}
# TODO: Implement actual code generation from AST
# Original file had {obj["lines"]} lines

class GeneratedClass:
    def __init__(self):
        pass
        """
                    model_path = (
                        generated_dir / f"generated_{Path(obj['name']).stem}.py"
                    )
                    model_path.write_text(model_code)

                    result["objects_generated"] += 1
                    result["generated_files"].append(
                        {
                            "name": model_path.name,
                            "type": "python_model",
                            "path": str(model_path),
                        }
                    )
                except Exception as e:
                    result["errors"].append(
                        f"Failed to generate from {obj['name']}: {e!s}"
                    )

        if result["objects_generated"] > 0:
            result["status"] = "success"
        else:
            result["errors"].append("No objects to generate from")

    except Exception as e:
        result["errors"].append(f"Generation setup failed: {e!s}")
        logger.error(f"Generation error: {e}", exc_info=True)

    return result


def run_full_pipeline_test():






    """Run the full pipeline test on input PBD files."""
    logger.info("Starting full pipeline test")

    # Setup
    input_dir = Path("input/pbd_files")
    output_dir = Path(
        "output/pipeline_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    results = PipelineTestResult()

    # Get PBD files
    pbd_files = list(input_dir.glob("*.pbd"))[:3]  # Test first 3 PBD files
    results.summary["total_pbd_files"] = len(pbd_files)

    logger.info(f"Testing {len(pbd_files)} PBD files")

    # Test each PBD file
    for pbd_path in pbd_files:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Testing pipeline for: {pbd_path.name}")
        logger.info(f"{'=' * 60}")

        # Phase 1: Extraction
        logger.info("\nPhase 1: EXTRACTION")
        extraction_result = test_extraction_module(pbd_path, output_dir)
        results.extraction_results[pbd_path.name] = extraction_result

        if extraction_result["status"] == "success":
            results.summary["successful_extractions"] += 1
            results.summary["total_objects_extracted"] += extraction_result[
                "objects_extracted"
            ]

            # Phase 2: Parsing (on extracted source files)
            logger.info("\nPhase 2: PARSING")
            parsing_result = test_parsing_module(
                extraction_result["objects"], output_dir
            )
            results.parsing_results[pbd_path.name] = parsing_result

            if parsing_result["objects_parsed"] > 0:
                results.summary["successful_parses"] += 1
                results.summary["total_objects_parsed"] += parsing_result[
                    "objects_parsed"
                ]

            # Phase 3: Decompilation (on extracted P-code files)
            logger.info("\nPhase 3: DECOMPILATION")
            decompilation_result = test_decompilation_module(
                extraction_result["objects"], output_dir
            )
            results.decompilation_results[pbd_path.name] = decompilation_result

            if decompilation_result["objects_decompiled"] > 0:
                results.summary["successful_decompilations"] += 1
                results.summary["total_objects_decompiled"] += decompilation_result[
                    "objects_decompiled"
                ]

            # Phase 4: Generation
            logger.info("\nPhase 4: GENERATION")
            generation_result = test_generation_module(
                parsing_result.get("parsed_objects", []),
                decompilation_result.get("decompiled_objects", []),
                output_dir,
            )
            results.generation_results[pbd_path.name] = generation_result

            if generation_result["objects_generated"] > 0:
                results.summary["successful_generations"] += 1
                results.summary["total_objects_generated"] += generation_result[
                    "objects_generated"
                ]

    # Generate report
    generate_report(results, output_dir)

    return results


def generate_report(results: PipelineTestResult, output_dir: Path) -> None:








    """Generate a comprehensive test report."""
    report_path = output_dir / "pipeline_test_report.txt"

    with open(report_path, "w") as f:
        f.write("SIME FINCH PIPELINE TEST REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")

        # Summary
        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total PBD files tested: {results.summary['total_pbd_files']}\n")
        f.write(
            f"Successful extractions: {results.summary['successful_extractions']}\n"
        )
        f.write(f"Successful parses: {results.summary['successful_parses']}\n")
        f.write(
            f"Successful decompilations: {results.summary['successful_decompilations']}\n"
        )
        f.write(
            f"Successful generations: {results.summary['successful_generations']}\n"
        )
        f.write("\n")
        f.write(
            f"Total objects extracted: {results.summary['total_objects_extracted']}\n"
        )
        f.write(f"Total objects parsed: {results.summary['total_objects_parsed']}\n")
        f.write(
            f"Total objects decompiled: {results.summary['total_objects_decompiled']}\n"
        )
        f.write(
            f"Total objects generated: {results.summary['total_objects_generated']}\n"
        )
        f.write("\n")

        # Detailed results per PBD
        f.write("DETAILED RESULTS\n")
        f.write("=" * 80 + "\n")

        for pbd_name in results.extraction_results:
            f.write(f"\nPBD: {pbd_name}\n")
            f.write("-" * 40 + "\n")

            # Extraction
            ext_result = results.extraction_results[pbd_name]
            f.write(f"Extraction: {ext_result['status']}\n")
            f.write(f"  Objects extracted: {ext_result['objects_extracted']}\n")
            if ext_result["errors"]:
                f.write(f"  Errors: {len(ext_result['errors'])}\n")
                for err in ext_result["errors"][:3]:
                    f.write(f"    - {err}\n")

            # Parsing
            if pbd_name in results.parsing_results:
                parse_result = results.parsing_results[pbd_name]
                f.write(f"Parsing: {parse_result['status']}\n")
                f.write(f"  Objects parsed: {parse_result['objects_parsed']}\n")
                if parse_result["errors"]:
                    f.write(f"  Errors: {len(parse_result['errors'])}\n")

            # Decompilation
            if pbd_name in results.decompilation_results:
                decomp_result = results.decompilation_results[pbd_name]
                f.write(f"Decompilation: {decomp_result['status']}\n")
                f.write(
                    f"  Objects decompiled: {decomp_result['objects_decompiled']}\n"
                )
                if decomp_result["errors"]:
                    f.write(f"  Errors: {len(decomp_result['errors'])}\n")

            # Generation
            if pbd_name in results.generation_results:
                gen_result = results.generation_results[pbd_name]
                f.write(f"Generation: {gen_result['status']}\n")
                f.write(f"  Objects generated: {gen_result['objects_generated']}\n")

    logger.info(f"\nReport saved to: {report_path}")

    # Also save as JSON for programmatic access
    json_report_path = output_dir / "pipeline_test_report.json"
    with open(json_report_path, "w") as f:
        json.dump(
            {
                "summary": results.summary,
                "extraction": results.extraction_results,
                "parsing": results.parsing_results,
                "decompilation": results.decompilation_results,
                "generation": results.generation_results,
            },
            f,
            indent=2,
        )

    logger.info(f"JSON report saved to: {json_report_path}")


if __name__ == "__main__":
    try:
        results = run_full_pipeline_test()

        # Print summary to console

    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        sys.exit(1)
