"""Control flow generator for Python code generation.

This module provides control flow structures used during code generation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode


@dataclass
class ControlFlow(PBNode):
    """Control flow structure for code generation."""

    type: str  # if, while, for, try
    condition: Any | None = None
    body: list[Any] = field(default_factory=list)
    else_body: list[Any] = field(default_factory=list)
    finally_body: list[Any] = field(default_factory=list)

    @property
    def has_else(self) -> bool:
        """Check if the control flow has an else block."""
        return bool(self.else_body)

    @property
    def has_finally(self) -> bool:
        """Check if the control flow has a finally block."""
        return bool(self.finally_body)
