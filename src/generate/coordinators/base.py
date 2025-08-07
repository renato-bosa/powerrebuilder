"""Base generation coordinator with common functionality."""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.contracts.interfaces import Event, EventType, IEventBus

logger = logging.getLogger(__name__)


class BaseGenerationCoordinator(ABC):
    """Base class for all generation coordinators."""

    def __init__(
        self, input_dir: Path, output_dir: Path, event_bus: IEventBus | None = None
    ) -> None:
        """Initialize base generation coordinator.

        Args:
            input_dir: Directory containing input files
            output_dir: Directory for generated code
            event_bus: Optional event bus for notifications
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.event_bus = event_bus

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize converters (will be set by subclasses)
        self.converters: Any = {}

    @abstractmethod
    def generate(self, config: dict[str, Any]) -> dict[str, Any]:
        """Generate code from input files.

        Args:
            config: Generation configuration

        Returns:
            Generation results
        """

    @abstractmethod
    def get_generator_type(self) -> str:
        """Get the type of generator.

        Returns:
            Generator type identifier
        """

    def publish_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Publish an event if event bus is available."""
        if self.event_bus:
            from datetime import datetime

            event = Event(
                type=event_type,
                source=f"{self.__class__.__name__}",
                timestamp=datetime.now(),
                data=data,
            )
            self.event_bus.publish(event)

    def find_files(self, pattern: str) -> list[Path]:
        """Find files matching a pattern in input directory."""
        return list(self.input_dir.rglob(pattern))

    def read_json_file(self, file_path: Path) -> dict[str, Any]:
        """Read and parse a JSON file."""
        try:
            with file_path.open() as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to read %s: %s", file_path, e)
            raise

    def extract_object_name(self, file_path: Path, suffix: str) -> str:
        """Extract object name from file path."""
        return file_path.stem.replace(suffix, "")

    def process_files(
        self, files: list[Path], processor_func, file_type: str
    ) -> dict[str, Any]:
        """Process a list of files with a given processor function.

        Args:
            files: List of files to process
            processor_func: Function to process each file
            file_type: Type of files being processed

        Returns:
            Processing results
        """
        results: dict[str, Any] = {"processed": 0, "failed": 0, "files": [], "errors": []}

        total = len(files)

        for idx, file_path in enumerate(files):
            try:
                # Publish progress event
                self.publish_event(
                    EventType.PROGRESS_UPDATE,
                    {
                        "current": idx + 1,
                        "total": total,
                        "file": str(file_path),
                        "type": file_type,
                    },
                )

                # Process file
                processor_func(file_path)
                results["processed"] += 1
                results["files"].append(str(file_path))

                # Publish file processed event
                self.publish_event(
                    EventType.FILE_PROCESSED,
                    {"file": str(file_path), "type": file_type, "status": "success"},
                )

            except Exception as e:
                logger.error("Failed to process %s: %s", file_path, e)
                results["failed"] += 1
                results["errors"].append({"file": str(file_path), "error": str(e)})

                # Publish error event
                self.publish_event(
                    EventType.ERROR_OCCURRED,
                    {"file": str(file_path), "type": file_type, "error": str(e)},
                )

        return results
