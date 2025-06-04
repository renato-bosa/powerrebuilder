"""Configuration for the opcode discovery pipeline."""

import glob
from pathlib import Path


class DiscoveryConfig:
    """Configuration for opcode discovery pipeline."""

    def __init__(self) -> None:
        # Coverage target (0-1)
        self.coverage_target = 0.95

        # Maximum iterations to run
        self.max_iterations = 10

        # Minimum occurrences for an opcode to be considered
        self.min_occurrence_threshold = 5

        # Test file patterns
        self.test_file_patterns = [
            "output/test_bytes_fix/**/*.fun",
            "output/test_bytes_fix/**/*.win",
            "output/test_bytes_fix/**/*.dwo",
            "output/test_bytes_fix/**/*.udo",
        ]

        # Specific test files (if you want to override patterns)
        self.specific_test_files: list[Path] | None = None

        # Maximum number of test files to use
        self.max_test_files = 10

        # Output directory for reports
        self.report_dir = Path("output/opcode_discovery_reports")

        # Backup directory for opcodes.yaml
        self.backup_dir = Path("output/opcode_backups")

        # Enable detailed logging
        self.verbose = False

        # Categories for new opcodes based on byte ranges
        self.opcode_categories = {
            (0x00, 0x1F): "control",
            (0x20, 0x7F): "ascii",
            (0x80, 0x9F): "special",
            (0xA0, 0xBF): "variable_ops",
            (0xC0, 0xCF): "constants",
            (0xD0, 0xDF): "control_flow",
            (0xE0, 0xE3): "jumps",
            (0xE4, 0xE7): "variable_access",
            (0xE8, 0xEB): "store_ops",
            (0xEC, 0xEF): "test_ops",
            (0xF0, 0xFF): "extended_ops",
        }

    def get_test_files(self) -> list[Path]:
        """Get list of test files based on configuration."""
        if self.specific_test_files:
            return self.specific_test_files

        # Collect files matching patterns
        all_files = []
        for pattern in self.test_file_patterns:
            files = glob.glob(pattern, recursive=True)
            all_files.extend([Path(f) for f in files])

        # Remove duplicates and sort by size (smaller files first)
        unique_files = list(set(all_files))
        unique_files.sort(key=lambda f: f.stat().st_size)

        # Limit to max_test_files
        return unique_files[:self.max_test_files]

    def get_category_for_opcode(self, opcode: int) -> str:
        """Get the category for an opcode based on its value."""
        for (start, end), category in self.opcode_categories.items():
            if start <= opcode <= end:
                return category
        return "unknown"

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
