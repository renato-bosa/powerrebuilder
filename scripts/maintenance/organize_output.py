#!/usr/bin/env python3
"""Script to organize the output directory by moving test outputs to a dedicated folder."""

import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def organize_output_directory(output_dir: Path, dry_run: bool = True) -> None:
    """Organize output directory by moving test directories to test-runs subfolder.

    Args:
        output_dir: Path to the output directory
        dry_run: If True, only show what would be moved without actually moving
    """
    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        return

    # Create test-runs directory
    test_runs_dir = output_dir / "test-runs"

    # Find all test_* directories
    test_dirs = [
        d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("test_")
    ]

    # Also find pipeline_test_* directories
    pipeline_test_dirs = [
        d
        for d in output_dir.iterdir()
        if d.is_dir() and d.name.startswith("pipeline_test_")
    ]

    all_test_dirs = test_dirs + pipeline_test_dirs

    if not all_test_dirs:
        logger.info("No test directories found to organize")
        return

    logger.info(f"Found {len(all_test_dirs)} test directories to organize")

    if dry_run:
        logger.info("DRY RUN - Showing what would be moved:")
        for test_dir in all_test_dirs:
            logger.info(f"  Would move: {test_dir.name} -> test-runs/{test_dir.name}")
    else:
        # Create test-runs directory if it doesn't exist
        test_runs_dir.mkdir(exist_ok=True)
        logger.info(f"Created/verified directory: {test_runs_dir}")

        # Move each test directory
        moved_count = 0
        for test_dir in all_test_dirs:
            try:
                dest = test_runs_dir / test_dir.name
                if dest.exists():
                    logger.warning(f"Destination already exists, skipping: {dest}")
                    continue

                shutil.move(str(test_dir), str(dest))
                logger.info(f"Moved: {test_dir.name} -> test-runs/{test_dir.name}")
                moved_count += 1
            except Exception as e:
                logger.exception(f"Failed to move {test_dir.name}: {e}")

        logger.info(f"Successfully moved {moved_count} directories")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Organize output directory")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Path to output directory (default: output)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually move files (default is dry run)",
    )

    args = parser.parse_args()

    organize_output_directory(args.output_dir, dry_run=not args.execute)


if __name__ == "__main__":
    main()
