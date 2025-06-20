#!/usr/bin/env python3
"""Analyze the gap between existing converters and actual generation."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_converters():
    """Analyze what converters exist."""
    print("Existing Converters Analysis")
    print("=" * 60)
    
    converter_dir = Path("generate/converters")
    converters = list(converter_dir.glob("*.py"))
    
    print(f"\nFound {len(converters)} converter modules:")
    for conv in sorted(converters):
        if conv.name != "__init__.py":
            print(f"  - {conv.name}")
    
    # Check specific converter capabilities
    print("\nConverter Capabilities:")
    
    # Check AST converter
    ast_conv = converter_dir / "ast_converter.py"
    if ast_conv.exists():
        with open(ast_conv) as f:
            content = f.read()
            if "def convert_to_python" in content:
                print("  ✓ AST Converter has Python support")
            else:
                print("  ✗ AST Converter lacks Python support")
            if "def convert_to_dart" in content:
                print("  ✓ AST Converter has Dart support")
            else:
                print("  ✗ AST Converter lacks explicit Dart support")
    
    # Check UI converter
    ui_conv = converter_dir / "ui_converter.py"
    if ui_conv.exists():
        with open(ui_conv) as f:
            content = f.read()
            control_count = content.count('": {')
            print(f"  ✓ UI Converter supports {control_count}+ controls")
    
    # Check event converter
    event_conv = converter_dir / "event_converter.py"
    if event_conv.exists():
        with open(event_conv) as f:
            content = f.read()
            event_count = content.count('": "')
            print(f"  ✓ Event Converter maps {event_count}+ events")

def analyze_generation():
    """Analyze what the generation coordinator actually does."""
    print("\n\nGeneration Coordinator Analysis")
    print("=" * 60)
    
    gen_coord = Path("generate/generate_coordinator.py")
    if gen_coord.exists():
        with open(gen_coord) as f:
            content = f.read()
            
        print("\nGeneration approach:")
        if "Environment" in content and "FileSystemLoader" in content:
            print("  ✓ Uses Jinja2 template-based generation")
        
        if "from generate.converters" in content:
            imports = [line for line in content.split('\n') if 'from generate.converters' in line]
            print(f"\nImported converters ({len(imports)}):")
            for imp in imports:
                print(f"  - {imp.strip()}")
        else:
            print("\n  ✗ Does not import converters (except RelationshipExtractor)")
        
        # Check what generators are defined
        generators = []
        for line in content.split('\n'):
            if line.strip().startswith("class ") and "Generator" in line:
                generators.append(line.strip())
        
        print(f"\nDefined generators ({len(generators)}):")
        for gen in generators:
            print(f"  - {gen}")
        
        # Check extraction functions
        extract_funcs = []
        for line in content.split('\n'):
            if line.strip().startswith("def extract_") and "_from_ast" in line:
                extract_funcs.append(line.strip())
        
        print(f"\nExtraction functions ({len(extract_funcs)}):")
        for func in extract_funcs:
            print(f"  - {func}")

def analyze_integration_gap():
    """Analyze the gap between converters and generation."""
    print("\n\nIntegration Gap Analysis")
    print("=" * 60)
    
    print("\nCurrent situation:")
    print("  1. Comprehensive converters exist for Dart/Flutter")
    print("  2. Generation uses templates instead of converters")
    print("  3. Only RelationshipExtractor is imported/used")
    print("  4. No Python code generation exists")
    
    print("\nRequired work:")
    print("  1. Connect existing converters to generation pipeline")
    print("  2. Add Python generation to converters OR")
    print("  3. Create Python-specific generators using templates")
    print("  4. Update generate_coordinator to use converters")
    
    print("\nRecommendation:")
    print("  - For Dart/Flutter: Connect existing converters")
    print("  - For Python: Create template-based generators")
    print("    (Following the existing pattern)")

if __name__ == "__main__":
    analyze_converters()
    analyze_generation()
    analyze_integration_gap()