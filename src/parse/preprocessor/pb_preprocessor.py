"""PowerBuilder preprocessor for handling includes and conditional compilation.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Core/PWBPreprocessor.class.st
"""


import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PreprocessorState:
    """State for tracking preprocessor context."""

    characters_ignored: int = 0
    in_binary_section: bool = False
    in_multiline_comment: bool = False


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

    def __init__(self, base_path: Path) -> None:




        """Initialize preprocessor.

        Args:
            base_path: Base path for resolving include files
        """
        self.base_path = base_path
        self.defines: set[str] = set()
        self.include_stack: list[Path] = []
        self.macros: dict[str, str] = {}
        self.state = PreprocessorState()

    def add_define(self, symbol: str) -> None:




        """Add a preprocessor symbol definition.

        Args:
            symbol: Symbol to define
        """
        self.defines.add(symbol)

    def add_macro(self, name: str, value: str) -> None:




        """Add a macro definition.

        Args:
            name: Macro name
            value: Macro expansion value
        """
        self.macros[name] = value

    def preprocess(self, source: str, file_path: Path | None = None) -> str:




        """Preprocess PowerBuilder source code.

        Args:
            source: Source code to preprocess
            file_path: Optional path of source file for resolving includes

        Returns:
            Preprocessed source code
        """
        if file_path:
            self.include_stack.append(file_path)

        try:
            # Reset state
            self.state = PreprocessorState()

            # Process header and get content
            source = self._process_header(source)

            # Process includes first
            source = self._process_includes(source)

            # Process conditional compilation
            source = self._process_conditionals(source)

            # Expand macros
            source = self._expand_macros(source)

            # Process comments, strings, and special sections
            return self._process_content(source)

        finally:
            if file_path:
                self.include_stack.pop()

    def _process_header(self, source: str) -> str:




        """Process PowerBuilder file header.

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

            # Process strings
            string_match = self.STRING.match(source, i)
            if string_match:
                result.append(string_match.group())
                i = string_match.end()
                continue

            # Process comments
            if not self.state.in_multiline_comment:
                # Single line comments
                comment_match = self.SINGLE_LINE_COMMENT.match(source, i)
                if comment_match:
                    result.append(self._replace_non_white_chars(comment_match.group()))
                    i = comment_match.end()
                    continue

                # Multi-line comments
                if source[i : i + 2] == "/*":
                    self.state.in_multiline_comment = True
                    comment_start = i
                    i += 2
                    continue

            elif source[i : i + 2] == "*/":
                self.state.in_multiline_comment = False
                comment = source[comment_start : i + 2]
                result.append(self._replace_non_white_chars(comment))
                i += 2
                continue

            # Process Espelette newlines
            newline_match = self.ESPELETTE_NEWLINE.match(source, i)
            if newline_match:
                result.append(self._replace_non_space_chars(newline_match.group()))
                i = newline_match.end()
                continue

            # Regular code
            if not self.state.in_multiline_comment:
                result.append(source[i])
            i += 1

        return "".join(result)

    def _replace_non_white_chars(self, text: str) -> str:




        """Replace non-whitespace characters with spaces.

        Args:
            text: Text to process

        Returns:
            Text with non-whitespace chars replaced
        """
        return "".join(" " if not c.isspace() else c for c in text)

    def _replace_non_space_chars(self, text: str) -> str:




        """Replace non-space characters with spaces.

        Args:
            text: Text to process

        Returns:
            Text with non-space chars replaced
        """
        return "".join(" " if not c.isspace() or c == "\n" else c for c in text)

    def _process_includes(self, source: str) -> str:




        """Process include directives.

        Args:
            source: Source code

        Returns:
            Source with includes expanded
        """

        def replace_include(match: re.Match) -> str:


            include_file = match.group(1).strip('"')
            include_path = self._resolve_include_path(include_file)

            # Check for circular includes
            if include_path in self.include_stack:
                msg = f"Circular include detected: {include_path}"
                raise ValueError(msg)

            try:
                with open(include_path, encoding="utf-8") as f:
                    included_source = f.read()
                return self.preprocess(included_source, include_path)
            except FileNotFoundError:
                msg = f"Include file not found: {include_path}"
                raise ValueError(msg)

        return re.sub(
            r'^\s*\$include\s+"([^"]+)"',
            replace_include,
            source,
            flags=re.MULTILINE,
        )

    def _process_conditionals(self, source: str) -> str:




        """Process conditional compilation directives.

        Args:
            source: Source code

        Returns:
            Source with conditionals processed
        """
        lines = source.splitlines(keepends=True)
        result = []
        skip_stack = []  # Stack of booleans indicating whether to skip lines
        current_skip = False  # Current skip state

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("$ifdef "):
                symbol = stripped[7:].strip()
                skip = symbol not in self.defines
                skip_stack.append(skip)
                current_skip = any(skip_stack)
                # Don't add directive line to result
            elif stripped.startswith("$ifndef "):
                symbol = stripped[8:].strip()
                skip = symbol in self.defines
                skip_stack.append(skip)
                current_skip = any(skip_stack)
                # Don't add directive line to result
            elif stripped == "$else":
                if not skip_stack:
                    msg = "$else without matching $ifdef/$ifndef"
                    raise ValueError(msg)
                skip_stack[-1] = not skip_stack[-1]
                current_skip = any(skip_stack)
                # Don't add directive line to result
            elif stripped == "$endif":
                if not skip_stack:
                    msg = "$endif without matching $ifdef/$ifndef"
                    raise ValueError(msg)
                skip_stack.pop()
                current_skip = any(skip_stack) if skip_stack else False
                # Don't add directive line to result
            elif not current_skip:
                # Only add non-directive lines that aren't being skipped
                result.append(line)

        if skip_stack:
            msg = "Unclosed $ifdef/$ifndef"
            raise ValueError(msg)

        return "".join(result)

    def _expand_macros(self, source: str) -> str:




        """Expand macro definitions.

        Args:
            source: Source code

        Returns:
            Source with macros expanded
        """
        result = source
        for name, value in self.macros.items():
            result = re.sub(rf"\b{re.escape(name)}\b", value, result)
        return result

    def _resolve_include_path(self, include_file: str) -> Path:




        """Resolve path for include file.

        Args:
            include_file: Include file name/path

        Returns:
            Resolved absolute path
        """
        # First check relative to current file
        if self.include_stack:
            current_dir = self.include_stack[-1].parent
            include_path = current_dir / include_file
            if include_path.exists():
                return include_path

        # Then check relative to base path
        include_path = self.base_path / include_file
        if include_path.exists():
            return include_path

        msg = f"Include file not found: {include_file}"
        raise FileNotFoundError(msg)
