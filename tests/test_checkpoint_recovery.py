"""Test checkpoint recovery functionality."""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from common.error_recovery import PipelineCheckpoint
from common.pipeline_coordinator import PipelineCoordinator


class TestCheckpointRecovery(unittest.TestCase):
    """Test checkpoint recovery in the pipeline."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_checkpoint_save_and_load(self):
        """Test saving and loading checkpoints."""
        checkpoint_dir = Path(self.temp_dir) / "checkpoint"
        checkpoint = PipelineCheckpoint(checkpoint_dir)
        
        # Save checkpoint
        processed = ["file1.srw", "file2.sru"]
        failed = ["file3.srd"]
        state = {"extract_stats": {"successful": 2, "failed": 1}}
        
        checkpoint.save("extract", processed, failed, state)
        
        # Load checkpoint
        data = checkpoint.load()
        self.assertIsNotNone(data)
        self.assertEqual(data["stage"], "extract")
        self.assertEqual(data["processed_files"], processed)
        self.assertEqual(data["failed_files"], failed)
        self.assertEqual(data["state"], state)
        
    def test_pipeline_recovery_from_extract_stage(self):
        """Test pipeline recovery from extract stage checkpoint."""
        config = {"auto_recover_checkpoint": True}
        coordinator = PipelineCoordinator(
            str(self.input_dir),
            str(self.output_dir),
            config=config
        )
        
        # Create a checkpoint from extract stage
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": "extract",
            "processed_files": ["file1.srw", "file2.sru"],
            "failed_files": ["file3.srd"],
            "state": {"total": 5}
        }
        
        # Mock the checkpoint load
        with patch.object(coordinator.checkpoint, 'load', return_value=checkpoint_data):
            # Mock the stage methods
            with patch.object(coordinator, '_run_extract_stage') as mock_extract:
                with patch.object(coordinator, '_run_parse_stage') as mock_parse:
                    with patch.object(coordinator, '_run_decompile_stage') as mock_decompile:
                        with patch.object(coordinator, '_run_generate_stage') as mock_generate:
                            # Configure mocks
                            mock_extract.return_value = {
                                'processed': 2,
                                'successful': 2,
                                'errors': 0,
                                'extracted_files': ['file4.srw', 'file5.sru']
                            }
                            mock_parse.return_value = {'successful': 4}
                            mock_decompile.return_value = {'successful': 4}
                            mock_generate.return_value = {'successful': 4}
                            
                            # Process files with recovery
                            all_files = ["file1.srw", "file2.sru", "file3.srd", "file4.srw", "file5.sru"]
                            results = coordinator.process_files(all_files)
                            
                            # Verify extract was called only for remaining files
                            mock_extract.assert_called_once()
                            args = mock_extract.call_args[0][0]
                            self.assertEqual(set(args), {"file4.srw", "file5.sru"})
                            
                            # Verify other stages were called
                            mock_parse.assert_called_once()
                            mock_decompile.assert_called_once()
                            mock_generate.assert_called_once()
                            
                            # Check results
                            self.assertEqual(results['stages']['extract']['successful'], 4)  # 2 + 2
                            
    def test_pipeline_recovery_from_parse_stage(self):
        """Test pipeline recovery from parse stage checkpoint."""
        config = {"auto_recover_checkpoint": True}
        coordinator = PipelineCoordinator(
            str(self.input_dir),
            str(self.output_dir),
            config=config
        )
        
        # Create a checkpoint from parse stage
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": "parse",
            "processed_files": ["file1.ast.json", "file2.ast.json"],
            "failed_files": [],
            "state": {
                "extract_stats": {"successful": 5, "failed": 0},
                "total_parsed": 2
            }
        }
        
        # Mock the checkpoint load
        with patch.object(coordinator.checkpoint, 'load', return_value=checkpoint_data):
            # Mock the stage methods
            with patch.object(coordinator, '_run_parse_stage') as mock_parse:
                with patch.object(coordinator, '_run_decompile_stage') as mock_decompile:
                    with patch.object(coordinator, '_run_generate_stage') as mock_generate:
                        # Configure mocks
                        mock_parse.return_value = {'successful': 5}
                        mock_decompile.return_value = {'successful': 5}
                        mock_generate.return_value = {'successful': 5}
                        
                        # Process files with recovery
                        all_files = ["file1.srw", "file2.sru", "file3.srd", "file4.srw", "file5.sru"]
                        results = coordinator.process_files(all_files)
                        
                        # Verify extract was not called (already completed)
                        self.assertEqual(results['stages']['extract']['successful'], 5)
                        
                        # Verify other stages were called
                        mock_parse.assert_called_once()
                        mock_decompile.assert_called_once()
                        mock_generate.assert_called_once()
                        
    def test_checkpoint_clear_on_completion(self):
        """Test that checkpoint is cleared after successful completion."""
        config = {"auto_recover_checkpoint": False}
        coordinator = PipelineCoordinator(
            str(self.input_dir),
            str(self.output_dir),
            config=config
        )
        
        # Create a test file
        test_file = self.input_dir / "test.srw"
        test_file.write_text("test content")
        
        with patch.object(coordinator.checkpoint, 'clear') as mock_clear:
            with patch.object(coordinator, '_run_extract_stage', return_value={'successful': 1, 'errors': 0}):
                with patch.object(coordinator, '_run_parse_stage', return_value={'successful': 1}):
                    with patch.object(coordinator, '_run_decompile_stage', return_value={'successful': 0}):
                        with patch.object(coordinator, '_run_generate_stage', return_value={'successful': 1}):
                            # Process file
                            coordinator.process_files([str(test_file)])
                            
                            # Verify checkpoint was cleared
                            mock_clear.assert_called_once()
                            
    def test_old_checkpoint_ignored(self):
        """Test that old checkpoints are ignored."""
        config = {"auto_recover_checkpoint": False}  # Disable auto-recovery
        coordinator = PipelineCoordinator(
            str(self.input_dir),
            str(self.output_dir),
            config=config
        )
        
        # Create an old checkpoint (40 minutes ago)
        from datetime import timedelta
        old_time = datetime.now() - timedelta(minutes=40)
        checkpoint_data = {
            "timestamp": old_time.isoformat(),
            "stage": "extract",
            "processed_files": ["old_file.srw"],
            "failed_files": [],
            "state": {}
        }
        
        # Mock the checkpoint load and clear
        with patch.object(coordinator.checkpoint, 'load', return_value=checkpoint_data):
            with patch.object(coordinator.checkpoint, 'clear') as mock_clear:
                with patch.object(coordinator, '_run_extract_stage') as mock_extract:
                    mock_extract.return_value = {'successful': 1, 'errors': 0}
                    
                    # Try to process - should ignore old checkpoint
                    with patch.object(coordinator, '_run_parse_stage', return_value={'successful': 1}):
                        with patch.object(coordinator, '_run_decompile_stage', return_value={'successful': 0}):
                            with patch.object(coordinator, '_run_generate_stage', return_value={'successful': 1}):
                                coordinator.process_files(["new_file.srw"])
                    
                    # Verify checkpoint was cleared
                    self.assertEqual(mock_clear.call_count, 2)  # Once for old checkpoint, once on completion
                    
                    # Verify extract was called for all files (not recovery)
                    mock_extract.assert_called_once()
                    args = mock_extract.call_args[0][0]
                    self.assertEqual(args, ["new_file.srw"])


if __name__ == '__main__':
    unittest.main()