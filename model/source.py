"""Source code representation for PowerBuilder.

This module contains classes for handling PowerBuilder source files and code.
"""

from __future__ import annotations

from dataclasses import dataclass

from .utils.base import PBNode


# ─── Source Core ──────────────────────────────────────────────────────
@dataclass
class SourceFile(PBNode):
    """PowerBuilder source file."""

    path: str
    type: str  # window, datawindow, function, etc.
    content: str
    encoding: str = "utf-8"


@dataclass
class SourcePosition(PBNode):
    """Source code position."""

    line: int
    column: int
    offset: int


@dataclass
class SourceRange(PBNode):
    """Source code range."""

    start: SourcePosition
    end: SourcePosition
    file: SourceFile | None = None


# ─── Source Elements ────────────────────────────────────────────────────
@dataclass
class SourceComment(PBNode):
    """Source code comment."""

    text: str
    range: SourceRange
    is_multiline: bool = False


@dataclass
class SourceDirective(PBNode):
    """Source code directive."""

    type: str  # include, ifdef, etc.
    value: str
    range: SourceRange


@dataclass
class SourceSection(PBNode):
    """Source code section."""

    type: str  # forward, variables, etc.
    content: list[PBNode]
    range: SourceRange


# ─── File Organization ──────────────────────────────────────────────────
@dataclass
class FileHeader(PBNode):
    """PowerBuilder file header."""

    version: str
    export_info: dict[str, str]
    range: SourceRange


@dataclass
class FileFooter(PBNode):
    """PowerBuilder file footer."""

    checksum: str | None = None
    range: SourceRange | None = None


# ─── Source Location Tracking ────────────────────────────────────────────
class SourceLocationTracker:
    """Tracks source code locations for AST nodes."""

    def __init__(self, source_file: SourceFile) -> None:
        """Initialize the location tracker.
        
        Args:
            source_file: The source file being tracked
        """
        self.source_file = source_file
        self.line_starts = self._calculate_line_starts(source_file.content)
        self.node_locations: dict[int, SourceRange] = {}  # node_id -> location

    def _calculate_line_starts(self, content: str) -> list[int]:
        """Calculate the start offset of each line.
        
        Args:
            content: Source code content
            
        Returns:
            List of line start offsets
        """
        line_starts = [0]
        for i, char in enumerate(content):
            if char == '\n':
                line_starts.append(i + 1)
        return line_starts

    def get_position(self, offset: int) -> SourcePosition:
        """Get line and column position from offset.
        
        Args:
            offset: Character offset in the source
            
        Returns:
            SourcePosition with line and column
        """
        line = 0
        for i, start in enumerate(self.line_starts):
            if start > offset:
                line = i - 1
                break
        else:
            line = len(self.line_starts) - 1
            
        column = offset - self.line_starts[line]
        return SourcePosition(line=line + 1, column=column + 1, offset=offset)

    def get_range(self, start_offset: int, end_offset: int) -> SourceRange:
        """Get source range from offsets.
        
        Args:
            start_offset: Start character offset
            end_offset: End character offset
            
        Returns:
            SourceRange with start and end positions
        """
        start_pos = self.get_position(start_offset)
        end_pos = self.get_position(end_offset)
        return SourceRange(start=start_pos, end=end_pos, file=self.source_file)

    def track_node(self, node: PBNode, start_offset: int, end_offset: int) -> None:
        """Track location for an AST node.
        
        Args:
            node: AST node to track
            start_offset: Start offset in source
            end_offset: End offset in source
        """
        node_id = id(node)
        self.node_locations[node_id] = self.get_range(start_offset, end_offset)
        
        # Also attach the range directly to the node if possible
        if hasattr(node, '__dict__'):
            node.source_range = self.node_locations[node_id]

    def get_node_location(self, node: PBNode) -> SourceRange | None:
        """Get tracked location for a node.
        
        Args:
            node: AST node
            
        Returns:
            SourceRange if tracked, None otherwise
        """
        # First check if node has source_range attribute
        if hasattr(node, 'source_range'):
            return node.source_range
            
        # Otherwise check tracked locations
        node_id = id(node)
        return self.node_locations.get(node_id)

    def get_source_text(self, range: SourceRange) -> str:
        """Get source text for a range.
        
        Args:
            range: Source range
            
        Returns:
            Source text within the range
        """
        if range.file != self.source_file:
            raise ValueError("Range is from a different source file")
            
        return self.source_file.content[range.start.offset:range.end.offset]


# ─── Source Code Manager ─────────────────────────────────────────────────
class SourceCodeManager:
    """Manages source code files and operations."""

    def __init__(self) -> None:
        """Initialize the source code manager."""
        self.source_files: dict[str, SourceFile] = {}
        self.location_trackers: dict[str, SourceLocationTracker] = {}

    def add_source_file(self, path: str, content: str, file_type: str, encoding: str = "utf-8") -> SourceFile:
        """Add a source file to the manager.
        
        Args:
            path: File path
            content: File content
            file_type: Type of PowerBuilder file
            encoding: File encoding
            
        Returns:
            Created SourceFile object
        """
        source_file = SourceFile(
            path=path,
            type=file_type,
            content=content,
            encoding=encoding
        )
        
        self.source_files[path] = source_file
        self.location_trackers[path] = SourceLocationTracker(source_file)
        
        return source_file

    def get_source_file(self, path: str) -> SourceFile | None:
        """Get a source file by path.
        
        Args:
            path: File path
            
        Returns:
            SourceFile if found, None otherwise
        """
        return self.source_files.get(path)

    def get_location_tracker(self, path: str) -> SourceLocationTracker | None:
        """Get location tracker for a file.
        
        Args:
            path: File path
            
        Returns:
            SourceLocationTracker if found, None otherwise
        """
        return self.location_trackers.get(path)

    def extract_comments(self, source_file: SourceFile) -> list[SourceComment]:
        """Extract comments from a source file.
        
        Args:
            source_file: Source file to process
            
        Returns:
            List of SourceComment objects
        """
        comments = []
        content = source_file.content
        tracker = self.location_trackers.get(source_file.path)
        
        if not tracker:
            tracker = SourceLocationTracker(source_file)
            
        # Single-line comments
        import re
        for match in re.finditer(r'//.*$', content, re.MULTILINE):
            start, end = match.span()
            range = tracker.get_range(start, end)
            comments.append(SourceComment(
                text=match.group(0)[2:].strip(),
                range=range,
                is_multiline=False
            ))
            
        # Multi-line comments
        for match in re.finditer(r'/\*.*?\*/', content, re.DOTALL):
            start, end = match.span()
            range = tracker.get_range(start, end)
            text = match.group(0)[2:-2].strip()
            comments.append(SourceComment(
                text=text,
                range=range,
                is_multiline=True
            ))
            
        return sorted(comments, key=lambda c: c.range.start.offset)

    def find_text_in_source(self, source_file: SourceFile, text: str) -> list[SourceRange]:
        """Find all occurrences of text in source file.
        
        Args:
            source_file: Source file to search
            text: Text to find
            
        Returns:
            List of SourceRange objects for matches
        """
        ranges = []
        tracker = self.location_trackers.get(source_file.path)
        
        if not tracker:
            tracker = SourceLocationTracker(source_file)
            
        content = source_file.content
        start = 0
        
        while True:
            pos = content.find(text, start)
            if pos == -1:
                break
                
            range = tracker.get_range(pos, pos + len(text))
            ranges.append(range)
            start = pos + 1
            
        return ranges


# ─── Convenience Functions ────────────────────────────────────────────
def create_source_manager() -> SourceCodeManager:
    """Create and initialize a source code manager.
    
    Returns:
        Configured SourceCodeManager instance
    """
    return SourceCodeManager()


def track_ast_locations(ast_nodes: list[PBNode], source_file: SourceFile, location_map: dict[PBNode, tuple[int, int]]) -> SourceLocationTracker:
    """Track source locations for AST nodes.
    
    Args:
        ast_nodes: List of AST nodes
        source_file: Source file
        location_map: Map of node to (start_offset, end_offset)
        
    Returns:
        Configured SourceLocationTracker
    """
    tracker = SourceLocationTracker(source_file)
    
    for node, (start, end) in location_map.items():
        tracker.track_node(node, start, end)
        
    return tracker
