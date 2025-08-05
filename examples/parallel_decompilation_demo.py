#!/usr/bin/env python3
"""Demo script showcasing parallel PowerBuilder decompilation capabilities.

This script demonstrates the enhanced parallel processing and progress reporting
features of the PowerRebuilder decompiler.
"""

import logging
import tempfile
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

console = Console()


def create_demo_files(demo_dir: Path, file_count: int = 20) -> list[Path]:
    """Create demo P-code files for testing.
    
    Args:
        demo_dir: Directory to create files in
        file_count: Number of demo files to create
        
    Returns:
        List of created file paths
    """
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    # Create files of varying sizes
    for i in range(file_count):
        if i < 5:
            # Small files (< 1KB)
            size = 100 + i * 50
            file_ext = ".fun"
        elif i < 10:
            # Medium files (1-10KB)
            size = 1024 + i * 1024
            file_ext = ".men"
        elif i < 15:
            # Large files (10-100KB)
            size = 10240 + i * 10240
            file_ext = ".udo"
        else:
            # Extra large files (100KB+)
            size = 102400 + i * 51200
            file_ext = ".win"
        
        file_path = demo_dir / f"demo_object_{i:03d}{file_ext}"
        
        # Create file with mock P-code data
        with file_path.open('wb') as f:
            # Write a simple header
            f.write(b"PB_MOCK_HEADER")
            f.write(b"\x00" * 24)  # Header padding
            
            # Write mock P-code instructions
            for j in range(size // 16):
                # Mock instruction: opcode + operands
                f.write(bytes([0x01 + (j % 20)]))  # Variable opcode
                f.write(j.to_bytes(2, 'little'))  # 16-bit operand
                f.write(b"\x00" * 13)  # Padding to make 16 bytes
        
        created_files.append(file_path)
    
    return created_files


def demo_sequential_vs_parallel():
    """Demonstrate sequential vs parallel decompilation performance."""
    console.print(Panel.fit(
        "[bold blue]PowerRebuilder Parallel Decompilation Demo[/bold blue]\n"
        "Comparing sequential vs parallel processing performance",
        border_style="blue"
    ))
    
    # Create temporary demo files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_sequential = temp_path / "output_sequential"
        output_parallel = temp_path / "output_parallel"
        
        console.print("\n[yellow]Creating demo P-code files...[/yellow]")
        demo_files = create_demo_files(input_dir, file_count=25)
        
        total_size = sum(f.stat().st_size for f in demo_files)
        console.print(f"Created {len(demo_files)} demo files ({total_size / 1024 / 1024:.2f} MB total)")
        
        # Import coordinators
        from src.decompile.coordinator import DecompileCoordinator
        from src.decompile.parallel_coordinator import ParallelDecompileCoordinator
        
        # Create performance comparison table
        results_table = Table(title="Performance Comparison")
        results_table.add_column("Method", style="cyan")
        results_table.add_column("Duration (s)", style="yellow")
        results_table.add_column("Files/sec", style="green")
        results_table.add_column("MB/sec", style="magenta")
        results_table.add_column("Success Rate", style="blue")
        
        console.print("\n[bold green]Running Sequential Decompilation...[/bold green]")
        
        # Sequential processing
        start_time = time.time()
        try:
            sequential_coordinator = DecompileCoordinator(
                input_dir=input_dir,
                output_dir=output_sequential,
            )
            sequential_result = sequential_coordinator.decompile()
            sequential_duration = time.time() - start_time
            
            sequential_files_per_sec = sequential_result["processed_files"] / sequential_duration
            sequential_mb_per_sec = total_size / sequential_duration / 1024 / 1024
            sequential_success_rate = f"{sequential_result['processed_files'] / sequential_result['total_files'] * 100:.1f}%"
            
            results_table.add_row(
                "Sequential",
                f"{sequential_duration:.2f}",
                f"{sequential_files_per_sec:.2f}",
                f"{sequential_mb_per_sec:.2f}",
                sequential_success_rate,
            )
            
        except Exception as e:
            logger.error("Sequential processing failed: %s", e)
            results_table.add_row("Sequential", "FAILED", "-", "-", "-")
            sequential_duration = 0
        
        console.print("\n[bold green]Running Parallel Decompilation...[/bold green]")
        
        # Parallel processing
        start_time = time.time()
        try:
            parallel_coordinator = ParallelDecompileCoordinator(
                input_dir=input_dir,
                output_dir=output_parallel,
                use_adaptive_parallelism=True,
            )
            parallel_result = parallel_coordinator.decompile()
            parallel_duration = time.time() - start_time
            
            parallel_files_per_sec = parallel_result["processed_files"] / parallel_duration
            parallel_mb_per_sec = total_size / parallel_duration / 1024 / 1024
            parallel_success_rate = f"{parallel_result['processed_files'] / parallel_result['total_files'] * 100:.1f}%"
            
            results_table.add_row(
                "Parallel (Adaptive)",
                f"{parallel_duration:.2f}",
                f"{parallel_files_per_sec:.2f}",
                f"{parallel_mb_per_sec:.2f}",
                parallel_success_rate,
            )
            
            # Calculate speedup
            if sequential_duration > 0:
                speedup = sequential_duration / parallel_duration
                results_table.add_row(
                    "[bold]Speedup Factor[/bold]",
                    f"[bold]{speedup:.2f}x[/bold]",
                    f"[bold]{parallel_files_per_sec / sequential_files_per_sec:.2f}x[/bold]",
                    f"[bold]{parallel_mb_per_sec / sequential_mb_per_sec:.2f}x[/bold]",
                    "-",
                )
            
        except Exception as e:
            logger.error("Parallel processing failed: %s", e)
            results_table.add_row("Parallel", "FAILED", "-", "-", "-")
        
        # Display results
        console.print("\n")
        console.print(results_table)
        
        # Show adaptive configuration if available
        if hasattr(parallel_coordinator, 'adaptive_config') and parallel_coordinator.adaptive_config:
            config = parallel_coordinator.adaptive_config
            
            config_table = Table(title="Adaptive Configuration")
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="white")
            config_table.add_column("Reasoning", style="dim")
            
            config_table.add_row("Use Parallelism", str(config.use_parallelism), "")
            config_table.add_row("Use Processes", str(config.use_processes), "")
            config_table.add_row("Max Workers", str(config.max_workers), "")
            config_table.add_row("Memory Mapping", str(config.use_memory_mapping), "")
            config_table.add_row("Section Parallelism", str(config.section_parallelism), "")
            config_table.add_row("Confidence", f"{config.confidence:.0%}", "")
            
            console.print("\n")
            console.print(config_table)
            
            if config.reasoning:
                console.print("\n[bold]Adaptive Reasoning:[/bold]")
                for reason in config.reasoning:
                    console.print(f"  • {reason}")


def demo_adaptive_parallelism():
    """Demonstrate adaptive parallelism with different workload patterns."""
    console.print(Panel.fit(
        "[bold blue]Adaptive Parallelism Demo[/bold blue]\n"
        "Testing different workload patterns",
        border_style="blue"
    ))
    
    from src.decompile.adaptive_parallelism import get_adaptive_engine, optimize_for_files
    
    engine = get_adaptive_engine()
    
    # Test different workload scenarios
    scenarios = [
        ("Small workload (5 small files)", 5, lambda i: 500),
        ("Medium workload (15 mixed files)", 15, lambda i: 1024 * (1 + i % 5)),
        ("Large workload (50 mixed files)", 50, lambda i: 1024 * (1 + i % 10)),
        ("Memory-intensive (10 large files)", 10, lambda i: 1024 * 1024 * (1 + i % 3)),
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        scenario_table = Table(title="Adaptive Configuration Scenarios")
        scenario_table.add_column("Scenario", style="cyan")
        scenario_table.add_column("Workers", style="yellow")
        scenario_table.add_column("Processes", style="green")
        scenario_table.add_column("Memory Map", style="magenta")
        scenario_table.add_column("Confidence", style="blue")
        scenario_table.add_column("Summary", style="white")
        
        for scenario_name, file_count, size_func in scenarios:
            # Create scenario files
            scenario_dir = temp_path / scenario_name.lower().replace(" ", "_")
            scenario_files = []
            
            for i in range(file_count):
                file_path = scenario_dir / f"file_{i:03d}.fun"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                size = size_func(i)
                with file_path.open('wb') as f:
                    f.write(b"MOCK" * (size // 4))
                
                scenario_files.append(file_path)
            
            # Get adaptive configuration
            config = optimize_for_files(scenario_files)
            
            # Get summary
            summary = engine.get_recommended_config_summary(config)
            
            scenario_table.add_row(
                scenario_name,
                str(config.max_workers) if config.use_parallelism else "1",
                "✓" if config.use_processes else "✗",
                "✓" if config.use_memory_mapping else "✗",
                f"{config.confidence:.0%}",
                summary[:50] + "..." if len(summary) > 50 else summary,
            )
        
        console.print("\n")
        console.print(scenario_table)


def main():
    """Run the parallel decompilation demo."""
    try:
        console.print("[bold green]PowerRebuilder Parallel Processing Demo[/bold green]\n")
        
        # Demo 1: Sequential vs Parallel comparison
        demo_sequential_vs_parallel()
        
        console.print("\n" + "="*80 + "\n")
        
        # Demo 2: Adaptive parallelism scenarios
        demo_adaptive_parallelism()
        
        console.print("\n[bold green]Demo completed successfully![/bold green]")
        console.print("\nTo use parallel processing in your own decompilation:")
        console.print("  [cyan]sime-finch decompile --parallel input_dir output_dir[/cyan]")
        console.print("  [cyan]sime-finch decompile --parallel --max-workers 8 input_dir output_dir[/cyan]")
        console.print("  [cyan]sime-finch decompile --parallel --use-threads input_dir output_dir[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")
        logger.exception("Demo failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())