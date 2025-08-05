#!/usr/bin/env python3
"""Main entry point for the PowerBuilder reverse engineering tool (PowerRebuilder).

This script orchestrates the entire pipeline for converting PowerBuilder applications
to modern web applications through a SEQUENTIAL five-stage process:

1. Extract: Extracts compiled P-code files (.fun) from PowerBuilder binary files (PBL/PBD)

2. Decompile: Converts P-code bytecode (.fun) to PowerBuilder source code (.sru)
   - MUST run BEFORE Parse because Parse requires source code, not bytecode

3. Parse: Processes PowerBuilder source files (.sru) into Abstract Syntax Trees (ASTs)
   - Takes decompiled source as input, outputs structured AST JSON

4. Model: Builds semantic models from parsed ASTs
   - Transforms AST JSON into typed object models

5. Generate: Produces modern applications from semantic models:
   - Backend: Python/Litestar API services
   - Frontend: Flutter/React/Astro applications

The CLI supports both individual pipeline steps and end-to-end processing.
Command-line interface is provided through Click.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import click

# Dependency injection imports removed - files no longer exist
# from src.common.di_configuration import create_config_from_env
# from src.common.injection import get_container
from src.common.output_handler import check_and_prepare_output_directory
from src.common.pipeline.progress import PipelineProgress
from src.core.logging import configure_pipeline_logging, get_logger
from src.decompile.coordinator import decompile_directory, extract_database_schema
from src.extract.pbd.extraction import binary_to_readable_format
# stream_extract_pbd was removed during consolidation - using Library class instead

# Initial basic logging setup - will be reconfigured by CLI
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
logger: logging.Logger = get_logger("tool_pb")

# Default paths
DEFAULT_EXTRACT_INPUT: str = "input"
DEFAULT_EXTRACT_OUTPUT: str = "data/output/current/extracted"
DEFAULT_PARSE_INPUT: str = "data/output/current/extracted"
DEFAULT_PARSE_OUTPUT: str = "data/output/current/parsed"
DEFAULT_ALL_PBL_INPUT: str = "input"
DEFAULT_ALL_BASE_OUTPUT: str = "output"


@click.group()
@click.version_option(version="0.1.0", prog_name="sime-finch")
@click.option(
    "--loglevel",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=False,
    ),
    default="INFO",
    help="Set the logging level.",
    show_default=True,
)
@click.option(
    "--traceback/--no-traceback",
    default=False,
    help="Show full traceback on error.",
)
@click.option(
    "--no-overwrite",
    is_flag=True,
    default=False,
    help="Prevent overwriting existing output files. Will exit if output directory contains files.",
)
@click.pass_context
def cli(ctx: click.Context, loglevel: str, traceback: bool, no_overwrite: bool) -> None:
    """SIME Finch: PowerBuilder Reverse Engineering Toolkit."""
    # Use optimized logging configuration
    verbose = loglevel.upper() == "DEBUG"
    configure_pipeline_logging("powerrebuilder", verbose=verbose)

    # Override with specific log level if needed
    if loglevel.upper() != "INFO":
        logging.getLogger().setLevel(getattr(logging, loglevel.upper()))

    # DI container initialization removed - files no longer exist
    # container = get_container()
    # config = create_config_from_env()
    # config.configure(container)

    ctx.obj = {"traceback": traceback, "no_overwrite": no_overwrite}
    logger.debug(f"Loglevel set to {loglevel.upper()}")
    logger.debug(f"Traceback on error: {traceback}")
    logger.debug(f"No overwrite mode: {no_overwrite}")


# Extract group for all extraction-related commands
@cli.group()
def extract() -> None:
    """PowerBuilder extraction utilities."""


@extract.command("files")
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True),
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
@click.pass_context
def extract_files(
    ctx: click.Context,
    input_dir: str,
    output_dir: str,
    debug: bool,
    enable_byte_recovery: bool,
) -> None:
    """Extract PB source from PBL/PBD files.

    INPUT_DIR: Directory containing PBL/PBD files
    OUTPUT_DIR: Directory to write extracted source files
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("extract.extract_coordinator").setLevel(logging.DEBUG)
        logging.getLogger("extract.pbd").setLevel(logging.DEBUG)

    try:
        input_path = Path(input_dir)
        
        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="extract"
        )
        
        if not should_proceed:
            logger.info("Extraction cancelled by user")
            sys.exit(0)

        logger.info(
            f"Extracting from {input_dir} to {output_path} (byte_recovery={enable_byte_recovery})",
        )

        # Use simple extraction approach
        from src.extract.extract import extract_with_recovery

        # Handle both files and directories
        if input_path.is_file():
            # Single file extraction
            success = extract_with_recovery(
                input_path,
                output_path,
                show_progress=True,
                enable_byte_recovery=enable_byte_recovery,
                extract_resources=True,
            )
        else:
            # Directory extraction - find all PBL/PBD files
            pbl_files = []
            for ext in ["*.pbl", "*.pbd", "*.PBL", "*.PBD"]:
                pbl_files.extend(input_path.glob(ext))
                pbl_files.extend(input_path.rglob(ext))  # Recursive search
            
            # Remove duplicates
            pbl_files = list(set(pbl_files))
            
            if not pbl_files:
                logger.warning(f"No PBL/PBD files found in {input_path}")
                return
            
            logger.info(f"Found {len(pbl_files)} PBL/PBD files to extract")
            
            # Extract each file
            success = True
            for pbl_file in sorted(pbl_files):
                # Create output subdirectory based on input file name
                file_output = output_path / pbl_file.stem
                file_output.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"Extracting {pbl_file.name} to {file_output}")
                
                file_success = extract_with_recovery(
                    pbl_file,
                    file_output,
                    show_progress=True,
                    enable_byte_recovery=enable_byte_recovery,
                    extract_resources=True,
                    )
                
                if not file_success:
                    success = False
                    logger.error(f"Failed to extract {pbl_file}")

        if not success:
            logger.error("Extraction completed with errors")

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
                    with open(output_path, encoding="utf-8"):
                        pass
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
@click.pass_context
def parse(ctx: click.Context, input_dir: str, output_dir: str) -> None:
    """Parse PowerBuilder SOURCE files into Abstract Syntax Trees (ASTs).

    This processes SOURCE files extracted from PBL/PBD archives:
    - Window files (.srw)
    - User object files (.sru)
    - Function files (.srf)
    - Menu files (.srm)
    - Structure files (.srs)
    - Application files (.sra)
    - DataWindow files (.srd)

    NOTE: This stage runs in PARALLEL with the Decompile stage.
    P-code files (.fun, .win, etc.) are handled by Decompile, not Parse.

    INPUT_DIR: Directory containing extracted PowerBuilder source files
    OUTPUT_DIR: Directory to write parsed AST data
    """
    try:
        import json
        from pathlib import Path

        from src.parse.coordinator import ParseCoordinator

        input_path = Path(input_dir)
        
        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="parse"
        )
        
        if not should_proceed:
            logger.info("Parsing cancelled by user")
            sys.exit(0)

        logger.info(
            f"Starting PowerBuilder file parsing from {input_path} to {output_path}...",
        )

        # Create parse coordinator in simple mode
        coordinator = ParseCoordinator(input_path, output_path)
        # Parse all PowerBuilder files in the directory
        parsed_data = coordinator.process()

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
    default="data/output/current/decompiled",
)
@click.option(
    "--parallel",
    "-p",
    is_flag=True,
    default=False,
    help="Enable parallel processing for faster decompilation",
)
@click.option(
    "--max-workers",
    "-w",
    type=int,
    default=None,
    help="Maximum number of parallel workers (defaults to CPU count)",
)
@click.option(
    "--use-processes",
    is_flag=True,
    default=True,
    help="Use process-based parallelism instead of threads (default: True)",
)
@click.option(
    "--use-threads",
    "use_processes",
    flag_value=False,
    help="Use thread-based parallelism instead of processes",
)
@click.option(
    "--memory-mapping",
    is_flag=True,
    default=True,
    help="Enable memory mapping for large files (default: True)",
)
@click.option(
    "--no-memory-mapping",
    "memory_mapping",
    flag_value=False,
    help="Disable memory mapping for large files",
)
@click.option(
    "--progress",
    is_flag=True,
    default=True,
    help="Show enhanced progress reporting (default: True)",
)
@click.option(
    "--no-progress",
    "progress",
    flag_value=False,
    help="Disable enhanced progress reporting",
)
@click.pass_context
def decompile(
    ctx: click.Context,
    input_dir: str, 
    output_dir: str,
    parallel: bool,
    max_workers: int | None,
    use_processes: bool,
    memory_mapping: bool,
    progress: bool,
) -> None:
    """Decompile PowerBuilder P-CODE files to high-level pseudocode.

    This processes P-CODE (bytecode) files extracted from PBL/PBD archives:
    - Function P-code (.fun)
    - Window P-code (.win)
    - User object P-code (.udo)
    - Menu P-code (.men)
    - Menu function P-code (.mef)
    - Application P-code (.apl)
    - Application function P-code (.apf)

    NOTE: This stage runs in PARALLEL with the Parse stage.
    Source files (.srw, .sru, etc.) are handled by Parse, not Decompile.

    \b
    Examples:
      # Basic decompilation
      sime-finch decompile data/output/current/extracted data/output/current/decompiled
      
      # Enable parallel processing with 8 workers
      sime-finch decompile --parallel --max-workers 8 input_dir output_dir
      
      # Use thread-based parallelism for I/O-bound workloads
      sime-finch decompile --parallel --use-threads input_dir output_dir
      
      # Disable progress bars for automated scripts
      sime-finch decompile --no-progress input_dir output_dir

    INPUT_DIR: Directory containing extracted PowerBuilder P-code files
    OUTPUT_DIR: Directory to write decompiled high-level code
    """
    try:
        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="decompile"
        )
        
        if not should_proceed:
            logger.info("Decompilation cancelled by user")
            sys.exit(0)
            
        logger.info(f"Decompiling PCode from {input_dir} to {output_path}...")
        output_dir_str = str(output_path)  # Convert back to string for coordinators
        
        if parallel:
            # Use parallel coordinator for enhanced performance
            logger.info("Using parallel decompilation with enhanced progress reporting")
            from src.decompile.parallel_coordinator import ParallelDecompileCoordinator
            
            coordinator = ParallelDecompileCoordinator(
                input_dir=input_dir,
                output_dir=output_dir_str,
                max_workers=max_workers,
                use_processes=use_processes,
                enable_memory_mapping=memory_mapping,
                progress_refresh_rate=0.1 if progress else 1.0,
            )
            
            result = coordinator.decompile()
            
            # Log summary
            if result["status"] == "completed":
                logger.info("Parallel decompilation completed successfully:")
                logger.info("  Files processed: %d/%d", result["processed_files"], result["total_files"])
                if "performance" in result:
                    perf = result["performance"]
                    logger.info("  Duration: %s seconds", perf.get("duration_seconds", "N/A"))
                    logger.info("  Success rate: %s", perf.get("success_rate", "N/A"))
                    logger.info("  Throughput: %s MB/s", perf.get("throughput_mb_per_sec", "N/A"))
            else:
                logger.error("Parallel decompilation failed: %s", result.get("error", "Unknown error"))
                sys.exit(1)
        else:
            # Use enhanced coordinator with caching and parallel processing
            logger.info("Using enhanced sequential decompilation with caching")
            from src.decompile.coordinator import DecompileCoordinator
            
            coordinator = DecompileCoordinator(
                input_dir=input_dir,
                output_dir=output_dir_str,
                enable_byte_recovery=False,
                output_format="pb",
                enable_filtering=True,
            )
            
            result = coordinator.decompile(
                enable_cache=True,
                enable_parallel=False,  # Sequential mode but with caching
            )
            
            # Log enhanced results
            if result["status"] == "completed":
                logger.info("Enhanced decompilation completed successfully:")
                logger.info("  Files processed: %d/%d", result["decompiled"], result["total_files"])
                logger.info("  Cache hit rate: %s", result.get("cache_hit_rate", "N/A"))
                logger.info("  Duration: %.1f seconds", result.get("duration_seconds", 0))
            else:
                logger.error("Enhanced decompilation failed: %s", result.get("error", "Unknown error"))
                sys.exit(1)
        
        logger.info("Decompilation complete.")
    except Exception as e:
        logger.exception(f"Failed to decompile: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=DEFAULT_PARSE_OUTPUT,
)
@click.argument(
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default="data/output/current/model",
)
@click.pass_context
def model(ctx: click.Context, input_dir: str, output_dir: str) -> None:
    """Convert parsed AST files to semantic model objects.

    This is the Model stage of the pipeline, which converts Abstract Syntax Trees
    (ASTs) from the Parse stage into structured semantic models that can be used
    by the Generate stage to produce modern code.

    INPUT_DIR: Directory containing parsed AST JSON files
    OUTPUT_DIR: Directory for model JSON files
    """
    try:
        from src.model.coordinator import ModelCoordinator

        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="model"
        )
        
        if not should_proceed:
            logger.info("Model conversion cancelled by user")
            sys.exit(0)

        logger.info(f"Converting ASTs from {input_dir} to models in {output_path}")

        # Initialize coordinator with services
        from src.model.services import (
            ASTProcessor,
            EntityFactory,
            EntityValidator,
            ModelExtractor,
            ModelPersistence,
            RelationshipManager,
        )

        coordinator = ModelCoordinator(
            entity_factory=EntityFactory(),
            entity_validator=EntityValidator(),
            relationship_manager=RelationshipManager(),
            ast_processor=ASTProcessor(),
            model_extractor=ModelExtractor(),
            model_persistence=ModelPersistence(),
            input_dir=input_dir,
            output_dir=str(output_path),
        )

        # Convert all AST files
        result = coordinator.convert_directory()

        # Log results
        success_rate = (
            result["processed"] / (result["processed"] + result["failed"])
            if (result["processed"] + result["failed"]) > 0
            else 0
        )
        logger.info(
            f"Model conversion complete. Processed: {result['processed']}, "
            f"Failed: {result['failed']}, Success rate: {success_rate:.1%}"
        )

        # Save summary
        summary_file = output_path / "model_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "model_at": datetime.now().isoformat(),
                    "input_directory": str(input_dir),
                    "output_directory": str(output_dir),
                    **result,
                },
                f,
                indent=2,
            )

        logger.info(f"Model summary saved to {summary_file}")

    except ImportError as e:
        logger.exception(f"Failed to import model modules: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Failed to convert models: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--model-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing model files from Model stage",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for generated code",
)
@click.option(
    "--parsed-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing parsed AST files (legacy)",
)
@click.option(
    "--decompiled-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing decompiled functions (legacy)",
)
@click.option(
    "--target",
    type=click.Choice(["python", "flutter", "both"]),
    default="both",
    help="Target language to generate",
)
def generate(
    model_dir: str | None,
    output_dir: str | None,
    parsed_dir: str | None,
    decompiled_dir: str | None,
    target: str,
) -> None:
    """Generate modern application code from model files.

    This is the final stage of the pipeline, which takes semantic model objects
    from the Model stage and generates modern application code:
    - Backend: Python/Litestar APIs, SQLModel models, Pydantic schemas
    - Frontend: Flutter/Dart UI, screens, widgets, state management

    Note: --parsed-dir and --decompiled-dir are kept for backward compatibility.
    Use --model-dir for the new pipeline that reads from Model stage output.
    """
    try:
        from src.generate.coordinator import (
            GenerateCoordinator,
            generate_flutter,
            generate_models,
            generate_services,
        )

        # Use new pipeline if model-dir is provided
        if model_dir and output_dir:
            logger.info(f"Generating {target} code from model files...")
            coordinator = GenerateCoordinator(model_dir, output_dir)
            results = coordinator.process()

            # Results is a dict with counts, not file lists
            if isinstance(results, dict):
                total_files = results.get("files_generated", 0)
                logger.info(f"Generated {total_files} files")
                logger.info(
                    f"  Processed: {results.get('total_models', 0)} model files"
                )
                logger.info(f"  Failed: {len(results.get('failed_files', []))} files")

        # Fall back to legacy pipeline
        elif parsed_dir:
            logger.info("Using legacy generation pipeline...")

            if target in ["python", "both"]:
                logger.info("Generating database models...")
                generate_models(parsed_dir)

                if decompiled_dir:
                    logger.info("Generating service layer...")
                    generate_services(parsed_dir, decompiled_dir)

            if target in ["flutter", "both"]:
                logger.info("Generating Flutter frontend...")
                generate_flutter(parsed_dir)

            logger.info("Code generation complete.")
        else:
            raise click.UsageError(
                "Either --model-dir and --output-dir or --parsed-dir must be provided"
            )

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


@cli.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=".",
    show_default=True,
    help="PowerBuilder project directory containing source files",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    default="output/schema",
    show_default=True,
    help="Output directory for schema documentation",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "json"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Output format for documentation",
)
@click.option(
    "--include-flows/--no-flows",
    default=True,
    show_default=True,
    help="Include data flow analysis in documentation",
)
def schema(project_dir: str, output_dir: str, format: str, include_flows: bool) -> None:
    """Extract and document database schema from PowerBuilder code.

    This command analyzes PowerBuilder source files to extract:
    - Database tables and columns
    - Table relationships (foreign keys)
    - Business logic functions and their database operations
    - UI elements and their data bindings
    - Data flow between components

    The output is a comprehensive documentation file that maps all database
    interactions in human-readable format.
    """
    try:
        logger.info("Extracting database schema from PowerBuilder project...")
        logger.info(f"Project directory: {project_dir}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Documentation format: {format}")

        # Create progress tracker
        progress = PipelineProgress(total_steps=3)
        progress.start_step("Extracting database schema", 1)

        # Extract schema with progress tracking
        extract_database_schema(
            project_dir=project_dir,
            output_dir=output_dir,
            output_format=format,
            progress=progress,
        )

        progress.complete_step(1)
        logger.info("Database schema extraction complete!")

        # Show output location
        output_path = Path(output_dir)
        doc_file = (
            output_path
            / f"database_schema_documentation.{format if format != 'html' else 'html'}"
        )
        logger.info(f"Documentation saved to: {doc_file}")
        logger.info(f"Raw data saved to: {output_path / 'database_schema_raw.json'}")

    except Exception as e:
        logger.exception(f"Failed to extract database schema: {e}")
        if click.get_current_context().obj.get("traceback"):
            raise
        sys.exit(1)


@cli.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
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
    """Run the full pipeline: extract, decompile, parse, model, generate.

    Pipeline Execution Flow (Sequential):
    1. Extract: Produces .fun files from PBL/PBD archives
    2. Decompile: Converts .fun files to .sru source files
    3. Parse: Processes .sru files into Abstract Syntax Trees (ASTs)
    4. Model: Converts ASTs into structured model objects
    5. Generate: Produces Python/Dart code from model objects

    All stages run SEQUENTIALLY, with each stage feeding into the next.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("extract.extract_coordinator").setLevel(logging.DEBUG)
        logging.getLogger("extract.pbd").setLevel(logging.DEBUG)
        logging.getLogger("parse").setLevel(logging.DEBUG)
        logger.info("Debug logging enabled for 'all' pipeline.")

    start_time = time.time()

    try:
        # Import and use PipelineCoordinator
        from src.common.pipeline.pipeline_coordinator import PipelineCoordinator

        # Configure pipeline
        config = {
            "extract": {
                "preserve_structure": True,
                "extract_resources": True,
                "enable_byte_recovery": enable_byte_recovery,
            },
            "decompile": {
                "debug_mode": debug,
            },
            "parse": {
                "strict_mode": False,
                "resolve_imports": True,
            },
            "model": {},
            "generate": {
                "target_framework": "flutter",
                "null_safety": True,
                "generate_tests": False,
            },
            "cleanup_temp": False,  # Keep temp files for debugging
            "auto_recover_checkpoint": True,
        }

        # Check and prepare output directory
        no_overwrite = ctx.obj.get("no_overwrite", False)
        output_path, should_proceed = check_and_prepare_output_directory(
            base_output_dir,
            allow_overwrite=not no_overwrite,
            force_overwrite=False,
            interactive=True,
            stage_name="full pipeline"
        )
        
        if not should_proceed:
            logger.info("Full pipeline cancelled by user")
            sys.exit(0)

        # Create pipeline coordinator
        logger.info("Initializing pipeline coordinator...")
        coordinator = PipelineCoordinator(
            input_dir=pbl_input_dir, output_dir=str(output_path), config=config
        )

        # Find all PBL/PBD files to process
        input_path = Path(pbl_input_dir)
        pbl_files = []

        if input_path.is_file():
            # Single file
            if input_path.suffix.lower() in [".pbl", ".pbd"]:
                pbl_files.append(str(input_path))
        else:
            # Directory - find all PBL/PBD files
            for ext in ["*.pbl", "*.pbd"]:
                pbl_files.extend(str(f) for f in input_path.rglob(ext))

        if not pbl_files:
            logger.error("No PBL/PBD files found in %s", pbl_input_dir)
            sys.exit(1)

        logger.info("Found %d PBL/PBD files to process", len(pbl_files))

        # Run the pipeline
        logger.info("Starting sequential pipeline execution...")
        results = coordinator.process_files(pbl_files)

        # Display results
        logger.info("Pipeline execution completed!")
        logger.info("Results:")
        logger.info("  Total files processed: %d", results.get("total_files", 0))
        logger.info("  Successful: %d", results.get("successful", 0))
        logger.info("  Failed: %d", results.get("failed", 0))

        # Display stage results
        if "stages" in results:
            logger.info("\nStage Results:")
            for stage_name, stage_stats in results["stages"].items():
                logger.info("  %s:", stage_name.capitalize())
                logger.info("    Processed: %d", stage_stats.get("processed", 0))
                logger.info("    Successful: %d", stage_stats.get("successful", 0))
                logger.info("    Failed: %d", stage_stats.get("failed", 0))

        # Display error summary if any
        if results.get("error_summary"):
            logger.warning("\nError Summary:")
            error_summary = results["error_summary"]
            if "errors" in error_summary:
                for stage, count in error_summary["errors"].items():
                    if count > 0:
                        logger.warning("  %s: %d errors", stage, count)
            if "warnings" in error_summary:
                for stage, count in error_summary["warnings"].items():
                    if count > 0:
                        logger.warning("  %s: %d warnings", stage, count)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"\nTotal pipeline execution time: {elapsed_time:.2f} seconds")

        # Exit with appropriate code
        if results.get("failed", 0) > 0:
            sys.exit(1)

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
    help="Target the common 'data/output/current/extracted/recovery' directory.",
)
@click.option(
    "--full-extracted",
    is_flag=True,
    help="Target the common 'data/output/current/extracted' directory.",
)
@click.option(
    "--full-decompiled",
    is_flag=True,
    help="Target the common 'data/output/current/decompiled' directory.",
)
@click.option(
    "--full-parsed",
    is_flag=True,
    help="Target the common 'data/output/current/parsed' directory.",
)
@click.option(
    "--test-outputs",
    is_flag=True,
    help="Clean all test output directories (test_*).",
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
        dirs_to_clean.append(Path("data/output/current/extracted/recovery"))
    if full_extracted:
        logger.warning(
            "Targeting 'data/output/current/extracted'. This is a primary output directory.",
        )
        dirs_to_clean.append(Path("data/output/current/extracted"))
    if full_decompiled:
        dirs_to_clean.append(Path("data/output/current/decompiled"))
    if full_parsed:
        dirs_to_clean.append(Path("data/output/current/parsed"))
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
            "No target directory specified. Use an argument or one of the flags.",
        )
        logger.info("Common large directories that can be targeted:")
        logger.info(
            "  data/output/current/extracted/recovery  (often very large due to byte recovery)",
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
                    f"Listing contents of {d_path.resolve()} (dry run, use --force to delete):",
                )
                # List top-level contents for brevity
                count = 0
                for item in d_path.iterdir():
                    logger.info(
                        f"  - {item.name} ({'DIR' if item.is_dir() else 'FILE'})",
                    )
                    count += 1
                    if count >= 20:
                        logger.info(
                            "  ... and more (listing capped at 20 items for brevity).",
                        )
                        break
                if count == 0:
                    logger.info("  (Directory is empty)")
        else:
            logger.warning(
                f"Directory not found or is not a directory: {d_path.resolve()}",
            )


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
    required=True,
)
@click.argument(
    "output_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
@click.option(
    "--streaming/--no-streaming",
    default=True,
    help="Use streaming extraction for large files (default: enabled)",
)
@click.option(
    "--async/--sync",
    "use_async",
    default=False,
    help="Use async extraction for better performance",
)
@click.option(
    "--chunk-size",
    type=int,
    default=8192,
    help="Chunk size for streaming operations (default: 8192)",
)
def extract_streaming(
    input_path: Path,
    output_path: Path,
    streaming: bool,
    use_async: bool,
    chunk_size: int,
) -> None:
    """Extract PBD files using the Library class.
    
    NOTE: Streaming and async functionality was removed during code consolidation.
    All extraction now uses the Library class for consistency and simplicity.
    The streaming and use_async parameters are kept for CLI compatibility but ignored.
    """
    if streaming or use_async:
        logger.warning(
            "Streaming and async extraction was removed during consolidation. "
            "Using standard Library class extraction instead."
        )
    logger.info("Extracting PBD files using Library class...")

    output_path.mkdir(parents=True, exist_ok=True)

    if input_path.is_file() and input_path.suffix.lower() in (".pbd", ".pbl"):
        # Single file extraction - using Library class (streaming was removed during consolidation)
        from src.extract.pbd.library import Library
        with Library(input_path) as lib:
            lib.extract_all(output_path)
            logger.info(f"Extracted {len(lib)} entries from {input_path.name}")
    else:
        # Directory extraction
        pbd_files = list(input_path.glob("*.pbd")) + list(input_path.glob("*.pbl"))
        logger.info(f"Found {len(pbd_files)} PBD/PBL files")

        for pbd_file in pbd_files:
            file_output = output_path / pbd_file.stem
            # Using Library class (streaming was removed during consolidation)
            from src.extract.pbd.library import Library
            with Library(pbd_file) as lib:
                lib.extract_all(file_output)
                logger.info(f"Extracted {len(lib)} entries from {pbd_file.name}")


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
@click.argument(
    "output_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
@click.option(
    "--target",
    type=click.Choice(["flutter", "python", "typescript"]),
    default="flutter",
    help="Target language for code generation",
)
@click.option(
    "--parallel/--sequential",
    default=True,
    help="Run Parse and Decompile stages in parallel (default: enabled)",
)
@click.option(
    "--async/--sync",
    "use_async",
    default=False,
    help="Use async pipeline for better performance",
)
@click.option(
    "--cache/--no-cache",
    default=True,
    help="Enable caching for parsed ASTs (default: enabled)",
)
@click.option(
    "--streaming/--no-streaming",
    default=True,
    help="Use streaming for large files (default: enabled)",
)
def all_parallel(
    input_path: Path,
    output_path: Path,
    target: str,
    parallel: bool,
    use_async: bool,
    cache: bool,
    streaming: bool,
) -> None:
    """Run the full pipeline with performance optimizations.

    This command runs the complete PowerBuilder to target language conversion
    with various performance optimizations:

    - Parallel execution of Parse and Decompile stages
    - Async processing for better I/O handling
    - Streaming support for large files
    - Caching of parsed ASTs
    """
    from src.common.pipeline.pipeline_coordinator import PipelineCoordinator

    logger.info("Running optimized pipeline:")
    logger.info(f"  Target: {target}")
    logger.info(f"  Parallel: {'enabled' if parallel else 'disabled'}")
    logger.info(f"  Async: {'enabled' if use_async else 'disabled'}")
    logger.info(f"  Cache: {'enabled' if cache else 'disabled'}")
    logger.info(f"  Streaming: {'enabled' if streaming else 'disabled'}")

    coordinator = PipelineCoordinator(
        input_dir=input_path,
        output_dir=output_path,
        config={
            "target": target,
            "parallel": parallel,
            "cache": {"enabled": cache},
            "streaming": streaming,
        },
    )

    # Find all PBL/PBD files to process
    input_path_obj = Path(input_path)
    pbl_files = []

    if input_path_obj.is_file():
        # Single file
        if input_path_obj.suffix.lower() in [".pbl", ".pbd"]:
            pbl_files.append(str(input_path_obj))
    else:
        # Directory - find all PBL/PBD files
        for ext in ["*.pbl", "*.pbd"]:
            pbl_files.extend(str(f) for f in input_path_obj.rglob(ext))

    if not pbl_files:
        logger.error("No PBL/PBD files found in %s", input_path)
        sys.exit(1)

    logger.info("Found %d PBL/PBD files to process", len(pbl_files))

    # Run the pipeline
    logger.info("Starting parallel pipeline execution...")
    results = coordinator.process_files(pbl_files)

    # Print summary
    logger.info("\nPipeline Summary:")
    logger.info(f"  Total files: {results.get('total_files', 0)}")
    logger.info(f"  Successful: {results.get('successful', 0)}")
    logger.info(f"  Failed: {results.get('failed', 0)}")

    if results.get("error_summary", {}).get("errors"):
        logger.error("Pipeline completed with errors")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully")


@cli.command()
@click.option(
    "--size", type=int, default=1000, help="Maximum number of entries to cache"
)
@click.option("--memory", type=int, default=512, help="Maximum cache memory in MB")
def cache_stats(size: int, memory: int) -> None:
    """Display cache statistics and optionally configure cache settings."""
    import asyncio

    from src.core.cache import get_ast_cache, get_validation_cache

    async def show_stats() -> None:
        ast_cache = await get_ast_cache()
        validation_cache = await get_validation_cache()

        logger.info("AST Cache Statistics:")
        stats = ast_cache.stats()
        logger.info(f"  Size: {stats['size']} entries")
        logger.info(f"  Memory: {stats['memory'] / 1024 / 1024:.1f} MB")
        logger.info(f"  Hit rate: {stats['hit_rate']:.2%}")
        logger.info(f"  Hits: {stats['hits']}")
        logger.info(f"  Misses: {stats['misses']}")

        logger.info("\nValidation Cache Statistics:")
        stats = validation_cache.stats()
        logger.info(f"  Size: {stats['size']} entries")
        logger.info(f"  Memory: {stats['memory'] / 1024 / 1024:.1f} MB")
        logger.info(f"  Hit rate: {stats['hit_rate']:.2%}")
        logger.info(f"  Hits: {stats['hits']}")
        logger.info(f"  Misses: {stats['misses']}")

    asyncio.run(show_stats())


if __name__ == "__main__":
    cli()
