"""Unified state management for the PowerBuilder pipeline.

This module provides a centralized state management system with:
- Atomic stage completion
- Rollback capabilities
- State persistence
- Thread-safe operations
"""

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.contracts import IPipelineState, IStateManager, StageStatus

logger = logging.getLogger(__name__)


@dataclass
class StageState:
    """State of a single pipeline stage."""

    name: str
    status: StageStatus = StageStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    checkpoint_id: str | None = None


@dataclass
class PipelineState(IPipelineState):
    """Implementation of pipeline state.

    This class maintains the complete state of a pipeline execution including
    stage statuses, results, and context.
    """

    id: str
    stages: dict[str, StageState] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    checkpoints: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )

    def get_stage_status(self, stage: str) -> StageStatus:
        """Get status of a stage."""
        with self._lock:
            if stage in self.stages:
                return self.stages[stage].status
            return StageStatus.PENDING

    def set_stage_status(self, stage: str, status: StageStatus) -> None:
        """Set status of a stage."""
        with self._lock:
            if stage not in self.stages:
                self.stages[stage] = StageState(name=stage)

            stage_state = self.stages[stage]
            stage_state.status = status

            # Update timestamps
            if status == StageStatus.RUNNING:
                stage_state.start_time = datetime.now()
                if self.start_time is None:
                    self.start_time = stage_state.start_time
            elif status in [StageStatus.COMPLETED, StageStatus.FAILED]:
                stage_state.end_time = datetime.now()

            # Check if all stages are complete
            all_complete = all(
                s.status
                in [
                    StageStatus.COMPLETED,
                    StageStatus.FAILED,
                    StageStatus.ROLLED_BACK,
                ]
                for s in self.stages.values()
            )
            if all_complete and self.end_time is None:
                self.end_time = datetime.now()

    def get_stage_result(self, stage: str) -> dict[str, Any] | None:
        """Get result of a stage."""
        with self._lock:
            if stage in self.stages:
                return self.stages[stage].result
            return None

    def set_stage_result(self, stage: str, result: dict[str, Any]) -> None:
        """Set result of a stage."""
        with self._lock:
            if stage not in self.stages:
                self.stages[stage] = StageState(name=stage)
            self.stages[stage].result = result

    def get_context(self) -> dict[str, Any]:
        """Get pipeline context."""
        with self._lock:
            return self.context.copy()

    def update_context(self, updates: dict[str, Any]) -> None:
        """Update pipeline context."""
        with self._lock:
            self.context.update(updates)

    def get_start_time(self) -> datetime | None:
        """Get pipeline start time."""
        return self.start_time

    def get_end_time(self) -> datetime | None:
        """Get pipeline end time."""
        return self.end_time

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        with self._lock:
            return {
                "id": self.id,
                "stages": {
                    name: {
                        "name": stage.name,
                        "status": stage.status.value,
                        "start_time": stage.start_time.isoformat()
                        if stage.start_time
                        else None,
                        "end_time": stage.end_time.isoformat()
                        if stage.end_time
                        else None,
                        "result": stage.result,
                        "error": stage.error,
                        "checkpoint_id": stage.checkpoint_id,
                    }
                    for name, stage in self.stages.items()
                },
                "context": self.context,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "checkpoints": self.checkpoints,
            }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineState":
        """Create PipelineState from dictionary."""
        state = cls(id=data["id"])

        # Restore stages
        for name, stage_data in data.get("stages", {}).items():
            stage = StageState(
                name=stage_data["name"],
                status=StageStatus(stage_data["status"]),
                start_time=datetime.fromisoformat(stage_data["start_time"])
                if stage_data.get("start_time")
                else None,
                end_time=datetime.fromisoformat(stage_data["end_time"])
                if stage_data.get("end_time")
                else None,
                result=stage_data.get("result"),
                error=stage_data.get("error"),
                checkpoint_id=stage_data.get("checkpoint_id"),
            )
            state.stages[name] = stage

        # Restore other fields
        state.context = data.get("context", {})
        state.start_time = (
            datetime.fromisoformat(data["start_time"])
            if data.get("start_time")
            else None
        )
        state.end_time = (
            datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        )
        state.checkpoints = data.get("checkpoints", {})

        return state


class StateManager(IStateManager):
    """Manages pipeline state with persistence and recovery."""

    def __init__(self, state_dir: Path | None = None) -> None:
        """Initialize state manager.

        Args:
            state_dir: Directory for state persistence
        """
        self.state_dir = state_dir
        self.states: dict[str, PipelineState] = {}
        self._lock = threading.Lock()

        if self.state_dir:
            self.state_dir.mkdir(parents=True, exist_ok=True)

    def create_state(self, pipeline_id: str) -> IPipelineState:
        """Create new pipeline state."""
        with self._lock:
            state = PipelineState(id=pipeline_id)
            self.states[pipeline_id] = state
            self._persist_state(state)
            return state

    def get_state(self, pipeline_id: str) -> IPipelineState | None:
        """Get pipeline state by ID."""
        with self._lock:
            return self.states.get(pipeline_id)

    def save_checkpoint(
        self, pipeline_id: str, stage: str, data: dict[str, Any]
    ) -> str:
        """Save checkpoint for a stage."""
        with self._lock:
            state = self.states.get(pipeline_id)
            if not state:
                raise ValueError(f"Pipeline {pipeline_id} not found")

            checkpoint_id = f"{stage}_{datetime.now().timestamp()}"
            state.checkpoints[checkpoint_id] = {
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }

            if stage in state.stages:
                state.stages[stage].checkpoint_id = checkpoint_id

            self._persist_state(state)
            return checkpoint_id

    def restore_checkpoint(
        self, pipeline_id: str, checkpoint_id: str
    ) -> dict[str, Any]:
        """Restore checkpoint data."""
        with self._lock:
            state = self.states.get(pipeline_id)
            if not state:
                raise ValueError(f"Pipeline {pipeline_id} not found")

            checkpoint = state.checkpoints.get(checkpoint_id)
            if not checkpoint:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")

            return checkpoint["data"]

    def _persist_state(self, state: PipelineState) -> None:
        """Persist state to disk."""
        if not self.state_dir:
            return

        state_file = self.state_dir / f"{state.id}.json"
        try:
            with open(state_file, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
        except Exception as e:
            logger.error("Failed to persist state for %s: %s", state.id, e)

    def load_state(self, pipeline_id: str) -> IPipelineState | None:
        """Load state from disk."""
        if not self.state_dir:
            return None

        state_file = self.state_dir / f"{pipeline_id}.json"
        if not state_file.exists():
            return None

        try:
            with open(state_file) as f:
                data = json.load(f)
            state = PipelineState.from_dict(data)
            with self._lock:
                self.states[pipeline_id] = state
            return state
        except Exception as e:
            logger.error("Failed to load state for %s: %s", pipeline_id, e)
            return None
