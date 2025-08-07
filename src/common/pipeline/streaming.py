"""In-memory streaming infrastructure for pipeline stages.

This module provides:
- Stream interfaces for passing data between stages
- Bounded queues to prevent memory overflow
- Async support for concurrent processing
- Backpressure handling
"""

import asyncio
import logging
import pickle
import queue
import tempfile
import threading
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


class StreamState(Enum):
    """Stream state."""

    CREATED = "created"
    OPEN = "open"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class StreamMetadata:
    """Metadata for a stream."""

    source_stage: str
    target_stage: str
    data_type: str
    item_count: int = 0
    byte_count: int = 0
    error_count: int = 0


class IStream[Any]Reader(Protocol[T]):
    """Interface for reading from a stream."""

    def read(self) -> T | None:
        """Read next item from stream."""
        ...

    def read_batch(self, size: int) -> list[T]:
        """Read batch of items."""
        ...

    def close(self) -> None:
        """Close the stream."""
        ...

    @property
    def is_closed(self) -> bool:
        """Check if stream is closed."""
        ...


class IStream[Any]Writer(Protocol[T]):
    """Interface for writing to a stream."""

    def write(self, item: T) -> None:
        """Write item to stream."""
        ...

    def write_batch(self, items: list[T]) -> None:
        """Write batch of items."""
        ...

    def close(self) -> None:
        """Close the stream."""
        ...

    def flush(self) -> None:
        """Flush any buffered data."""
        ...


class IStream[Any](IStream[Any]Reader[T], IStream[Any]Writer[T], Protocol[T]):
    """Bidirectional stream interface."""

    @property
    def metadata(self) -> StreamMetadata:
        """Get stream metadata."""
        ...


class BoundedQueue[Any]:
    """Thread-safe bounded queue with backpressure."""

    def __init__(self, maxsize: int = 1000) -> None:
        """Initialize bounded queue.

        Args:
            maxsize: Maximum queue size
        """
        self._queue = queue.Queue[Any](maxsize=maxsize)
        self._closed = threading.Event()
        self._lock = threading.Lock()

    def put(self, item: Any, timeout: float | None = None) -> None:
        """Put item in queue.

        Args:
            item: Item to add
            timeout: Timeout in seconds

        Raises:
            queue.Full: If queue is full and timeout expires
            ValueError: If queue is closed
        """
        if self._closed.is_set():
            raise ValueError("Queue[Any] is closed")

        self._queue.put(item, timeout=timeout)

    def get(self, timeout: float | None = None) -> Any:
        """Get item from queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Next item from queue

        Raises:
            queue.Empty: If queue is empty and timeout expires
        """
        if self._closed.is_set() and self._queue.empty():
            raise queue.Empty("Queue[Any] is closed and empty")

        return self._queue.get(timeout=timeout)

    def close(self) -> None:
        """Close the queue."""
        self._closed.set()

    @property
    def is_closed(self) -> bool:
        """Check if queue is closed."""
        return self._closed.is_set()

    @property
    def size(self) -> int:
        """Get queue size."""
        return self._queue.qsize()

    @property
    def is_full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()


class MemoryStream(IStream[Any][T]):
    """In-memory stream implementation."""

    def __init__(
        self,
        source_stage: str,
        target_stage: str,
        data_type: str,
        maxsize: int = 1000,
    ) -> None:
        """Initialize memory stream.

        Args:
            source_stage: Source stage name
            target_stage: Target stage name
            data_type: Type of data in stream
            maxsize: Maximum queue size
        """
        self._queue = BoundedQueue[Any](maxsize)
        self._metadata = StreamMetadata(
            source_stage=source_stage, target_stage=target_stage, data_type=data_type
        )
        self._state = StreamState.OPEN

    def write(self, item: T) -> None:
        """Write item to stream."""
        if self._state != StreamState.OPEN:
            raise ValueError(f"Cannot write to stream in state: {self._state}")

        try:
            self._queue.put(item, timeout=30)  # 30 second timeout
            self._metadata.item_count += 1

            # Estimate byte count (rough approximation)
            import sys

            self._metadata.byte_count += sys.getsizeof(item)

        except queue.Full:
            logger.warning(
                "Stream queue full for %s -> %s. Applying backpressure.",
                self._metadata.source_stage,
                self._metadata.target_stage,
            )
            raise
        except Exception:
            self._metadata.error_count += 1
            self._state = StreamState.ERROR
            raise

    def write_batch(self, items: list[T]) -> None:
        """Write batch of items."""
        for item in items:
            self.write(item)

    def read(self) -> T | None:
        """Read next item from stream."""
        try:
            # Non-blocking with small timeout
            return self._queue.get(timeout=0.1)
        except queue.Empty:
            if self._queue.is_closed:
                return None
            raise

    def read_batch(self, size: int) -> list[T]:
        """Read batch of items."""
        items = []
        for _ in range(size):
            try:
                item = self.read()
                if item is None:
                    break
                items.append(item)
            except queue.Empty:
                break
        return items

    def close(self) -> None:
        """Close the stream."""
        self._queue.close()
        self._state = StreamState.CLOSED
        logger.debug(
            "Closed stream %s -> %s. Items: %d, Bytes: %d",
            self._metadata.source_stage,
            self._metadata.target_stage,
            self._metadata.item_count,
            self._metadata.byte_count,
        )

    def flush(self) -> None:
        """Flush is a no-op for memory streams."""
        # For memory streams, ensure any pending operations are completed
        # Since we're using a Queue[Any], all writes are immediate
        # Log current state for debugging
        logger.debug(
            "Flushing stream %s -> %s. Queue[Any] size: %d",
            self._metadata.source_stage,
            self._metadata.target_stage,
            self._queue.size,
        )

    @property
    def is_closed(self) -> bool:
        """Check if stream is closed."""
        return self._state == StreamState.CLOSED

    @property
    def metadata(self) -> StreamMetadata:
        """Get stream metadata."""
        return self._metadata


class AsyncMemoryStream:
    """Async in-memory stream implementation."""

    def __init__(
        self,
        source_stage: str,
        target_stage: str,
        data_type: str,
        maxsize: int = 1000,
    ) -> None:
        """Initialize async memory stream.

        Args:
            source_stage: Source stage name
            target_stage: Target stage name
            data_type: Type of data in stream
            maxsize: Maximum queue size
        """
        self._queue: asyncio.Queue[Any] = asyncio.Queue[Any](maxsize=maxsize)
        self._metadata = StreamMetadata(
            source_stage=source_stage, target_stage=target_stage, data_type=data_type
        )
        self._state = StreamState.OPEN
        self._closed = asyncio.Event()

    async def write(self, item: Any) -> None:
        """Write item to stream."""
        if self._state != StreamState.OPEN:
            raise ValueError(f"Cannot write to stream in state: {self._state}")

        try:
            await asyncio.wait_for(self._queue.put(item), timeout=30)
            self._metadata.item_count += 1

            import sys

            self._metadata.byte_count += sys.getsizeof(item)

        except TimeoutError:
            logger.warning(
                "Stream queue full for %s -> %s. Applying backpressure.",
                self._metadata.source_stage,
                self._metadata.target_stage,
            )
            raise
        except Exception:
            self._metadata.error_count += 1
            self._state = StreamState.ERROR
            raise

    async def read(self) -> Any | None:
        """Read next item from stream."""
        if self._closed.is_set() and self._queue.empty():
            return None

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=0.1)
        except TimeoutError:
            if self._closed.is_set():
                return None
            raise

    async def close(self) -> None:
        """Close the stream."""
        self._closed.set()
        self._state = StreamState.CLOSED

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Async iteration support."""
        while True:
            item = await self.read()
            if item is None:
                break
            yield item

    @property
    def metadata(self) -> StreamMetadata:
        """Get stream metadata."""
        return self._metadata


class StreamManager:
    """Manages streams between pipeline stages."""

    def __init__(self) -> None:
        """Initialize stream manager."""
        self._streams: dict[str, IStream[Any]] = {}
        self._lock = threading.Lock()

    def create_stream(
        self,
        stream_id: str,
        source_stage: str,
        target_stage: str,
        data_type: str,
        maxsize: int = 1000,
    ) -> IStream[Any]:
        """Create a new stream.

        Args:
            stream_id: Unique stream identifier
            source_stage: Source stage name
            target_stage: Target stage name
            data_type: Type of data in stream
            maxsize: Maximum queue size

        Returns:
            Created stream
        """
        with self._lock:
            if stream_id in self._streams:
                raise ValueError(f"Stream {stream_id} already exists")

            stream = MemoryStream(
                source_stage=source_stage,
                target_stage=target_stage,
                data_type=data_type,
                maxsize=maxsize,
            )

            self._streams[stream_id] = stream
            logger.info(
                "Created stream %s: %s -> %s (%s)",
                stream_id,
                source_stage,
                target_stage,
                data_type,
            )

            return stream

    def get_stream(self, stream_id: str) -> IStream[Any] | None:
        """Get existing stream.

        Args:
            stream_id: Stream identifier

        Returns:
            Stream or None if not found
        """
        return self._streams.get(stream_id)

    def close_stream(self, stream_id: str) -> None:
        """Close a stream.

        Args:
            stream_id: Stream identifier
        """
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                stream.close()
                del self._streams[stream_id]
                logger.info("Closed stream %s", stream_id)

    def close_all(self) -> None:
        """Close all streams."""
        with self._lock:
            for _stream_id, stream in list(self._streams.items()):
                stream.close()
            self._streams.clear()
            logger.info("Closed all streams")

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all streams.

        Returns:
            Dictionary of stream statistics
        """
        stats = {}
        with self._lock:
            for stream_id, stream in self._streams.items():
                metadata = stream.metadata
                stats[stream_id] = {
                    "source": metadata.source_stage,
                    "target": metadata.target_stage,
                    "type": metadata.data_type,
                    "items": metadata.item_count,
                    "bytes": metadata.byte_count,
                    "errors": metadata.error_count,
                }
        return stats


class FileBackedStream(IStream[Any]):
    """Stream that spills to disk when memory limit is reached."""

    def __init__(
        self,
        source_stage: str,
        target_stage: str,
        data_type: str,
        memory_limit: int = 100,  # Items in memory
        temp_dir: Path | None = None,
    ) -> None:
        """Initialize file-backed stream.

        Args:
            source_stage: Source stage name
            target_stage: Target stage name
            data_type: Type of data in stream
            memory_limit: Number of items to keep in memory
            temp_dir: Directory for temporary files
        """
        self._memory_stream = MemoryStream(
            source_stage=source_stage,
            target_stage=target_stage,
            data_type=data_type,
            maxsize=memory_limit,
        )
        self._temp_dir = temp_dir or Path(tempfile.gettempdir())
        self._spill_files: list[Path] = []
        self._current_spill_file: Path | None = None
        self._spill_count = 0
        self._lock = threading.Lock()
        self._read_spill_index = 0
        self._current_read_file = None

    def write(self, item: Any) -> None:
        """Write item to stream."""
        try:
            self._memory_stream.write(item)
        except queue.Full:
            # Spill to disk
            self._spill_to_disk()
            self._memory_stream.write(item)

    def write_batch(self, items: list[Any]) -> None:
        """Write batch of items."""
        for item in items:
            self.write(item)

    def read(self) -> Any | None:
        """Read next item from stream."""
        try:
            item = self._memory_stream.read()
            if item is not None:
                return item
        except queue.Empty:
            pass

        # Try to load from spill files
        if self._spill_files and self._read_spill_index < len(self._spill_files):
            self._load_from_disk()
            try:
                return self._memory_stream.read()
            except queue.Empty:
                return None

        return None

    def read_batch(self, size: int) -> list[Any]:
        """Read batch of items."""
        items = []
        for _ in range(size):
            item = self.read()
            if item is None:
                break
            items.append(item)
        return items

    def close(self) -> None:
        """Close the stream and clean up resources."""
        self._memory_stream.close()

        # Clean up spill files
        with self._lock:
            for spill_file in self._spill_files:
                try:
                    if spill_file.exists():
                        spill_file.unlink()
                        logger.debug("Deleted spill file: %s", spill_file)
                except Exception as e:
                    logger.warning("Failed to delete spill file %s: %s", spill_file, e)
            self._spill_files.clear()

    def flush(self) -> None:
        """Flush memory to disk if needed."""
        if self._memory_stream._queue.size > 0:
            self._spill_to_disk()

    @property
    def is_closed(self) -> bool:
        """Check if stream is closed."""
        return self._memory_stream.is_closed

    @property
    def metadata(self) -> StreamMetadata:
        """Get stream metadata."""
        return self._memory_stream.metadata

    def _spill_to_disk(self) -> None:
        """Spill memory contents to disk."""
        with self._lock:
            # Create a new spill file
            spill_file = (
                self._temp_dir / f"stream_spill_{id(self)}_{self._spill_count}.pkl"
            )
            self._spill_count += 1

            items_to_spill = []

            # Drain the memory queue
            while True:
                try:
                    item = self._memory_stream._queue.get(timeout=0)
                    items_to_spill.append(item)
                except queue.Empty:
                    break

            if items_to_spill:
                try:
                    # Write items to disk using pickle
                    with open(spill_file, "wb") as f:
                        pickle.dump(items_to_spill, f)

                    self._spill_files.append(spill_file)
                    logger.info(
                        "Spilled %d items to disk: %s", len(items_to_spill), spill_file
                    )
                except Exception as e:
                    logger.error("Failed to spill to disk: %s", e)
                    # Put items back in queue if spill failed
                    for item in items_to_spill:
                        try:
                            self._memory_stream._queue.put(item, timeout=0)
                        except queue.Full:
                            break
                    raise

    def _load_from_disk(self) -> None:
        """Load data from spill files back into memory."""
        with self._lock:
            if self._read_spill_index >= len(self._spill_files):
                return

            spill_file = self._spill_files[self._read_spill_index]

            try:
                # Read items from disk
                with open(spill_file, "rb") as f:
                    items = pickle.load(f)

                # Put items back into memory queue
                items_loaded = 0
                for item in items:
                    try:
                        self._memory_stream._queue.put(item, timeout=0)
                        items_loaded += 1
                    except queue.Full:
                        # Can't fit all items, save the rest for later
                        remaining_items = items[items_loaded:]
                        if remaining_items:
                            # Create a new spill file with remaining items
                            new_spill_file = (
                                self._temp_dir
                                / f"stream_spill_{id(self)}_{self._spill_count}.pkl"
                            )
                            self._spill_count += 1
                            with open(new_spill_file, "wb") as f:
                                pickle.dump(remaining_items, f)
                            # Insert at next position
                            self._spill_files.insert(
                                self._read_spill_index + 1, new_spill_file
                            )
                        break

                # If we loaded all items from this file, move to next
                if items_loaded == len(items):
                    self._read_spill_index += 1
                    # Delete the file we just read
                    try:
                        spill_file.unlink()
                        logger.debug("Deleted read spill file: %s", spill_file)
                    except Exception as e:
                        logger.warning(
                            "Failed to delete spill file %s: %s", spill_file, e
                        )

                logger.debug("Loaded %d items from disk: %s", items_loaded, spill_file)

            except Exception as e:
                logger.error("Failed to load from disk %s: %s", spill_file, e)
                self._read_spill_index += 1  # Skip this file
                raise


# Global stream manager instance
_stream_manager = StreamManager()


def get_stream_manager() -> StreamManager:
    """Get the global stream manager."""
    return _stream_manager
