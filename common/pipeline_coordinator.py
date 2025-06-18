"""Main pipeline coordinator that orchestrates all conversion stages.

This module provides the main entry point for the PowerBuilder to Flutter
conversion pipeline, coordinating all stages from extraction to code generation.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from extract.extract_coordinator import extract_pbls
from parse.parse_coordinator import parse_powerbuilder_directory  
from decompile.decompile_coordinator import decompile_directory
from generate.generate_coordinator import GenerateCoordinator
from .error_recovery import (
    retry, FileErrorCollector, ResourceChecker, 
    PipelineCheckpoint, ResourceError
)
from .exceptions import ExtractError

# Import error handling
try:
    # Try to import actual coordinators if they exist
    from extract.extract_coordinator import ExtractCoordinator
except ImportError:
    # Define a fallback coordinator
    class ExtractCoordinator:
        def __init__(self, *args, **kwargs):
            self.input_dir = args[0] if args else kwargs.get('input_dir', '')
            self.output_dir = args[1] if len(args) > 1 else kwargs.get('output_dir', '')
            
        def extract_files(self, file_paths):
            # Use the extract_pbls function
            from pathlib import Path
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            try:
                extract_pbls(file_paths, self.output_dir)
                return {'processed': len(file_paths), 'errors': 0}
            except Exception as e:
                return {'processed': len(file_paths), 'errors': len(file_paths)}

try:
    from parse.parse_coordinator import ParseCoordinator
except ImportError:
    class ParseCoordinator:
        def __init__(self, *args, **kwargs):
            self.input_dir = args[0] if args else kwargs.get('input_dir', '')
            self.output_dir = args[1] if len(args) > 1 else kwargs.get('output_dir', '')
            
        def parse_file(self, file_path):
            # Minimal mock implementation
            from types import SimpleNamespace
            return SimpleNamespace(ast=None, object_type='unknown', object_name='unknown')

try:
    from decompile.decompile_coordinator import DecompileCoordinator  
except ImportError:
    class DecompileCoordinator:
        def __init__(self, *args, **kwargs):
            self.input_dir = args[0] if args else kwargs.get('input_dir', '')
            self.output_dir = args[1] if len(args) > 1 else kwargs.get('output_dir', '')
            
        def decompile_file(self, input_file, output_file):
            # Minimal mock implementation
            return False


logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Orchestrates the complete PowerBuilder to Flutter conversion pipeline."""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 temp_dir: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
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
        
        # Stage directories
        self.extracted_dir = self.temp_dir / 'extracted'
        self.parsed_dir = self.temp_dir / 'parsed'
        self.decompiled_dir = self.temp_dir / 'decompiled'
        
        # Initialize stages
        self._init_stages()
        
        # Pipeline state
        self.start_time = None
        self.end_time = None
        self.stage_results = {}
        
        # Error recovery
        self.error_collector = FileErrorCollector()
        self.checkpoint = PipelineCheckpoint(self.temp_dir / '.checkpoint')
    
    def _init_stages(self):
        """Initialize all pipeline stages."""
        # Extract stage
        extract_config = self.config.get('extract', {})
        self.extractor = ExtractCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.extracted_dir),
            preserve_structure=extract_config.get('preserve_structure', True),
            extract_resources=extract_config.get('extract_resources', True)
        )
        
        # Parse stage
        parse_config = self.config.get('parse', {})
        self.parser = ParseCoordinator(
            input_dir=str(self.extracted_dir),
            output_dir=str(self.parsed_dir),
            strict_mode=parse_config.get('strict_mode', False),
            resolve_imports=parse_config.get('resolve_imports', True)
        )
        
        # Decompile stage
        decompile_config = self.config.get('decompile', {})
        self.decompiler = DecompileCoordinator(
            input_dir=str(self.extracted_dir),
            output_dir=str(self.decompiled_dir),
            debug_mode=decompile_config.get('debug_mode', False)
        )
        
        # Generate stage
        generate_config = self.config.get('generate', {})
        self.generator = GenerateCoordinator(
            input_dir=str(self.parsed_dir),
            output_dir=str(self.output_dir),
            framework=generate_config.get('target_framework', 'flutter'),
            null_safety=generate_config.get('null_safety', True),
            generate_tests=generate_config.get('generate_tests', False)
        )
    
    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process specified files through the pipeline.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary with pipeline results
        """
        self.start_time = datetime.now()
        results = {
            'total_files': len(file_paths),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'stages': {}
        }
        
        try:
            # Check resources before starting
            logger.info("Checking system resources...")
            ResourceChecker.check_all(self.temp_dir)
            
            # Check for existing checkpoint
            checkpoint_data = self.checkpoint.load()
            if checkpoint_data:
                logger.info(f"Found checkpoint from {checkpoint_data['timestamp']}")
                # TODO: Implement checkpoint recovery
            # Stage 1: Extract
            logger.info("Stage 1: Extracting files...")
            extract_stats = self._run_extract_stage(file_paths)
            results['stages']['extract'] = extract_stats
            
            if extract_stats.get('errors', 0) == len(file_paths):
                raise Exception("All files failed during extraction")
            
            # Stage 2: Parse
            logger.info("Stage 2: Parsing extracted files...")
            parse_stats = self._run_parse_stage()
            results['stages']['parse'] = parse_stats
            
            # Stage 3: Decompile (for P-code files)
            logger.info("Stage 3: Decompiling P-code files...")
            decompile_stats = self._run_decompile_stage()
            results['stages']['decompile'] = decompile_stats
            
            # Stage 4: Generate
            logger.info("Stage 4: Generating Flutter/Dart code...")
            generate_stats = self._run_generate_stage()
            results['stages']['generate'] = generate_stats
            
            # Calculate overall success
            results['successful'] = generate_stats.get('successful', 0)
            results['failed'] = len(file_paths) - results['successful']
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
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
                logger.info(f"Temporary files preserved in: {self.temp_dir}")
            
            # Clear checkpoint on completion
            self.checkpoint.clear()
        
        return results
    
    def process_directory(self, patterns: Optional[List[str]] = None) -> Dict[str, Any]:
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
        
        logger.info(f"Found {len(file_paths)} files to process")
        return self.process_files(file_paths)
    
    def _run_extract_stage(self, file_paths: List[str]) -> Dict[str, Any]:
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
            except Exception as e:
                logger.error(f"Failed to extract {file_path}: {e}")
                self.error_collector.add_error('extract', file_path, e)
            finally:
                processed += 1
                
        # Save checkpoint after extract stage
        self.checkpoint.save(
            'extract', 
            extracted_files,
            [fp for fp in file_paths if fp not in extracted_files],
            {'total': len(file_paths)}
        )
        
        return {
            'processed': processed,
            'successful': successful,
            'errors': processed - successful,
            'extracted_files': extracted_files
        }
    
    @retry(max_attempts=3, exceptions=(ExtractError, IOError))
    def _extract_file_with_retry(self, file_path: str) -> None:
        """Extract a single file with retry logic."""
        # Use the extract_pbls function for individual files
        extract_pbls([file_path], str(self.extracted_dir))
    
    def _run_parse_stage(self) -> Dict[str, Any]:
        """Run the parsing stage."""
        try:
            # Find extracted files
            extracted_files = list(self.extracted_dir.rglob('*'))
            source_files = [f for f in extracted_files if f.suffix in 
                          ['.srw', '.sru', '.srd', '.srm', '.srf', '.srs', '.sra']]
            
            successful = 0
            failed = 0
            parsed_objects = []
            
            for file_path in source_files:
                try:
                    result = self.parser.parse_file(str(file_path))
                    if result and result.ast:
                        successful += 1
                        parsed_objects.append({
                            'file': str(file_path),
                            'type': result.object_type,
                            'name': result.object_name
                        })
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Failed to parse {file_path}: {e}")
                    failed += 1
            
            # Save parsed summary
            self._save_parsed_summary(parsed_objects)
            
            return {
                'processed': len(source_files),
                'successful': successful,
                'failed': failed,
                'parsed_objects': parsed_objects
            }
        except Exception as e:
            logger.error(f"Parse stage failed: {e}")
            return {'processed': 0, 'successful': 0, 'failed': 0}
    
    def _run_decompile_stage(self) -> Dict[str, Any]:
        """Run the decompilation stage for P-code files."""
        try:
            # Find P-code files
            pcode_extensions = ['.fun', '.win', '.udo', '.men', '.apl']
            pcode_files = []
            for ext in pcode_extensions:
                pcode_files.extend(self.extracted_dir.rglob(f'*{ext}'))
            
            if not pcode_files:
                return {'processed': 0, 'successful': 0, 'skipped': True}
            
            successful = 0
            failed = 0
            
            for file_path in pcode_files:
                try:
                    output_file = self.decompiled_dir / file_path.relative_to(self.extracted_dir)
                    output_file = output_file.with_suffix('.pb')
                    
                    result = self.decompiler.decompile_file(str(file_path), str(output_file))
                    if result:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Failed to decompile {file_path}: {e}")
                    failed += 1
            
            return {
                'processed': len(pcode_files),
                'successful': successful,
                'failed': failed
            }
        except Exception as e:
            logger.error(f"Decompile stage failed: {e}")
            return {'processed': 0, 'successful': 0, 'failed': 0}
    
    def _run_generate_stage(self) -> Dict[str, Any]:
        """Run the code generation stage."""
        try:
            # Load parsed summary
            parsed_summary = self._load_parsed_summary()
            
            if not parsed_summary:
                return {'processed': 0, 'successful': 0, 'no_data': True}
            
            # Generate code for each parsed object
            successful = 0
            failed = 0
            generated_files = []
            
            for obj in parsed_summary:
                try:
                    result = self.generator.generate_from_object(
                        object_type=obj['type'],
                        object_name=obj['name'],
                        ast_file=obj['file']
                    )
                    
                    if result:
                        successful += 1
                        generated_files.extend(result.get('files', []))
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Failed to generate code for {obj['name']}: {e}")
                    failed += 1
            
            return {
                'processed': len(parsed_summary),
                'successful': successful,
                'failed': failed,
                'generated_files': generated_files
            }
        except Exception as e:
            logger.error(f"Generate stage failed: {e}")
            return {'processed': 0, 'successful': 0, 'failed': 0}
    
    def _save_parsed_summary(self, parsed_objects: List[Dict[str, Any]]):
        """Save summary of parsed objects for the generate stage."""
        import json
        summary_file = self.parsed_dir / 'parsed_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(parsed_objects, f, indent=2)
    
    def _load_parsed_summary(self) -> Optional[List[Dict[str, Any]]]:
        """Load summary of parsed objects."""
        import json
        summary_file = self.parsed_dir / 'parsed_summary.json'
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
        return None
    
    def _cleanup_temp(self):
        """Clean up temporary directories."""
        try:
            if self.temp_dir.exists() and self.temp_dir != self.output_dir:
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary directory")
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get detailed pipeline summary."""
        return {
            'pipeline': 'PowerBuilder to Flutter Converter',
            'version': '1.0.0',
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': (self.end_time - self.start_time).total_seconds() 
                       if self.start_time and self.end_time else None,
            'stages': self.stage_results,
            'configuration': self.config
        }