"""Pipeline module for PowerRebuilder.

This module provides the core pipeline functionality for processing
PowerBuilder applications through various stages.
"""

from .base import NoOpProgressTracker, PipelineStage, PipelineSummary
from .modes.parallel import ParallelPipeline
from .modes.streaming import AsyncStreamingPipeline
from .progress import PipelineProgress

# Alias ParallelPipeline as Pipeline for backward compatibility
Pipeline = ParallelPipeline

__all__ = [
    "AsyncStreamingPipeline",
    "NoOpProgressTracker",
    "ParallelPipeline",
    "Pipeline",
    "PipelineProgress",
    "PipelineStage",
    "PipelineSummary",
]
