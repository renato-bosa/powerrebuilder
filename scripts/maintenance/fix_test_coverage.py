#!/usr/bin/env python3
"""Comprehensive script to fix and improve test coverage.

This script automates the process of:
1. Fixing import errors in test files
2. Running tests incrementally to identify issues
3. Generating coverage reports
4. Providing actionable recommendations
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class TestCoverageFixer:
    """Tool to fix test coverage issues systematically."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.test_dir = project_root / "tests"
        self.coverage_report = {}
        self.import_errors = []
        self.test_failures = []

    def analyze_import_errors(self) -> dict[str, list[str]]:
        """Find all import errors in test files."""
        import_errors = {}

        # Common import mappings from old to new
        import_mappings = {
            "decompile.opcodes_unified": "decompile.opcodes.opcodes",
            "model.pb_base": "model.base.pb_behavioral",
            "model.base.pb_type": "model.ast.types",
            "parse.logging": "logging",
            "model.utils.logging": "logging",
            "model.utils.errors": "common.exceptions",
            "parse.exceptions": "common.exceptions",
            "model.pb_datawindow.datawindow_stubs": "model.pb_datawindow.datawindow",
        }

        # Find all test files
        test_files = list(self.test_dir.rglob("test_*.py"))

        for test_file in test_files:
            errors = []
            content = test_file.read_text()

            # Check for outdated imports
            for old_import, new_import in import_mappings.items():
                if old_import in content:
                    errors.append(f"Replace '{old_import}' with '{new_import}'")

            # Try to run the file and catch import errors
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import sys; sys.path.insert(0, '{self.project_root}'); import {test_file.stem}",
                ],
                cwd=test_file.parent,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0 and "ImportError" in result.stderr:
                errors.append(
                    f"Import error: {result.stderr.split('ImportError:')[1].strip()}"
                )

            if errors:
                import_errors[str(test_file.relative_to(self.project_root))] = errors

        return import_errors

    def fix_import_errors(self, dry_run: bool = True) -> int:
        """Automatically fix common import errors."""
        import_mappings = {
            r"from decompile\.opcodes_unified": "from decompile.opcodes.opcodes",
            r"from model\.pb_base": "from model.base.pb_behavioral",
            r"from model\.base\.pb_type": "from model.ast.types",
            r"from parse\.logging import get_logger": "import logging",
            r"from model\.utils\.logging import get_logger": "import logging",
            r"get_logger\([^)]+\)": "logging.getLogger(__name__)",
            r"from model\.utils\.errors": "from common.exceptions",
            r"from parse\.exceptions": "from common.exceptions",
            r"from extract\.pbd_core\.exceptions": "from common.exceptions",
            r"model\.pb_datawindow\.datawindow_stubs": "model.pb_datawindow.datawindow",
        }

        fixed_count = 0
        test_files = list(self.test_dir.rglob("test_*.py"))

        for test_file in test_files:
            content = test_file.read_text()
            original_content = content

            for old_pattern, new_pattern in import_mappings.items():
                content = re.sub(old_pattern, new_pattern, content)

            if content != original_content:
                if not dry_run:
                    test_file.write_text(content)
                else:
                    pass
                fixed_count += 1

        return fixed_count

    def run_tests_incrementally(self) -> dict[str, Any]:
        """Run tests one by one to identify specific failures."""
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "failures": [],
        }

        test_files = sorted(self.test_dir.rglob("test_*.py"))

        for test_file in test_files:
            relative_path = test_file.relative_to(self.project_root)

            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            results["total_tests"] += 1

            if result.returncode == 0:
                results["passed"] += 1
            else:
                if "FAILED" in result.stdout:
                    results["failed"] += 1
                elif "ERROR" in result.stdout or "ImportError" in result.stderr:
                    results["error"] += 1
                else:
                    results["skipped"] += 1

                results["failures"].append(
                    {
                        "file": str(relative_path),
                        "stdout": result.stdout[-500:],  # Last 500 chars
                        "stderr": result.stderr[-500:],
                    }
                )

        return results

    def generate_coverage_report(self) -> dict[str, Any]:
        """Run tests with coverage and analyze results."""
        # Run coverage
        subprocess.run(
            [sys.executable, "-m", "coverage", "run", "-m", "pytest", "-xvs"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Generate report
        subprocess.run(
            [sys.executable, "-m", "coverage", "report", "--show-missing"],
            cwd=self.project_root,
            check=False,
        )

        # Generate JSON report for analysis
        subprocess.run(
            [sys.executable, "-m", "coverage", "json"],
            cwd=self.project_root,
            check=False,
        )

        # Read coverage data
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            return {
                "total_coverage": coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                ),
                "files": len(coverage_data.get("files", {})),
                "summary": coverage_data.get("totals", {}),
            }
        return {"error": "Coverage report not generated"}

    def generate_test_strategy(self) -> list[dict[str, Any]]:
        """Generate prioritized test improvement strategy."""
        strategy = []

        # Priority 1: Fix existing tests
        strategy.append(
            {
                "priority": 1,
                "action": "Fix Import Errors",
                "description": "Update all import statements to match current module structure",
                "impact": "High - Will allow existing tests to run",
                "effort": "Low - Can be automated",
                "commands": [
                    "python scripts/maintenance/fix_test_coverage.py --fix-imports",
                ],
            }
        )

        # Priority 2: Fix pytest configuration
        strategy.append(
            {
                "priority": 2,
                "action": "Update pytest Configuration",
                "description": "Remove or expand testpaths restriction in pyproject.toml",
                "impact": "High - Will include all test files",
                "effort": "Low - Configuration change",
                "file_changes": {
                    "pyproject.toml": "Remove or expand 'testpaths' to include all test directories",
                },
            }
        )

        # Priority 3: Add tests for coordinators
        coordinator_files = [
            "extract/extract_coordinator.py",
            "parse/parse_coordinator.py",
            "decompile/decompile_coordinator.py",
            "generate/generate_coordinator.py",
            "model/model_coordinator.py",
        ]

        strategy.append(
            {
                "priority": 3,
                "action": "Test Coordinators",
                "description": "Add tests for coordinator classes that orchestrate major functionality",
                "impact": "Very High - Coordinators are critical components",
                "effort": "Medium",
                "files_to_test": coordinator_files,
            }
        )

        # Priority 4: Integration tests
        strategy.append(
            {
                "priority": 4,
                "action": "Add Integration Tests",
                "description": "Create end-to-end tests for the complete pipeline",
                "impact": "Very High - Tests actual workflow",
                "effort": "Medium",
                "test_scenarios": [
                    "Extract → Parse → Decompile → Generate",
                    "Error handling across modules",
                    "Different file type processing",
                ],
            }
        )

        # Priority 5: Extract module tests
        strategy.append(
            {
                "priority": 5,
                "action": "Improve Extract Module Coverage",
                "description": "Add tests for PBD extraction components",
                "impact": "High - Extract is critical but has low coverage (36.4%)",
                "effort": "High",
                "focus_areas": [
                    "pbd_core/library.py",
                    "pbd_core/entry.py",
                    "pbd_io/scanner.py",
                ],
            }
        )

        return strategy

    def create_sample_tests(self) -> None:
        """Create sample test templates for critical untested components."""
        templates = {
            "test_coordinator_template.py": '''"""Test template for coordinator classes."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import the coordinator to test
from {module}.{coordinator} import {CoordinatorClass}


class Test{CoordinatorClass}:
    """Test cases for {CoordinatorClass}."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator instance for testing."""
        return {CoordinatorClass}()

    def test_initialization(self, coordinator):
        """Test coordinator initializes correctly."""
        assert coordinator is not None
        # Add initialization assertions

    def test_main_workflow(self, coordinator, tmp_path):
        """Test main coordination workflow."""
        # Setup test data
        input_path = tmp_path / "input"
        input_path.mkdir()
        output_path = tmp_path / "output"

        # Run coordinator
        result = coordinator.process(input_path, output_path)

        # Verify results
        assert output_path.exists()
        assert result is not None

    def test_error_handling(self, coordinator):
        """Test coordinator handles errors gracefully."""
        with pytest.raises(Exception):
            coordinator.process(Path("/nonexistent"), Path("/nonexistent"))

    @patch('{module}.{coordinator}.subprocess')
    def test_subprocess_calls(self, mock_subprocess, coordinator):
        """Test coordinator makes correct subprocess calls."""
        # Mock subprocess behavior
        mock_subprocess.run.return_value.returncode = 0

        # Run coordinator
        coordinator.process(Path("."), Path("."))

        # Verify subprocess was called correctly
        assert mock_subprocess.run.called
''',
            "test_integration_template.py": '''"""Integration test template for full pipeline."""

import pytest
from pathlib import Path
import tempfile
import shutil

from main import extract_files, parse_files, decompile_files, generate_code


class TestPipelineIntegration:
    """End-to-end pipeline integration tests."""

    @pytest.fixture
    def test_workspace(self):
        """Create temporary workspace for testing."""
        workspace = Path(tempfile.mkdtemp())
        yield workspace
        shutil.rmtree(workspace)

    @pytest.fixture
    def sample_pbd_file(self):
        """Provide sample PBD file for testing."""
        # Return path to a small test PBD file
        return Path("tests/fixtures/sample.pbd")

    def test_full_pipeline(self, test_workspace, sample_pbd_file):
        """Test complete pipeline from PBD to generated code."""
        # Setup paths
        extracted_dir = test_workspace / "extracted"
        parsed_dir = test_workspace / "parsed"
        decompiled_dir = test_workspace / "decompiled"
        generated_dir = test_workspace / "generated"

        # Step 1: Extract
        extract_result = extract_files(sample_pbd_file, extracted_dir)
        assert extract_result["success"]
        assert extracted_dir.exists()
        assert len(list(extracted_dir.rglob("*"))) > 0

        # Step 2: Parse
        parse_result = parse_files(extracted_dir, parsed_dir)
        assert parse_result["success"]
        assert parsed_dir.exists()

        # Step 3: Decompile
        decompile_result = decompile_files(extracted_dir, decompiled_dir)
        assert decompile_result["success"]
        assert decompiled_dir.exists()

        # Step 4: Generate
        generate_result = generate_code(parsed_dir, decompiled_dir, generated_dir)
        assert generate_result["success"]
        assert generated_dir.exists()
        assert (generated_dir / "backend").exists()
        assert (generated_dir / "frontend").exists()

    def test_pipeline_error_recovery(self, test_workspace):
        """Test pipeline handles errors gracefully."""
        # Test with invalid input
        result = extract_files(Path("/nonexistent.pbd"), test_workspace / "extracted")
        assert not result["success"]
        assert "error" in result

    def test_pipeline_performance(self, test_workspace, sample_pbd_file):
        """Test pipeline performance metrics."""
        import time

        start_time = time.time()

        # Run full pipeline
        extract_files(sample_pbd_file, test_workspace / "extracted")
        # ... continue with other steps

        end_time = time.time()
        duration = end_time - start_time

        # Pipeline should complete in reasonable time
        assert duration < 60  # Less than 1 minute for small file
''',
        }

        # Create templates directory
        templates_dir = self.project_root / "tests" / "templates"
        templates_dir.mkdir(exist_ok=True)

        for filename, content in templates.items():
            (templates_dir / filename).write_text(content)


def main() -> None:
    """Main entry point for test coverage fixer."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix and improve test coverage")
    parser.add_argument("--analyze", action="store_true", help="Analyze import errors")
    parser.add_argument("--fix-imports", action="store_true", help="Fix import errors")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without changing files",
    )
    parser.add_argument(
        "--run-tests", action="store_true", help="Run tests incrementally"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--strategy", action="store_true", help="Generate test improvement strategy"
    )
    parser.add_argument(
        "--create-templates", action="store_true", help="Create sample test templates"
    )
    parser.add_argument("--all", action="store_true", help="Run all operations")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    fixer = TestCoverageFixer(project_root)

    if args.analyze or args.all:
        errors = fixer.analyze_import_errors()
        for issues in errors.values():
            for _issue in issues:
                pass

    if args.fix_imports or args.all:
        fixer.fix_import_errors(dry_run=args.dry_run)

    if args.run_tests:
        fixer.run_tests_incrementally()

    if args.coverage or args.all:
        fixer.generate_coverage_report()

    if args.strategy or args.all:
        strategy = fixer.generate_test_strategy()
        for _item in strategy:
            pass

    if args.create_templates:
        fixer.create_sample_tests()


if __name__ == "__main__":
    main()
