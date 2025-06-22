"""Attribute-related classes for PowerBuilder model.

This module contains classes for handling PowerBuilder attributes and attribute access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .utils.base import PBNode

if TYPE_CHECKING:
    from .ast.types import Type


# ─── ported from model/pb_attribute.py ─────────────────────────────────
@dataclass
class Attribute(PBNode):
    """PowerBuilder attribute node."""

    name: str
    type: Type
    is_constant: bool = False
    is_readonly: bool = False
    default_value: str | None = None


# ─── ported from model/pb_attribute_access.py ───────────────────────────
@dataclass
class AttributeAccess(PBNode):
    """PowerBuilder attribute access node."""

    attribute: Attribute
    array_index: str | None = None
    is_unchecked: bool = False
