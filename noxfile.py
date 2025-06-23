"""Nox configuration for multi-version testing and automation.

This file defines test sessions that run across multiple Python versions
and different testing scenarios for the SIME Finch PowerBuilder toolkit.
"""

import nox
from pathlib import Path

# Supported Python versions for testing
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]
MAIN_PYTHON = "3.13"

# Test locations
TESTS_DIR = "tests"
SOURCES = ["parse", "model", "extract", "decompile", "generate", "common"]

# Development dependencies that should be installed for testing
DEV_DEPS = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-xdist>=3.6.0",
    "hypothesis>=6.112.0",
    "syrupy>=4.6.1",
    "coverage>=7.6.0",
]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite across multiple Python versions."""
    session.log(f"Running tests on Python {session.python}")
    
    # Install package in development mode
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    
    # Run core test suite
    session.run(
        "pytest",
        TESTS_DIR,
        "--tb=short",
        "--maxfail=10",
        "-x",  # Stop on first failure for CI efficiency
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def tests_with_coverage(session: nox.Session) -> None:
    """Run tests with coverage reporting."""
    session.log("Running tests with coverage analysis")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    
    # Run with coverage
    session.run(
        "pytest",
        TESTS_DIR,
        "--cov=parse",
        "--cov=model", 
        "--cov=extract",
        "--cov=decompile",
        "--cov=generate",
        "--cov=common",
        "--cov-branch",
        "--cov-report=term-missing:skip-covered",
        "--cov-report=html",
        "--cov-report=xml",
        "--tb=short",
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def hypothesis_focused(session: nox.Session) -> None:
    """Run property-based tests with increased examples."""
    session.log("Running focused Hypothesis property-based testing")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    
    # Run only Hypothesis tests with more examples
    session.run(
        "pytest",
        "-m", "hypothesis",
        "--hypothesis-profile=thorough",
        "-v",
        "--tb=short",
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def snapshot_tests(session: nox.Session) -> None:
    """Run snapshot tests and update snapshots if needed."""
    session.log("Running snapshot tests")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    
    # Run snapshot tests
    session.run(
        "pytest",
        "-k", "snapshot",
        "--tb=short",
        "-v",
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def lint(session: nox.Session) -> None:
    """Run linting checks."""
    session.log("Running lint checks")
    
    session.install("ruff>=0.8.0")
    
    # Run ruff linting
    session.run("ruff", "check", *SOURCES, external=True)
    session.run("ruff", "format", "--check", *SOURCES, external=True)


@nox.session(python=MAIN_PYTHON)
def type_check(session: nox.Session) -> None:
    """Run type checking with mypy."""
    session.log("Running type checks")
    
    session.install("-e", ".")
    session.install("mypy>=1.13.0")
    session.install("types-setuptools", "types-pyyaml", "types-click", "types-tqdm")
    
    # Run mypy
    session.run("mypy", *SOURCES, external=True)


@nox.session(python=PYTHON_VERSIONS)
def integration_tests(session: nox.Session) -> None:
    """Run integration tests across Python versions."""
    session.log(f"Running integration tests on Python {session.python}")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    
    # Run only integration tests
    session.run(
        "pytest",
        "-m", "integration",
        "--tb=short",
        "-v",
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def performance_tests(session: nox.Session) -> None:
    """Run performance benchmarks."""
    session.log("Running performance benchmarks")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    session.install("pytest-benchmark>=4.0.0")
    
    # Run benchmark tests
    session.run(
        "pytest",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--tb=short",
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def docs(session: nox.Session) -> None:
    """Build documentation."""
    session.log("Building documentation")
    
    session.install("-e", ".")
    session.install(
        "mkdocs>=1.6.1",
        "mkdocs-material>=9.5.50",
        "mkdocstrings[python]>=0.27.0",
    )
    
    # Build docs
    session.run("mkdocs", "build", "--strict", external=True)


@nox.session(python=MAIN_PYTHON)
def dependency_audit(session: nox.Session) -> None:
    """Audit dependencies for security vulnerabilities."""
    session.log("Auditing dependencies")
    
    session.install("safety>=3.0.0")
    session.install("-e", ".")
    
    # Run safety check
    session.run("safety", "check", external=True)


@nox.session(python=MAIN_PYTHON, name="update-snapshots")
def update_snapshots(session: nox.Session) -> None:
    """Update all snapshot tests."""
    session.log("Updating snapshot tests")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    
    # Update snapshots
    session.run(
        "pytest",
        "-k", "snapshot",
        "--snapshot-update",
        "--tb=short",
        "-v",
        external=True,
    )


@nox.session(python=MAIN_PYTHON)
def profile_tests(session: nox.Session) -> None:
    """Profile test execution to identify slow tests."""
    session.log("Profiling test execution")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    session.install("pytest-profiling>=1.7.0")
    
    # Run with profiling
    session.run(
        "pytest",
        "--profile",
        "--profile-svg",
        "tests/test_decompile/",
        "-v",
        external=True,
    )


@nox.session(python=MAIN_PYTHON, name="test-install")
def test_install(session: nox.Session) -> None:
    """Test package installation from different sources."""
    session.log("Testing package installation")
    
    # Test wheel installation
    session.run("python", "-m", "pip", "install", "--upgrade", "build", external=True)
    session.run("python", "-m", "build", external=True)
    
    # Install from wheel
    dist_dir = Path("dist")
    wheels = list(dist_dir.glob("*.whl"))
    if wheels:
        session.install(str(wheels[-1]))  # Install latest wheel
        
        # Test basic import
        session.run("python", "-c", "import parse; print('Package installed successfully')", external=True)


# Define session groups for convenience
@nox.session(python=MAIN_PYTHON, name="ci")
def ci(session: nox.Session) -> None:
    """Run all CI checks (fast version for CI/CD)."""
    session.log("Running CI test suite")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    session.install("ruff>=0.8.0")
    
    # Quick linting
    session.run("ruff", "check", *SOURCES, external=True)
    
    # Core tests only (no slow tests)
    session.run(
        "pytest",
        "-m", "not slow",
        "--maxfail=5",
        "-x",
        "--tb=short",
        external=True,
    )


@nox.session(python=MAIN_PYTHON, name="dev")
def dev(session: nox.Session) -> None:
    """Set up development environment."""
    session.log("Setting up development environment")
    
    session.install("-e", ".")
    session.install(*DEV_DEPS)
    session.install("ruff>=0.8.0", "mypy>=1.13.0")
    session.install("pre-commit>=4.0.1")
    
    # Install pre-commit hooks
    session.run("pre-commit", "install", external=True)
    
    session.log("Development environment ready!")
    session.log("Run 'nox -s tests' to run tests")
    session.log("Run 'nox -s lint' to run linting")
    session.log("Run 'nox -s type_check' to run type checking")


# Configure default sessions
nox.options.sessions = ["tests", "lint", "type_check"]
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = False