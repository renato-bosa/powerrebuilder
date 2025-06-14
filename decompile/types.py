"""Shared types for the decompile module.

This module contains types that are used across multiple decompile modules
to avoid circular import issues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from decompile.core.pcode_decoder import PCodeInstruction


class BlockType(Enum):
    """Types of control flow blocks."""

    BASIC = auto()
    IF = auto()
    WHILE = auto()
    FOR = auto()
    DO_WHILE = auto()
    REPEAT_UNTIL = auto()
    CHOOSE_CASE = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    EVENT = auto()
    FUNCTION = auto()


@dataclass
class ControlBlock:
    """Represents a control flow block."""

    type: BlockType
    start_addr: int
    end_addr: int
    instructions: list[PCodeInstruction] = field(default_factory=list)
    statements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # For nested structures
    then_block: ControlBlock | None = None
    else_block: ControlBlock | None = None
    body: ControlBlock | None = None
    cases: list[dict[str, Any]] = field(default_factory=list)
    default_case: ControlBlock | None = None
    catch_blocks: list[dict[str, Any]] = field(default_factory=list)
    finally_block: ControlBlock | None = None
