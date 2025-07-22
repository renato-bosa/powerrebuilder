"""DataWindow extraction integration with the decompile pipeline.

This module integrates DataWindow extraction with the overall decompile
pipeline, handling relationships between DataWindows and other objects.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from src.decompile.datawindow_utils import DataWindowDetector
from src.decompile.extractors.datawindow import (
    DataWindowDefinition,
    DataWindowExtractor,
    ExtractedData,
)
from src.decompile.extractors.datawindow_extractor import (
    EnhancedDataWindowDefinition,
    EnhancedDataWindowExtractor,
)
from src.model.ast.node_kind import NodeKind
from src.model.ast.nodes.base import ASTNode

logger = logging.getLogger(__name__)


@dataclass
class DataWindowReference:
    """Represents a reference to a DataWindow in code."""

    object_name: str
    datawindow_name: str
    reference_type: str  # "control", "datastore", "composite", "nested"
    location: str  # file/object where referenced
    line_number: int = 0
    context: str = ""  # surrounding code context


@dataclass
class DataWindowRelationship:
    """Represents relationships between DataWindows and other objects."""

    parent_object: str
    parent_type: str  # "window", "userobject", "datawindow"
    child_datawindow: str
    relationship_type: str  # "contains", "inherits", "references", "nested"
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataWindowContext:
    """Complete context for a DataWindow including all relationships."""

    definition: DataWindowDefinition | EnhancedDataWindowDefinition
    references: list[DataWindowReference] = field(default_factory=list)
    relationships: list[DataWindowRelationship] = field(default_factory=list)
    inheritance_chain: list[str] = field(default_factory=list)
    nested_datawindows: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class DataWindowIntegrationManager:
    """Manages DataWindow extraction and integration with the decompile pipeline."""

    # Patterns for detecting DataWindow references in code
    REFERENCE_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "control": re.compile(r'(\w+)\.dataobject\s*=\s*["\']([^"\']+)["\']'),
        "datastore": re.compile(
            r'create\s+datastore.*?dataobject\s*=\s*["\']([^"\']+)["\']', re.DOTALL
        ),
        "setsqlselect": re.compile(r'(\w+)\.SetSQLSelect\s*\(["\']([^"\']+)["\']'),
        "modify": re.compile(r'(\w+)\.Modify\s*\(["\']datawindow\.([^"\']+)["\']'),
        "describe": re.compile(r'(\w+)\.Describe\s*\(["\']datawindow\.([^"\']+)["\']'),
        "composite": re.compile(r'report\s*=\s*["\']([^"\']+)["\']'),
        "nested": re.compile(r'nest_\w+\.dataobject\s*=\s*["\']([^"\']+)["\']'),
    }

    def __init__(self):
        """Initialize the integration manager."""
        self.detector = DataWindowDetector()
        self.base_extractor = DataWindowExtractor()
        self.enhanced_extractor = EnhancedDataWindowExtractor()
        self._datawindow_cache: dict[str, DataWindowContext] = {}

    def extract_from_pbd_object(
        self, dw_data: bytes, object_name: str
    ) -> tuple[str, bool]:
        """Extract DataWindow syntax from PBD object data.

        Args:
            dw_data: Raw DataWindow data from PBD
            object_name: Name of the DataWindow object

        Returns:
            Tuple of (syntax, success)
        """
        if not dw_data:
            return "", False

        # Detect format
        format_type = self.detector.detect_format(dw_data)

        if format_type == "text":
            # Handle text-based DataWindow
            try:
                # Detect encoding
                metadata = self.detector.extract_metadata(dw_data)
                encoding = metadata.get("encoding", "utf-8")

                # Decode to text
                syntax = dw_data.decode(encoding, errors="ignore")

                # Clean up any binary artifacts
                syntax = self._clean_extracted_syntax(syntax)

                return syntax, True

            except Exception as e:
                logger.error("Failed to decode text DataWindow %s: %s", object_name, e)
                return "", False

        elif format_type == "binary":
            # Handle binary DataWindow
            logger.debug("Binary DataWindow detected for %s", object_name)

            # Try to extract embedded text syntax
            syntax = self._extract_from_binary(dw_data, object_name)
            if syntax:
                return syntax, True

            return "", False

        else:
            logger.warning("Unknown DataWindow format for %s", object_name)
            return "", False

    def extract_datawindow(
        self, source: str, filename: str = "", use_enhanced: bool = True
    ) -> ExtractedData:
        """Extract DataWindow with optional enhanced features.

        Args:
            source: DataWindow source code
            filename: Optional filename
            use_enhanced: Whether to use enhanced extraction

        Returns:
            ExtractedData with parsed DataWindow
        """
        if use_enhanced:
            return self.enhanced_extractor.extract(source, filename)
        return self.base_extractor.extract(source, filename)

    def analyze_object_for_datawindows(
        self, ast_node: ASTNode, object_name: str
    ) -> list[DataWindowReference]:
        """Analyze an AST node for DataWindow references.

        Args:
            ast_node: AST node to analyze
            object_name: Name of the containing object

        Returns:
            List of DataWindow references found
        """
        references = []

        # Walk the AST looking for DataWindow references
        self._find_datawindow_references(ast_node, object_name, references)

        return references

    def build_datawindow_context(
        self, dw_name: str, project_data: dict[str, Any]
    ) -> DataWindowContext:
        """Build complete context for a DataWindow.

        Args:
            dw_name: DataWindow name
            project_data: Project-wide data including all objects

        Returns:
            Complete DataWindow context
        """
        # Check cache first
        if dw_name in self._datawindow_cache:
            return self._datawindow_cache[dw_name]

        # Extract DataWindow definition
        dw_source = project_data.get("datawindows", {}).get(dw_name, "")
        if not dw_source:
            logger.warning("DataWindow %s not found in project data", dw_name)
            return DataWindowContext(
                definition=DataWindowDefinition(),
                metadata={"error": f"DataWindow {dw_name} not found"},
            )

        # Extract definition
        result = self.extract_datawindow(dw_source, dw_name)
        if not result.success:
            return DataWindowContext(
                definition=DataWindowDefinition(), metadata={"error": result.error}
            )

        context = DataWindowContext(definition=result.data)

        # Find all references to this DataWindow
        context.references = self._find_all_references(dw_name, project_data)

        # Build relationships
        context.relationships = self._build_relationships(dw_name, project_data)

        # Extract inheritance chain
        context.inheritance_chain = self._extract_inheritance_chain(
            dw_name, project_data
        )

        # Find nested DataWindows
        if hasattr(result.data, "composite_reports"):
            context.nested_datawindows = result.data.composite_reports

        # Add metadata
        context.metadata = result.metadata

        # Cache the context
        self._datawindow_cache[dw_name] = context

        return context

    def integrate_with_decompile_pipeline(
        self, decompiled_objects: dict[str, Any]
    ) -> dict[str, Any]:
        """Integrate DataWindow extraction with decompiled objects.

        Args:
            decompiled_objects: Dictionary of decompiled objects

        Returns:
            Enhanced dictionary with DataWindow contexts
        """
        enhanced_objects = decompiled_objects.copy()

        # Extract all DataWindows
        datawindows = {}
        for obj_name, obj_data in decompiled_objects.items():
            if self._is_datawindow_object(obj_name, obj_data):
                # Extract DataWindow
                source = obj_data.get("source", "")
                result = self.extract_datawindow(source, obj_name)

                if result.success:
                    datawindows[obj_name] = result.data

        # Build contexts for all DataWindows
        dw_contexts = {}
        project_data = {
            "datawindows": {name: dw for name, dw in datawindows.items()},
            "objects": decompiled_objects,
        }

        for dw_name in datawindows:
            dw_contexts[dw_name] = self.build_datawindow_context(dw_name, project_data)

        # Add DataWindow contexts to enhanced objects
        enhanced_objects["datawindow_contexts"] = dw_contexts

        # Enhance object metadata with DataWindow relationships
        for obj_name, obj_data in enhanced_objects.items():
            if obj_name != "datawindow_contexts":
                obj_data["datawindow_references"] = self._get_object_dw_references(
                    obj_name, dw_contexts
                )

        return enhanced_objects

    def _clean_extracted_syntax(self, syntax: str) -> str:
        """Clean up extracted DataWindow syntax."""
        # Remove null bytes
        syntax = syntax.replace("\x00", "")

        # Remove binary markers
        binary_markers = [
            "Start of PowerBuilder Binary Data Section",
            "End of PowerBuilder Binary Data Section",
        ]
        for marker in binary_markers:
            syntax = syntax.replace(marker, "")

        # Clean up extra whitespace
        syntax = re.sub(r"\n\s*\n\s*\n", "\n\n", syntax)

        return syntax.strip()

    def _extract_from_binary(self, data: bytes, object_name: str) -> str | None:
        """Extract text syntax from binary DataWindow."""
        # Look for text sections in binary data
        text_start_markers = [b"release ", b"HA$PBExportHeader$", b"datawindow("]

        for marker in text_start_markers:
            if marker in data:
                start_idx = data.find(marker)
                # Find end of text section
                end_markers = [b"\x00\x00", b"DAT*", b"Start of PowerBuilder Binary"]
                end_idx = len(data)

                for end_marker in end_markers:
                    idx = data.find(end_marker, start_idx)
                    if idx > 0 and idx < end_idx:
                        end_idx = idx

                # Extract text section
                text_data = data[start_idx:end_idx]

                # Try to decode
                for encoding in ["utf-8", "utf-16-le", "latin-1"]:
                    try:
                        syntax = text_data.decode(encoding, errors="ignore")
                        return self._clean_extracted_syntax(syntax)
                    except:
                        continue

        return None

    def _find_datawindow_references(
        self, node: ASTNode, object_name: str, references: list[DataWindowReference]
    ):
        """Recursively find DataWindow references in AST."""
        # Check current node
        if node.kind == NodeKind.ASSIGNMENT:
            # Check for dataobject assignments
            if hasattr(node, "target") and hasattr(node, "value"):
                target = str(node.target)
                value = str(node.value)

                if "dataobject" in target.lower() and value.strip("\"'"):
                    ref = DataWindowReference(
                        object_name=object_name,
                        datawindow_name=value.strip("\"'"),
                        reference_type="control",
                        location=object_name,
                        line_number=node.line if hasattr(node, "line") else 0,
                        context=f"{target} = {value}",
                    )
                    references.append(ref)

        # Check for function calls
        elif node.kind == NodeKind.FUNCTION_CALL:
            if hasattr(node, "name") and hasattr(node, "arguments"):
                func_name = str(node.name).lower()

                # Check for DataWindow-related functions
                if func_name in ["setsqlselect", "modify", "describe"]:
                    if node.arguments:
                        arg_value = str(node.arguments[0]).strip("\"'")
                        ref = DataWindowReference(
                            object_name=object_name,
                            datawindow_name=arg_value,
                            reference_type=func_name,
                            location=object_name,
                            line_number=node.line if hasattr(node, "line") else 0,
                            context=str(node),
                        )
                        references.append(ref)

        # Recurse into children
        if hasattr(node, "children"):
            for child in node.children:
                self._find_datawindow_references(child, object_name, references)

    def _find_all_references(
        self, dw_name: str, project_data: dict[str, Any]
    ) -> list[DataWindowReference]:
        """Find all references to a DataWindow in the project."""
        references = []

        # Search all objects
        for obj_name, obj_data in project_data.get("objects", {}).items():
            if "source" in obj_data:
                source = obj_data["source"]

                # Search for patterns
                for ref_type, pattern in self.REFERENCE_PATTERNS.items():
                    for match in pattern.finditer(source):
                        found_dw = (
                            match.group(2) if ref_type == "control" else match.group(1)
                        )

                        if found_dw == dw_name:
                            ref = DataWindowReference(
                                object_name=obj_name,
                                datawindow_name=dw_name,
                                reference_type=ref_type,
                                location=obj_name,
                                context=match.group(0),
                            )
                            references.append(ref)

        return references

    def _build_relationships(
        self, dw_name: str, project_data: dict[str, Any]
    ) -> list[DataWindowRelationship]:
        """Build relationships for a DataWindow."""
        relationships = []

        # Find containing objects
        for obj_name, obj_data in project_data.get("objects", {}).items():
            if "datawindows" in obj_data:
                if dw_name in obj_data["datawindows"]:
                    rel = DataWindowRelationship(
                        parent_object=obj_name,
                        parent_type=obj_data.get("type", "unknown"),
                        child_datawindow=dw_name,
                        relationship_type="contains",
                    )
                    relationships.append(rel)

        # Check for inheritance
        dw_data = project_data.get("datawindows", {}).get(dw_name, {})
        if isinstance(dw_data, dict) and "inherits_from" in dw_data:
            parent_dw = dw_data["inherits_from"]
            rel = DataWindowRelationship(
                parent_object=parent_dw,
                parent_type="datawindow",
                child_datawindow=dw_name,
                relationship_type="inherits",
            )
            relationships.append(rel)

        return relationships

    def _extract_inheritance_chain(
        self, dw_name: str, project_data: dict[str, Any]
    ) -> list[str]:
        """Extract the inheritance chain for a DataWindow."""
        chain = []
        current = dw_name

        while current:
            dw_data = project_data.get("datawindows", {}).get(current, {})
            if isinstance(dw_data, dict) and "inherits_from" in dw_data:
                parent = dw_data["inherits_from"]
                chain.append(parent)
                current = parent
            else:
                break

        return chain

    def _is_datawindow_object(self, obj_name: str, obj_data: dict[str, Any]) -> bool:
        """Check if an object is a DataWindow."""
        # Check by name pattern
        if self.detector.is_datawindow_file(obj_name):
            return True

        # Check by content
        if "source" in obj_data:
            source = obj_data["source"]
            if isinstance(source, str):
                return "datawindow(" in source.lower() and "release" in source.lower()

        return False

    def _get_object_dw_references(
        self, obj_name: str, dw_contexts: dict[str, DataWindowContext]
    ) -> list[str]:
        """Get list of DataWindows referenced by an object."""
        referenced_dws = []

        for dw_name, context in dw_contexts.items():
            for ref in context.references:
                if ref.object_name == obj_name:
                    if dw_name not in referenced_dws:
                        referenced_dws.append(dw_name)

        return referenced_dws


# Create singleton instance
integration_manager = DataWindowIntegrationManager()


# Backward compatibility
class DataWindowExtractionManager:
    """Legacy manager for backward compatibility."""

    def __init__(self):
        self.manager = integration_manager

    def extract_from_pbd_object(
        self, dw_data: bytes, object_name: str
    ) -> tuple[str, bool]:
        """Extract DataWindow syntax from PBD object data."""
        return self.manager.extract_from_pbd_object(dw_data, object_name)


# Legacy instance
extraction_manager = DataWindowExtractionManager()
