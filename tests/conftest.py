"""Test configuration and fixtures for PowerBuilder model tests."""

import logging
import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    # Save current state
    original_level = logging.root.level
    original_handlers = logging.root.handlers[:]

    yield

    # Restore state
    logging.root.handlers.clear()
    logging.root.handlers.extend(original_handlers)
    logging.root.setLevel(original_level)

    # Reset specific logger levels that may have been changed
    # Include both old and new names for coordinators during transition
    for logger_name in [
        "extract.pbd.structures.data_block",
        "extract.pbd.extraction",
        "extract.pbd.io",
        "decompile.analysis",
        "decompile.core.pcode_decoder",
        "decompile.core.expression_reconstructor",
        # Old coordinator names (for compatibility)
        "extract.extract_coordinator",
        "decompile.decompile_coordinator",
        "parse.parse_coordinator",
        "model.model_coordinator",
        "generate.generate_coordinator",
        # New coordinator names (after renaming)
        "extract.extract_coordinator",
        "decompile.decompile_coordinator",
        "parse.parse_coordinator",
        "model.model_coordinator",
        "generate.generate_coordinator",
    ]:
        logging.getLogger(logger_name).setLevel(logging.NOTSET)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--profile",
        action="store_true",
        default=False,
        help="Profile CPU usage during tests with pyinstrument",
    )


@pytest.fixture
def cpu_profiler(request):
    """CPU profiler fixture using pyinstrument."""
    if not request.config.getoption("--profile"):
        yield None
        return

    from pyinstrument import Profiler

    profiler = Profiler()
    profiler.start()

    yield profiler

    profiler.stop()

    # Print to console
    print("\n" + "=" * 80)
    print(f"CPU Profile for {request.node.name}")
    print("=" * 80)
    print(profiler.output_text(unicode=True, show_all=False))

    # Save HTML report
    reports_dir = Path("profile_reports")
    reports_dir.mkdir(exist_ok=True)

    test_name = request.node.name.replace("[", "_").replace("]", "_")
    html_file = reports_dir / f"{test_name}.html"

    with open(html_file, "w") as f:
        f.write(profiler.output_html())

    print(f"\nDetailed report saved to: {html_file}\n")
