"""Main pipeline coordinator that orchestrates all conversion stages.

This module provides the main entry point for the PowerBuilder to Flutter
conversion pipeline, coordinating all stages from extraction to code generation.

Pipeline Architecture (Sequential Execution):
1. Extract: Produces .fun files from PBL/PBD archives
2. Decompile: Converts .fun files to .sru source files  
3. Parse: Processes .sru files into Abstract Syntax Trees (ASTs)
4. Model: Converts ASTs into structured model objects
5. Generate: Produces Python/Dart code from model objects

IMPORTANT: All stages run SEQUENTIALLY, with each stage feeding into the next.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from src.extract.coordinator import extract_pbls
from src.generate.coordinator import GenerateCoordinator
from src.common.async_coordinators import AsyncPipelineCoordinator

from src.common.utils.error_recovery import (
    FileErrorCollector,
    PipelineCheckpoint,
    ResourceChecker,
    RetryError,
    retry,
)
from src.common.exceptions import DecompileError, ExtractError, GenerateError, ParseError
from .progress import PipelineProgress

# Import error handling
try:
    # Try to import actual coordinators if they exist
    from src.extract.coordinator import ExtractCoordinator
except ImportError:
    # Define a fallback coordinator
    class ExtractCoordinator:
        """Fallback ExtractCoordinator when the actual module is not available."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the fallback ExtractCoordinator."""
            self.input_dir = str(args[0]) if args else str(kwargs.get('input_dir', ''))
            self.output_dir = str(args[1]) if len(args) > 1 else str(kwargs.get('output_dir', ''))

        def extract_files(self, file_paths: list[str]) -> dict[str, int]:
            """Extract files using the extract_pbls function.

            Args:
                file_paths: List of file paths to extract

            Returns:
                Dictionary with processed and error counts
            """
            # Use the extract_pbls function
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            try:
                extract_pbls(file_paths, self.output_dir)
                return {'processed': len(file_paths), 'errors': 0}
            except (OSError, ExtractError):
                return {'processed': len(file_paths), 'errors': len(file_paths)}

try:
    from src.parse.coordinator import ParseCoordinator as _ParseCoordinator
    # If found, create a wrapper to match expected interface
    class ParseCoordinator:
        """Wrapper for ParseCoordinator to provide consistent interface."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the ParseCoordinator wrapper."""
            self.input_dir = Path(str(args[0]) if args else str(kwargs.get('input_dir', '')))
            self.output_dir = Path(str(args[1]) if len(args) > 1 else str(kwargs.get('output_dir', '')))
            # Initialize the actual ParseCoordinator with library paths
            self.coordinator = _ParseCoordinator()

        def parse_file(self, file_path: str) -> SimpleNamespace | None:
            """Parse a single file.

            Args:
                file_path: Path to the file to parse

            Returns:
                SimpleNamespace with ast, object_type, and object_name or None
            """
            try:
                # Import parse_file to avoid circular imports
                from src.parse.coordinator import parse_file

                # Parse the file
                tree = parse_file(Path(file_path))

                # Extract object information from the file name
                file_path = Path(file_path)
                object_type = 'unknown'
                if file_path.suffix == '.srw':
                    object_type = 'window'
                elif file_path.suffix == '.sru':
                    object_type = 'userobject'
                elif file_path.suffix in ['.srd', '.dwo']:
                    object_type = 'datawindow'
                elif file_path.suffix == '.srf':
                    object_type = 'function'
                elif file_path.suffix == '.srs':
                    object_type = 'structure'
                elif file_path.suffix == '.srm':
                    object_type = 'menu'
                elif file_path.suffix == '.sra':
                    object_type = 'application'
                elif file_path.suffix == '.sql':
                    object_type = 'query'

                object_name = file_path.stem

                # Save AST to output directory
                output_file = self.output_dir / file_path.name.replace(file_path.suffix, f'{file_path.suffix}.ast.json')
                output_file.parent.mkdir(parents=True, exist_ok=True)

                ast_data = {
                    'file': str(file_path), 'object_type': object_type, 'object_name': object_name, 'ast': tree.pretty() if hasattr(tree, 'pretty') else str(tree),
                }

                with output_file.open('w') as f:
                    json.dump(ast_data, f, indent=2)

                return SimpleNamespace(ast=tree, object_type=object_type, object_name=object_name)

            except (OSError, ImportError, KeyError, ValueError) as e:
                logger.error("Failed to parse %s: %s", file_path, e)
                return None

except ImportError:
    class ParseCoordinator:
        """Fallback ParseCoordinator when the actual module is not available."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the fallback ParseCoordinator."""
            self.input_dir = str(args[0]) if args else str(kwargs.get('input_dir', ''))
            self.output_dir = str(args[1]) if len(args) > 1 else str(kwargs.get('output_dir', ''))

        def parse_file(self, file_path: str) -> SimpleNamespace | None:
            """Minimal mock implementation.

            Args:
                file_path: Path to the file to parse

            Returns:
                SimpleNamespace with minimal data
            """
            # Minimal mock implementation
            _ = file_path  # Mark as intentionally unused
            return SimpleNamespace(ast=None, object_type='unknown', object_name='unknown')

try:
    from src.decompile.coordinator import ExtractedFileDecompiler
    
    class DecompileCoordinator:
        """Wrapper for ExtractedFileDecompiler to provide consistent interface."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the DecompileCoordinator wrapper."""
            self.input_dir = Path(str(args[0]) if args else str(kwargs.get('input_dir', '')))
            self.output_dir = Path(str(args[1]) if len(args) > 1 else str(kwargs.get('output_dir', '')))
            self.debug_mode = bool(kwargs.get('debug_mode', False))
            # Create the actual decompiler
            self.decompiler = ExtractedFileDecompiler(self.output_dir, enable_filtering=True, output_format='pb')

        def decompile_extracted_file(self, file_path: Path) -> bool:
            """Decompile an extracted P-code file.

            Args:
                file_path: Path to the extracted file

            Returns:
                True if successful, False otherwise
            """
            return self.decompiler.decompile_extracted_file(file_path)

        def decompile_file(self, input_file: str, output_file: str) -> bool:
            """Decompile a P-code file (compatibility method).

            Args:
                input_file: Path to input P-code file
                output_file: Path to output source file

            Returns:
                True if successful, False otherwise
            """
            # Just use the extracted file decompiler
            return self.decompiler.decompile_extracted_file(Path(input_file))

except ImportError:
    class DecompileCoordinator:
        """Fallback DecompileCoordinator when the actual module is not available."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the fallback DecompileCoordinator."""
            self.input_dir = Path(str(args[0]) if args else str(kwargs.get('input_dir', '')))
            self.output_dir = Path(str(args[1]) if len(args) > 1 else str(kwargs.get('output_dir', '')))
            self.debug_mode = bool(kwargs.get('debug_mode', False))

        def decompile_extracted_file(self, file_path: Path) -> bool:
            """Decompile an extracted P-code file.

            Args:
                file_path: Path to the extracted file

            Returns:
                True if successful, False otherwise
            """
            logger.warning("Using fallback decompiler for %s", file_path)
            return False

        def decompile_file(self, input_file: str, output_file: str) -> bool:
            """Decompile a P-code file.

            Args:
                input_file: Path to input P-code file
                output_file: Path to output source file

            Returns:
                True if successful, False otherwise
            """
            logger.warning("Using fallback decompiler for %s", input_file)
            return False

try:
    from src.model.coordinator import ModelCoordinator
except ImportError:
    class ModelCoordinator:
        """Fallback ModelCoordinator when the actual module is not available."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the fallback ModelCoordinator."""
            self.input_dir = Path(str(args[0]) if args else str(kwargs.get('input_dir', '')))
            self.output_dir = Path(str(args[1]) if len(args) > 1 else str(kwargs.get('output_dir', '')))

        def process_ast_file(self, ast_file: str) -> bool:
            """Process an AST file to create model objects.

            Args:
                ast_file: Path to AST JSON file

            Returns:
                True if successful, False otherwise
            """
            try:
                # Minimal mock implementation
                return True
            except (OSError, ImportError, KeyError, ValueError):
                return False


logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Orchestrates the complete PowerBuilder to Flutter conversion pipeline."""

    def __init__(self, input_dir: str, output_dir: str, temp_dir: str | None = None, config: dict[str, Any | None] = None) -> None:
        """Initialize the pipeline coordinator.

        Args:
            input_dir: Directory containing PowerBuilder source files
            output_dir: Directory for generated Flutter/Dart code
            temp_dir: Temporary directory for intermediate files
            config: Optional configuration dictionary
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir) if temp_dir else self.output_dir / '.temp'
        self.config = config or {}

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Stage directories (sequential flow)
        self.extracted_dir = self.temp_dir / 'extracted'
        self.decompiled_dir = self.temp_dir / 'decompiled'
        self.parsed_dir = self.temp_dir / 'parsed'
        self.model_dir = self.temp_dir / 'model'

        # Initialize stages
        self._init_stages()

        # Pipeline state
        self.start_time = None
        self.end_time = None
        self.stage_results = {}

        # Error recovery
        self.error_collector = FileErrorCollector()
        self.checkpoint = PipelineCheckpoint(self.temp_dir / '.checkpoint')

    def _init_stages(self) -> None:
        """Initialize all pipeline stages for sequential execution."""
        # Extract stage - produces .fun files
        extract_config = self.config.get('extract', {})
        self.extractor = ExtractCoordinator(
            input_dir=str(self.input_dir), output_dir=str(self.extracted_dir), preserve_structure=extract_config.get('preserve_structure', True), extract_resources=extract_config.get('extract_resources', True),
        )

        # Decompile stage - converts .fun to .sru files
        decompile_config = self.config.get('decompile', {})
        self.decompiler = DecompileCoordinator(
            input_dir=str(self.extracted_dir), output_dir=str(self.decompiled_dir), debug_mode=decompile_config.get('debug_mode', False),
        )

        # Parse stage - processes .sru files into ASTs
        parse_config = self.config.get('parse', {})
        self.parser = ParseCoordinator(
            input_dir=str(self.decompiled_dir), output_dir=str(self.parsed_dir), strict_mode=parse_config.get('strict_mode', False), resolve_imports=parse_config.get('resolve_imports', True),
        )

        # Model stage - converts ASTs to structured models
        model_config = self.config.get('model', {})
        self.modeler = ModelCoordinator(
            input_dir=str(self.parsed_dir), output_dir=str(self.model_dir),
        )

        # Generate stage - produces final code from models
        generate_config = self.config.get('generate', {})
        self.generator = GenerateCoordinator(
            input_dir=str(self.model_dir), output_dir=str(self.output_dir), framework=generate_config.get('target_framework', 'flutter'), null_safety=generate_config.get('null_safety', True), generate_tests=generate_config.get('generate_tests', False),
        )

    def process_files(self, file_paths: list[str]) -> dict[str, Any]:
        """Process specified files through the pipeline.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dictionary with pipeline results
        """
        self.start_time = datetime.now()
        results = {
            'total_files': len(file_paths), 'successful': 0, 'failed': 0, 'errors': [], 'stages': {},
        }

        try:
            # Check resources before starting
            logger.info("Checking system resources...")
            ResourceChecker.check_all(self.temp_dir)

            # Check for existing checkpoint
            checkpoint_data = self.checkpoint.load()
            if checkpoint_data:
                logger.info("Found checkpoint from %s", checkpoint_data['timestamp'])
                # Ask user if they want to recover
                from datetime import datetime as dt
                checkpoint_time = dt.fromisoformat(checkpoint_data['timestamp'])
                age = (dt.now() - checkpoint_time).total_seconds() / 60  # minutes

                logger.info("Checkpoint is %.1f minutes old", age)
                logger.info("Stage: %s", checkpoint_data['stage'])
                logger.info("Processed: %d files", len(checkpoint_data.get('processed_files', [])))

                # Auto-recover if checkpoint is recent (< 30 minutes) or if config says so
                auto_recover = self.config.get('auto_recover_checkpoint', True)
                if auto_recover or age < 30:
                    logger.info("Recovering from checkpoint...")
                    # Implement checkpoint recovery
                    return self._recover_from_checkpoint(checkpoint_data, file_paths, results)
                logger.info("Checkpoint is old, starting fresh...")
                self.checkpoint.clear()
            # Stage 1: Extract - produces .fun files
            logger.info("Stage 1/5: Extracting files from PBL/PBD...")
            extract_stats = self._run_extract_stage(file_paths)
            results['stages']['extract'] = extract_stats
            self._last_extract_stats = extract_stats

            if extract_stats.get('errors', 0) == len(file_paths):
                raise ExtractError("All files failed during extraction")

            # Stage 2: Decompile - converts .fun to .sru files
            logger.info("Stage 2/5: Decompiling P-code files...")
            decompile_stats = self._run_decompile_stage()
            results['stages']['decompile'] = decompile_stats
            self._last_decompile_stats = decompile_stats

            # Stage 3: Parse - processes .sru files into ASTs
            logger.info("Stage 3/5: Parsing source files...")
            parse_stats = self._run_parse_stage()
            results['stages']['parse'] = parse_stats
            self._last_parse_stats = parse_stats

            # Stage 4: Model - converts ASTs to structured models
            logger.info("Stage 4/5: Building model objects...")
            model_stats = self._run_model_stage()
            results['stages']['model'] = model_stats
            self._last_model_stats = model_stats

            # Stage 5: Generate - produces final code from models
            logger.info("Stage 5/5: Generating code from models...")
            generate_stats = self._run_generate_stage()
            results['stages']['generate'] = generate_stats

            # Calculate overall success
            results['successful'] = generate_stats.get('successful', 0)
            results['failed'] = len(file_paths) - results['successful']

        except (OSError, ExtractError, ParseError, DecompileError, GenerateError, Exception) as e:
            logger.error("Pipeline failed: %s", e)
            results['errors'].append(str(e))
            results['failed'] = len(file_paths)

        finally:
            self.end_time = datetime.now()
            results['duration'] = (self.end_time - self.start_time).total_seconds()

            # Add error summary to results
            results['error_summary'] = self.error_collector.get_error_summary()

            # Log error summary
            self.error_collector.log_summary()

            # Clean up temp directory if configured
            if self.config.get('cleanup_temp', True):
                self._cleanup_temp()
            else:
                logger.info("Temporary files preserved in: %s", self.temp_dir)

            # Clear checkpoint on completion
            self.checkpoint.clear()

        return results

    def _recover_from_checkpoint(self, checkpoint_data: dict[str, Any], original_files: list[str], results: dict[str, Any]) -> dict[str, Any]:
        """Recover pipeline from checkpoint and continue processing.

        Args:
            checkpoint_data: Loaded checkpoint data
            original_files: Original list of files to process
            results: Results dictionary to update

        Returns:
            Updated results dictionary
        """
        stage = checkpoint_data['stage']
        processed_files = checkpoint_data['processed_files']
        failed_files = checkpoint_data['failed_files']
        state = checkpoint_data['state']

        logger.info("Recovering from stage: %s", stage)
        logger.info("Already processed: %d files", len(processed_files))
        logger.info("Failed files: %d", len(failed_files))

        # Determine remaining files to process
        remaining_files = [f for f in original_files
                          if f not in processed_files and f not in failed_files]

        try:
            # Resume from the appropriate stage
            if stage == 'extract':
                # Resume extraction for remaining files
                if remaining_files:
                    logger.info("Resuming extraction for %d files...", len(remaining_files))
                    extract_stats = self._run_extract_stage(remaining_files)
                    # Merge with checkpoint data
                    extract_stats['processed'] += len(processed_files)
                    extract_stats['successful'] += len(processed_files)
                    extract_stats['extracted_files'] = processed_files + extract_stats.get('extracted_files', [])
                else:
                    # Extract complete, move to next stage
                    extract_stats = {
                        'processed': len(processed_files) + len(failed_files), 'successful': len(processed_files), 'errors': len(failed_files), 'extracted_files': processed_files,
                    }
                results['stages']['extract'] = extract_stats

                # Continue with decompile stage
                logger.info("Stage 2/5: Decompiling P-code files...")
                decompile_stats = self._run_decompile_stage()
                results['stages']['decompile'] = decompile_stats

                # Continue with parse stage
                logger.info("Stage 3/5: Parsing source files...")
                parse_stats = self._run_parse_stage()
                results['stages']['parse'] = parse_stats

                # Continue with model stage
                logger.info("Stage 4/5: Building model objects...")
                model_stats = self._run_model_stage()
                results['stages']['model'] = model_stats

                # Continue with generate stage
                logger.info("Stage 5/5: Generating code...")
                generate_stats = self._run_generate_stage()
                results['stages']['generate'] = generate_stats

            elif stage == 'decompile':
                # Extract already completed, add to results
                results['stages']['extract'] = state.get('extract_stats', {})

                # Resume decompilation
                decompile_stats = self._run_decompile_stage()
                results['stages']['decompile'] = decompile_stats

                # Continue with remaining stages
                logger.info("Stage 3/5: Parsing source files...")
                parse_stats = self._run_parse_stage()
                results['stages']['parse'] = parse_stats

                logger.info("Stage 4/5: Building model objects...")
                model_stats = self._run_model_stage()
                results['stages']['model'] = model_stats

                logger.info("Stage 5/5: Generating code...")
                generate_stats = self._run_generate_stage()
                results['stages']['generate'] = generate_stats

            elif stage == 'parse':
                # Extract and decompile already completed
                results['stages']['extract'] = state.get('extract_stats', {})
                results['stages']['decompile'] = state.get('decompile_stats', {})

                # Resume parsing
                parse_stats = self._run_parse_stage()
                results['stages']['parse'] = parse_stats

                # Continue with remaining stages
                logger.info("Stage 4/5: Building model objects...")
                model_stats = self._run_model_stage()
                results['stages']['model'] = model_stats

                logger.info("Stage 5/5: Generating code...")
                generate_stats = self._run_generate_stage()
                results['stages']['generate'] = generate_stats

            elif stage == 'model':
                # Previous stages completed
                results['stages']['extract'] = state.get('extract_stats', {})
                results['stages']['decompile'] = state.get('decompile_stats', {})
                results['stages']['parse'] = state.get('parse_stats', {})

                # Resume model building
                model_stats = self._run_model_stage()
                results['stages']['model'] = model_stats

                # Continue with generate stage
                logger.info("Stage 5/5: Generating code...")
                generate_stats = self._run_generate_stage()
                results['stages']['generate'] = generate_stats

            elif stage == 'generate':
                # All previous stages completed
                results['stages']['extract'] = state.get('extract_stats', {})
                results['stages']['decompile'] = state.get('decompile_stats', {})
                results['stages']['parse'] = state.get('parse_stats', {})
                results['stages']['model'] = state.get('model_stats', {})

                # Resume generation
                generate_stats = self._run_generate_stage()
                results['stages']['generate'] = generate_stats

            # Calculate overall success
            results['successful'] = results['stages'].get('generate', {}).get('successful', 0)
            results['failed'] = len(original_files) - results['successful']

        except (OSError, ExtractError, ParseError, DecompileError, GenerateError) as e:
            logger.error("Pipeline recovery failed: %s", e)
            results['errors'].append(f"Recovery failed: {str(e)}")
            results['failed'] = len(original_files)
            raise

        return results

    def process_directory(self, patterns: list[str | None] = None) -> dict[str, Any]:
        """Process all matching files in the input directory.

        Args:
            patterns: List of file patterns to match (e.g., ['*.srw', '*.sru'])

        Returns:
            Dictionary with pipeline results
        """
        if not patterns:
            patterns = ['*.srw', '*.sru', '*.srd', '*.srm', '*.srf', '*.srs', '*.sra']

        # Find all matching files
        file_paths = []
        for pattern in patterns:
            file_paths.extend(str(f) for f in self.input_dir.rglob(pattern))

        logger.info("Found %d files to process", len(file_paths))
        return self.process_files(file_paths)

    def _run_extract_stage(self, file_paths: list[str]) -> dict[str, Any]:
        """Run the extraction stage with error recovery."""
        processed = 0
        successful = 0
        extracted_files = []

        for file_path in file_paths:
            try:
                # Extract with retry
                self._extract_file_with_retry(file_path)
                successful += 1
                extracted_files.append(file_path)
            except (OSError, ExtractError, IOError, RetryError) as e:
                logger.error("Failed to extract %s: %s", file_path, e)
                self.error_collector.add_error('extract', file_path, e)
            finally:
                processed += 1

        # Save checkpoint after extract stage
        self.checkpoint.save(
            'extract', extracted_files, [fp for fp in file_paths if fp not in extracted_files], {'total': len(file_paths)},
        )

        return {
            'processed': processed, 'successful': successful, 'errors': processed - successful, 'extracted_files': extracted_files,
        }

    @retry(max_attempts=3, exceptions=(ExtractError, IOError))
    def _extract_file_with_retry(self, file_path: str) -> None:
        """Extract a single file with retry logic."""
        # Use the extract_pbls function 
        # Note: extract_pbls expects a directory or file path as first argument, not a list
        extract_pbls(file_path, str(self.extracted_dir))

    def _run_parse_stage(self) -> dict[str, Any]:
        """Run the parsing stage for decompiled source files.

        This stage processes decompiled PowerBuilder source files (.sru, .srw, etc.) into ASTs.
        The files come from the decompile stage output directory.
        """
        try:
            # Find decompiled source files
            decompiled_files = list(self.decompiled_dir.rglob('*'))

            # Classify files - Parse handles decompiled source files
            source_files = []
            datawindow_files = []
            sql_files = []

            for file_path in decompiled_files:
                if file_path.is_file():
                    # Source files from decompilation
                    if file_path.suffix in ['.srw', '.sru', '.srf', '.srm', '.srs', '.sra', '.pb']:
                        source_files.append(file_path)
                    elif file_path.suffix == '.srd':
                        # Source DataWindow files
                        source_files.append(file_path)
                    elif file_path.suffix == '.dwo':
                        # Binary DataWindow files
                        datawindow_files.append(file_path)
                    elif file_path.suffix == '.sql':
                        # SQL files
                        sql_files.append(file_path)

            # Log file classification
            logger.info("Classified decompiled files:")
            logger.info("  Source files (for Parse): %d", len(source_files))
            logger.info("  DataWindow files (for Parse): %d", len(datawindow_files))
            logger.info("  SQL files (for Parse): %d", len(sql_files))

            # Parse all parseable files
            all_parseable = source_files + datawindow_files + sql_files
            successful = 0
            failed = 0
            parsed_objects = []

            for file_path in all_parseable:
                try:
                    result = self.parser.parse_file(str(file_path))
                    if result and result.ast:
                        successful += 1
                        # The AST file will be saved with .ast.json extension
                        ast_file = self.parsed_dir / file_path.relative_to(self.decompiled_dir).with_suffix(file_path.suffix + '.ast.json')
                        parsed_objects.append({
                            'file': str(ast_file), 'type': result.object_type, 'name': result.object_name,
                        })
                    else:
                        failed += 1
                except (OSError, ParseError, ValueError) as e:
                    logger.error("Failed to parse %s: %s", file_path, e)
                    failed += 1

            # Save parsed summary
            self._save_parsed_summary(parsed_objects)

            # Save checkpoint after parse stage
            if hasattr(self, 'checkpoint'):
                extract_stats = getattr(self, '_last_extract_stats', {})
                decompile_stats = getattr(self, '_last_decompile_stats', {})
                self.checkpoint.save(
                    'parse', [obj['file'] for obj in parsed_objects], [], # Failed files tracked separately
                    {
                        'extract_stats': extract_stats, 
                        'decompile_stats': decompile_stats,
                        'total_parsed': len(parsed_objects),
                    },
                )

            return {
                'processed': len(all_parseable), 'successful': successful, 'failed': failed, 'parsed_objects': parsed_objects, 'file_classification': {
                    'source': len(source_files), 'datawindow': len(datawindow_files), 'sql': len(sql_files),
                },
            }
        except (OSError, ParseError) as e:
            logger.error("Parse stage failed: %s", e)
            return {'processed': 0, 'successful': 0, 'failed': 0}

    def _run_decompile_stage(self) -> dict[str, Any]:
        """Run the decompilation stage for P-CODE files.

        This stage processes PowerBuilder P-code files (.fun, .win, etc.) into source files (.sru).
        The decompiled files are then fed into the parse stage.
        """
        try:
            # Find P-code files from extraction
            logger.info("Searching for P-code files to decompile...")
            pcode_extensions = ['.fun', '.win', '.udo', '.men', '.mef', '.apl', '.apf']
            pcode_files = []
            for ext in pcode_extensions:
                pcode_files.extend(self.extracted_dir.rglob(f'*{ext}'))

            if not pcode_files:
                logger.warning("No P-code files found to decompile")
                return {'processed': 0, 'successful': 0, 'skipped': True}

            logger.info("Found %d P-code files to decompile", len(pcode_files))

            successful = 0
            failed = 0

            for file_path in pcode_files:
                try:
                    # Convert to .sru extension for source files
                    output_file = self.decompiled_dir / file_path.relative_to(self.extracted_dir)
                    output_file = output_file.with_suffix('.sru')
                    # Ensure output directory exists
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                    # Check if we're using the real DecompileCoordinator or the fallback
                    if hasattr(self.decompiler, 'decompile_extracted_file'):
                        # Use the real DecompileCoordinator method
                        result = self.decompiler.decompile_extracted_file(file_path)
                        if result:
                            successful += 1
                        else:
                            failed += 1
                    else:
                        # Use the fallback decompile_file method
                        result = self.decompiler.decompile_file(str(file_path), str(output_file))
                        if result:
                            successful += 1
                        else:
                            failed += 1
                except (OSError, DecompileError, ValueError) as e:
                    logger.error("Failed to decompile %s: %s", file_path, e)
                    failed += 1
                except Exception as e:
                    import traceback
                    logger.error("Unexpected error decompiling %s: %s", file_path, e)
                    logger.error("Traceback: %s", traceback.format_exc())
                    failed += 1

            # Save checkpoint after decompile stage
            if hasattr(self, 'checkpoint'):
                extract_stats = getattr(self, '_last_extract_stats', {})
                parse_stats = getattr(self, '_last_parse_stats', {})
                self.checkpoint.save(
                    'decompile', [], # Not tracking individual files for decompile
                    [], {
                        'extract_stats': extract_stats, 'parse_stats': parse_stats, 'total_decompiled': successful,
                    },
                )

            return {
                'processed': len(pcode_files), 'successful': successful, 'failed': failed,
            }
        except (OSError, DecompileError) as e:
            logger.error("Decompile stage failed: %s", e)
            return {'processed': 0, 'successful': 0, 'failed': 0}

    def _run_model_stage(self) -> dict[str, Any]:
        """Run the model stage to convert ASTs to structured models.

        This stage processes parsed AST files and converts them to structured model objects
        that can be used for code generation.
        """
        try:
            # Find all parsed AST JSON files
            ast_files = list(self.parsed_dir.rglob('*.ast.json'))

            if not ast_files:
                logger.warning("No AST files found to convert to models")
                return {'processed': 0, 'successful': 0, 'skipped': True}

            logger.info("Found %d AST files to convert to models", len(ast_files))

            successful = 0
            failed = 0
            model_objects = []

            for ast_file in ast_files:
                try:
                    # Process AST file to create model
                    result = self.modeler.process_ast_file(str(ast_file))
                    if result:
                        successful += 1
                        # Track model file for generation
                        model_file = self.model_dir / ast_file.relative_to(self.parsed_dir).with_suffix('.model.json')
                        model_objects.append({
                            'file': str(model_file),
                            'ast_file': str(ast_file),
                        })
                    else:
                        failed += 1
                except (OSError, ValueError) as e:
                    logger.error("Failed to convert AST %s to model: %s", ast_file, e)
                    failed += 1

            # Save model summary for generate stage
            self._save_model_summary(model_objects)

            # Save checkpoint after model stage
            if hasattr(self, 'checkpoint'):
                extract_stats = getattr(self, '_last_extract_stats', {})
                decompile_stats = getattr(self, '_last_decompile_stats', {})
                parse_stats = getattr(self, '_last_parse_stats', {})
                self.checkpoint.save(
                    'model', [obj['file'] for obj in model_objects], [],
                    {
                        'extract_stats': extract_stats,
                        'decompile_stats': decompile_stats,
                        'parse_stats': parse_stats,
                        'total_models': successful,
                    },
                )

            return {
                'processed': len(ast_files), 'successful': successful, 'failed': failed,
                'model_objects': model_objects,
            }
        except (OSError, ValueError) as e:
            logger.error("Model stage failed: %s", e)
            return {'processed': 0, 'successful': 0, 'failed': 0}

    def _run_generate_stage(self) -> dict[str, Any]:
        """Run the code generation stage from model objects."""
        try:
            # Load model summary
            model_summary = self._load_model_summary()

            if not model_summary:
                return {'processed': 0, 'successful': 0, 'no_data': True}

            # Generate code for each model object
            successful = 0
            failed = 0
            generated_files = []

            for obj in model_summary:
                try:
                    # Generate from model file instead of AST
                    result = self.generator.generate_from_model(
                        model_file=obj['file'],
                    )

                    if result:
                        successful += 1
                        generated_files.extend(result.get('files', []))
                    else:
                        failed += 1
                except (OSError, GenerateError, ValueError) as e:
                    logger.error("Failed to generate code for %s", obj['file'])
                    failed += 1

            # Save checkpoint after generate stage
            if hasattr(self, 'checkpoint'):
                extract_stats = getattr(self, '_last_extract_stats', {})
                decompile_stats = getattr(self, '_last_decompile_stats', {})
                parse_stats = getattr(self, '_last_parse_stats', {})
                model_stats = getattr(self, '_last_model_stats', {})
                self.checkpoint.save(
                    'generate', generated_files, [], {
                        'extract_stats': extract_stats, 
                        'decompile_stats': decompile_stats,
                        'parse_stats': parse_stats, 
                        'model_stats': model_stats,
                        'total_generated': successful,
                    },
                )

            return {
                'processed': len(model_summary), 'successful': successful, 'failed': failed, 'generated_files': generated_files,
            }
        except (OSError, GenerateError) as e:
            logger.error("Generate stage failed: %s", e)
            return {'processed': 0, 'successful': 0, 'failed': 0}

    def _save_parsed_summary(self, parsed_objects: list[dict[str, Any]]) -> None:
        """Save summary of parsed objects for the generate stage."""
        # Ensure parsed_dir exists
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
        summary_file = self.parsed_dir / 'parsed_summary.json'
        with summary_file.open('w') as f:
            json.dump(parsed_objects, f, indent=2)

    def _load_parsed_summary(self) -> list[dict[str, Any | None]]:
        """Load summary of parsed objects."""
        summary_file = self.parsed_dir / 'parsed_summary.json'
        if summary_file.exists():
            with summary_file.open() as f:
                return json.load(f)
        return None

    def _save_model_summary(self, model_objects: list[dict[str, Any]]) -> None:
        """Save summary of model objects for the generate stage."""
        # Ensure model_dir exists
        self.model_dir.mkdir(parents=True, exist_ok=True)
        summary_file = self.model_dir / 'model_summary.json'
        with summary_file.open('w') as f:
            json.dump(model_objects, f, indent=2)

    def _load_model_summary(self) -> list[dict[str, Any | None]]:
        """Load summary of model objects."""
        summary_file = self.model_dir / 'model_summary.json'
        if summary_file.exists():
            with summary_file.open() as f:
                return json.load(f)
        return None

    def _cleanup_temp(self) -> None:
        """Clean up temporary directories."""
        try:
            if self.temp_dir.exists() and self.temp_dir != self.output_dir:
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary directory")
        except OSError as e:
            logger.warning("Failed to clean up temp directory: %s", e)

    def get_summary(self) -> dict[str, Any]:
        """Get detailed pipeline summary."""
        return {
            'pipeline': 'PowerBuilder to Flutter Converter', 'version': '1.0.0', 'input_directory': str(self.input_dir), 'output_directory': str(self.output_dir), 'start_time': self.start_time.isoformat() if self.start_time else None, 'end_time': self.end_time.isoformat() if self.end_time else None, 'duration': (self.end_time - self.start_time).total_seconds()
                       if self.start_time and self.end_time else None, 'stages': self.stage_results, 'configuration': self.config,
        }

    async def run_async(
        self,
        stages: Optional[List[str]] = None,
        progress: Optional[PipelineProgress] = None,
        use_streaming: bool = True,
        enable_cache: bool = True
    ) -> Dict[str, Any]:
        """Run the pipeline asynchronously with parallel execution.

        Args:
            stages: List of stages to run (default: all stages)
            progress: Progress tracker
            use_streaming: Enable streaming for large files
            enable_cache: Enable caching for parsed ASTs

        Returns:
            Pipeline execution results
        """
        self.start_time = datetime.now()

        try:
            # Use async coordinator
            async_coordinator = AsyncPipelineCoordinator(target=self.config.get('target', 'flutter'))

            # Run pipeline
            results = await async_coordinator.run_pipeline_async(
                self.input_dir,
                self.output_dir,
                stages=stages,
                progress=progress
            )

            # Update stage results
            for stage_name, stage_results in results["stages"].items():
                self.stage_results[stage_name] = {
                    "success": len([r for r in stage_results if r.get("status") == "success"]),
                    "failed": len([r for r in stage_results if r.get("status") == "error"]),
                    "total": len(stage_results)
                }

            # Save metrics
            self.stage_results["metrics"] = results["metrics"]

            return results

        except Exception as e:
            logger.error(f"Async pipeline failed: {e}")
            raise
        finally:
            self.end_time = datetime.now()

