#!/usr/bin/env python3
"""Batch process PowerBuilder files through the conversion pipeline."""

import os
import sys
import subprocess
import time
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_pipeline_on_batch(pbd_files, batch_num, output_base):
    """Run the pipeline on a batch of PBD files."""
    batch_output = output_base / f"batch_{batch_num}"
    
    # Create temporary directory with just this batch
    temp_input = Path(f"temp_batch_{batch_num}")
    temp_input.mkdir(exist_ok=True)
    
    # Copy files to temp directory
    for pbd_file in pbd_files:
        subprocess.run(['cp', str(pbd_file), str(temp_input)], check=True)
    
    logger.info(f"Processing batch {batch_num} with {len(pbd_files)} files")
    
    # Run the pipeline
    cmd = [
        'python', 'main.py', 'all',
        '--pbl-input-dir', str(temp_input),
        '--base-output-dir', str(batch_output),
        '--enable-byte-recovery'
    ]
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 minute timeout per batch
        duration = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"Batch {batch_num} completed successfully in {duration:.1f} seconds")
            # Extract success metrics from output if available
            if "Successful:" in result.stdout:
                logger.info(result.stdout.split('\n')[-20:])  # Last 20 lines
        else:
            logger.error(f"Batch {batch_num} failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr[-1000:]}")  # Last 1000 chars
            
    except subprocess.TimeoutExpired:
        logger.error(f"Batch {batch_num} timed out after 30 minutes")
    except Exception as e:
        logger.error(f"Batch {batch_num} failed with exception: {e}")
    finally:
        # Cleanup temp directory
        subprocess.run(['rm', '-rf', str(temp_input)], check=True)
    
    return batch_output

def main():
    """Main batch processing function."""
    # Get all PBD files
    input_dir = Path("data/input/pbd_files")
    pbd_files = sorted(list(input_dir.glob("*.pbd")))
    
    logger.info(f"Found {len(pbd_files)} PBD files to process")
    
    # Process in batches
    batch_size = 5
    output_base = Path("output/batch_pipeline_run")
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Save overall start time
    overall_start = time.time()
    
    # Process each batch
    successful_batches = 0
    failed_batches = 0
    
    for i in range(0, len(pbd_files), batch_size):
        batch_num = i // batch_size + 1
        batch_files = pbd_files[i:i + batch_size]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting batch {batch_num}/{(len(pbd_files) + batch_size - 1) // batch_size}")
        logger.info(f"Files: {[f.name for f in batch_files]}")
        logger.info(f"{'='*60}")
        
        try:
            batch_output = run_pipeline_on_batch(batch_files, batch_num, output_base)
            
            # Check if output was generated
            if batch_output.exists() and any(batch_output.rglob("*")):
                successful_batches += 1
                logger.info(f"Batch {batch_num} output saved to {batch_output}")
            else:
                failed_batches += 1
                logger.warning(f"Batch {batch_num} produced no output")
                
        except Exception as e:
            failed_batches += 1
            logger.error(f"Failed to process batch {batch_num}: {e}")
    
    # Summary
    overall_duration = time.time() - overall_start
    logger.info(f"\n{'='*60}")
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info(f"Total time: {overall_duration/60:.1f} minutes")
    logger.info(f"Successful batches: {successful_batches}")
    logger.info(f"Failed batches: {failed_batches}")
    logger.info(f"Output directory: {output_base}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()