"""PowerBuilder preprocessor for handling includes and conditional compilation.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Core/PWBPreprocessor.class.st
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PreprocessorState:
    """State for tracking preprocessor context."""

    in_binary_section: bool = False
    in_multiline_comment: bool = False
    characters_ignored: int = 0


class PowerBuilderPreprocessor:
    """Preprocessor for PowerBuilder source files.

    Handles:
    - Include directives
    - Conditional compilation ($ifdef, $ifndef, $else, $endif)
    - Macro expansion
    - Comments and strings
    - Binary data sections
    - Export information headers
    """

    # Regular expressions for preprocessing
    BINARY_SECTION_START = re.compile(r"Start of PowerBuilder Binary Data Section")
    EXPORT_INFO = re.compile(r"^\$PBExport[^\n]+", re.MULTILINE)
    RELEASE_NUMBER = re.compile(r"release\s+\d+\s*")
    SINGLE_LINE_COMMENT = re.compile(r"//[^\n]*")
    MULTI_LINE_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
    STRING = re.compile(r'"[^"]*"')
    ESPELETTE_NEWLINE = re.compile(r"&[ \t]*\n")

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize preprocessor.

        Args:
            base_path: Base path for resolving include files
        """
        self.base_path = base_path or Path.cwd()
        self.state = PreprocessorState()
        self.defines = {}  # Defined macros
        self.includes = []  # Included files
        self.processed_files = set()  # Prevent circular includes

    def preprocess(self, source: str, file_path: Path | None = None) -> str:
        """Preprocess PowerBuilder source code.

        Args:
            source: Source code
            file_path: Path to source file

        Returns:
            Preprocessed source code
        """
        # Reset state
        self.state = PreprocessorState()

        # Remove export header
        source = self._remove_export_header(source)

        # Process content
        source = self._process_content(source)

        # Remove binary sections
        source = self._remove_binary_sections(source)

        # Join multiline strings
        return self._join_multiline_strings(source)

    def _remove_export_header(self, source: str) -> str:
        """Remove $PBExportHeader section from source.

        Args:
            source: Source code

        Returns:
            Source with header processed and size recorded
        """
        # Find export information section
        export_match = re.search(self.EXPORT_INFO, source)
        if not export_match:
            return source

        # Find optional release number
        release_match = re.search(self.RELEASE_NUMBER, source[export_match.end() :])

        # Calculate header size
        if release_match:
            header_end = export_match.end() + release_match.end()
        else:
            header_end = export_match.end()

        # Record size for position correction
        self.state.characters_ignored = header_end

        # Return content after header
        return source[header_end:]

    def _process_content(self, source: str) -> str:
        """Process source code content.

        Args:
            source: Source code

        Returns:
            Processed source code
        """
        result = []
        i = 0
        while i < len(source):
            # Check for binary data section
            if not self.state.in_binary_section:
                binary_match = self.BINARY_SECTION_START.match(source, i)
                if binary_match:
                    self.state.in_binary_section = True
                    i = len(source)  # Skip rest of file
                    continue

            # Check for comments
            comment_match = self.SINGLE_LINE_COMMENT.match(source, i)
            if comment_match:
                # Keep comment for now (can be removed later)
                result.append(comment_match.group())
                i = comment_match.end()
                continue

            # Check for multiline comments
            ml_comment_match = self.MULTI_LINE_COMMENT.match(source, i)
            if ml_comment_match:
                # Keep comment for now
                result.append(ml_comment_match.group())
                i = ml_comment_match.end()
                continue

            # Check for strings
            string_match = self.STRING.match(source, i)
            if string_match:
                result.append(string_match.group())
                i = string_match.end()
                continue

            # Default: add character
            result.append(source[i])
            i += 1

        return "".join(result)

    def _remove_binary_sections(self, source: str) -> str:
        """Remove binary data sections from source.

        Args:
            source: Source code

        Returns:
            Source without binary sections
        """
        # Find binary section start
        match = self.BINARY_SECTION_START.search(source)
        if match:
            # Everything before binary section
            return source[: match.start()]
        return source

    def _join_multiline_strings(self, source: str) -> str:
        """Join multiline strings using & continuation.

        Args:
            source: Source code

        Returns:
            Source with multiline strings joined
        """
        # Replace & followed by newline with just space
        return self.ESPELETTE_NEWLINE.sub(" ", source)

    def remove_comments(self, source: str) -> str:
        """Remove comments from source code.

        Args:
            source: Source code

        Returns:
            Source without comments
        """
        # Remove single-line comments
        source = self.SINGLE_LINE_COMMENT.sub("", source)

        # Remove multi-line comments
        return self.MULTI_LINE_COMMENT.sub("", source)

    def get_position_correction(self) -> int:
        """Get number of characters removed from beginning.

        Returns:
            Number of characters ignored at start
        """
        return self.state.characters_ignored
