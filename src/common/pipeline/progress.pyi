from typing import Protocol

from rich.progress import Progress, Task

class ProgressCallback(Protocol):
    def __call__(self, current: int, total: int, message: str = "") -> None: ...

class ProgressTracker:
    progress: Progress
    tasks: dict[str, Task]

    def __init__(self) -> None: ...
    def start_task(self, task_id: str, description: str, total: int) -> None: ...
    def update_task(
        self, task_id: str, advance: int = 1, message: str | None = None
    ) -> None: ...
    def complete_task(self, task_id: str) -> None: ...
