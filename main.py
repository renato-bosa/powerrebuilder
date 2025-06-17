#!/usr/bin/env python3
"""Main entry point for the PowerBuilder reverse engineering tool (SIME Finch).

This script orchestrates the entire pipeline for converting PowerBuilder applications
to modern web applications:

1. Extract: Extracts raw source code from PowerBuilder binary files (PBL/PBD)
2. Parse: Lexes and parses the PowerBuilder source into Abstract Syntax Trees (ASTs)
3. Decompile: Converts PowerBuilder PCode into structured pseudocode
4. Generate: Produces backend (Litestar) and frontend (React/Astro) code

The CLI supports both individual pipeline steps and end-to-end processing.
Command-line interface is provided through Click.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import click

from common.logging_config import configure_pipeline_logging, get_logger
from common.progress import PipelineProgress
from decompile.decompile_coordinator import decompile_directory
from extract.extract_coordinator import extract_pbls
from extract.pbd.extraction.extractor import extract_pbl
from extract.pbd.utils.text_extraction import binary_to_readable_format

# Initial basic logging setup - will be reconfigured by CLI
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
logger: logging.Logger = get_logger("tool_pb")

# Default paths
DEFAULT_EXTRACT_INPUT: str = "input"
DEFAULT_EXTRACT_OUTPUT: str = "output/extracted"
DEFAULT_PARSE_INPUT: str = "output/extracted"
DEFAULT_PARSE_OUTPUT: str = "output/parsed"
DEFAULT_ALL_PBL_INPUT: str = "input"
DEFAULT_ALL_BASE_OUTPUT: str = "output"


@click.group()
@click.version_option(version="0.1.0", prog_name="sime-finch")
@click.option(
    "--loglevel",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
    help="Set the logging level.",
    show_default=True,
)
@click.option(
    "--traceback/--no-traceback", default=False, help="Show full traceback on error."
)
@click.pass_context
def cli(ctx: click.Context, loglevel: str, traceback: bool) -> None:
    """SIME Finch: PowerBuilder Reverse Engineering Toolkit."""
    # Use optimized logging configuration
    verbose = loglevel.upper() == "DEBUG"
    configure_pipeline_logging(verbose=verbose)

    # Override with specific log level if needed
    if loglevel.upper() != "INFO":
        logging.getLogger().setLevel(getattr(logging, loglevel.upper()))

    ctx.obj = {"traceback": traceback}
    logger.debug(f"Loglevel set to {loglevel.upper()}")
    logger.debug(f"Traceback on error: {traceback}")


# Extract group for all extraction-related commands
@cli.group()
def extract() -> None:
    """PowerBuilder extraction utilities."""


@extract.command("files")
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_EXTRACT_INPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_EXTRACT_OUTPUT,
)
@click.option("--debug", is_flag=True, help="Enable debug logging for extraction")
@click.option(
    "--enable-byte-recovery",
    is_flag=True,
    help="Enable byte-level recovery for corrupted files",
)
@click.option("--unicode", is_flag=True, help="Use unicode mode for extraction")
def extract_files(
    input_dir: str,
    output_dir: str,
    debug: bool,
    enable_byte_recovery: bool,
    unicode: bool,
) -> None:
    """Extract PB source from PBL/PBD files.

    INPUT_DIR: Directory containing PBL/PBD files
    OUTPUT_DIR: Directory to write extracted source files
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logging.getLogger("extract.extract_coordinator").setLevel(logging.DEBUG)
        logging.getLogger("extract.pbd").setLevel(logging.DEBUG)

    try:
        logger.info(
            f"Extracting from {input_dir} to {output_dir} (byte_recovery={enable_byte_recovery}, unicode={unicode})"
        )

        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        if input_path.is_file():
            # Single file extraction
            logger.info(f"Extracting file: {input_path}")
            extract_pbl(str(input_path), str(output_path))
        else:
            # Directory extraction
            extract_pbls(
                str(input_path),
                str(output_path),
                enable_byte_recovery=enable_byte_recovery,
            )

        logger.info("Extraction complete")
    except Exception as e:
        logger.exception(f"Failed to extract: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@extract.command("to-text")
@click.argument(
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    help="Output text file path (default: input file with .txt extension)",
)
@click.option("-s", "--stdout", is_flag=True, help="Also print to stdout")
def extract_to_text(input_file: str, output: str | None, stdout: bool) -> None:
    """Convert PowerBuilder binary files to readable text format."""
    input_path = Path(input_file)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        # Default: same name with .txt extension
        output_path = input_path.with_suffix(".txt")

    try:
        logger.info(f"Converting {input_path} to text format...")
        result = binary_to_readable_format(input_path, output_path)

        if result:
            logger.info(f"Successfully converted. Output saved to {output_path}")

            # Also print to stdout if requested
            if stdout:
                # Read the converted text and print to stdout
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        print(f.read())
                except Exception as e:
                    logger.error(f"Failed to read output file for stdout: {e}")
        else:
            logger.error("Conversion failed")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Failed to convert to text: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@extract.command("inspect")
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
def extract_inspect(files: tuple[str, ...]) -> None:
    """Inspect PBD file structure."""
    # Path to the consolidated pbd_inspector.py script
    script_path = (
        Path(__file__).parent / "extract" / "pbd" / "utils" / "pbd_inspector.py"
    )

    if not script_path.exists():
        logger.error(f"Inspector utility not found at: {script_path}")
        sys.exit(1)

    # Build command with arguments - add --inspect flag for structure analysis
    cmd = [sys.executable, str(script_path), "--inspect"]
    if files:
        cmd.extend(files)

    # Run the script
    try:
        sys.exit(subprocess.call(cmd))
    except Exception as e:
        logger.exception(f"Failed to run inspector utility: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@extract.command("hexdump")
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
def extract_hexdump(files: tuple[str, ...]) -> None:
    """View hexdump of PowerBuilder files."""
    # Path to the consolidated pbd_inspector.py script
    script_path = (
        Path(__file__).parent / "extract" / "pbd" / "utils" / "pbd_inspector.py"
    )

    if not script_path.exists():
        logger.error(f"Inspector utility not found at: {script_path}")
        sys.exit(1)

    # Build command with arguments - no special flags for hexdump mode
    cmd = [sys.executable, str(script_path)]
    if files:
        cmd.extend(files)

    # Run the script
    try:
        sys.exit(subprocess.call(cmd))
    except Exception as e:
        logger.exception(f"Failed to run hexdump utility: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_PARSE_INPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_PARSE_OUTPUT,
)
def parse(input_dir: str, output_dir: str) -> None:
    """Parse raw PowerBuilder files into structured data.

    INPUT_DIR: Directory containing extracted PowerBuilder files
    OUTPUT_DIR: Directory to write parsed data
    """
    try:
        import json
        from pathlib import Path

        from parse.parse_coordinator import parse_powerbuilder_directory

        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Starting PowerBuilder file parsing from {input_path} to {output_path}..."
        )

        # Parse all PowerBuilder files in the directory
        parsed_data = parse_powerbuilder_directory(input_path, output_path)

        # Save parsed data summary
        summary_file = output_path / "parsed_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, default=str)

        logger.info(f"Parsing complete. Summary saved to {summary_file}")
        logger.info(f"Parsed {len(parsed_data.get('files', []))} files")

    except ImportError as e:
        logger.exception(f"Failed to import parsing modules: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Failed to parse files: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_EXTRACT_OUTPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default="output/decompiled",
)
def decompile(input_dir: str, output_dir: str) -> None:
    """Decompile PowerBuilder PCode to structured pseudocode.

    INPUT_DIR: Directory containing extracted PowerBuilder files
    OUTPUT_DIR: Directory to write decompiled code
    """
    try:
        logger.info(f"Decompiling PCode from {input_dir} to {output_dir}...")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        decompile_directory(input_dir, output_dir)
        logger.info("Decompilation complete.")
    except Exception as e:
        logger.exception(f"Failed to decompile: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--parsed-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="output/parsed",
    help="Directory containing parsed AST files",
)
@click.option(
    "--decompiled-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="output/decompiled",
    help="Directory containing decompiled functions",
)
def generate(parsed_dir: str, decompiled_dir: str) -> None:
    """Generate code from parsed and decompiled data."""
    try:
        from generate.generate_coordinator import (
            generate_flutter,
            generate_models,
            generate_services,
        )

        logger.info("Generating database models...")
        generate_models(parsed_dir)

        logger.info("Generating service layer...")
        generate_services(parsed_dir, decompiled_dir)

        logger.info("Generating Flutter frontend...")
        generate_flutter(parsed_dir)

        logger.info("Code generation complete.")
    except ImportError as e:
        logger.exception(f"Failed to import generation modules: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Failed to generate code: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option(
    "--pbl-input-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_ALL_PBL_INPUT,
    show_default=True,
    help="Input directory containing PBL/PBD files.",
)
@click.option(
    "--base-output-dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_ALL_BASE_OUTPUT,
    show_default=True,
    help="Base directory for all output (extracted, parsed, decompiled, generated).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging for the pipeline, especially extraction.",
)
@click.option(
    "--enable-byte-recovery",
    is_flag=True,
    default=False,
    help='Enable byte-level recovery during extraction phase of "all" pipeline.',
)
@click.pass_context
def all(
    ctx: click.Context,
    pbl_input_dir: str,
    base_output_dir: str,
    debug: bool,
    enable_byte_recovery: bool,
) -> None:
    """Run the full pipeline: extract, parse, decompile, generate."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logging.getLogger("extract.extract_coordinator").setLevel(logging.DEBUG)
        logging.getLogger("extract.pbd").setLevel(logging.DEBUG)
        logging.getLogger("parse").setLevel(logging.DEBUG)
        logger.info("Debug logging enabled for 'all' pipeline.")

    start_time = time.time()

    with PipelineProgress().pipeline_context(total_steps=5) as progress:
        try:
            # Define paths
            extract_input_dir_path = Path(pbl_input_dir)
            base_output_dir_path = Path(base_output_dir)

            extract_output_dir_path = base_output_dir_path / "extracted"
            decompile_output_dir_path = base_output_dir_path / "decompiled"
            parse_output_dir_path = base_output_dir_path / "parsed"

            # Create output directories if they don't exist
            extract_output_dir_path.mkdir(parents=True, exist_ok=True)
            decompile_output_dir_path.mkdir(parents=True, exist_ok=True)
            parse_output_dir_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Extract PBL/PBD files
            progress.start_step("Extracting PowerBuilder files", 1)
            logger.info(
                f"Step 1/5: Extracting PowerBuilder files from {extract_input_dir_path} to {extract_output_dir_path} (byte_recovery={enable_byte_recovery})..."
            )
            extract_pbls(
                str(extract_input_dir_path),
                str(extract_output_dir_path),
                enable_byte_recovery=enable_byte_recovery,
                progress=progress,
            )
            progress.complete_step(1)

            # Step 2: Decompile PCode from extracted files
            progress.start_step("Decompiling P-code", 2)
            logger.info(
                f"Step 2/5: Decompiling PCode from {extract_output_dir_path} to {decompile_output_dir_path}..."
            )
            decompile_directory(
                str(extract_output_dir_path),
                str(decompile_output_dir_path),
                progress=progress,
            )
            progress.complete_step(2)

            # Step 3: Parse extracted source files
            from parse.parse_coordinator import parse_powerbuilder_directory

            progress.start_step("Parsing extracted files", 3)
            logger.info(
                f"Step 3/5: Parsing extracted source files from {extract_output_dir_path} to {parse_output_dir_path}..."
            )
            parse_summary = parse_powerbuilder_directory(
                extract_output_dir_path, parse_output_dir_path
            )
            progress.complete_step(3)

            # Save parsing summary
            summary_file = parse_output_dir_path / "parsed_summary.json"
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(parse_summary, f, indent=2, default=str)
            logger.info(
                f"Parsed {parse_summary['parsed_files']} files successfully, {parse_summary['failed_files']} failed"
            )

            # Step 4: Convert AST to Model objects
            from parse.ast_to_model import ASTToModelConverter

            progress.start_step("Building models", 4)
            model_output_dir_path = base_output_dir_path / "model"
            model_output_dir_path.mkdir(parents=True, exist_ok=True)
            logger.info("Step 4/5: Converting AST to model objects...")

            converter = ASTToModelConverter()
            model_objects = []

            # Process parsed AST files and convert to model objects
            # Find all parsed AST JSON files
            ast_files = list(parse_output_dir_path.rglob("*.ast.json"))
            logger.info(f"Found {len(ast_files)} parsed AST files to convert to model")

            success_count = 0
            error_count = 0

            for ast_file in ast_files:
                try:
                    # Load the parsed AST data
                    with open(ast_file, encoding="utf-8") as f:
                        ast_data = json.load(f)

                    # Extract the AST from the wrapper
                    if "ast" in ast_data:
                        # For now, skip files where AST is stored as pretty-printed string
                        # TODO: Implement proper AST deserialization
                        if isinstance(ast_data["ast"], str):
                            logger.debug(
                                f"Skipping {ast_file.name} - AST is pretty-printed string"
                            )
                            continue

                        # Convert AST to model objects using the converter
                        model_objs = converter.convert_file(ast_data["ast"])
                    else:
                        logger.debug(f"No AST found in {ast_file.name}")
                        continue

                    if model_objs:
                        model_objects.extend(model_objs)

                        # Save model objects to JSON
                        relative_path = ast_file.relative_to(parse_output_dir_path)
                        # Remove .ast.json and add .model.json
                        model_file = (
                            model_output_dir_path
                            / relative_path.parent
                            / relative_path.name.replace(".ast.json", ".model.json")
                        )
                        model_file.parent.mkdir(parents=True, exist_ok=True)

                        # Serialize model objects
                        model_data = {
                            "file": str(relative_path),
                            "models": [
                                {
                                    "type": type(obj).__name__,
                                    "data": obj.__dict__
                                    if hasattr(obj, "__dict__")
                                    else str(obj),
                                }
                                for obj in model_objs
                            ],
                        }

                        with open(model_file, "w", encoding="utf-8") as f:
                            json.dump(model_data, f, indent=2)

                        success_count += 1
                        logger.debug(
                            f"Converted {ast_file.name} to {len(model_objs)} model objects"
                        )
                    else:
                        logger.debug(f"No model objects generated from {ast_file.name}")

                except Exception as e:
                    logger.warning(f"Failed to convert {ast_file.name}: {e}")
                    error_count += 1

            logger.info(
                f"Model conversion complete: {success_count} successful, {error_count} errors"
            )
            logger.info(f"Total model objects created: {len(model_objects)}")
            progress.complete_step(4)

            # Step 5: Generate code from model
            from generate.generate_coordinator import (
                generate_flutter,
                generate_models,
                generate_services,
            )

            progress.start_step("Generating output", 5)
            logger.info("Step 5/5: Generating code...")
            generate_models(str(parse_output_dir_path))
            generate_services(
                str(parse_output_dir_path), str(decompile_output_dir_path)
            )
            generate_flutter(str(parse_output_dir_path))
            progress.complete_step(5)

            elapsed = time.time() - start_time
            logger.info(f"Pipeline complete in {elapsed:.2f} seconds.")
        except ImportError as e:
            logger.exception(f"Failed to import required modules: {e}")
            if click.get_current_context().obj.get("traceback"):
                raise
            sys.exit(1)
        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            if click.get_current_context().obj.get("traceback"):
                raise
            sys.exit(1)


@cli.command()
@click.argument(
    "target_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    required=False,
)
@click.option(
    "--force",
    is_flag=True,
    help="Actually delete the files/directories. Without this, it only lists what would be deleted.",
)
@click.option(
    "--full-recovery",
    is_flag=True,
    help="Target the common 'output/extracted/recovery' directory.",
)
@click.option(
    "--full-extracted",
    is_flag=True,
    help="Target the common 'output/extracted' directory.",
)
@click.option(
    "--full-decompiled",
    is_flag=True,
    help="Target the common 'output/decompiled' directory.",
)
@click.option(
    "--full-parsed", is_flag=True, help="Target the common 'output/parsed' directory."
)
@click.option(
    "--test-outputs", is_flag=True, help="Clean all test output directories (test_*)."
)
def clean_output(
    target_dir: str | None,
    force: bool,
    full_recovery: bool,
    full_extracted: bool,
    full_decompiled: bool,
    full_parsed: bool,
    test_outputs: bool,
) -> None:
    """Clean specific output directories. Lists contents by default; use --force to delete."""
    import shutil

    dirs_to_clean: list[Path] = []
    if target_dir:
        dirs_to_clean.append(Path(target_dir))
    if full_recovery:
        dirs_to_clean.append(Path("output/extracted/recovery"))
    if full_extracted:
        logger.warning(
            "Targeting 'output/extracted'. This is a primary output directory."
        )
        dirs_to_clean.append(Path("output/extracted"))
    if full_decompiled:
        dirs_to_clean.append(Path("output/decompiled"))
    if full_parsed:
        dirs_to_clean.append(Path("output/parsed"))
    if test_outputs:
        output_path = Path("output")
        if output_path.exists():
            # Find all test_* directories
            test_dirs = [
                d
                for d in output_path.iterdir()
                if d.is_dir() and d.name.startswith("test_")
            ]
            dirs_to_clean.extend(test_dirs)
            logger.info(f"Found {len(test_dirs)} test output directories")

    if not dirs_to_clean:
        logger.info(
            "No target directory specified. Use an argument or one of the flags."
        )
        logger.info("Common large directories that can be targeted:")
        logger.info(
            "  output/extracted/recovery  (often very large due to byte recovery)"
        )
        logger.info("  output/extracted           (all extracted files)")
        logger.info("  output/decompiled          (decompiled outputs)")
        logger.info("  output/parsed              (parsed ASTs and structures)")
        logger.info("  --test-outputs             (all test_* directories)")
        return

    for d_path in dirs_to_clean:
        if d_path.exists() and d_path.is_dir():
            logger.info(f"Targeting directory for cleaning: {d_path.resolve()}")
            if force:
                logger.warning(f"--force specified. Deleting {d_path.resolve()}...")
                try:
                    shutil.rmtree(d_path)
                    logger.info(f"Successfully deleted {d_path.resolve()}.")
                except Exception as e:
                    logger.exception(f"Error deleting {d_path.resolve()}: {e}")
            else:
                logger.info(
                    f"Listing contents of {d_path.resolve()} (dry run, use --force to delete):"
                )
                # List top-level contents for brevity
                count = 0
                for item in d_path.iterdir():
                    logger.info(
                        f"  - {item.name} ({'DIR' if item.is_dir() else 'FILE'})"
                    )
                    count += 1
                    if count >= 20:
                        logger.info(
                            "  ... and more (listing capped at 20 items for brevity)."
                        )
                        break
                if count == 0:
                    logger.info("  (Directory is empty)")
        else:
            logger.warning(
                f"Directory not found or is not a directory: {d_path.resolve()}"
            )


if __name__ == "__main__":
    cli()
