#!/usr/bin/env python3
"""Test script to verify .fun file creation during PBD extraction."""

import logging
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extract.extract_coordinator import extract_pbls
from extract.pbd_core.core import extract_pbl

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_fun_file_creation():
    """Test if .fun files are created during extraction."""
    # Find a test PBD file
    test_files = list(Path("tests/fixtures/pbd_files").glob("*.pbd"))
    if not test_files:
        test_files = list(Path("input").rglob("*.pbd"))[:1]
    
    if not test_files:
        logger.error("No PBD files found for testing")
        return False
    
    test_file = test_files[0]
    logger.info(f"Testing with file: {test_file}")
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "extracted"
        output_dir.mkdir(parents=True)
        
        try:
            # Extract the PBD file
            logger.info(f"Extracting to: {output_dir}")
            extract_pbl(str(test_file), str(output_dir))
            
            # Check for .fun files
            fun_files = list(output_dir.rglob("*.fun"))
            txt_files = list(output_dir.rglob("*.txt"))
            
            logger.info(f"Found {len(txt_files)} .txt files")
            logger.info(f"Found {len(fun_files)} .fun files")
            
            if fun_files:
                logger.info("✓ .fun files ARE being created!")
                for fun_file in fun_files[:5]:  # Show first 5
                    logger.info(f"  - {fun_file.name}")
                return True
            else:
                logger.warning("✗ No .fun files found!")
                
                # Show what files were created
                all_files = list(output_dir.rglob("*"))
                if all_files:
                    logger.info("Files that were created:")
                    for f in all_files[:10]:
                        if f.is_file():
                            logger.info(f"  - {f.name}")
                            
                # Check if any source files were extracted
                source_exts = {'.sru', '.srw', '.srd', '.srm', '.srf', '.sra'}
                source_files = [f for f in txt_files if any(f.name.endswith(ext + '.txt') for ext in source_exts)]
                if source_files:
                    logger.info(f"Found {len(source_files)} source files that should have .fun files")
                    for sf in source_files[:5]:
                        logger.info(f"  - {sf.name}")
                
                return False
                
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = test_fun_file_creation()
    sys.exit(0 if success else 1)