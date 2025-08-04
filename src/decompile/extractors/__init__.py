"""DataWindow extraction module.

This module provides comprehensive DataWindow extraction capabilities including:
- Base DataWindow parsing and structure extraction
- Enhanced extraction for complex DataWindow types
- Integration with the decompile pipeline
- Relationship and dependency tracking
"""

from .datawindow import (
    DataWindowBand,
    DataWindowColumn,
    DataWindowControl,
    DataWindowDefinition,
    DataWindowExtractor,
    ExtractedData,
)
from .datawindow import (
    extraction_manager as base_extraction_manager,
)
from .datawindow_extractor import (
    DataWindowCrosstab,
    DataWindowGraph,
    DataWindowGroup,
    DataWindowTreeNode,
    EnhancedDataWindowDefinition,
    EnhancedDataWindowExtractor,
    enhanced_extraction_manager,
)
from .datawindow_integration import (
    DataWindowContext,
    DataWindowIntegrationManager,
    DataWindowReference,
    DataWindowRelationship,
    extraction_manager,  # Legacy compatibility
    integration_manager,
)

__all__ = [
    "DataWindowBand",
    "DataWindowColumn",
    "DataWindowContext",
    "DataWindowControl",
    "DataWindowCrosstab",
    "DataWindowDefinition",
    # Base extraction
    "DataWindowExtractor",
    "DataWindowGraph",
    "DataWindowGroup",
    # Integration
    "DataWindowIntegrationManager",
    "DataWindowReference",
    "DataWindowRelationship",
    "DataWindowTreeNode",
    "EnhancedDataWindowDefinition",
    # Enhanced extraction
    "EnhancedDataWindowExtractor",
    "ExtractedData",
    "base_extraction_manager",
    "enhanced_extraction_manager",
    "extraction_manager",  # Legacy compatibility
    "integration_manager",
]
