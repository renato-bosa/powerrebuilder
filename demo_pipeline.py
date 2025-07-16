#!/usr/bin/env python3
"""
PowerBuilder Pipeline Demonstration

This script demonstrates the complete pipeline from PBD to modern code.
"""

import os
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """Run a command and capture output"""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Success!")
            if result.stdout:
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print("❌ Failed!")
            if result.stderr:
                print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def show_file_sample(filepath, lines=20):
    """Show a sample of a file's contents"""
    if os.path.exists(filepath):
        print(f"\n📄 Sample from {filepath}:")
        print("-" * 60)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines_list = content.split('\n')
                for i, line in enumerate(lines_list[:lines]):
                    print(f"{i+1:4d}: {line}")
                if len(lines_list) > lines:
                    print(f"      ... ({len(lines_list) - lines} more lines)")
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print(f"❌ File not found: {filepath}")


def main():
    """Run the complete pipeline demonstration"""
    
    print("🚀 PowerBuilder to Modern Code Pipeline Demonstration")
    print("=" * 60)
    
    # Setup directories
    demo_dir = Path("data/pipeline_demo")
    demo_dir.mkdir(exist_ok=True)
    
    # Create a simple test PBD file for demonstration
    # In a real scenario, you would use an existing PBD file
    test_pbd = "data/dcm_email.pbd"
    
    if not os.path.exists(test_pbd):
        print(f"⚠️  Test file {test_pbd} not found. Creating a mock example...")
        # For demo purposes, we'll show what the pipeline would do
        
    print(f"\n📦 Input PBD file: {test_pbd}")
    
    # Stage 1: Extract
    print("\n\n🔧 STAGE 1: EXTRACT - PBD to P-code")
    print("This stage extracts compiled P-code from PowerBuilder PBD files")
    
    extract_dir = demo_dir / "1_extracted"
    if run_command(f"python main.py extract {test_pbd} {extract_dir}"):
        # Show extracted files
        print("\n📁 Extracted files:")
        for f in extract_dir.glob("*.fun"):
            print(f"  - {f.name}")
            show_file_sample(str(f), lines=10)
            break  # Just show one sample
    
    # Stage 2: Decompile
    print("\n\n🔧 STAGE 2: DECOMPILE - P-code to PowerBuilder Source")
    print("This stage converts binary P-code back to readable PowerBuilder source")
    
    decompile_dir = demo_dir / "2_decompiled"
    if run_command(f"python main.py decompile {extract_dir} {decompile_dir}"):
        # Show decompiled source
        for f in decompile_dir.glob("*.sru"):
            show_file_sample(str(f), lines=30)
            break  # Just show one sample
    
    # Stage 3: Parse
    print("\n\n🔧 STAGE 3: PARSE - PowerBuilder Source to AST")
    print("This stage parses PowerBuilder source into an Abstract Syntax Tree")
    
    parse_dir = demo_dir / "3_parsed"
    if run_command(f"python main.py parse {decompile_dir} {parse_dir}"):
        # Show AST structure
        for f in parse_dir.glob("*.ast.json"):
            show_file_sample(str(f), lines=40)
            break  # Just show one sample
    
    # Stage 4: Model
    print("\n\n🔧 STAGE 4: MODEL - AST to Semantic Model")
    print("This stage builds high-level semantic models from the AST")
    
    model_dir = demo_dir / "4_model"
    if run_command(f"python main.py model {parse_dir} {model_dir}"):
        # Show model structure
        for f in model_dir.glob("*.model.json"):
            show_file_sample(str(f), lines=30)
            break  # Just show one sample
    
    # Stage 5: Generate
    print("\n\n🔧 STAGE 5: GENERATE - Model to Modern Code")
    print("This stage generates Flutter and Python code from semantic models")
    
    generate_dir = demo_dir / "5_generated"
    if run_command(f"python main.py generate {model_dir} {generate_dir}"):
        # Show generated Flutter code
        flutter_dir = generate_dir / "flutter"
        if flutter_dir.exists():
            print("\n🎯 Generated Flutter code:")
            for f in flutter_dir.rglob("*.dart"):
                show_file_sample(str(f), lines=40)
                break
        
        # Show generated Python code
        python_dir = generate_dir / "python"
        if python_dir.exists():
            print("\n🐍 Generated Python code:")
            for f in python_dir.rglob("*.py"):
                show_file_sample(str(f), lines=40)
                break
    
    print("\n\n✨ Pipeline demonstration complete!")
    print(f"Check the output in: {demo_dir}")
    
    # Show final directory structure
    print("\n📁 Final output structure:")
    for root, dirs, files in os.walk(demo_dir):
        level = root.replace(str(demo_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # Limit to 5 files per directory
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... and {len(files) - 5} more files")


if __name__ == "__main__":
    main()