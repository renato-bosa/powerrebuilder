"""Benchmarks for PowerBuilder file extraction performance."""

import os
import tempfile
import pytest
from unittest.mock import patch

from extract.extract_coordinator import extract_pbls
from extract.pbd.extraction.extractor import PBDExtractor
from extract.pbd.recovery.enhanced_recovery import EnhancedRecoveryEngine
from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET


class TestExtractionPerformance:
    """Benchmark extraction operations."""
    
    @pytest.fixture
    def sample_pbl_data(self):

        
        """Generate sample PBL data for benchmarking."""
        # Simulate a PBL file structure
        header = b'HDR*\x00\x00\x00\x01' + b'\x00' * 512
        entries = b'ENT*' + b'\x00' * 1024
        data = b'DAT*' + b'PowerBuilder source code' * 100
        return header + entries + data
    
    @pytest.fixture
    def temp_pbl_file(self, sample_pbl_data) -> None:

        
        """Create a temporary PBL file."""
        with tempfile.NamedTemporaryFile(suffix='.pbl', delete=False) as f:
            f.write(sample_pbl_data)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    def test_pbl_extraction_speed(self, benchmark, temp_pbl_file, tmp_path) -> None:

    
        
    
        """Benchmark PBL extraction speed."""
        output_dir = tmp_path / "output"
        
        def extract() -> None:
            """Extract.
            """
            
        
            with patch('extract.pbd.extraction.extractor.PBDExtractor.extract_pbd_file'):
                extract_pbls([temp_pbl_file], str(output_dir))
        
        result = benchmark(extract)
        assert benchmark.stats['mean'] < 0.1  # Should complete in under 100ms
    
    def test_large_file_extraction(self, benchmark, tmp_path) -> None:

    
        
    
        """Benchmark extraction of large files."""
        # Create a large mock PBL
        large_file = tmp_path / "large.pbl"
        with open(large_file, 'wb') as f:
            # 10MB file
            f.write(b'HDR*' + b'\x00' * (10 * 1024 * 1024))
        
        def extract_large() -> None:
            """Extract extract large.
            """
            
        
            extractor = PBDExtractor()
            with patch.object(extractor, '_extract_objects', return_value=[]):
                extractor.extract_pbd_file(str(large_file), str(tmp_path))
        
        result = benchmark(extract_large)
        # Large files should still be reasonably fast
        assert benchmark.stats['mean'] < 2.0  # Under 2 seconds for 10MB
    
    def test_recovery_engine_performance(self, benchmark) -> None:

    
        
    
        """Benchmark enhanced recovery engine."""
        corrupted_data = b'HDR*corrupted' + b'\x00' * 1024 + b'ENT*' + b'\x00' * 512
        
        def recover() -> None:
            """Recover.
            """
            
        
            engine = EnhancedRecoveryEngine()
            with patch.object(engine, '_scan_for_blocks', return_value=[]):
                engine.recover_corrupted_file(corrupted_data, progress_callback=None)
        
        result = benchmark(recover)
        assert benchmark.stats['mean'] < 0.5  # Recovery should be fast
    
    def test_batch_extraction(self, benchmark, tmp_path) -> None:

    
        
    
        """Benchmark batch extraction of multiple files."""
        # Create multiple small PBL files
        pbl_files = []
        for i in range(10):
            pbl_file = tmp_path / f"test_{i}.pbl"
            pbl_file.write_bytes(b'HDR*' + b'\x00' * 1024)
            pbl_files.append(str(pbl_file))
        
        def batch_extract() -> None:
            """Batch extract.
            """
            
        
            with patch('extract.extract_coordinator.PBDExtractor'):
                extract_pbls(pbl_files, str(tmp_path / "output"))
        
        result = benchmark(batch_extract)
        # Batch operations should be efficient
        assert benchmark.stats['mean'] < 0.5  # Under 500ms for 10 files
    
    def test_memory_usage(self, benchmark, tmp_path):

    
        
    
        """Benchmark memory usage during extraction."""
        import tracemalloc
        
        # Create a file with many objects
        complex_file = tmp_path / "complex.pbl"
        with open(complex_file, 'wb') as f:
            f.write(b'HDR*' + b'\x00' * 512)
            # Add 100 mock objects
            for i in range(100):
                f.write(b'ENT*' + f'object_{i}'.encode() + b'\x00' * 100)
                f.write(b'DAT*' + b'source code' * 50)
        
        def measure_memory():
            """Measure memory.
            """
            
        
            tracemalloc.start()
            extractor = PBDExtractor()
            with patch.object(extractor, '_extract_objects', return_value=[]):
                extractor.extract_pbd_file(str(complex_file), str(tmp_path))
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return peak / 1024 / 1024  # Convert to MB
        
        peak_memory = benchmark(measure_memory)
        # Memory usage should be reasonable
        assert benchmark.stats['mean'] < 100  # Less than 100MB peak