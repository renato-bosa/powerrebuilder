"""Pipeline module for PowerRebuilder.

This module provides the core pipeline functionality for processing
PowerBuilder applications through various stages.
"""

from .base import PipelineStage, PipelineSummary, NoOpProgressTracker
from .progress import PipelineProgress
from .modes.parallel import ParallelPipeline
from .modes.streaming import AsyncStreamingPipeline

# Alias ParallelPipeline as Pipeline for backward compatibility
Pipeline = ParallelPipeline

__all__ = [
    "Pipeline",
    "ParallelPipeline",
    "AsyncStreamingPipeline",
    "PipelineProgress",
    "PipelineStage",
    "PipelineSummary",
    "NoOpProgressTracker",
]
