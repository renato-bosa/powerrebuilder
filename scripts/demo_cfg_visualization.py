#!/usr/bin/env python3
"""Demonstration of Control Flow Graph (CFG) visualization capabilities.

This script shows how the CFG visualizer can generate visual representations
of PowerBuilder P-code control flow, supporting both method-level and 
class-level visualization with export to DOT/GraphViz format.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from decompile.core.pcode_decoder import PCodeInstruction
from decompile.visualization.cfg_visualizer import (
    CFGVisualizer,
    VisualizationLevel,
    VisualizationOptions,
)


def create_simple_method() -> list[PCodeInstruction]:
    """Create a simple method with basic control flow."""
    return [
        PCodeInstruction(address=0x00, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x0A', operand_values=[10], text_format="PUSHCONST 10", opcode_value=0x10),
        PCodeInstruction(address=0x02, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x01', operand_values=[1], text_format="PUSHVAR 1", opcode_value=0x11),
        PCodeInstruction(address=0x04, opcode=b'\x30', opcode_name="GT", operands=b'', operand_values=[], text_format="GT", opcode_value=0x30),
        PCodeInstruction(address=0x06, opcode=b'\x41', opcode_name="JUMPFALSE", operands=b'\x0C', operand_values=[0x0C], text_format="JUMPFALSE 0x0C", opcode_value=0x41),
        PCodeInstruction(address=0x08, opcode=b'\x50', opcode_name="CALL", operands=b'processLarge', operand_values=["processLarge"], text_format="CALL processLarge", opcode_value=0x50),
        PCodeInstruction(address=0x0A, opcode=b'\x42', opcode_name="JUMP", operands=b'\x0E', operand_values=[0x0E], text_format="JUMP 0x0E", opcode_value=0x42),
        PCodeInstruction(address=0x0C, opcode=b'\x50', opcode_name="CALL", operands=b'processSmall', operand_values=["processSmall"], text_format="CALL processSmall", opcode_value=0x50),
        PCodeInstruction(address=0x0E, opcode=b'\x60', opcode_name="RETURN", operands=b'', operand_values=[], text_format="RETURN", opcode_value=0x60),
    ]


def create_loop_method() -> list[PCodeInstruction]:
    """Create a method with a for loop."""
    return [
        # Initialize i = 0
        PCodeInstruction(address=0x00, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x00', operand_values=[0], text_format="PUSHCONST 0", opcode_value=0x10),
        PCodeInstruction(address=0x02, opcode=b'\x20', opcode_name="POPVAR", operands=b'\x01', operand_values=[1], text_format="POPVAR 1", opcode_value=0x20),
        # Loop condition: i < 10
        PCodeInstruction(address=0x04, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x01', operand_values=[1], text_format="PUSHVAR 1", opcode_value=0x11),
        PCodeInstruction(address=0x06, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x0A', operand_values=[10], text_format="PUSHCONST 10", opcode_value=0x10),
        PCodeInstruction(address=0x08, opcode=b'\x31', opcode_name="LT", operands=b'', operand_values=[], text_format="LT", opcode_value=0x31),
        PCodeInstruction(address=0x0A, opcode=b'\x41', opcode_name="JUMPFALSE", operands=b'\x18', operand_values=[0x18], text_format="JUMPFALSE 0x18", opcode_value=0x41),
        # Loop body
        PCodeInstruction(address=0x0C, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x01', operand_values=[1], text_format="PUSHVAR 1", opcode_value=0x11),
        PCodeInstruction(address=0x0E, opcode=b'\x50', opcode_name="CALL", operands=b'processItem', operand_values=["processItem"], text_format="CALL processItem", opcode_value=0x50),
        # Increment i++
        PCodeInstruction(address=0x10, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x01', operand_values=[1], text_format="PUSHVAR 1", opcode_value=0x11),
        PCodeInstruction(address=0x12, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x01', operand_values=[1], text_format="PUSHCONST 1", opcode_value=0x10),
        PCodeInstruction(address=0x14, opcode=b'\x33', opcode_name="ADD", operands=b'', operand_values=[], text_format="ADD", opcode_value=0x33),
        PCodeInstruction(address=0x15, opcode=b'\x20', opcode_name="POPVAR", operands=b'\x01', operand_values=[1], text_format="POPVAR 1", opcode_value=0x20),
        # Jump back to condition
        PCodeInstruction(address=0x16, opcode=b'\x42', opcode_name="JUMP", operands=b'\x04', operand_values=[0x04], text_format="JUMP 0x04", opcode_value=0x42),
        # After loop
        PCodeInstruction(address=0x18, opcode=b'\x60', opcode_name="RETURN", operands=b'', operand_values=[], text_format="RETURN", opcode_value=0x60),
    ]


def create_nested_method() -> list[PCodeInstruction]:
    """Create a method with nested control structures."""
    return [
        # Outer if condition
        PCodeInstruction(address=0x00, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x01', operand_values=[1], text_format="PUSHVAR 1", opcode_value=0x11),
        PCodeInstruction(address=0x02, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x00', operand_values=[0], text_format="PUSHCONST 0", opcode_value=0x10),
        PCodeInstruction(address=0x04, opcode=b'\x30', opcode_name="GT", operands=b'', operand_values=[], text_format="GT", opcode_value=0x30),
        PCodeInstruction(address=0x06, opcode=b'\x41', opcode_name="JUMPFALSE", operands=b'\x24', operand_values=[0x24], text_format="JUMPFALSE 0x24", opcode_value=0x41),
        
        # Inner loop (while j < n)
        PCodeInstruction(address=0x08, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x00', operand_values=[0], text_format="PUSHCONST 0", opcode_value=0x10),
        PCodeInstruction(address=0x0A, opcode=b'\x20', opcode_name="POPVAR", operands=b'\x02', operand_values=[2], text_format="POPVAR 2", opcode_value=0x20),
        # Loop condition
        PCodeInstruction(address=0x0C, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x02', operand_values=[2], text_format="PUSHVAR 2", opcode_value=0x11),
        PCodeInstruction(address=0x0E, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x01', operand_values=[1], text_format="PUSHVAR 1", opcode_value=0x11),
        PCodeInstruction(address=0x10, opcode=b'\x31', opcode_name="LT", operands=b'', operand_values=[], text_format="LT", opcode_value=0x31),
        PCodeInstruction(address=0x12, opcode=b'\x41', opcode_name="JUMPFALSE", operands=b'\x22', operand_values=[0x22], text_format="JUMPFALSE 0x22", opcode_value=0x41),
        
        # Inner if in loop
        PCodeInstruction(address=0x14, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x02', operand_values=[2], text_format="PUSHVAR 2", opcode_value=0x11),
        PCodeInstruction(address=0x16, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x05', operand_values=[5], text_format="PUSHCONST 5", opcode_value=0x10),
        PCodeInstruction(address=0x18, opcode=b'\x32', opcode_name="EQ", operands=b'', operand_values=[], text_format="EQ", opcode_value=0x32),
        PCodeInstruction(address=0x1A, opcode=b'\x41', opcode_name="JUMPFALSE", operands=b'\x1E', operand_values=[0x1E], text_format="JUMPFALSE 0x1E", opcode_value=0x41),
        PCodeInstruction(address=0x1C, opcode=b'\x50', opcode_name="CALL", operands=b'special', operand_values=["special"], text_format="CALL special", opcode_value=0x50),
        
        # Increment j
        PCodeInstruction(address=0x1E, opcode=b'\x11', opcode_name="PUSHVAR", operands=b'\x02', operand_values=[2], text_format="PUSHVAR 2", opcode_value=0x11),
        PCodeInstruction(address=0x1F, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x01', operand_values=[1], text_format="PUSHCONST 1", opcode_value=0x10),
        PCodeInstruction(address=0x20, opcode=b'\x33', opcode_name="ADD", operands=b'', operand_values=[], text_format="ADD", opcode_value=0x33),
        PCodeInstruction(address=0x21, opcode=b'\x20', opcode_name="POPVAR", operands=b'\x02', operand_values=[2], text_format="POPVAR 2", opcode_value=0x20),
        # Jump back
        PCodeInstruction(address=0x22, opcode=b'\x42', opcode_name="JUMP", operands=b'\x0C', operand_values=[0x0C], text_format="JUMP 0x0C", opcode_value=0x42),
        
        # End of outer if
        PCodeInstruction(address=0x24, opcode=b'\x60', opcode_name="RETURN", operands=b'', operand_values=[], text_format="RETURN", opcode_value=0x60),
    ]


def demo_basic_visualization():
    """Demonstrate basic CFG visualization."""
    print("Basic CFG Visualization Demo")
    print("=" * 50)
    
    instructions = create_simple_method()
    visualizer = CFGVisualizer()
    
    # Generate visualization
    dot_content = visualizer.visualize_method("checkValue", instructions)
    
    # Save to file
    output_path = Path("output/cfg_demos/basic_method.dot")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dot_content)
    
    print(f"Generated basic CFG visualization: {output_path}")
    print("\nDOT content preview:")
    print("-" * 40)
    lines = dot_content.split('\n')[:20]
    for line in lines:
        print(line)
    print("...")
    
    # Generate statistics
    from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer
    analyzer = ControlFlowAnalyzer()
    blocks = analyzer.analyze(instructions)
    stats = visualizer.generate_summary_stats(blocks, analyzer.block_graph)
    
    print(f"\nCFG Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")


def demo_loop_visualization():
    """Demonstrate loop visualization."""
    print("\n\nLoop CFG Visualization Demo")
    print("=" * 50)
    
    instructions = create_loop_method()
    
    # Use different visualization options
    options = VisualizationOptions(
        show_addresses=True,
        show_conditions=True,
        highlight_loops=True,
        font_size=11,
    )
    visualizer = CFGVisualizer(options)
    
    # Generate visualization
    dot_content = visualizer.visualize_method("processArray", instructions)
    
    # Save to file
    output_path = Path("output/cfg_demos/loop_method.dot")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dot_content)
    
    print(f"Generated loop CFG visualization: {output_path}")
    
    # Show loop detection
    print("\nLoop edges detected in CFG")
    print("(Look for bold blue edges labeled 'loop' in the visualization)")


def demo_nested_visualization():
    """Demonstrate nested control structure visualization."""
    print("\n\nNested Control Structure Visualization Demo")
    print("=" * 50)
    
    instructions = create_nested_method()
    
    # Use simplified view
    options = VisualizationOptions(
        level=VisualizationLevel.METHOD,
        show_instructions=True,
        max_instructions_per_node=5,
        color_scheme="default",
    )
    visualizer = CFGVisualizer(options)
    
    # Generate visualization
    dot_content = visualizer.visualize_method("processNested", instructions)
    
    # Save to file
    output_path = Path("output/cfg_demos/nested_method.dot")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dot_content)
    
    print(f"Generated nested CFG visualization: {output_path}")


def demo_class_visualization():
    """Demonstrate class-level CFG visualization."""
    print("\n\nClass-Level CFG Visualization Demo")
    print("=" * 50)
    
    # Create multiple methods
    methods = {
        "initialize": [
            PCodeInstruction(address=0x00, opcode=b'\x10', opcode_name="PUSHCONST", operands=b'\x00', operand_values=[0], text_format="PUSHCONST 0", opcode_value=0x10),
            PCodeInstruction(address=0x02, opcode=b'\x20', opcode_name="POPVAR", operands=b'\x01', operand_values=[1], text_format="POPVAR 1", opcode_value=0x20),
            PCodeInstruction(address=0x04, opcode=b'\x60', opcode_name="RETURN", operands=b'', operand_values=[], text_format="RETURN", opcode_value=0x60),
        ],
        "checkValue": create_simple_method(),
        "processArray": create_loop_method(),
        "complexMethod": create_nested_method(),
    }
    
    visualizer = CFGVisualizer()
    
    # Generate class visualization
    dot_content = visualizer.visualize_class("SampleProcessor", methods)
    
    # Save to file
    output_path = Path("output/cfg_demos/class_cfg.dot")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dot_content)
    
    print(f"Generated class CFG visualization: {output_path}")
    print(f"Contains {len(methods)} methods in separate subgraphs")


def demo_dark_theme():
    """Demonstrate dark theme visualization."""
    print("\n\nDark Theme CFG Visualization Demo")
    print("=" * 50)
    
    instructions = create_simple_method()
    
    # Use dark theme
    options = VisualizationOptions(
        color_scheme="dark",
        font_name="Monaco",
        font_size=10,
    )
    visualizer = CFGVisualizer(options)
    
    # Generate visualization
    dot_content = visualizer.visualize_method("darkThemeDemo", instructions)
    
    # Save to file
    output_path = Path("output/cfg_demos/dark_theme.dot")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dot_content)
    
    print(f"Generated dark theme CFG visualization: {output_path}")


def demo_export_formats():
    """Demonstrate exporting to different formats."""
    print("\n\nExport Formats Demo")
    print("=" * 50)
    
    instructions = create_simple_method()
    visualizer = CFGVisualizer()
    
    # Generate DOT
    dot_content = visualizer.visualize_method("exportDemo", instructions)
    
    # Save DOT
    dot_path = Path("output/cfg_demos/export_demo.dot")
    dot_path.parent.mkdir(parents=True, exist_ok=True)
    dot_path.write_text(dot_content)
    
    print(f"Saved DOT file: {dot_path}")
    
    # Try to export to SVG (requires Graphviz)
    svg_path = Path("output/cfg_demos/export_demo.svg")
    success = visualizer.export_to_svg(dot_content, svg_path)
    
    if success:
        print(f"Exported to SVG: {svg_path}")
        print("(Open in a browser to view the interactive graph)")
    else:
        print("SVG export requires Graphviz to be installed")
        print("Install with: brew install graphviz (macOS) or apt-get install graphviz (Linux)")
    
    print("\nTo convert DOT files to other formats:")
    print("  - PNG: dot -Tpng input.dot -o output.png")
    print("  - PDF: dot -Tpdf input.dot -o output.pdf")
    print("  - SVG: dot -Tsvg input.dot -o output.svg")


def main():
    """Run all CFG visualization demonstrations."""
    print("PowerBuilder Control Flow Graph (CFG) Visualization Demo")
    print("=" * 70)
    print("This demonstrates the CFG visualization capabilities:")
    print("- Method-level control flow visualization")
    print("- Class-level visualization with multiple methods")
    print("- Support for various control structures (if/else, loops, nested)")
    print("- Export to DOT/GraphViz format")
    print("- Customizable visualization options and themes")
    print()
    
    demo_basic_visualization()
    demo_loop_visualization()
    demo_nested_visualization()
    demo_class_visualization()
    demo_dark_theme()
    demo_export_formats()
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("\nGenerated files in: output/cfg_demos/")
    print("Open .dot files with Graphviz or convert to images:")
    print("  dot -Tpng file.dot -o file.png")


if __name__ == "__main__":
    main()