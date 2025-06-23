"""Post-processing filters for decompiled output."""


import logging

logger = logging.getLogger(__name__)


class DecompiledOutputFilter:
    """Filter repetitive patterns from decompiled output."""

    def __init__(
        self, max_consecutive_returns: int = 10, max_consecutive_blank_lines: int = 3, max_repeated_pattern: int = 5, ) -> None:
        """Initialize the filter.

        Args:
            max_consecutive_returns: Maximum consecutive return statements to keep
            max_consecutive_blank_lines: Maximum consecutive blank lines to keep
            max_repeated_pattern: Maximum times to repeat any pattern
        """
        self.max_consecutive_returns = max_consecutive_returns
        self.max_consecutive_blank_lines = max_consecutive_blank_lines
        self.max_repeated_pattern = max_repeated_pattern

    def filter_output(self, content: str) -> str:




        """Filter repetitive patterns from decompiled output.

        Args:
            content: Raw decompiled content

        Returns:
            Filtered content with repetitions reduced
        """
        lines = content.split("\n")
        filtered_lines = []

        # Track consecutive patterns
        consecutive_returns = 0
        consecutive_blanks = 0
        return_values_seen = set()
        skipped_returns = 0

        # Pattern detection
        pattern_history: list[str] = []
        pattern_count = 0
        last_pattern = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Handle return statements
            if line_stripped.startswith("return"):
                consecutive_returns += 1
                consecutive_blanks = 0

                # Extract return value if present
                if " " in line_stripped:
                    return_value = line_stripped.split(" ", 1)[1]
                    return_values_seen.add(return_value)

                # Keep first few returns
                if consecutive_returns <= self.max_consecutive_returns:
                    filtered_lines.append(line)
                else:
                    skipped_returns += 1
                    # Add summary comment when we start skipping
                    if consecutive_returns == self.max_consecutive_returns + 1:
                        filtered_lines.append(
                            f"    // ... {len(return_values_seen)} unique return values"
                        )
                        filtered_lines.append("    // ... skipping repetitive returns")
                continue

            # Handle blank lines
            if not line_stripped:
                consecutive_blanks += 1
                if consecutive_blanks <= self.max_consecutive_blank_lines:
                    filtered_lines.append(line)
                continue

            # Reset counters for non-return, non-blank lines
            if consecutive_returns > self.max_consecutive_returns:
                # Add summary of skipped returns
                filtered_lines.append(
                    f"    // ... skipped {skipped_returns} return statements"
                )

            consecutive_returns = 0
            consecutive_blanks = 0
            return_values_seen.clear()
            skipped_returns = 0

            # Check for repeated patterns (like identical if blocks)
            if self._is_pattern_start(line_stripped):
                pattern = self._extract_pattern(lines, i)
                if pattern == last_pattern:
                    pattern_count += 1
                    if pattern_count > self.max_repeated_pattern:
                        # Skip this pattern occurrence
                        if pattern_count == self.max_repeated_pattern + 1:
                            filtered_lines.append(
                                f"    // ... pattern repeats {pattern_count} more times"
                            )
                        continue
                else:
                    pattern_count = 1
                    last_pattern = pattern

            filtered_lines.append(line)

        # Final summary if needed
        if consecutive_returns > self.max_consecutive_returns:
            filtered_lines.append(
                f"    // ... skipped {skipped_returns} return statements"
            )

        return "\n".join(filtered_lines)

    def _is_pattern_start(self, line: str) -> bool:




        """Check if a line starts a recognizable pattern."""
        pattern_starters = [
            "if ", "for ", "while ", "do ", "switch ", "L_", "// ERROR:", "// OPCODE:", ]
        return any(line.startswith(starter) for starter in pattern_starters)

    def _extract_pattern(self, lines: list[str], start_idx: int) -> str:




        """Extract a pattern block starting at the given index."""
        if start_idx >= len(lines):
            return ""

        pattern_lines = []
        indent_level = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        for i in range(start_idx, min(start_idx + 20, len(lines))):
            line = lines[i]
            current_indent = len(line) - len(line.lstrip())

            # Stop at decreased indentation (end of block)
            if line.strip() and current_indent < indent_level:
                break

            pattern_lines.append(line)

            # Stop at obvious block ends
            if line.strip() in ["end if", "end for", "end while", "end do", "}"]:
                break

        return "\n".join(pattern_lines)

    def filter_file(self, input_path: str, output_path: str) -> None:




        """Filter a file and write the result.

        Args:
            input_path: Path to input file
            output_path: Path to output file
        """
        try:
            with open(input_path, encoding="utf-8") as f:
                content = f.read()

            filtered = self.filter_output(content)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(filtered)

            # Log reduction statistics
            original_lines = len(content.split("\n"))
            filtered_lines = len(filtered.split("\n"))
            reduction = (
                (1 - filtered_lines / original_lines) * 100 if original_lines > 0 else 0
            )

            if reduction > 10:  # Only log significant reductions
                logger.info(
                    f"Filtered {input_path}: {original_lines} -> {filtered_lines} lines "
                    f"({reduction:.1f}% reduction)"
                )

        except Exception as e:
            logger.error("Error filtering %s: %s", input_path, e)
            # On error, copy as-is
            import shutil

            shutil.copy2(input_path, output_path)