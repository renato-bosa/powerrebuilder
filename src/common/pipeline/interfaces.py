"""Pipeline interfaces extracted from contracts for better organization."""

from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


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
    def execute(
        self, input_dir: Path, output_dir: Path, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the pipeline stage."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get stage name."""
        ...

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """Get stage dependencies."""
        ...


class IPipelineCoordinator(Protocol):
    """Interface for pipeline coordinator."""

    @abstractmethod
    def run(
        self, input_dir: Path, output_dir: Path, stages: list[str] | None = None
    ) -> dict[str, Any]:
        """Run the pipeline."""
        ...

    @abstractmethod
    def register_stage(self, stage: IPipelineStage) -> None:
        """Register a pipeline stage."""
        ...

    @abstractmethod
    def get_stages(self) -> dict[str, IPipelineStage]:
        """Get registered stages."""
        ...

    @abstractmethod
    def validate_pipeline(self) -> bool:
        """Validate pipeline configuration."""
        ...
