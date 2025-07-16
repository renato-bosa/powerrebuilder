# Streaming Support for Large PBD Files

## Overview
Implemented streaming support for extracting large PBD files (>4MB) to improve memory efficiency and enable extraction of files that would otherwise cause memory issues.

## Implementation Details

### 1. Streaming Threshold
- **Threshold**: 4MB (4,194,304 bytes)
- Files exceeding this size automatically use streaming extraction
- Falls back to standard extraction if streaming fails

### 2. Core Components

#### Extract Coordinator (`src/extract/coordinator.py`)
- Added `STREAMING_THRESHOLD` constant
- Added `_extract_with_streaming()` method for large file handling
- Added `_check_memory_pressure()` for memory management
- Modified `extract_with_recovery()` to detect and use streaming for large files

#### Streaming PBD Reader (`src/extract/pbd/reader.py`)
- `StreamingPBDReader` class for synchronous streaming
- `AsyncStreamingPBDReader` class for asynchronous streaming
- Uses `StreamReader` from common utilities for efficient chunk-based reading
- Implements memory-mapped file access when available

#### Progress Tracking (`src/extract/pbd/io/progress.py`)
- Enhanced `TqdmProgressTracker` to support byte-level progress
- Added support for `unit_scale` and `unit_divisor` for human-readable sizes
- Shows transfer speeds (MB/s) and ETA for large files

### 3. Key Features

#### Memory Management
- Automatic garbage collection when memory usage exceeds 70%
- Resource monitoring with memory pressure checks every 10 entries
- Chunked reading to avoid loading entire file into memory

#### Progress Tracking
- Compound progress tracking (file count + current file progress)
- Byte-level progress with transfer speeds
- ETA calculation for large file operations

#### Error Handling
- Graceful fallback to standard extraction if streaming fails
- Memory error recovery with forced garbage collection
- Detailed logging of streaming operations

### 4. Usage

The streaming extraction is automatic. When a file exceeds the threshold:
```python
# Automatic detection in extract_with_recovery()
if file_size > STREAMING_THRESHOLD:
    logger.info("File %s (%s bytes) exceeds streaming threshold", file_name, file_size)
    if _extract_with_streaming(...):
        return True
    # Falls back to standard extraction if streaming fails
```

### 5. Benefits
- **Memory Efficiency**: Processes large files without loading them entirely into memory
- **Progress Visibility**: Real-time progress with speeds and ETA
- **Scalability**: Can handle PBD files of any size (limited only by disk space)
- **Reliability**: Automatic memory management and fallback mechanisms

### 6. Technical Details

#### StreamReader Features
- Memory-mapped file support for efficient random access
- Chunked reading with configurable chunk size (default 8KB)
- Pattern searching without loading entire file
- Support for both synchronous and asynchronous operations

#### Entry Iteration
- Streams NOD blocks one at a time
- Extracts entries without loading all metadata at once
- Custom file-like wrapper for compatibility with existing extraction code

#### Data Extraction
- Streams DAT blocks on demand
- Minimal memory footprint per entry
- Compatible with all existing file types and formats