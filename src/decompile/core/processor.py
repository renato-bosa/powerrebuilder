"""Post-process decompiled PowerBuilder code.

This module handles post-processing of decompiled code, including:
- Label cleanup and removal
- Code artifact cleanup
- Output optimization
- Special case handling
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from src.decompile.reconstruction.formatter import (
    FormattingOptions,
    PowerBuilderFormatter,
)
from src.decompile.types import BlockType, ControlBlock

logger = logging.getLogger(__name__)


class DecompiledOutputFilter:
    """Filter for cleaning up decompiled output.
    
    This class provides post-processing filters to clean up the raw decompiled
    output before it's written to files. It handles common cleanup tasks like
    removing redundant labels, cleaning empty blocks, and normalizing whitespace.
    """

    def __init__(self) -> None:
        """Initialize the filter."""
        self.filters = [
            self._remove_redundant_labels,
            self._clean_empty_blocks,
            self._normalize_whitespace,
        ]

    def filter_output(self, content: str) -> str:
        """Apply all filters to the output content.

        Args:
            content: Raw decompiled content

        Returns:
            Filtered content
        """
        filtered = content
        for filter_func in self.filters:
            filtered = filter_func(filtered)
        return filtered

    def _remove_redundant_labels(self, content: str) -> str:
        """Remove redundant labels from the output.
        
        Args:
            content: Content to process
            
        Returns:
            Content with redundant labels removed
        """
        # TODO: Implement label cleanup based on usage analysis
        return content

    def _clean_empty_blocks(self, content: str) -> str:
        """Remove empty code blocks.
        
        Args:
            content: Content to process
            
        Returns:
            Content with empty blocks cleaned
        """
        lines = content.split("\n")
        cleaned = []

        for line in lines:
            # Skip lines that are just comments about empty blocks
            if "// Empty block" in line:
                continue
            cleaned.append(line)

        return "\n".join(cleaned)

    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in the output.
        
        Args:
            content: Content to process
            
        Returns:
            Content with normalized whitespace
        """
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split("\n")]

        # Remove excessive blank lines (more than 2 consecutive)
        cleaned = []
        blank_count = 0

        for line in lines:
            if not line:
                blank_count += 1
                if blank_count <= 2:
                    cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)

        return "\n".join(cleaned)


class ProcessingMode(Enum):
    """Processing modes for different optimization levels."""

    MINIMAL = auto()  # Minimal processing, preserve most artifacts
    STANDARD = auto()  # Standard cleanup and optimization
    AGGRESSIVE = auto()  # Aggressive optimization, may lose some debug info


@dataclass
class ProcessingOptions:
    """Options for post-processing."""

    mode: ProcessingMode = ProcessingMode.STANDARD
    remove_labels: bool = True
    remove_unreachable_code: bool = True
    optimize_expressions: bool = True
    merge_consecutive_assignments: bool = True
    simplify_conditionals: bool = True
    remove_empty_blocks: bool = True
    preserve_comments: bool = True
    preserve_debug_info: bool = False
    inline_simple_functions: bool = False
    formatting_options: FormattingOptions | None = None


class PostProcessor:
    """Post-processes decompiled PowerBuilder code."""

    def __init__(self, options: ProcessingOptions | None = None) -> None:
        """Initialize the post-processor.

        Args:
            options: Processing options (uses defaults if None)
        """
        self.options = options or ProcessingOptions()
        self.formatter = PowerBuilderFormatter(self.options.formatting_options)
        self._label_references: set[str] = set()
        self._label_definitions: set[str] = set()

    def process_object(
        self, blocks: list[ControlBlock], metadata: dict[str, Any]
    ) -> str:
        """Process a complete decompiled object.

        Args:
            blocks: List of control flow blocks
            metadata: Object metadata

        Returns:
            Processed and formatted PowerBuilder code
        """
        # First pass: analyze labels
        if self.options.remove_labels:
            self._analyze_labels(blocks)

        # Process each block
        processed_blocks = []
        for block in blocks:
            processed_block = self._process_block(block)
            if processed_block is not None:  # Skip removed blocks
                processed_blocks.append(processed_block)

        # Apply formatting
        return self.formatter.format_object(processed_blocks, metadata)

    def _process_block(self, block: ControlBlock) -> ControlBlock | None:
        """Process a single control flow block.

        Args:
            block: Block to process

        Returns:
            Processed block or None if block should be removed
        """
        # Process statements
        if hasattr(block, "statements") and block.statements:
            block.statements = self._process_statements(block.statements)

        # Process nested blocks
        if hasattr(block, "then_block") and block.then_block:
            processed = self._process_block(block.then_block)
            block.then_block = processed

        if hasattr(block, "else_block") and block.else_block:
            processed = self._process_block(block.else_block)
            block.else_block = processed

        if hasattr(block, "body") and block.body:
            processed = self._process_block(block.body)
            block.body = processed

        if hasattr(block, "cases") and block.cases:
            processed_cases = []
            for case in block.cases:
                if isinstance(case, dict) and "body" in case:
                    processed_body = self._process_block(case["body"])
                    if processed_body:
                        case["body"] = processed_body
                        processed_cases.append(case)
                else:
                    processed_cases.append(case)
            block.cases = processed_cases

        if hasattr(block, "default_case") and block.default_case:
            processed = self._process_block(block.default_case)
            block.default_case = processed

        if hasattr(block, "try_body") and block.try_body:
            processed = self._process_block(block.try_body)
            block.try_body = processed

        if hasattr(block, "catch_blocks") and block.catch_blocks:
            for catch in block.catch_blocks:
                if "body" in catch:
                    processed = self._process_block(catch["body"])
                    if processed:
                        catch["body"] = processed

        if hasattr(block, "finally_block") and block.finally_block:
            processed = self._process_block(block.finally_block)
            block.finally_block = processed

        # Check if block should be removed
        if self.options.remove_empty_blocks and self._is_empty_block(block):
            return None

        # Optimize block structure
        if self.options.mode != ProcessingMode.MINIMAL:
            block = self._optimize_block_structure(block)

        return block

    def _process_statements(self, statements: list[str]) -> list[str]:
        """Process a list of statements.

        Args:
            statements: List of statements to process

        Returns:
            Processed statements
        """
        processed = []
        i = 0

        while i < len(statements):
            stmt = statements[i]

            # Skip empty statements
            if not stmt or (isinstance(stmt, str) and not stmt.strip()):
                i += 1
                continue

            # Handle labels
            if self.options.remove_labels and self._is_label(stmt):
                label_name = self._extract_label_name(stmt)
                if label_name and label_name not in self._label_references:
                    # Label is not referenced, remove it
                    logger.debug("Removing unreferenced label: %s", label_name)
                    i += 1
                    continue

            # Handle comments
            if self._is_comment(stmt):
                if self.options.preserve_comments:
                    processed.append(stmt)
                i += 1
                continue

            # Apply statement-level optimizations
            if self.options.mode != ProcessingMode.MINIMAL:
                stmt = self._optimize_statement(stmt)

            # Check for consecutive assignments to merge
            if (
                self.options.merge_consecutive_assignments
                and i + 1 < len(statements)
                and self._can_merge_assignments(stmt, statements[i + 1])
            ):
                merged = self._merge_assignments(stmt, statements[i + 1])
                processed.append(merged)
                i += 2  # Skip next statement
                continue

            processed.append(stmt)
            i += 1

        # Apply additional processing based on mode
        if self.options.mode == ProcessingMode.AGGRESSIVE:
            processed = self._aggressive_optimization(processed)

        return processed

    def _analyze_labels(self, blocks: list[ControlBlock]) -> None:
        """Analyze label usage across all blocks.

        Args:
            blocks: List of blocks to analyze
        """
        self._label_references.clear()
        self._label_definitions.clear()

        for block in blocks:
            self._analyze_labels_in_block(block)

    def _analyze_labels_in_block(self, block: ControlBlock) -> None:
        """Analyze labels in a single block.

        Args:
            block: Block to analyze
        """
        if hasattr(block, "statements") and block.statements:
            for stmt in block.statements:
                if self._is_label(stmt):
                    label_name = self._extract_label_name(stmt)
                    if label_name:
                        self._label_definitions.add(label_name)
                else:
                    # Check for label references (GOTO statements)
                    references = self._find_label_references(stmt)
                    self._label_references.update(references)

        # Analyze nested blocks
        for attr in [
            "then_block",
            "else_block",
            "body",
            "try_body",
            "finally_block",
            "default_case",
        ]:
            if hasattr(block, attr):
                nested_block = getattr(block, attr)
                if nested_block:
                    self._analyze_labels_in_block(nested_block)

        if hasattr(block, "cases") and block.cases:
            for case in block.cases:
                if isinstance(case, dict) and "body" in case:
                    self._analyze_labels_in_block(case["body"])

        if hasattr(block, "catch_blocks") and block.catch_blocks:
            for catch in block.catch_blocks:
                if "body" in catch:
                    self._analyze_labels_in_block(catch["body"])

    def _is_label(self, stmt: str) -> bool:
        """Check if a statement is a label.

        Args:
            stmt: Statement to check

        Returns:
            True if statement is a label
        """
        if not isinstance(stmt, str):
            return False

        stripped = stmt.strip()
        # Labels typically start with L_ and end with :
        return stripped.startswith("L_") and stripped.endswith(":")

    def _extract_label_name(self, stmt: str) -> str | None:
        """Extract label name from a label statement.

        Args:
            stmt: Label statement

        Returns:
            Label name without the colon, or None
        """
        if not self._is_label(stmt):
            return None

        stripped = stmt.strip()
        return stripped[:-1]  # Remove the colon

    def _find_label_references(self, stmt: str) -> set[str]:
        """Find label references in a statement.

        Args:
            stmt: Statement to search

        Returns:
            Set of referenced label names
        """
        references = set()

        if not isinstance(stmt, str):
            return references

        # Look for GOTO statements
        goto_pattern = r"\bgoto\s+(\w+)\b"
        matches = re.finditer(goto_pattern, stmt, re.IGNORECASE)
        for match in matches:
            references.add(match.group(1))

        # Look for other label references (e.g., in comments)
        label_ref_pattern = r"\bL_\w+\b"
        matches = re.finditer(label_ref_pattern, stmt)
        for match in matches:
            # Verify it's not the label definition itself
            if not stmt.strip().endswith(":"):
                references.add(match.group(0))

        return references

    def _is_comment(self, stmt: str) -> bool:
        """Check if a statement is a comment.

        Args:
            stmt: Statement to check

        Returns:
            True if statement is a comment
        """
        if not isinstance(stmt, str):
            return False

        stripped = stmt.strip()
        return stripped.startswith(("//", "/*"))

    def _is_empty_block(self, block: ControlBlock) -> bool:
        """Check if a block is empty.

        Args:
            block: Block to check

        Returns:
            True if block is empty
        """
        # Check statements
        if hasattr(block, "statements") and block.statements:
            # Filter out comments and labels
            real_statements = [
                s
                for s in block.statements
                if not self._is_comment(s) and not self._is_label(s)
            ]
            if real_statements:
                return False

        # Check nested blocks
        nested_attrs = [
            "then_block",
            "else_block",
            "body",
            "try_body",
            "finally_block",
            "default_case",
        ]
        for attr in nested_attrs:
            if hasattr(block, attr) and getattr(block, attr):
                return False

        if hasattr(block, "cases") and block.cases:
            return False

        return not (hasattr(block, "catch_blocks") and block.catch_blocks)

    def _optimize_statement(self, stmt: str) -> str:
        """Optimize a single statement.

        Args:
            stmt: Statement to optimize

        Returns:
            Optimized statement
        """
        if not isinstance(stmt, str):
            return stmt

        # Remove redundant parentheses
        if self.options.optimize_expressions:
            stmt = self._remove_redundant_parentheses(stmt)

        # Simplify boolean expressions
        if self.options.simplify_conditionals:
            stmt = self._simplify_boolean_expression(stmt)

        # Optimize common patterns
        return self._optimize_common_patterns(stmt)

    def _remove_redundant_parentheses(self, expr: str) -> str:
        """Remove redundant parentheses from an expression.

        Args:
            expr: Expression to process

        Returns:
            Expression with redundant parentheses removed
        """
        # Simple implementation - could be enhanced
        # Remove double parentheses
        while "((" in expr and "))" in expr:
            expr = expr.replace("((", "(").replace("))", ")")

        return expr

    def _simplify_boolean_expression(self, expr: str) -> str:
        """Simplify boolean expressions.

        Args:
            expr: Expression to simplify

        Returns:
            Simplified expression
        """
        # Common simplifications
        replacements = [
            (r"\bTRUE\s+AND\s+(\w+)\b", r"\1"),  # TRUE AND x -> x
            (r"\b(\w+)\s+AND\s+TRUE\b", r"\1"),  # x AND TRUE -> x
            (r"\bFALSE\s+OR\s+(\w+)\b", r"\1"),  # FALSE OR x -> x
            (r"\b(\w+)\s+OR\s+FALSE\b", r"\1"),  # x OR FALSE -> x
            (r"\bNOT\s+NOT\s+(\w+)\b", r"\1"),  # NOT NOT x -> x
            (r"\b(\w+)\s*=\s*TRUE\b", r"\1"),  # x = TRUE -> x
            (r"\b(\w+)\s*<>\s*FALSE\b", r"\1"),  # x <> FALSE -> x
        ]

        for pattern, replacement in replacements:
            expr = re.sub(pattern, replacement, expr, flags=re.IGNORECASE)

        return expr

    def _optimize_common_patterns(self, stmt: str) -> str:
        """Optimize common code patterns.

        Args:
            stmt: Statement to optimize

        Returns:
            Optimized statement
        """
        # Optimize self-assignment
        self_assign_pattern = r"^(\w+)\s*=\s*\1$"
        if re.match(self_assign_pattern, stmt.strip()):
            return f"// {stmt} // Removed self-assignment"

        # Optimize increment/decrement patterns
        inc_pattern = r"^(\w+)\s*=\s*\1\s*\+\s*1$"
        if re.match(inc_pattern, stmt.strip()):
            var_name = re.match(inc_pattern, stmt.strip()).group(1)
            return f"{var_name}++"

        dec_pattern = r"^(\w+)\s*=\s*\1\s*-\s*1$"
        if re.match(dec_pattern, stmt.strip()):
            var_name = re.match(dec_pattern, stmt.strip()).group(1)
            return f"{var_name}--"

        return stmt

    def _can_merge_assignments(self, stmt1: str, stmt2: str) -> bool:
        """Check if two assignments can be merged.

        Args:
            stmt1: First statement
            stmt2: Second statement

        Returns:
            True if assignments can be merged
        """
        if not isinstance(stmt1, str) or not isinstance(stmt2, str):
            return False

        # Check if both are assignments to the same variable
        assign_pattern = r"^(\w+)\s*=\s*(.+)$"
        match1 = re.match(assign_pattern, stmt1.strip())
        match2 = re.match(assign_pattern, stmt2.strip())

        if match1 and match2:
            var1 = match1.group(1)
            var2 = match2.group(1)
            return var1 == var2

        return False

    def _merge_assignments(self, stmt1: str, stmt2: str) -> str:
        """Merge two consecutive assignments.

        Args:
            stmt1: First assignment
            stmt2: Second assignment

        Returns:
            Merged assignment
        """
        assign_pattern = r"^(\w+)\s*=\s*(.+)$"
        match2 = re.match(assign_pattern, stmt2.strip())

        if match2:
            var = match2.group(1)
            value = match2.group(2)
            return f"{var} = {value}  // Merged consecutive assignments"

        return stmt2

    def _optimize_block_structure(self, block: ControlBlock) -> ControlBlock:
        """Optimize block structure.

        Args:
            block: Block to optimize

        Returns:
            Optimized block
        """
        # Optimize IF blocks
        if block.type == BlockType.IF:
            block = self._optimize_if_block(block)

        # Optimize loops
        elif block.type in [BlockType.WHILE, BlockType.FOR, BlockType.DO_WHILE]:
            block = self._optimize_loop_block(block)

        # Optimize CHOOSE CASE blocks
        elif block.type == BlockType.CHOOSE_CASE:
            block = self._optimize_choose_case_block(block)

        return block

    def _optimize_if_block(self, block: ControlBlock) -> ControlBlock:
        """Optimize IF block structure.

        Args:
            block: IF block to optimize

        Returns:
            Optimized block
        """
        # Simplify condition if possible
        if "condition" in block.metadata and self.options.simplify_conditionals:
            block.metadata["condition"] = self._simplify_boolean_expression(
                block.metadata["condition"]
            )

        # Remove empty branches
        if hasattr(block, "then_block") and self._is_empty_block(block.then_block):
            block.then_block = None

        if hasattr(block, "else_block") and self._is_empty_block(block.else_block):
            block.else_block = None

        # Convert IF with only ELSE to IF NOT
        if (
            (not hasattr(block, "then_block") or block.then_block is None)
            and hasattr(block, "else_block")
            and block.else_block
        ):
            # Negate condition
            if "condition" in block.metadata:
                block.metadata["condition"] = f"NOT ({block.metadata['condition']})"
            block.then_block = block.else_block
            block.else_block = None

        return block

    def _optimize_loop_block(self, block: ControlBlock) -> ControlBlock:
        """Optimize loop block structure.

        Args:
            block: Loop block to optimize

        Returns:
            Optimized block
        """
        # Check for infinite loops that can be simplified
        if "condition" in block.metadata:
            condition = block.metadata["condition"].strip().upper()
            if condition == "TRUE":
                # Infinite loop
                block.metadata["condition"] = "TRUE  // Infinite loop"

        return block

    def _optimize_choose_case_block(self, block: ControlBlock) -> ControlBlock:
        """Optimize CHOOSE CASE block structure.

        Args:
            block: CHOOSE CASE block to optimize

        Returns:
            Optimized block
        """
        # Remove empty cases
        if hasattr(block, "cases") and block.cases:
            non_empty_cases = []
            for case in block.cases:
                if isinstance(case, dict) and "body" in case:
                    if not self._is_empty_block(case["body"]):
                        non_empty_cases.append(case)
                else:
                    non_empty_cases.append(case)
            block.cases = non_empty_cases

        # Remove empty default case
        if hasattr(block, "default_case") and self._is_empty_block(block.default_case):
            block.default_case = None

        return block

    def _aggressive_optimization(self, statements: list[str]) -> list[str]:
        """Apply aggressive optimizations to statements.

        Args:
            statements: List of statements

        Returns:
            Aggressively optimized statements
        """
        optimized = []

        for stmt in statements:
            # Remove debug/trace statements
            if self._is_debug_statement(stmt):
                if self.options.preserve_debug_info:
                    optimized.append(f"// DEBUG: {stmt}")
                continue

            # Inline simple expressions
            if self.options.inline_simple_functions:
                stmt = self._inline_simple_functions(stmt)

            optimized.append(stmt)

        return optimized

    def _is_debug_statement(self, stmt: str) -> bool:
        """Check if a statement is a debug/trace statement.

        Args:
            stmt: Statement to check

        Returns:
            True if statement is a debug statement
        """
        if not isinstance(stmt, str):
            return False

        debug_patterns = [
            r'^\s*MessageBox\s*\(\s*"Debug"',
            r"^\s*Trace\s*\(",
            r"^\s*DebugBreak\s*\(",
            r"^\s*//\s*DEBUG:",
            r"^\s*//\s*TODO:",
            r"^\s*//\s*FIXME:",
        ]

        return any(re.match(pattern, stmt, re.IGNORECASE) for pattern in debug_patterns)

    def _inline_simple_functions(self, stmt: str) -> str:
        """Inline simple function calls.

        Args:
            stmt: Statement containing function calls

        Returns:
            Statement with inlined functions
        """
        # Inline simple math functions
        inline_patterns = [
            (r"\bAbs\s*\(\s*-(\d+)\s*\)", r"\1"),  # Abs(-5) -> 5
            (r"\bMax\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", self._inline_max),
            (r"\bMin\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", self._inline_min),
        ]

        for pattern, replacement in inline_patterns:
            if callable(replacement):
                stmt = re.sub(pattern, replacement, stmt, flags=re.IGNORECASE)
            else:
                stmt = re.sub(pattern, replacement, stmt, flags=re.IGNORECASE)

        return stmt

    @staticmethod
    def _inline_max(match: re.Match) -> str:
        """Inline Max function for constants."""
        a = int(match.group(1))
        b = int(match.group(2))
        return str(max(a, b))

    @staticmethod
    def _inline_min(match: re.Match) -> str:
        """Inline Min function for constants."""
        a = int(match.group(1))
        b = int(match.group(2))
        return str(min(a, b))
