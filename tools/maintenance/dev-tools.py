#!/usr/bin/env python3
"""Development tools runner for SIME Finch project.

This script provides a unified interface for running all development tools:
- UV for package management
- Ruff for linting and formatting
- MyPy and Pyright for type checking
- Pytest with coverage
- MkDocs for documentation
"""

import logging
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger(__name__)

console = Console()

# Project modules to check
MODULES = ["parse", "model", "extract", "decompile", "generate", "common", "main.py"]


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:








    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


@click.group()
def cli() -> None:



    """SIME Finch Development Tools."""
    pass


@cli.command()
def env() -> None:



    """Show environment information."""
    table = Table(title="Environment Information")
    table.add_column("Tool", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Path", style="dim")

    # UV
    uv_result = run_command(["uv", "--version"], check=False)
    if uv_result.returncode == 0:
        table.add_row("UV", uv_result.stdout.strip(), "uv")

    # Python
    py_result = run_command(["python", "--version"])
    py_path = run_command(["which", "python"])
    table.add_row("Python", py_result.stdout.strip(), py_path.stdout.strip())

    # Ruff
    ruff_result = run_command(["ruff", "--version"], check=False)
    if ruff_result.returncode == 0:
        table.add_row("Ruff", ruff_result.stdout.strip(), "ruff")

    # MyPy
    mypy_result = run_command(["mypy", "--version"], check=False)
    if mypy_result.returncode == 0:
        table.add_row("MyPy", mypy_result.stdout.strip().split()[1], "mypy")

    # Pyright
    pyright_result = run_command(["pyright", "--version"], check=False)
    if pyright_result.returncode == 0:
        table.add_row("Pyright", pyright_result.stdout.strip(), "pyright")

    console.print(table)


@cli.command()
@click.option("--fix", is_flag=True, help="Apply fixes automatically")
def lint(fix) -> None:



    """Run linting with Ruff."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running Ruff...", total=None)

        cmd = ["ruff", "check"] + MODULES
        if fix:
            cmd.append("--fix")

        result = run_command(cmd, check=False)

        progress.stop()

        if result.returncode == 0:
            console.print("✅ [green]No linting issues found![/green]")
        else:
            console.print("❌ [red]Linting issues found:[/red]")
            console.print(result.stdout)
            if result.stderr:
                console.print(result.stderr)
            sys.exit(1)


@cli.command()
def format() -> None:



    """Format code with Ruff."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Formatting code...", total=None)

        result = run_command(["ruff", "format"] + MODULES, check=False)

        progress.stop()

        if result.returncode == 0:
            console.print("✅ [green]Code formatted successfully![/green]")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print("❌ [red]Formatting failed:[/red]")
            console.print(result.stderr)
            sys.exit(1)


@cli.command()
@click.option("--strict", is_flag=True, help="Use strict type checking")
def typecheck(strict) -> None:



    """Run type checking with MyPy and Pyright."""
    results = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # MyPy
        task = progress.add_task("Running MyPy...", total=None)
        mypy_cmd = ["mypy"]
        if strict:
            mypy_cmd.append("--strict")
        mypy_cmd.extend(MODULES)

        mypy_result = run_command(mypy_cmd, check=False)
        results["mypy"] = mypy_result

        # Pyright
        progress.update(task, description="Running Pyright...")
        pyright_result = run_command(["pyright"] + MODULES, check=False)
        results["pyright"] = pyright_result

        progress.stop()

    # Display results
    has_errors = False

    if results["mypy"].returncode == 0:
        console.print("✅ [green]MyPy: No type errors found![/green]")
    else:
        console.print("❌ [red]MyPy found type errors:[/red]")
        console.print(results["mypy"].stdout)
        has_errors = True

    if results["pyright"].returncode == 0:
        console.print("✅ [green]Pyright: No type errors found![/green]")
    else:
        console.print("❌ [red]Pyright found type errors:[/red]")
        console.print(results["pyright"].stdout)
        has_errors = True

    if has_errors:
        sys.exit(1)


@cli.command()
@click.option("--parallel", "-n", default="auto", help="Number of parallel workers")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--failfast", "-x", is_flag=True, help="Stop on first failure")
@click.option("--hypothesis", is_flag=True, help="Run hypothesis tests")
@click.option("--slow", is_flag=True, help="Include slow tests")
def test(parallel, verbose, failfast, hypothesis, slow) -> None:



    """Run tests with pytest."""
    cmd = ["pytest"]

    if parallel:
        cmd.extend(["-n", parallel])

    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    if failfast:
        cmd.append("-x")

    if not slow:
        cmd.extend(["-m", "not slow"])

    if hypothesis:
        cmd.extend(["--hypothesis-show-statistics"])

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running tests...", total=None)

        result = run_command(cmd, check=False)

        progress.stop()

    # Print output
    console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr)

    if result.returncode != 0:
        sys.exit(1)


@cli.command()
def coverage() -> None:



    """Generate coverage report."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating coverage report...", total=None)

        # Run coverage
        result = run_command(["coverage", "html"], check=False)

        progress.stop()

    if result.returncode == 0:
        console.print("✅ [green]Coverage report generated![/green]")
        console.print("📊 Open htmlcov/index.html to view the report")

        # Try to get coverage percentage
        report_result = run_command(["coverage", "report", "--format=total"], check=False)
        if report_result.returncode == 0:
            try:
                percentage = float(report_result.stdout.strip())
                color = "green" if percentage >= 80 else "yellow" if percentage >= 60 else "red"
                console.print(f"📈 Total coverage: [{color}]{percentage:.1f}%[/{color}]")
            except Exception as e:
                logger.debug("Exception caught: %s", e)
    else:
        console.print("❌ [red]Coverage generation failed:[/red]")
        console.print(result.stderr)
        sys.exit(1)


@cli.command()
@click.option("--serve", is_flag=True, help="Serve documentation locally")
@click.option("--port", default=8000, help="Port for serving docs")
def docs(serve, port) -> None:



    """Build or serve documentation."""
    if serve:
        console.print(f"🚀 Serving documentation at http://localhost:{port}")
        console.print("Press Ctrl+C to stop")
        try:
            subprocess.run(["mkdocs", "serve", "-p", str(port)])
        except KeyboardInterrupt:
            console.print("\n👋 Documentation server stopped")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Building documentation...", total=None)

            result = run_command(["mkdocs", "build"], check=False)

            progress.stop()

        if result.returncode == 0:
            console.print("✅ [green]Documentation built successfully![/green]")
            console.print("📚 Output in site/ directory")
        else:
            console.print("❌ [red]Documentation build failed:[/red]")
            console.print(result.stderr)
            sys.exit(1)


@cli.command()
def all() -> None:



    """Run all checks (lint, format, typecheck, test)."""
    console.print(Panel.fit("🔧 Running All Development Checks", style="bold blue"))

    steps = [
        ("Formatting", ["ruff", "format"] + MODULES),
        ("Linting", ["ruff", "check"] + MODULES),
        ("Type Checking (MyPy)", ["mypy"] + MODULES),
        ("Type Checking (Pyright)", ["pyright"] + MODULES),
        ("Testing", ["pytest", "-n", "auto"]),
    ]

    failed = False

    for step_name, cmd in steps:
        console.print(f"\n📋 {step_name}...")
        result = run_command(cmd, check=False)

        if result.returncode == 0:
            console.print(f"✅ [green]{step_name} passed![/green]")
        else:
            console.print(f"❌ [red]{step_name} failed![/red]")
            console.print(result.stdout)
            if result.stderr:
                console.print(result.stderr)
            failed = True

    if not failed:
        console.print("\n🎉 [bold green]All checks passed![/bold green]")
    else:
        console.print("\n❌ [bold red]Some checks failed![/bold red]")
        sys.exit(1)


@cli.command()
def install() -> None:



    """Install all dependencies including dev dependencies."""
    console.print("📦 Installing dependencies with UV...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing dependencies...", total=None)

        result = run_command(["uv", "sync", "--dev"], check=False)

        progress.stop()

    if result.returncode == 0:
        console.print("✅ [green]Dependencies installed successfully![/green]")
    else:
        console.print("❌ [red]Installation failed:[/red]")
        console.print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()
