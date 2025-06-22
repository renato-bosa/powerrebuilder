"""Control Flow Graph (CFG) visualization for PowerBuilder P-code.

This module generates visual representations of control flow graphs
extracted from decompiled PowerBuilder code. It supports both method-level
and class-level visualization, with export to DOT/GraphViz format.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from decompile.analysis.control_flow_analyzer import ControlFlowAnalyzer
from decompile.core.pcode_decoder import PCodeInstruction
from decompile.types import BlockType, ControlBlock

logger = logging.getLogger(__name__)


class VisualizationLevel(Enum):
    """Level of detail for CFG visualization."""

    METHOD = "method"       # Single method/function
    CLASS = "class"        # All methods in a class
    MODULE = "module"      # Entire module/file
    SIMPLIFIED = "simplified"  # Simplified view with just control structures


@dataclass
class VisualizationOptions:
    """Options for CFG visualization."""

    # Basic options
    level: VisualizationLevel = VisualizationLevel.METHOD
    show_instructions: bool = True
    show_addresses: bool = True
    show_conditions: bool = True

    # Styling options
    font_name: str = "Courier"
    font_size: int = 10
    node_shape: str = "box"
    color_scheme: str = "default"

    # Layout options
    direction: str = "TB"  # Top-Bottom, can be LR for Left-Right
    rank_dir: str = "TB"

    # Filtering options
    max_instructions_per_node: int = 10
    collapse_linear_blocks: bool = False
    highlight_loops: bool = True
    highlight_exceptions: bool = True


class CFGVisualizer:
    """Generates visual control flow graphs from analyzed P-code."""

    # Color schemes
    COLOR_SCHEMES = {
        "default": {
            "basic": "#E8F4FD", "if": "#E8F4FD", "while": "#FFF4E6", "for": "#FFF4E6", "do_while": "#FFF4E6", "repeat_until": "#FFF4E6", "choose_case": "#F3E5F5", "case": "#FCE4EC", "try": "#FFEBEE", "catch": "#FFEBEE", "finally": "#FFEBEE", "entry": "#C8E6C9", "exit": "#FFCDD2", "border": "#333333", "edge": "#666666", "conditional_edge": "#FF5722", "loop_edge": "#2196F3", }, "dark": {
            "basic": "#37474F", "if": "#455A64", "while": "#5D4037", "for": "#5D4037", "do_while": "#5D4037", "repeat_until": "#5D4037", "choose_case": "#4A148C", "case": "#880E4F", "try": "#B71C1C", "catch": "#B71C1C", "finally": "#B71C1C", "entry": "#1B5E20", "exit": "#D32F2F", "border": "#FFFFFF", "edge": "#CCCCCC", "conditional_edge": "#FF9800", "loop_edge": "#64B5F6", },
    }

    def __init__(self, options: VisualizationOptions | None = None) -> None:


        """Initialize the CFG visualizer.

        Args:
            options: Visualization options
        """
        self.options = options or VisualizationOptions()
        self.colors = self.COLOR_SCHEMES.get(
            self.options.color_scheme, self.COLOR_SCHEMES["default"],
        )

    def visualize_method(
        self, method_name: str, instructions: list[PCodeInstruction], output_path: Path | None = None,
    ) -> str:




        """Visualize control flow for a single method.

        Args:
            method_name: Name of the method
            instructions: P-code instructions for the method
            output_path: Optional path to save the DOT file

        Returns:
            DOT format string
        """
        # Analyze control flow
        analyzer = ControlFlowAnalyzer()
        blocks = analyzer.analyze(instructions)

        # Generate DOT
        dot_content = self._generate_dot(
            f"{method_name}_cfg", blocks, analyzer.block_graph, analyzer.labels,
        )

        # Save if path provided
        if output_path:
            output_path.write_text(dot_content)
            logger.info("Saved CFG visualization to %s", output_path)

        return dot_content

    def visualize_class(
        self, class_name: str, methods: dict[str, list[PCodeInstruction]], output_path: Path | None = None,
    ) -> str:




        """Visualize control flow for an entire class.

        Args:
            class_name: Name of the class
            methods: Dictionary mapping method names to instructions
            output_path: Optional path to save the DOT file

        Returns:
            DOT format string
        """
        # Generate DOT with subgraphs for each method
        lines = []
        lines.append(f'digraph "{class_name}_cfg" {{')
        lines.append(f'  label="{class_name} Control Flow"')
        lines.append(f'  fontname="{self.options.font_name}";')
        lines.append(f"  fontsize={self.options.font_size + 4};")
        lines.append(f"  rankdir={self.options.direction};")
        lines.append("  compound=true;")
        lines.append("")

        # Process each method
        for method_name, instructions in methods.items():
            if not instructions:
                continue

            # Analyze control flow
            analyzer = ControlFlowAnalyzer()
            blocks = analyzer.analyze(instructions)

            # Create subgraph for method
            lines.append(f'  subgraph "cluster_{method_name}" {{')
            lines.append(f'    label="{method_name}";')
            lines.append(f"    style=filled;")
            lines.append(f'    fillcolor="#F5F5F5";')
            lines.append("")

            # Add nodes and edges for this method
            method_lines = self._generate_method_content(
                blocks,
                analyzer.block_graph,
                analyzer.labels,
                prefix=f"{method_name}_",
            )

            for line in method_lines:
                lines.append(f"    {line}")

            lines.append("  }")
            lines.append("")

        lines.append("}")

        dot_content = "\n".join(lines)

        # Save if path provided
        if output_path:
            output_path.write_text(dot_content)
            logger.info("Saved class CFG visualization to %s", output_path)

        return dot_content

    def _generate_dot(
        self,
        graph_name: str,
        blocks: list[ControlBlock],
        block_graph: dict[int, list[int]],
        labels: dict[int, str],
    ) -> str:




        """Generate DOT format representation of the CFG.

        Args:
            graph_name: Name for the graph
            blocks: Control flow blocks
            block_graph: Graph edges (block index -> list of target indices)
            labels: Address labels

        Returns:
            DOT format string
        """
        lines = []

        # Graph header
        lines.append(f'digraph "{graph_name}" {{')
        lines.append(f"  rankdir={self.options.direction};")
        lines.append(f'  fontname="{self.options.font_name}";')
        lines.append(f"  fontsize={self.options.font_size};")
        lines.append(f'  node [shape={self.options.node_shape}, fontname="{self.options.font_name}", fontsize={self.options.font_size}];')
        lines.append(f'  edge [fontname="{self.options.font_name}", fontsize={self.options.font_size - 2}];')
        lines.append("")

        # Add nodes and edges
        content_lines = self._generate_method_content(blocks, block_graph, labels)
        lines.extend(f"  {line}" for line in content_lines)

        lines.append("}")

        return "\n".join(lines)

    def _generate_method_content(
        self,
        blocks: list[ControlBlock],
        block_graph: dict[int, list[int]],
        labels: dict[int, str],
        prefix: str = "",
    ) -> list[str]:




        """Generate DOT content for a method's CFG.

        Args:
            blocks: Control flow blocks
            block_graph: Graph edges
            labels: Address labels
            prefix: Prefix for node IDs (for subgraphs)

        Returns:
            List of DOT content lines
        """
        lines = []

        # Track which blocks we've already processed
        processed_blocks: set[int] = set()

        # Add entry node
        if blocks:
            lines.append(f'{prefix}entry [label="Entry", style=filled, fillcolor="{self.colors["entry"]}"];')
            lines.append(f"{prefix}entry -> {prefix}block_0;")
            lines.append("")

        # Process blocks
        for i, block in enumerate(blocks):
            node_lines = self._generate_block_node(block, i, labels, prefix)
            lines.extend(node_lines)
            processed_blocks.add(i)

            # Add edges
            if i in block_graph:
                for target_idx in block_graph[i]:
                    edge_attrs = self._get_edge_attributes(block, blocks[target_idx] if target_idx < len(blocks) else None)
                    lines.append(f"{prefix}block_{i} -> {prefix}block_{target_idx} [{edge_attrs}];")

        # Add exit nodes for blocks with no successors
        exit_blocks = []
        for i, block in enumerate(blocks):
            # Check if it's a return/exit block or has no successors
            if block.instructions and block.instructions[-1].opcode_name in ["RETURN", "RET", "HALT", "EXIT"]:
                exit_blocks.append(i)
            elif i not in block_graph or not block_graph[i]:
                # Dead end blocks also go to exit
                exit_blocks.append(i)

        if exit_blocks:
            lines.append("")
            lines.append(f'{prefix}exit [label="Exit", style=filled, fillcolor="{self.colors["exit"]}"];')
            for exit_idx in exit_blocks:
                lines.append(f"{prefix}block_{exit_idx} -> {prefix}exit;")

        return lines

    def _generate_block_node(
        self,
        block: ControlBlock,
        block_idx: int,
        labels: dict[int, str],
        prefix: str = "",
    ) -> list[str]:




        """Generate DOT node for a control block.

        Args:
            block: Control flow block
            block_idx: Index of the block
            labels: Address labels
            prefix: Prefix for node ID

        Returns:
            List of DOT lines for the node
        """
        lines = []

        # Build label content
        label_parts = []

        # Add block type header
        if block.type != BlockType.BASIC:
            label_parts.append(f"[{block.type.name}]")

        # Add address info
        if self.options.show_addresses and block.start_addr in labels:
            label_parts.append(f"{labels[block.start_addr]}:")
        elif self.options.show_addresses:
            label_parts.append(f"{block.start_addr:04X}:")

        # Add condition for control structures
        if self.options.show_conditions and block.metadata:
            if "condition" in block.metadata:
                label_parts.append(f"if ({block.metadata["condition"]})")
            elif "expression" in block.metadata:
                label_parts.append(f"switch ({block.metadata["expression"]})")

        # Add instructions  
        if self.options.show_instructions and block.instructions:
            if self.options.level == VisualizationLevel.SIMPLIFIED:
                # Just show count
                label_parts.append(f"[{len(block.instructions)} instructions]")
            else:
                # Show actual instructions
                max_inst = self.options.max_instructions_per_node
                for j, inst in enumerate(block.instructions[:
                    max_inst]):
                    inst_str = self._format_instruction(inst)
                    label_parts.append(inst_str)

                if len(block.instructions) > max_inst:
                    label_parts.append(f"... +{len(block.instructions) - max_inst} more")

        # Handle nested blocks (if/then/else, loops, etc.)
        if block.then_block and self.options.show_instructions:
            label_parts.append("THEN:")
            for inst in block.then_block.instructions[:3]:  # Show first few
                label_parts.append(f"  {self._format_instruction(inst)}")
            if len(block.then_block.instructions) > 3:
                label_parts.append(f"  ... +{len(block.then_block.instructions) - 3} more")

        if block.else_block and self.options.show_instructions:
            label_parts.append("ELSE:")
            for inst in block.else_block.instructions[:3]:  # Show first few
                label_parts.append(f"  {self._format_instruction(inst)}")
            if len(block.else_block.instructions) > 3:
                label_parts.append(f"  ... +{len(block.else_block.instructions) - 3} more")

        if block.body and self.options.show_instructions:
            label_parts.append("BODY:")
            for inst in block.body.instructions[:3]:  # Show first few
                label_parts.append(f"  {self._format_instruction(inst)}")
            if len(block.body.instructions) > 3:
                label_parts.append(f"  ... +{len(block.body.instructions) - 3} more")

        if hasattr(block, "cases") and block.cases:
            label_parts.append(f"CASES: {len(block.cases)}")

        # Build node attributes
        node_color = self._get_block_color(block)
        label_text = "\\l".join(label_parts) + "\\l"  # Left-aligned lines

        lines.append(
            f'{prefix}block_{block_idx} [label="{label_text}", '
            f'style=filled, fillcolor="{node_color}", '
            f'color="{self.colors["border"]}"];',
        )

        return lines

    def _format_instruction(self, inst: PCodeInstruction) -> str:




        """Format a single instruction for display.

        Args:
            inst: P-code instruction

        Returns:
            Formatted instruction string
        """
        parts = []

        if self.options.show_addresses:
            parts.append(f"{inst.address:04X}")

        parts.append(inst.opcode_name)

        if inst.operand_values:
            operands = []
            for op in inst.operand_values:
                if isinstance(op, str):
                    operands.append(f'"{op}"')
                else:
                    operands.append(str(op))
            parts.append(" ".join(operands))

        return " ".join(parts)

    def _get_block_summary(self, block: ControlBlock) -> str:




        """Get a summary of a block for nested display.

        Args:
            block: Control flow block

        Returns:
            Summary string
        """
        if not block.instructions:
            return "[empty]"
        return f"[{len(block.instructions)} inst]"

    def _get_block_color(self, block: ControlBlock) -> str:




        """Get the fill color for a block based on its type.

        Args:
            block: Control flow block

        Returns:
            Color string
        """
        type_map = {
            BlockType.BASIC: "basic",
            BlockType.IF: "if",
            BlockType.WHILE: "while",
            BlockType.FOR: "for",
            BlockType.DO_WHILE: "do_while",
            BlockType.REPEAT_UNTIL: "repeat_until",
            BlockType.CHOOSE_CASE: "choose_case",
            BlockType.CASE: "case",
            BlockType.TRY: "try",
            BlockType.CATCH: "catch",
            BlockType.FINALLY: "finally",
        }

        color_key = type_map.get(block.type, "basic")
        return self.colors.get(color_key, self.colors["basic"])

    def _get_edge_attributes(
        self,
        source_block: ControlBlock,
        target_block: ControlBlock | None,
    ) -> str:




        """Get DOT attributes for an edge.

        Args:
            source_block: Source block
            target_block: Target block (if exists)

        Returns:
            DOT attribute string
        """
        attrs = []

        # Determine edge type
        if source_block.instructions:
            last_inst = source_block.instructions[-1]

            # Conditional edges
            if last_inst.opcode_name in ControlFlowAnalyzer.CONDITIONAL_TERMINATORS:
                attrs.append(f'color="{self.colors["conditional_edge"]}"')
                attrs.append('style="dashed"')

                # Label the edge
                if last_inst.opcode_name in ["JUMPTRUE", "BRTRUE"]:
                    attrs.append('label="T"')
                elif last_inst.opcode_name in ["JUMPFALSE", "BRFALSE"]:
                    attrs.append('label="F"')

            # Loop back edges
            elif (target_block and 
                  target_block.start_addr < source_block.start_addr):
                attrs.append(f'color="{self.colors["loop_edge"]}"')
                attrs.append('style="bold"')
                attrs.append('label="loop"')

        # Default edge
        if not attrs:
            attrs.append(f'color="{self.colors["edge"]}"')

        return ", ".join(attrs)

    def export_to_svg(
        self,
        dot_content: str,
        svg_path: Path,
        engine: str = "dot",
    ) -> bool:




        """Export DOT content to SVG using Graphviz.

        Args:
            dot_content: DOT format content
            svg_path: Path to save SVG file
            engine: Graphviz engine (dot, neato, circo, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            import tempfile

            # Write DOT to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False) as f:
                f.write(dot_content)
                dot_file = f.name

            # Run Graphviz
            cmd = [engine, "-Tsvg", dot_file, "-o", str(svg_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Clean up
            Path(dot_file).unlink()

            if result.returncode == 0:
                logger.info("Exported CFG to SVG: %s", svg_path)
                return True
            else:
                logger.error("Graphviz error: %s", result.stderr)
                return False

        except Exception as e:
            logger.error("Failed to export to SVG: %s", e)
            return False

    def generate_summary_stats(
        self,
        blocks: list[ControlBlock],
        block_graph: dict[int, list[int]],
    ) -> dict[str, int]:




        """Generate summary statistics for the CFG.

        Args:
            blocks: Control flow blocks
            block_graph: Graph edges

        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_blocks": len(blocks),
            "basic_blocks": 0,
            "if_blocks": 0,
            "loop_blocks": 0,
            "switch_blocks": 0,
            "total_instructions": 0,
            "total_edges": sum(len(targets) for targets in block_graph.values()),
            "cyclomatic_complexity": 0,
        }

        # Count block types
        for block in blocks:
            stats["total_instructions"] += len(block.instructions)

            if block.type == BlockType.BASIC:
                stats["basic_blocks"] += 1
            elif block.type == BlockType.IF:
                stats["if_blocks"] += 1
            elif block.type in [BlockType.WHILE, BlockType.FOR, 
                              BlockType.DO_WHILE, BlockType.REPEAT_UNTIL,]:
                stats["loop_blocks"] += 1
            elif block.type == BlockType.CHOOSE_CASE:
                stats["switch_blocks"] += 1

        # Calculate cyclomatic complexity
        # CC = E - N + 2P (E=edges, N=nodes, P=connected components)
        # For a single method, P=1
        stats["cyclomatic_complexity"] = stats["total_edges"] - stats["total_blocks"] + 2

        return stats
