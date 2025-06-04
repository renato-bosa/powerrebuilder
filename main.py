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

import logging
import sys
import time
from importlib import metadata
from pathlib import Path

import click

from decompile.legacy.decompile_structured import decompile_directory
from extract.pbd_cli.extract_coordinator import extract_pbls

# Import necessary modules for extraction
# We could also import other utility functions if needed:
# from extract.pbd_core.utils.hexdump_viewer import hex_dump
# from extract.pbd_core.utils.inspect_pbd import inspect_pbd_file

# Import main functions from the refactored modules

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger: logging.Logger = logging.getLogger("tool_pb")

# Default paths
DEFAULT_EXTRACT_INPUT: str = 'input/netpsych/legacy/pbd_files'
DEFAULT_EXTRACT_OUTPUT: str = 'output/extracted'
DEFAULT_PARSE_INPUT: str = 'output/extracted'
DEFAULT_PARSE_OUTPUT: str = 'output/parsed'
DEFAULT_ALL_PBL_INPUT: str = 'input/netpsych/legacy/pbd_files'
DEFAULT_ALL_BASE_OUTPUT: str = 'output'


@click.group()
@click.version_option(version=metadata.version("sime-finch"), prog_name="sime-finch")
@click.option('--loglevel', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False),
              default='INFO', help='Set the logging level.', show_default=True)
@click.option('--traceback/--no-traceback', default=False, help='Show full traceback on error.')
@click.pass_context
def cli(ctx: click.Context, loglevel: str, traceback: bool) -> None:
    """SIME Finch: PowerBuilder Reverse Engineering Toolkit."""
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                        level=getattr(logging, loglevel.upper()))
    ctx.obj = {'traceback': traceback}
    logger.debug(f"Loglevel set to {loglevel.upper()}")
    logger.debug(f"Traceback on error: {traceback}")


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
              default=DEFAULT_PARSE_INPUT)
@click.argument('output_dir', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
              default=DEFAULT_PARSE_OUTPUT)
def parse(input_dir: str, output_dir: str) -> None:
    """Parse raw PowerBuilder files into structured data.

    INPUT_DIR: Directory containing extracted PowerBuilder files
    OUTPUT_DIR: Directory to write parsed data
    """
    try:
        from parse.parse_schema import parse_database_schema
        from parse.parse_ui import parse_powerbuilder_files

        logger.info(f"Starting PowerBuilder file parsing from {input_dir} to {output_dir}...")
        parse_powerbuilder_files(input_dir, output_dir)

        logger.info("Parsing database schema...")
        parse_database_schema(input_dir, output_dir)

        logger.info("Parsing complete.")
    except ImportError as e:
        logger.error(f"Failed to import parsing modules: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to parse files: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)


@cli.command()
def generate() -> None:
    """Generate code from parsed and decompiled data."""
    try:
        from generate.generate_coordinator import (
            generate_frontend,
            generate_models,
            generate_services,
        )

        logger.info("Generating database models...")
        generate_models()

        logger.info("Generating service layer...")
        generate_services()

        logger.info("Generating frontend components...")
        generate_frontend()

        logger.info("Code generation complete.")
    except ImportError as e:
        logger.error(f"Failed to import generation modules: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to generate code: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
              default=DEFAULT_EXTRACT_INPUT)
@click.argument('output_dir', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
              default=DEFAULT_EXTRACT_OUTPUT)
@click.option('--debug', is_flag=True, help='Enable debug logging for extraction')
@click.option('--enable-byte-recovery', is_flag=True, help='Enable byte-level recovery for corrupted files')
def extract(input_dir: str, output_dir: str, debug: bool, enable_byte_recovery: bool) -> None:
    """Extract PB source from PBL/PBD files.

    INPUT_DIR: Directory containing PBL/PBD files
    OUTPUT_DIR: Directory to write extracted source files
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logging.getLogger('extract.pbd_cli.orchestrator').setLevel(logging.DEBUG)
        logging.getLogger('extract.pbd_core').setLevel(logging.DEBUG)

    try:
        logger.info(f"Extracting from {input_dir} to {output_dir} (byte_recovery={enable_byte_recovery})")
        extract_pbls(input_dir, output_dir, enable_byte_recovery=enable_byte_recovery)
        logger.info("Extraction complete")
    except Exception as e:
        logger.error(f"Failed to extract: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)


@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True})
@click.option('--pbl-input-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
              default=DEFAULT_ALL_PBL_INPUT, show_default=True,
              help="Input directory containing PBL/PBD files.")
@click.option('--base-output-dir', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
              default=DEFAULT_ALL_BASE_OUTPUT, show_default=True,
              help="Base directory for all output (extracted, parsed, decompiled, generated).")
@click.option('--debug', is_flag=True, help='Enable debug logging for the pipeline, especially extraction.')
@click.option('--enable-byte-recovery', is_flag=True, default=False, help='Enable byte-level recovery during extraction phase of "all" pipeline.')
@click.pass_context
def all(ctx: click.Context, pbl_input_dir: str, base_output_dir: str, debug: bool, enable_byte_recovery: bool) -> None:
    """Run the full pipeline: extract, parse, decompile, generate."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logging.getLogger('extract.pbd_cli.orchestrator').setLevel(logging.DEBUG)
        logging.getLogger('extract.pbd_core').setLevel(logging.DEBUG)
        logging.getLogger('parse').setLevel(logging.DEBUG)
        logger.info("Debug logging enabled for 'all' pipeline.")

    time.time()
    logger.info("Starting full pipeline...")

    try:
        # Define paths
        extract_input_dir_path = Path(pbl_input_dir)
        base_output_dir_path = Path(base_output_dir)

        extract_output_dir_path = base_output_dir_path / "extracted"
        parse_output_dir_path = base_output_dir_path / "parsed"
        decompile_input_dir_path = extract_output_dir_path  # Decompile from extracted files
        decompile_output_dir_path = base_output_dir_path / "decompiled"

        # Create output directories if they don't exist
        extract_output_dir_path.mkdir(parents=True, exist_ok=True)
        parse_output_dir_path.mkdir(parents=True, exist_ok=True)
        decompile_output_dir_path.mkdir(parents=True, exist_ok=True)

        # Extract PBL/PBD files
        from extract.pbd_cli.extract_coordinator import extract_pbls
        logger.info(f"Extracting PowerBuilder files from {extract_input_dir_path} to {extract_output_dir_path} (byte_recovery={enable_byte_recovery})...")
        extract_pbls(str(extract_input_dir_path), str(extract_output_dir_path), enable_byte_recovery=enable_byte_recovery)

        # Parse extracted files
        from parse.parse_schema import parse_database_schema
        from parse.parse_ui import parse_powerbuilder_files
        logger.info(f"Parsing extracted files from {extract_output_dir_path} to {parse_output_dir_path}...")
        parse_powerbuilder_files(str(extract_output_dir_path), str(parse_output_dir_path))
        parse_database_schema(str(extract_output_dir_path), str(parse_output_dir_path))

        # Decompile PCode
        logger.info(f"Decompiling PCode from {decompile_input_dir_path} to {decompile_output_dir_path}...")
        decompile_directory(str(decompile_input_dir_path), str(decompile_output_dir_path))

        # Generate code
        # TODO: Refactor generate_* functions to accept output_dir arguments
        #       and use a subdirectory of base_output_dir_path (e.g., base_output_dir_path / "generated")
        from generate.generate_coordinator import (
            generate_frontend,
            generate_models,
            generate_services,
        )
        logger.info("Generating code...")
        generate_models()  # Assuming reads from parse_output_dir_path or a default location
        generate_services()  # Assuming reads from decompile_output_dir_path/parse_output_dir_path or default
        generate_frontend()  # Assuming reads from decompile_output_dir_path/parse_output_dir_path or default

        logger.info("Pipeline complete.")
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if click.get_current_context().obj.get('traceback'):
            raise
        sys.exit(1)


@cli.command()
@click.argument('target_dir', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), required=False)
@click.option('--force', is_flag=True, help='Actually delete the files/directories. Without this, it only lists what would be deleted.')
@click.option('--full-recovery', is_flag=True, help="Target the common 'output/extracted/recovery' directory.")
@click.option('--full-extracted', is_flag=True, help="Target the common 'output/extracted' directory.")
@click.option('--full-decompiled', is_flag=True, help="Target the common 'output/decompiled' directory.")
@click.option('--full-parsed', is_flag=True, help="Target the common 'output/parsed' directory.")
def clean_output(target_dir: str | None, force: bool, full_recovery: bool, full_extracted: bool, 
                 full_decompiled: bool, full_parsed: bool) -> None:
    """Clean specific output directories. Lists contents by default; use --force to delete."""
    import shutil

    dirs_to_clean: list[Path] = []
    if target_dir:
        dirs_to_clean.append(Path(target_dir))
    if full_recovery:
        dirs_to_clean.append(Path("output/extracted/recovery"))
    if full_extracted:
        # Carefully add this, as it's a primary output
        logger.warning("Targeting 'output/extracted'. This is a primary output directory.")
        dirs_to_clean.append(Path("output/extracted"))
    if full_decompiled:
        dirs_to_clean.append(Path("output/decompiled"))
    if full_parsed:
        dirs_to_clean.append(Path("output/parsed"))

    if not dirs_to_clean:
        logger.info("No target directory specified. Use an argument or one of the --full-* flags.")
        logger.info("Common large directories that can be targeted:")
        logger.info("  output/extracted/recovery  (often very large due to byte recovery)")
        logger.info("  output/extracted           (all extracted files)")
        logger.info("  output/decompiled          (decompiled outputs)")
        logger.info("  output/parsed              (parsed ASTs and structures)")
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
                    logger.error(f"Error deleting {d_path.resolve()}: {e}")
            else:
                logger.info(f"Listing contents of {d_path.resolve()} (dry run, use --force to delete):")
                # List top-level contents for brevity
                count = 0
                for item in d_path.iterdir():
                    logger.info(f"  - {item.name} ({'DIR' if item.is_dir() else 'FILE'})")
                    count += 1
                    if count >= 20:
                        logger.info("  ... and more (listing capped at 20 items for brevity).")
                        break
                if count == 0:
                    logger.info("  (Directory is empty)")
        else:
            logger.warning(f"Directory not found or is not a directory: {d_path.resolve()}")


if __name__ == "__main__":
    cli()
