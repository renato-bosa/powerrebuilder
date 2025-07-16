"""
Pipeline interfaces for clean architecture.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from enum import Enum


class PipelineStage(Enum):
    """Pipeline stages."""
    EXTRACT = "extract"
    PARSE = "parse"
    MODEL = "model"
    DECOMPILE = "decompile"
    GENERATE = "generate"


class IPipelineStage(Protocol):
    """Interface for pipeline stages."""

    @abstractmethod
    def execute(self, input_dir: Path, output_dir: Path, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the pipeline stage."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get stage name."""
        ...

    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get stage dependencies."""
        ...


class IPipelineCoordinator(Protocol):
    """Interface for pipeline coordinator."""

    @abstractmethod
    def run(self, input_dir: Path, output_dir: Path, stages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the pipeline."""
        ...

    @abstractmethod
    def register_stage(self, stage: IPipelineStage) -> None:
        """Register a pipeline stage."""
        ...

    @abstractmethod
    def get_stages(self) -> List[IPipelineStage]:
        """Get all registered stages."""
        ...

    @abstractmethod
    def get_stage(self, name: str) -> Optional[IPipelineStage]:
        """Get a specific stage by name."""
        ...