"""In-memory streaming infrastructure for pipeline stages.

This module provides:
- Stream interfaces for passing data between stages
- Bounded queues to prevent memory overflow
- Async support for concurrent processing
- Backpressure handling
"""

import asyncio
import logging
import queue
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, Iterator, Optional, Protocol, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


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


class IStreamReader(Protocol[T]):
    """Interface for reading from a stream."""
    
    def read(self) -> Optional[T]:
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


class IStreamWriter(Protocol[T]):
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


class IStream(IStreamReader[T], IStreamWriter[T], Protocol[T]):
    """Bidirectional stream interface."""
    
    @property
    def metadata(self) -> StreamMetadata:
        """Get stream metadata."""
        ...


class BoundedQueue:
    """Thread-safe bounded queue with backpressure."""
    
    def __init__(self, maxsize: int = 1000):
        """Initialize bounded queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self._queue = queue.Queue(maxsize=maxsize)
        self._closed = threading.Event()
        self._lock = threading.Lock()
    
    def put(self, item: Any, timeout: Optional[float] = None) -> None:
        """Put item in queue.
        
        Args:
            item: Item to add
            timeout: Timeout in seconds
            
        Raises:
            queue.Full: If queue is full and timeout expires
            ValueError: If queue is closed
        """
        if self._closed.is_set():
            raise ValueError("Queue is closed")
        
        self._queue.put(item, timeout=timeout)
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """Get item from queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Next item from queue
            
        Raises:
            queue.Empty: If queue is empty and timeout expires
        """
        if self._closed.is_set() and self._queue.empty():
            raise queue.Empty("Queue is closed and empty")
        
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
        """Get current queue size."""
        return self._queue.qsize()
    
    @property
    def is_full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()


class MemoryStream(IStream[T]):
    """In-memory stream implementation."""
    
    def __init__(
        self, 
        source_stage: str,
        target_stage: str,
        data_type: str,
        maxsize: int = 1000
    ):
        """Initialize memory stream.
        
        Args:
            source_stage: Source stage name
            target_stage: Target stage name
            data_type: Type of data in stream
            maxsize: Maximum queue size
        """
        self._queue = BoundedQueue(maxsize)
        self._metadata = StreamMetadata(
            source_stage=source_stage,
            target_stage=target_stage,
            data_type=data_type
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
                self._metadata.target_stage
            )
            raise
        except Exception as e:
            self._metadata.error_count += 1
            self._state = StreamState.ERROR
            raise
    
    def write_batch(self, items: list[T]) -> None:
        """Write batch of items."""
        for item in items:
            self.write(item)
    
    def read(self) -> Optional[T]:
        """Read next item from stream."""
        try:
            return self._queue.get(timeout=0.1)  # Non-blocking with small timeout
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
            self._metadata.byte_count
        )
    
    def flush(self) -> None:
        """Flush is a no-op for memory streams."""
        pass
    
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
        maxsize: int = 1000
    ):
        """Initialize async memory stream.
        
        Args:
            source_stage: Source stage name
            target_stage: Target stage name
            data_type: Type of data in stream
            maxsize: Maximum queue size
        """
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._metadata = StreamMetadata(
            source_stage=source_stage,
            target_stage=target_stage,
            data_type=data_type
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
            
        except asyncio.TimeoutError:
            logger.warning(
                "Stream queue full for %s -> %s. Applying backpressure.",
                self._metadata.source_stage,
                self._metadata.target_stage
            )
            raise
        except Exception as e:
            self._metadata.error_count += 1
            self._state = StreamState.ERROR
            raise
    
    async def read(self) -> Optional[Any]:
        """Read next item from stream."""
        if self._closed.is_set() and self._queue.empty():
            return None
        
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
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
    
    def __init__(self):
        """Initialize stream manager."""
        self._streams: Dict[str, IStream] = {}
        self._lock = threading.Lock()
    
    def create_stream(
        self,
        stream_id: str,
        source_stage: str,
        target_stage: str,
        data_type: str,
        maxsize: int = 1000
    ) -> IStream:
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
                maxsize=maxsize
            )
            
            self._streams[stream_id] = stream
            logger.info(
                "Created stream %s: %s -> %s (%s)",
                stream_id,
                source_stage,
                target_stage,
                data_type
            )
            
            return stream
    
    def get_stream(self, stream_id: str) -> Optional[IStream]:
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
            for stream_id, stream in list(self._streams.items()):
                stream.close()
            self._streams.clear()
            logger.info("Closed all streams")
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all streams.
        
        Returns:
            Dictionary of stream statistics
        """
        stats = {}
        with self._lock:
            for stream_id, stream in self._streams.items():
                metadata = stream.metadata
                stats[stream_id] = {
                    'source': metadata.source_stage,
                    'target': metadata.target_stage,
                    'type': metadata.data_type,
                    'items': metadata.item_count,
                    'bytes': metadata.byte_count,
                    'errors': metadata.error_count
                }
        return stats


class FileBackedStream(IStream):
    """Stream that spills to disk when memory limit is reached."""
    
    def __init__(
        self,
        source_stage: str,
        target_stage: str,
        data_type: str,
        memory_limit: int = 100,  # Items in memory
        temp_dir: Optional[Path] = None
    ):
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
            maxsize=memory_limit
        )
        self._temp_dir = temp_dir or Path("/tmp")
        self._spill_files: list[Path] = []
        self._current_spill_file: Optional[Path] = None
        self._spill_count = 0
        
        # TODO: Implement spill-to-disk logic
        logger.warning("FileBackedStream spill-to-disk not yet implemented")
    
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
    
    def read(self) -> Optional[Any]:
        """Read next item from stream."""
        item = self._memory_stream.read()
        if item is None and self._spill_files:
            # Load from spill files
            self._load_from_disk()
            item = self._memory_stream.read()
        return item
    
    def read_batch(self, size: int) -> list[Any]:
        """Read batch of items."""
        return self._memory_stream.read_batch(size)
    
    def close(self) -> None:
        """Close the stream."""
        self._memory_stream.close()
        # Clean up spill files
        for spill_file in self._spill_files:
            if spill_file.exists():
                spill_file.unlink()
    
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
        # TODO: Implement spill logic
        pass
    
    def _load_from_disk(self) -> None:
        """Load data from spill files."""
        # TODO: Implement load logic
        pass


# Global stream manager instance
_stream_manager = StreamManager()


def get_stream_manager() -> StreamManager:
    """Get the global stream manager."""
    return _stream_manager