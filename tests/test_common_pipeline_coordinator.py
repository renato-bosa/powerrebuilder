"""Tests for common.pipeline_coordinator module."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest

# Mock the problematic imports before importing pipeline_coordinator
import sys
from unittest.mock import Mock

# Create a mock module for generate.generate_coordinator
mock_generate_module = Mock()
mock_generate_module.GenerateCoordinator = Mock
sys.modules['generate.generate_coordinator'] = mock_generate_module

# Also mock parse.parse_coordinator to avoid the real import
mock_parse_module = Mock()
# Create a mock ParseCoordinator that accepts the expected arguments
class MockParseCoordinator:
    def __init__(self, *args, **kwargs):
        
        self.input_dir = kwargs.get('input_dir', '')
        self.output_dir = kwargs.get('output_dir', '')
        self.strict_mode = kwargs.get('strict_mode', False)
        self.resolve_imports = kwargs.get('resolve_imports', True)
    
    def parse_file(self, file_path):
        
    
        from types import SimpleNamespace
        return SimpleNamespace(ast=None, object_type='unknown', object_name='unknown')

mock_parse_module.ParseCoordinator = MockParseCoordinator
sys.modules['parse.parse_coordinator'] = mock_parse_module

# Mock the extract module functions
mock_extract_module = Mock()
mock_extract_module.extract_pbls = Mock()
sys.modules['extract.extract_coordinator'] = mock_extract_module

# Mock parse_powerbuilder_directory and decompile_directory
mock_parse_module.parse_powerbuilder_directory = Mock()
mock_decompile_module = Mock()
mock_decompile_module.decompile_directory = Mock()
sys.modules['decompile.decompile_coordinator'] = mock_decompile_module

from common.pipeline_coordinator import PipelineCoordinator
from common.exceptions import ExtractError
from common.error_recovery import RetryError


class TestPipelineCoordinator:
    """Test PipelineCoordinator class."""
    
    def setup_method(self):

    
        
    
        """Set up test environment."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)
        
    def teardown_method(self):

        
        
        
        """Clean up test environment."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_basic(self):

    
        
    
        """Test basic initialization."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        assert coordinator.input_dir == self.input_dir
        assert coordinator.output_dir == self.output_dir
        assert coordinator.temp_dir == self.output_dir / '.temp'
        assert coordinator.config == {}
        
        # Check directories were created
        assert coordinator.output_dir.exists()
        assert coordinator.temp_dir.exists()
        
        # Check stage directories
        assert coordinator.extracted_dir == coordinator.temp_dir / 'extracted'
        assert coordinator.parsed_dir == coordinator.temp_dir / 'parsed'
        assert coordinator.decompiled_dir == coordinator.temp_dir / 'decompiled'
    
    def test_initialization_with_config(self):

    
        
    
        """Test initialization with custom configuration."""
        custom_temp = Path(self.temp_dir) / "custom_temp"
        config = {
            'extract': {'preserve_structure': False},
            'parse': {'strict_mode': True},
            'decompile': {'debug_mode': True},
            'generate': {'target_framework': 'react', 'null_safety': False}
        }
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            temp_dir=str(custom_temp),
            config=config
        )
        
        assert coordinator.temp_dir == custom_temp
        assert coordinator.config == config
        assert custom_temp.exists()
    
    @patch('common.pipeline_coordinator.GenerateCoordinator')
    @patch('common.pipeline_coordinator.DecompileCoordinator')
    @patch('common.pipeline_coordinator.ParseCoordinator')
    @patch('common.pipeline_coordinator.ExtractCoordinator')
    def test_init_stages(self, mock_extract, mock_parse, mock_decompile, mock_generate):

        
        """Test stage initialization."""
        # ParseCoordinator has a different signature, so we need to handle it
        mock_parse.return_value = Mock()
        config = {
            'extract': {'preserve_structure': False, 'extract_resources': False},
            'parse': {'strict_mode': True, 'resolve_imports': False},
            'decompile': {'debug_mode': True},
            'generate': {'target_framework': 'react', 'null_safety': False, 'generate_tests': True}
        }
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            config=config
        )
        
        # Verify ExtractCoordinator initialization
        mock_extract.assert_called_once_with(
            input_dir=str(self.input_dir),
            output_dir=str(coordinator.extracted_dir),
            preserve_structure=False,
            extract_resources=False
        )
        
        # Verify ParseCoordinator initialization
        mock_parse.assert_called_once_with(
            input_dir=str(coordinator.extracted_dir),
            output_dir=str(coordinator.parsed_dir),
            strict_mode=True,
            resolve_imports=False
        )
        
        # Verify DecompileCoordinator initialization
        mock_decompile.assert_called_once_with(
            input_dir=str(coordinator.extracted_dir),
            output_dir=str(coordinator.decompiled_dir),
            debug_mode=True
        )
        
        # Verify GenerateCoordinator initialization
        mock_generate.assert_called_once_with(
            input_dir=str(coordinator.parsed_dir),
            output_dir=str(self.output_dir),
            framework='react',
            null_safety=False,
            generate_tests=True
        )
    
    @patch('common.pipeline_coordinator.extract_pbls')
    @patch('common.pipeline_coordinator.ResourceChecker')
    def test_process_files_success(self, mock_resource_checker, mock_extract_pbls):

        
        """Test successful file processing."""
        # Create test files
        test_files = []
        for i in range(3):
            file_path = self.input_dir / f"test{i}.srw"
            file_path.write_text("test content")
            test_files.append(str(file_path))
        
        # Mock stages
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock stage methods
        coordinator._run_extract_stage = Mock(return_value={
            'processed': 3, 'successful': 3, 'errors': 0,
            'extracted_files': test_files
        })
        coordinator._run_parse_stage = Mock(return_value={
            'processed': 3, 'successful': 3, 'failed': 0,
            'parsed_objects': [{'file': f, 'type': 'window', 'name': f'test{i}'} 
                             for i, f in enumerate(test_files)]
        })
        coordinator._run_decompile_stage = Mock(return_value={
            'processed': 0, 'successful': 0, 'skipped': True
        })
        coordinator._run_generate_stage = Mock(return_value={
            'processed': 3, 'successful': 3, 'failed': 0,
            'generated_files': ['file1.dart', 'file2.dart', 'file3.dart']
        })
        
        # Process files
        results = coordinator.process_files(test_files)
        
        # Verify results
        assert results['total_files'] == 3
        assert results['successful'] == 3
        assert results['failed'] == 0
        assert 'duration' in results
        assert len(results['stages']) == 4
        assert results['stages']['extract']['successful'] == 3
        assert results['stages']['parse']['successful'] == 3
        assert results['stages']['generate']['successful'] == 3
        
        # Verify method calls
        mock_resource_checker.check_all.assert_called_once()
        coordinator._run_extract_stage.assert_called_once_with(test_files)
        coordinator._run_parse_stage.assert_called_once()
        coordinator._run_decompile_stage.assert_called_once()
        coordinator._run_generate_stage.assert_called_once()
    
    @patch('common.pipeline_coordinator.ResourceChecker')
    def test_process_files_extract_failure(self, mock_resource_checker):

        
        """Test handling of extraction failures."""
        test_files = ['/path/to/file1.srw', '/path/to/file2.srw']
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock extract stage to fail
        coordinator._run_extract_stage = Mock(return_value={
            'processed': 2, 'successful': 0, 'errors': 2,
            'extracted_files': []
        })
        
        # Process files
        results = coordinator.process_files(test_files)
        
        # Verify results
        assert results['failed'] == 2
        assert "All files failed during extraction" in str(results['errors'])
    
    @patch('common.pipeline_coordinator.ResourceChecker')
    def test_process_files_with_exception(self, mock_resource_checker):

        
        """Test handling of exceptions during processing."""
        test_files = ['/path/to/file.srw']
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock stage to raise exception
        coordinator._run_extract_stage = Mock(side_effect=Exception("Test error"))
        
        # Process files
        results = coordinator.process_files(test_files)
        
        # Verify results
        assert results['failed'] == 1
        assert len(results['errors']) == 1
        assert "Test error" in results['errors'][0]
    
    def test_process_directory_default_patterns(self):

    
        
    
        """Test processing directory with default patterns."""
        # Create test files with different extensions
        extensions = ['.srw', '.sru', '.srd', '.srm', '.srf', '.srs', '.sra', '.txt']
        for ext in extensions:
            (self.input_dir / f"test{ext}").write_text("content")
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock process_files
        coordinator.process_files = Mock(return_value={'processed': 7})
        
        # Process directory
        results = coordinator.process_directory()
        
        # Verify only PowerBuilder files were selected
        call_args = coordinator.process_files.call_args[0][0]
        assert len(call_args) == 7  # All except .txt
        assert all(not path.endswith('.txt') for path in call_args)
    
    def test_process_directory_custom_patterns(self):

    
        
    
        """Test processing directory with custom patterns."""
        # Create test files
        (self.input_dir / "test.srw").write_text("content")
        (self.input_dir / "test.sru").write_text("content")
        (self.input_dir / "test.txt").write_text("content")
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock process_files
        coordinator.process_files = Mock(return_value={'processed': 1})
        
        # Process directory with custom pattern
        results = coordinator.process_directory(patterns=['*.srw'])
        
        # Verify only .srw files were selected
        call_args = coordinator.process_files.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].endswith('.srw')
    
    @patch('common.pipeline_coordinator.extract_pbls')
    def test_run_extract_stage(self, mock_extract_pbls):

        
        """Test extract stage execution."""
        test_files = ['/path/to/file1.srw', '/path/to/file2.srw']
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Run extract stage
        results = coordinator._run_extract_stage(test_files)
        
        # Verify results
        assert results['processed'] == 2
        assert results['successful'] == 2
        assert results['errors'] == 0
        assert results['extracted_files'] == test_files
        
        # Verify extract_pbls was called for each file
        assert mock_extract_pbls.call_count == 2
    
    @patch('common.pipeline_coordinator.extract_pbls')
    def test_run_extract_stage_with_failures(self, mock_extract_pbls):

        
        """Test extract stage with some failures."""
        test_files = ['/path/to/file1.srw', '/path/to/file2.srw', '/path/to/file3.srw']
        
        # Make second file fail
        mock_extract_pbls.side_effect = [None, Exception("Extract error"), None]
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Run extract stage
        results = coordinator._run_extract_stage(test_files)
        
        # Verify results
        assert results['processed'] == 3
        assert results['successful'] == 2
        assert results['errors'] == 1
        assert len(results['extracted_files']) == 2
    
    def test_extract_file_with_retry_success(self):

    
        
    
        """Test file extraction with retry on success."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        with patch('common.pipeline_coordinator.extract_pbls') as mock_extract:
            coordinator._extract_file_with_retry('/path/to/file.srw')
            mock_extract.assert_called_once_with(
                ['/path/to/file.srw'], 
                str(coordinator.extracted_dir)
            )
    
    @patch('common.pipeline_coordinator.extract_pbls')
    def test_extract_file_with_retry_failure(self, mock_extract_pbls):

        
        """Test file extraction with retry on failure."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Fail all retry attempts
        mock_extract_pbls.side_effect = ExtractError("Extract failed")
        
        with pytest.raises(RetryError):
            coordinator._extract_file_with_retry('/path/to/file.srw')
        
        # Should retry 3 times
        assert mock_extract_pbls.call_count == 3
    
    def test_run_parse_stage(self):

    
        
    
        """Test parse stage execution."""
        # Create extracted files
        extracted_dir = self.output_dir / '.temp' / 'extracted'
        extracted_dir.mkdir(parents=True)
        
        test_files = []
        for i in range(3):
            file_path = extracted_dir / f"test{i}.srw"
            file_path.write_text("content")
            test_files.append(file_path)
        
        # Add non-source file to test filtering
        (extracted_dir / "readme.txt").write_text("readme")
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock parser
        mock_result = Mock()
        mock_result.ast = "mock_ast"
        mock_result.object_type = "window"
        mock_result.object_name = "test_window"
        coordinator.parser.parse_file = Mock(return_value=mock_result)
        
        # Run parse stage
        results = coordinator._run_parse_stage()
        
        # Verify results
        assert results['processed'] == 3  # Only .srw files
        assert results['successful'] == 3
        assert results['failed'] == 0
        assert len(results['parsed_objects']) == 3
        
        # Verify parser was called for each source file
        assert coordinator.parser.parse_file.call_count == 3
    
    def test_run_parse_stage_with_failures(self):

    
        
    
        """Test parse stage with failures."""
        # Create extracted files
        extracted_dir = self.output_dir / '.temp' / 'extracted'
        extracted_dir.mkdir(parents=True)
        (extracted_dir / "test1.srw").write_text("content")
        (extracted_dir / "test2.srw").write_text("content")
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock parser to fail on second file
        mock_result = Mock()
        mock_result.ast = "mock_ast"
        mock_result.object_type = "window"
        mock_result.object_name = "test1"
        
        coordinator.parser.parse_file = Mock(
            side_effect=[mock_result, Exception("Parse error")]
        )
        
        # Run parse stage
        results = coordinator._run_parse_stage()
        
        # Verify results
        assert results['processed'] == 2
        assert results['successful'] == 1
        assert results['failed'] == 1
    
    def test_run_decompile_stage_no_pcode(self):

    
        
    
        """Test decompile stage with no P-code files."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Ensure extracted directory exists but is empty
        coordinator.extracted_dir.mkdir(parents=True, exist_ok=True)
        
        # Run decompile stage
        results = coordinator._run_decompile_stage()
        
        # Verify results
        assert results['processed'] == 0
        assert results['successful'] == 0
        assert results.get('skipped') is True
    
    def test_run_decompile_stage_with_pcode(self):

    
        
    
        """Test decompile stage with P-code files."""
        # Create P-code files
        extracted_dir = self.output_dir / '.temp' / 'extracted'
        extracted_dir.mkdir(parents=True)
        
        pcode_files = []
        for ext in ['.fun', '.win', '.udo']:
            file_path = extracted_dir / f"test{ext}"
            file_path.write_bytes(b"pcode content")
            pcode_files.append(file_path)
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock decompiler
        coordinator.decompiler.decompile_file = Mock(return_value=True)
        
        # Run decompile stage
        results = coordinator._run_decompile_stage()
        
        # Verify results
        assert results['processed'] == 3
        assert results['successful'] == 3
        assert results['failed'] == 0
        
        # Verify decompiler was called for each P-code file
        assert coordinator.decompiler.decompile_file.call_count == 3
    
    def test_run_generate_stage_no_data(self):

    
        
    
        """Test generate stage with no parsed data."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Ensure parsed directory exists but has no summary
        coordinator.parsed_dir.mkdir(parents=True, exist_ok=True)
        
        # Run generate stage
        results = coordinator._run_generate_stage()
        
        # Verify results
        assert results['processed'] == 0
        assert results['successful'] == 0
        assert results.get('no_data') is True
    
    def test_run_generate_stage_success(self):

    
        
    
        """Test successful generate stage."""
        # Create parsed summary
        parsed_dir = self.output_dir / '.temp' / 'parsed'
        parsed_dir.mkdir(parents=True)
        
        parsed_objects = [
            {'type': 'window', 'name': 'test_window', 'file': 'test.srw'},
            {'type': 'datawindow', 'name': 'test_dw', 'file': 'test.srd'}
        ]
        
        summary_file = parsed_dir / 'parsed_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(parsed_objects, f)
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Mock generator
        mock_result = {
            'files': ['test_window.dart', 'test_window_state.dart']
        }
        coordinator.generator.generate_from_object = Mock(return_value=mock_result)
        
        # Run generate stage
        results = coordinator._run_generate_stage()
        
        # Verify results
        assert results['processed'] == 2
        assert results['successful'] == 2
        assert results['failed'] == 0
        assert len(results['generated_files']) == 4  # 2 files per object
        
        # Verify generator was called for each object
        assert coordinator.generator.generate_from_object.call_count == 2
    
    def test_save_and_load_parsed_summary(self):

    
        
    
        """Test saving and loading parsed summary."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Create parsed directory
        coordinator.parsed_dir.mkdir(parents=True, exist_ok=True)
        
        # Test data
        parsed_objects = [
            {'type': 'window', 'name': 'test1', 'file': 'test1.srw'},
            {'type': 'userobject', 'name': 'test2', 'file': 'test2.sru'}
        ]
        
        # Save summary
        coordinator._save_parsed_summary(parsed_objects)
        
        # Verify file exists
        summary_file = coordinator.parsed_dir / 'parsed_summary.json'
        assert summary_file.exists()
        
        # Load summary
        loaded = coordinator._load_parsed_summary()
        
        # Verify loaded data
        assert loaded == parsed_objects
    
    def test_cleanup_temp(self):

    
        
    
        """Test temporary directory cleanup."""
        custom_temp = Path(self.temp_dir) / "pipeline_temp"
        custom_temp.mkdir(parents=True)
        (custom_temp / "test.txt").write_text("temp file")
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            temp_dir=str(custom_temp)
        )
        
        # Verify temp dir exists
        assert custom_temp.exists()
        
        # Clean up
        coordinator._cleanup_temp()
        
        # Verify temp dir was removed
        assert not custom_temp.exists()
    
    def test_cleanup_temp_same_as_output(self):

    
        
    
        """Test cleanup when temp dir is same as output dir."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Set temp_dir to output_dir
        coordinator.temp_dir = coordinator.output_dir
        
        # Clean up
        coordinator._cleanup_temp()
        
        # Verify output dir still exists
        assert coordinator.output_dir.exists()
    
    def test_get_summary(self):

    
        
    
        """Test summary generation."""
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            config={'test': 'config'}
        )
        
        # Set times
        coordinator.start_time = datetime.now()
        coordinator.end_time = coordinator.start_time
        
        # Set stage results
        coordinator.stage_results = {
            'extract': {'successful': 5},
            'parse': {'successful': 4}
        }
        
        # Get summary
        summary = coordinator.get_summary()
        
        # Verify summary
        assert summary['pipeline'] == 'PowerBuilder to Flutter Converter'
        assert summary['version'] == '1.0.0'
        assert summary['input_directory'] == str(self.input_dir)
        assert summary['output_directory'] == str(self.output_dir)
        assert summary['start_time'] is not None
        assert summary['end_time'] is not None
        assert summary['duration'] == 0.0
        assert summary['stages'] == coordinator.stage_results
        assert summary['configuration'] == {'test': 'config'}
    
    @patch('common.pipeline_coordinator.PipelineCheckpoint')
    def test_checkpoint_integration(self, mock_checkpoint_class):

        
        """Test checkpoint functionality integration."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.save = MagicMock()
        mock_checkpoint.load = MagicMock()
        mock_checkpoint.clear = MagicMock()
        mock_checkpoint_class.return_value = mock_checkpoint
        
        # Mock checkpoint data
        mock_checkpoint.load.return_value = {
            'stage': 'extract',
            'timestamp': '2024-01-01T00:00:00'
        }
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Don't mock _run_extract_stage directly to allow checkpoint save to be called
        # Instead, mock extract_pbls which is called within _run_extract_stage
        coordinator._run_parse_stage = Mock(return_value={
            'processed': 1, 'successful': 1, 'failed': 0
        })
        coordinator._run_decompile_stage = Mock(return_value={
            'processed': 0, 'successful': 0, 'skipped': True
        })
        coordinator._run_generate_stage = Mock(return_value={
            'processed': 1, 'successful': 1, 'failed': 0
        })
        
        # Process files
        with patch('common.pipeline_coordinator.ResourceChecker'):
            with patch('common.pipeline_coordinator.extract_pbls'):
                results = coordinator.process_files(['test.srw'])
        
        # Verify checkpoint was loaded
        mock_checkpoint.load.assert_called_once()
        
        # Verify checkpoint was saved after extract
        mock_checkpoint.save.assert_called()
        
        # Verify checkpoint was cleared on completion
        mock_checkpoint.clear.assert_called_once()
    
    @patch('common.pipeline_coordinator.FileErrorCollector')
    def test_error_collector_integration(self, mock_error_collector_class):

        
        """Test error collector functionality."""
        mock_error_collector = MagicMock()
        mock_error_collector_class.return_value = mock_error_collector
        mock_error_collector.get_error_summary.return_value = {
            'total_errors': 1,
            'by_stage': {'extract': 1}
        }
        
        coordinator = PipelineCoordinator(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir)
        )
        
        # Process files with an error
        with patch('common.pipeline_coordinator.extract_pbls') as mock_extract:
            mock_extract.side_effect = Exception("Extract failed")
            with patch('common.pipeline_coordinator.ResourceChecker'):
                results = coordinator.process_files(['test.srw'])
        
        # Verify error was collected
        mock_error_collector.add_error.assert_called()
        
        # Verify error summary was included in results
        assert 'error_summary' in results
        assert results['error_summary']['total_errors'] == 1
        
        # Verify error summary was logged
        mock_error_collector.log_summary.assert_called_once()