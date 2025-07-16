"""
Unified state management for the PowerBuilder pipeline.

This module provides a centralized state management system with:
- Atomic stage completion
- Rollback capabilities
- State persistence
- Thread-safe operations
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from ..contracts.state import IStateManager, IPipelineState, StageStatus

logger = logging.getLogger(__name__)


@dataclass
class StageState:
    """State of a single pipeline stage."""
    name: str
    status: StageStatus = StageStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    checkpoint_id: Optional[str] = None


@dataclass
class PipelineState(IPipelineState):
    """
    Implementation of pipeline state.

    This class maintains the complete state of a pipeline execution including
    stage statuses, results, and context.
    """

    id: str
    stages: Dict[str, StageState] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    checkpoints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

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
                    s.status in [StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.ROLLED_BACK]
                    for s in self.stages.values()
                )
                if all_complete and self.end_time is None:
                    self.end_time = datetime.now()

    def get_stage_result(self, stage: str) -> Optional[Dict[str, Any]]:
        """Get result of a stage."""
        with self._lock:
            if stage in self.stages:
                return self.stages[stage].result
            return None

    def set_stage_result(self, stage: str, result: Dict[str, Any]) -> None:
        """Set result of a stage."""
        with self._lock:
            if stage not in self.stages:
                self.stages[stage] = StageState(name=stage)
            self.stages[stage].result = result

    def get_context(self) -> Dict[str, Any]:
        """Get pipeline context."""
        with self._lock:
            return self.context.copy()

    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update pipeline context."""
        with self._lock:
            self.context.update(updates)

    def get_start_time(self) -> Optional[datetime]:
        """Get pipeline start time."""
        return self.start_time

    def get_end_time(self) -> Optional[datetime]:
        """Get pipeline end time."""
        return self.end_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        with self._lock:
            return {
                'id': self.id,
                'stages': {
                    name: {
                        'name': stage.name,
                        'status': stage.status.value,
                        'start_time': stage.start_time.isoformat() if stage.start_time else None,
                        'end_time': stage.end_time.isoformat() if stage.end_time else None,
                        'result': stage.result,
                        'error': stage.error,
                        'checkpoint_id': stage.checkpoint_id
                    }
                    for name, stage in self.stages.items()
                },
                'context': self.context,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'checkpoints': self.checkpoints
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineState':
        """Create state from dictionary."""
        state = cls(id=data['id'])

        # Restore stages
        for name, stage_data in data.get('stages', {}).items():
            stage = StageState(
                name=stage_data['name'],
                status=StageStatus(stage_data['status']),
                start_time=datetime.fromisoformat(stage_data['start_time']) if stage_data.get('start_time') else None,
                end_time=datetime.fromisoformat(stage_data['end_time']) if stage_data.get('end_time') else None,
                result=stage_data.get('result'),
                error=stage_data.get('error'),
                checkpoint_id=stage_data.get('checkpoint_id')
            )
            state.stages[name] = stage

        # Restore context
        state.context = data.get('context', {})

        # Restore timestamps
        if data.get('start_time'):
            state.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            state.end_time = datetime.fromisoformat(data['end_time'])

        # Restore checkpoints
        state.checkpoints = data.get('checkpoints', {})

        return state


class StateManager(IStateManager):
    """
    State manager implementation with persistence and rollback support.
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            state_dir: Directory for state persistence
        """
        self.state_dir = Path(state_dir) if state_dir else Path.cwd() / ".pipeline_state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._states: Dict[str, PipelineState] = {}
        self._lock = threading.Lock()
        self._id_counter = 0

    def create_state(self) -> IPipelineState:
        """Create a new pipeline state."""
        with self._lock:
            self._id_counter += 1
            state_id = f"pipeline_{self._id_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            state = PipelineState(id=state_id)
            self._states[state_id] = state
            return state

    def save_state(self, state: IPipelineState, path: Optional[Path] = None) -> None:
        """Save state to disk."""
        if not isinstance(state, PipelineState):
            raise ValueError("State must be a PipelineState instance")

        if path is None:
            path = self.state_dir / f"{state.id}.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)

        logger.info(f"Saved state to {path}")

    def load_state(self, path: Path) -> IPipelineState:
        """Load state from disk."""
        with open(path) as f:
            data = json.load(f)

        state = PipelineState.from_dict(data)

        with self._lock:
            self._states[state.id] = state

        logger.info(f"Loaded state from {path}")
        return state

    def create_checkpoint(self, state: IPipelineState, stage: str) -> str:
        """Create a checkpoint for rollback."""
        if not isinstance(state, PipelineState):
            raise ValueError("State must be a PipelineState instance")

        checkpoint_id = f"checkpoint_{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        with state._lock:
            # Create checkpoint data
            checkpoint_data = {
                'stage': stage,
                'timestamp': datetime.now().isoformat(),
                'stages': {
                    name: {
                        'status': s.status.value,
                        'result': s.result,
                        'error': s.error
                    }
                    for name, s in state.stages.items()
                },
                'context': state.context.copy()
            }

            state.checkpoints[checkpoint_id] = checkpoint_data

            # Update stage checkpoint reference
            if stage in state.stages:
                state.stages[stage].checkpoint_id = checkpoint_id

        # Persist checkpoint
        checkpoint_path = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        logger.info(f"Created checkpoint {checkpoint_id} for stage {stage}")
        return checkpoint_id

    def rollback(self, state: IPipelineState, checkpoint_id: str) -> IPipelineState:
        """Rollback to a checkpoint."""
        if not isinstance(state, PipelineState):
            raise ValueError("State must be a PipelineState instance")

        with state._lock:
            if checkpoint_id not in state.checkpoints:
                # Try loading from disk
                checkpoint_path = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
                if checkpoint_path.exists():
                    with open(checkpoint_path) as f:
                        checkpoint_data = json.load(f)
                else:
                    raise ValueError(f"Checkpoint {checkpoint_id} not found")
            else:
                checkpoint_data = state.checkpoints[checkpoint_id]

            # Restore stage states
            for name, stage_data in checkpoint_data['stages'].items():
                if name in state.stages:
                    stage = state.stages[name]
                    stage.status = StageStatus(stage_data['status'])
                    stage.result = stage_data.get('result')
                    stage.error = stage_data.get('error')
                else:
                    state.stages[name] = StageState(
                        name=name,
                        status=StageStatus(stage_data['status']),
                        result=stage_data.get('result'),
                        error=stage_data.get('error')
                    )

            # Mark rolled back stages
            checkpoint_stage = checkpoint_data['stage']
            found_checkpoint = False
            for name, stage in state.stages.items():
                if name == checkpoint_stage:
                    found_checkpoint = True
                if found_checkpoint and stage.status != StageStatus(checkpoint_data['stages'].get(name, {}).get('status', 'pending')):
                    stage.status = StageStatus.ROLLED_BACK

            # Restore context
            state.context = checkpoint_data['context'].copy()

        logger.info(f"Rolled back to checkpoint {checkpoint_id}")
        return state

    def get_state(self, state_id: str) -> Optional[IPipelineState]:
        """Get a state by ID."""
        with self._lock:
            return self._states.get(state_id)

    def list_states(self) -> List[str]:
        """List all state IDs."""
        with self._lock:
            return list(self._states.keys())

    def cleanup_old_states(self, days: int = 7) -> int:
        """Clean up states older than specified days."""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        removed = 0

        # Clean up state files
        for state_file in self.state_dir.glob("pipeline_*.json"):
            try:
                mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
                if mtime < cutoff_date:
                    state_file.unlink()
                    removed += 1
            except Exception as e:
                logger.warning(f"Failed to clean up {state_file}: {e}")

        # Clean up checkpoint files
        checkpoint_dir = self.state_dir / "checkpoints"
        if checkpoint_dir.exists():
            for checkpoint_file in checkpoint_dir.glob("checkpoint_*.json"):
                try:
                    mtime = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)
                    if mtime < cutoff_date:
                        checkpoint_file.unlink()
                        removed += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up {checkpoint_file}: {e}")

        logger.info(f"Cleaned up {removed} old state files")
        return removed


# Factory function for dependency injection
def create_state_manager() -> StateManager:
    """Factory function to create state manager."""
    return StateManager()