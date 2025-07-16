"""Post-processing filter for decompiled output."""

import logging

logger = logging.getLogger(__name__)


class DecompiledOutputFilter:
    """Filter for cleaning up decompiled output."""

    def __init__(self):
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
        """Remove redundant labels from the output."""
        # TODO: Implement label cleanup
        return content

    def _clean_empty_blocks(self, content: str) -> str:
        """Remove empty code blocks."""
        lines = content.split('\n')
        cleaned = []

        for line in lines:
            # Skip lines that are just comments about empty blocks
            if '// Empty block' in line:
                continue
            cleaned.append(line)

        return '\n'.join(cleaned)

    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in the output."""
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split('\n')]

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

        return '\n'.join(cleaned)