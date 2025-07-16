"""Streaming utilities for handling large files efficiently."""

import asyncio
from pathlib import Path
from typing import AsyncIterator, BinaryIO, Iterator, Optional, TypeVar, Union
import mmap
import struct

T = TypeVar('T')

class StreamReader:
    """Efficient streaming reader for large binary files."""

    def __init__(self, file_path: Union[str, Path], chunk_size: int = 8192):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self._file: Optional[BinaryIO] = None
        self._mmap: Optional[mmap.mmap] = None

    def __enter__(self):
        self._file = open(self.file_path, 'rb')
        try:
            # Try memory mapping for efficient random access
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        except (OSError, ValueError):
            # Fall back to regular file reading
            self._mmap = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._mmap:
            self._mmap.close()
        if self._file:
            self._file.close()

    def read_chunks(self, start: int = 0, size: Optional[int] = None) -> Iterator[bytes]:
        """Read file in chunks from start position."""
        if self._mmap:
            pos = start
            end = min(start + size, len(self._mmap)) if size else len(self._mmap)
            while pos < end:
                chunk_size = min(self.chunk_size, end - pos)
                yield self._mmap[pos:pos + chunk_size]
                pos += chunk_size
        else:
            self._file.seek(start)
            remaining = size
            while True:
                chunk_size = min(self.chunk_size, remaining) if remaining else self.chunk_size
                chunk = self._file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                if remaining:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break

    def read_at(self, offset: int, size: int) -> bytes:
        """Read specific bytes at offset."""
        if self._mmap:
            return self._mmap[offset:offset + size]
        else:
            self._file.seek(offset)
            return self._file.read(size)

    def find_pattern(self, pattern: bytes, start: int = 0) -> int:
        """Find pattern in file, return offset or -1 if not found."""
        if self._mmap:
            return self._mmap.find(pattern, start)
        else:
            # Streaming search for non-mmap files
            self._file.seek(start)
            buffer = bytearray()
            offset = start

            for chunk in self.read_chunks(start):
                buffer.extend(chunk)
                # Keep enough buffer to handle pattern spanning chunks
                if len(buffer) > len(pattern) * 2:
                    pos = buffer.find(pattern)
                    if pos != -1:
                        return offset - len(buffer) + pos
                    # Keep last part that might contain start of pattern
                    buffer = buffer[-len(pattern):]
                    offset += len(chunk)

            # Final check
            pos = buffer.find(pattern)
            if pos != -1:
                return offset - len(buffer) + pos
            return -1


class AsyncStreamReader:
    """Async streaming reader for concurrent file processing."""

    def __init__(self, file_path: Union[str, Path], chunk_size: int = 8192):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self._reader: Optional[StreamReader] = None
        self._executor = None

    async def __aenter__(self):
        import concurrent.futures
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._reader = await asyncio.get_event_loop().run_in_executor(
            self._executor, StreamReader, self.file_path, self.chunk_size
        )
        await asyncio.get_event_loop().run_in_executor(
            self._executor, self._reader.__enter__
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._reader:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._reader.__exit__, exc_type, exc_val, exc_tb
            )
        if self._executor:
            self._executor.shutdown(wait=True)

    async def read_chunks(self, start: int = 0, size: Optional[int] = None) -> AsyncIterator[bytes]:
        """Async read file in chunks."""
        loop = asyncio.get_event_loop()

        # Create sync iterator in thread
        sync_iter = await loop.run_in_executor(
            self._executor, self._reader.read_chunks, start, size
        )

        # Convert to async iterator
        while True:
            try:
                chunk = await loop.run_in_executor(
                    self._executor, next, sync_iter
                )
                yield chunk
            except StopIteration:
                break

    async def read_at(self, offset: int, size: int) -> bytes:
        """Async read specific bytes at offset."""
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._reader.read_at, offset, size
        )


class StreamWriter:
    """Streaming writer for efficient output generation."""

    def __init__(self, file_path: Union[str, Path], buffer_size: int = 65536):
        self.file_path = Path(file_path)
        self.buffer_size = buffer_size
        self._file: Optional[BinaryIO] = None
        self._buffer: bytearray = bytearray()

    def __enter__(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.file_path, 'wb')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        if self._file:
            self._file.close()

    def write(self, data: bytes):
        """Write data to buffer, flush when full."""
        self._buffer.extend(data)
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def write_struct(self, format_str: str, *values):
        """Write structured data."""
        self.write(struct.pack(format_str, *values))

    def flush(self):
        """Flush buffer to disk."""
        if self._buffer and self._file:
            self._file.write(self._buffer)
            self._buffer.clear()


class AsyncStreamWriter:
    """Async streaming writer for concurrent output."""

    def __init__(self, file_path: Union[str, Path], buffer_size: int = 65536):
        self.file_path = Path(file_path)
        self.buffer_size = buffer_size
        self._writer: Optional[StreamWriter] = None
        self._executor = None
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        import concurrent.futures
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._writer = StreamWriter(self.file_path, self.buffer_size)
        await asyncio.get_event_loop().run_in_executor(
            self._executor, self._writer.__enter__
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._writer:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._writer.__exit__, exc_type, exc_val, exc_tb
            )
        if self._executor:
            self._executor.shutdown(wait=True)

    async def write(self, data: bytes):
        """Async write data."""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._writer.write, data
            )

    async def flush(self):
        """Async flush buffer."""
        async with self._lock:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._writer.flush
            )


def stream_process_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    processor_func,
    chunk_size: int = 8192
):
    """Process file in streaming fashion."""
    with StreamReader(input_path, chunk_size) as reader:
        with StreamWriter(output_path) as writer:
            for chunk in reader.read_chunks():
                processed = processor_func(chunk)
                if processed:
                    writer.write(processed)


async def async_stream_process_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    processor_func,
    chunk_size: int = 8192
):
    """Async process file in streaming fashion."""
    async with AsyncStreamReader(input_path, chunk_size) as reader:
        async with AsyncStreamWriter(output_path) as writer:
            async for chunk in reader.read_chunks():
                processed = await processor_func(chunk) if asyncio.iscoroutinefunction(processor_func) else processor_func(chunk)
                if processed:
                    await writer.write(processed)