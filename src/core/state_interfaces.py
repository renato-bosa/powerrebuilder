"""State management interfaces for clean architecture."""

from abc import abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class StageStatus(Enum):
    """Stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class IPipelineState(Protocol):
    """Interface for pipeline state."""

    @abstractmethod
    def get_stage_status(self, stage: str) -> StageStatus:
        """Get status of a stage."""
        ...

    @abstractmethod
    def set_stage_status(self, stage: str, status: StageStatus) -> None:
        """Set status of a stage."""
        ...

    @abstractmethod
    def get_stage_result(self, stage: str) -> dict[str, Any] | None:
        """Get result of a stage."""
        ...

    @abstractmethod
    def set_stage_result(self, stage: str, result: dict[str, Any]) -> None:
        """Set result of a stage."""
        ...

    @abstractmethod
    def get_context(self) -> dict[str, Any]:
        """Get pipeline context."""
        ...

    @abstractmethod
    def update_context(self, updates: dict[str, Any]) -> None:
        """Update pipeline context."""
        ...

    @abstractmethod
    def get_start_time(self) -> datetime | None:
        """Get pipeline start time."""
        ...

    @abstractmethod
    def get_end_time(self) -> datetime | None:
        """Get pipeline end time."""
        ...


class IStateManager(Protocol):
    """Interface for state management."""

    @abstractmethod
    def create_state(self) -> IPipelineState:
        """Create a new pipeline state."""
        ...

    @abstractmethod
    def save_state(self, state: IPipelineState, path: Path) -> None:
        """Save state to disk."""
        ...

    @abstractmethod
    def load_state(self, path: Path) -> IPipelineState:
        """Load state from disk."""
        ...

    @abstractmethod
    def create_checkpoint(self, state: IPipelineState, stage: str) -> str:
        """Create a checkpoint for rollback."""
        ...

    @abstractmethod
    def rollback(self, state: IPipelineState, checkpoint_id: str) -> IPipelineState:
        """Rollback to a checkpoint."""
        ...
