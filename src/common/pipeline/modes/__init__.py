"""Pipeline execution modes.

This module provides different execution modes for the pipeline:
- Parallel: Execute stages in parallel when possible
- Streaming: Process items as a stream through the pipeline
"""

from .parallel import ParallelPipeline
from .streaming import AsyncStreamingPipeline

# Alias for backward compatibility
StreamingPipeline = AsyncStreamingPipeline

__all__ = ["AsyncStreamingPipeline", "ParallelPipeline", "StreamingPipeline"]
