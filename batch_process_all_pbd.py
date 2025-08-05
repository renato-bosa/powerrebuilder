#!/usr/bin/env python3
"""
Batch process all PBD files in the PowerRebuilder pipeline with proper error handling and timeout management.
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_process_all_pbd.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PBDProcessor:
    """Process PBD files through the PowerRebuilder pipeline."""
    
    def __init__(self, input_dir: str, base_output_dir: str, timeout_seconds: int = 1800):
        self.input_dir = Path(input_dir)
        self.base_output_dir = Path(base_output_dir)
        self.timeout_seconds = timeout_seconds
        self.results: Dict[str, Dict] = {}
        
    def get_pbd_files(self) -> List[Path]:
        """Get all PBD files from input directory."""
        return list(self.input_dir.glob("*.pbd"))
    
    def process_single_file(self, pbd_file: Path) -> Tuple[bool, str, float]:
        """Process a single PBD file through the pipeline."""
        logger.info(f"Processing {pbd_file.name}...")
        
        # Create file-specific output directory
        output_dir = self.base_output_dir / f"output_{pbd_file.stem}"
        
        # Create temporary directory with just this file
        temp_dir = Path("temp_single_process")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / pbd_file.name
        
        try:
            # Copy file to temp directory
            temp_file.write_bytes(pbd_file.read_bytes())
            
            # Build command
            cmd = [
                sys.executable, "main.py", "all",
                "--loglevel", "INFO",
                "--debug",
                "--traceback",
                "--enable-byte-recovery",
                "--pbl-input-dir", str(temp_dir),
                "--base-output-dir", str(output_dir)
            ]
            
            start_time = time.time()
            
            try:
                # Run with timeout
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=Path.cwd()
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if result.returncode == 0:
                    logger.info(f"✅ {pbd_file.name} completed successfully in {duration:.1f}s")
                    return True, result.stdout, duration
                else:
                    logger.error(f"❌ {pbd_file.name} failed with return code {result.returncode}")
                    logger.error(f"STDERR: {result.stderr}")
                    return False, result.stderr, duration
                    
            except subprocess.TimeoutExpired:
                end_time = time.time()
                duration = end_time - start_time
                logger.warning(f"⏰ {pbd_file.name} timed out after {duration:.1f}s")
                return False, f"Process timed out after {self.timeout_seconds}s", duration
                
        except Exception as e:
            logger.error(f"💥 Exception processing {pbd_file.name}: {e}")
            return False, str(e), 0.0
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
    
    def process_all_files(self) -> Dict[str, Dict]:
        """Process all PBD files."""
        pbd_files = self.get_pbd_files()
        logger.info(f"Found {len(pbd_files)} PBD files to process")
        
        successful = 0
        failed = 0
        total_time = 0.0
        
        for i, pbd_file in enumerate(pbd_files, 1):
            logger.info(f"\n=== Processing file {i}/{len(pbd_files)}: {pbd_file.name} ===")
            
            success, output, duration = self.process_single_file(pbd_file)
            total_time += duration
            
            self.results[pbd_file.name] = {
                'success': success,
                'output': output,
                'duration': duration,
                'index': i
            }
            
            if success:
                successful += 1
            else:
                failed += 1
                
            logger.info(f"Progress: {i}/{len(pbd_files)} files processed "
                       f"({successful} successful, {failed} failed)")
        
        # Print final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"FINAL RESULTS:")
        logger.info(f"Total files: {len(pbd_files)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success rate: {successful/len(pbd_files)*100:.1f}%")
        logger.info(f"Total processing time: {total_time:.1f}s")
        logger.info(f"Average time per file: {total_time/len(pbd_files):.1f}s")
        
        # List failed files
        if failed > 0:
            logger.info(f"\nFailed files:")
            for filename, result in self.results.items():
                if not result['success']:
                    logger.info(f"  - {filename}: {result['output'][:100]}...")
        
        return self.results


def main():
    """Main entry point."""
    input_dir = "/Users/michael/Projects/powerrebuilder/data/input/pbd_files"
    output_dir = "/Users/michael/Projects/powerrebuilder/output/batch_all_pbd_20250806"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    processor = PBDProcessor(
        input_dir=input_dir,
        base_output_dir=output_dir,
        timeout_seconds=1800  # 30 minutes per file
    )
    
    try:
        results = processor.process_all_files()
        
        # Save results to file
        import json
        results_file = Path(output_dir) / "batch_processing_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to: {results_file}")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()