#!/usr/bin/env python3
"""
PowerBuilder Pipeline Demonstration

This script demonstrates the complete pipeline from PBD to modern code.
"""

import os
import subprocess
from pathlib import Path


def run_command(cmd):
    """Run a command and capture output"""

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            if result.stdout:
                pass
        elif result.stderr:
            pass
        return result.returncode == 0
    except Exception:
        return False


def show_file_sample(filepath, lines=20):
    """Show a sample of a file's contents"""
    if os.path.exists(filepath):
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines_list = content.split("\n")
                for _i, _line in enumerate(lines_list[:lines]):
                    pass
                if len(lines_list) > lines:
                    pass
        except Exception:
            pass
    else:
        pass


def main():
    """Run the complete pipeline demonstration"""


    # Setup directories
    demo_dir = Path("data/pipeline_demo")
    demo_dir.mkdir(exist_ok=True)

    # Create a simple test PBD file for demonstration
    # In a real scenario, you would use an existing PBD file
    test_pbd = "data/dcm_email.pbd"

    if not os.path.exists(test_pbd):
        pass
        # For demo purposes, we'll show what the pipeline would do


    # Stage 1: Extract

    extract_dir = demo_dir / "1_extracted"
    if run_command(f"python main.py extract {test_pbd} {extract_dir}"):
        # Show extracted files
        for f in extract_dir.glob("*.fun"):
            show_file_sample(str(f), lines=10)
            break  # Just show one sample

    # Stage 2: Decompile

    decompile_dir = demo_dir / "2_decompiled"
    if run_command(f"python main.py decompile {extract_dir} {decompile_dir}"):
        # Show decompiled source
        for f in decompile_dir.glob("*.sru"):
            show_file_sample(str(f), lines=30)
            break  # Just show one sample

    # Stage 3: Parse

    parse_dir = demo_dir / "3_parsed"
    if run_command(f"python main.py parse {decompile_dir} {parse_dir}"):
        # Show AST structure
        for f in parse_dir.glob("*.ast.json"):
            show_file_sample(str(f), lines=40)
            break  # Just show one sample

    # Stage 4: Model

    model_dir = demo_dir / "4_model"
    if run_command(f"python main.py model {parse_dir} {model_dir}"):
        # Show model structure
        for f in model_dir.glob("*.model.json"):
            show_file_sample(str(f), lines=30)
            break  # Just show one sample

    # Stage 5: Generate

    generate_dir = demo_dir / "5_generated"
    if run_command(f"python main.py generate {model_dir} {generate_dir}"):
        # Show generated Flutter code
        flutter_dir = generate_dir / "flutter"
        if flutter_dir.exists():
            for f in flutter_dir.rglob("*.dart"):
                show_file_sample(str(f), lines=40)
                break

        # Show generated Python code
        python_dir = generate_dir / "python"
        if python_dir.exists():
            for f in python_dir.rglob("*.py"):
                show_file_sample(str(f), lines=40)
                break


    # Show final directory structure
    for root, _dirs, files in os.walk(demo_dir):
        level = root.replace(str(demo_dir), "").count(os.sep)
        " " * 2 * level
        " " * 2 * (level + 1)
        for _file in files[:5]:  # Limit to 5 files per directory
            pass
        if len(files) > 5:
            pass


if __name__ == "__main__":
    main()
