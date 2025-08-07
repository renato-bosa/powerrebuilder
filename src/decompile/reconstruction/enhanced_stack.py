"""Enhanced stack management system with state tracking and recovery.

This module provides advanced stack management capabilities for P-code reconstruction,
including state snapshots, pattern-based recovery, and context-aware placeholder generation.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class StackValueType(Enum):
    """Types of values that can be on the stack."""

    INTEGER = auto()
    LONG = auto()
    REAL = auto()
    DOUBLE = auto()
    DECIMAL = auto()
    STRING = auto()
    BOOLEAN = auto()
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    BLOB = auto()
    OBJECT = auto()
    ARRAY = auto()
    NULL = auto()
    UNKNOWN = auto()


class StackValueOrigin(Enum):
    """Origin of a stack value for tracking purposes."""

    CONSTANT = auto()  # Pushed constant value
    VARIABLE = auto()  # Local/global variable
    FIELD = auto()  # Object field
    METHOD_RESULT = auto()  # Function/method return value
    EXPRESSION = auto()  # Result of an expression
    PLACEHOLDER = auto()  # Generated placeholder
    RECOVERED = auto()  # Recovered from context
    UNKNOWN = auto()  # Unknown origin


@dataclass
class StackValue:
    """Enhanced stack value with type information and metadata."""

    expression: str
    value_type: StackValueType = StackValueType.UNKNOWN
    origin: StackValueOrigin = StackValueOrigin.UNKNOWN
    confidence: float = 1.0  # Confidence in the value (0.0-1.0)
    is_lvalue: bool = False
    source_offset: int | None = None  # P-code offset where value originated
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"StackValue({self.expression}, {self.value_type.name}, conf={self.confidence:.2f})"

    def with_confidence(self, confidence: float) -> "StackValue":
        """Return a copy with updated confidence."""
        return StackValue(
            expression=self.expression,
            value_type=self.value_type,
            origin=self.origin,
            confidence=confidence,
            is_lvalue=self.is_lvalue,
            source_offset=self.source_offset,
            metadata=self.metadata.copy(),
        )


@dataclass
class StackSnapshot:
    """Snapshot of stack state at a specific point."""

    offset: int
    stack: list[StackValue] = field(default_factory=list)
    locals_context: dict[int, str] = field(default_factory=dict)
    timestamp: str = ""

    def copy(self) -> "StackSnapshot":
        """Create a deep copy of this snapshot."""
        return StackSnapshot(
            offset=self.offset,
            stack=[
                StackValue(
                    expression=sv.expression,
                    value_type=sv.value_type,
                    origin=sv.origin,
                    confidence=sv.confidence,
                    is_lvalue=sv.is_lvalue,
                    source_offset=sv.source_offset,
                    metadata=sv.metadata.copy(),
                )
                for sv in self.stack
            ],
            locals_context=self.locals_context.copy(),
            timestamp=self.timestamp,
        )


class StackRecoveryStrategy(Enum):
    """Strategies for recovering from stack underflow."""

    PLACEHOLDER = auto()  # Generate placeholder values
    TYPE_INFERENCE = auto()  # Infer types from context
    PATTERN_MATCH = auto()  # Use pattern matching
    SNAPSHOT_REVERT = auto()  # Revert to previous snapshot
    MINIMAL_RECOVERY = auto()  # Minimal recovery to continue


class EnhancedStackManager:
    """Advanced stack manager with recovery capabilities."""

    def __init__(self) -> None:
        """Initialize the enhanced stack manager."""
        self.stack: list[StackValue] = []
        self.snapshots: list[StackSnapshot] = []
        self.locals: dict[int, str] = {}
        self.strings: dict[int, str] = {}
        self.methods: dict[int, str] = {}
        self.fields: dict[int, str] = {}

        # Recovery settings
        self.auto_recover = True
        self.max_snapshots = 20
        self.recovery_strategy = StackRecoveryStrategy.PLACEHOLDER

        # Statistics
        self.underflow_count = 0
        self.recovery_count = 0

        # Initialize with common PowerBuilder symbols
        self._init_common_symbols()

    def _init_common_symbols(self) -> None:
        """Initialize common PowerBuilder symbols."""
        self.locals[0] = "this"
        self.locals[1] = "return_value"
        self.locals[2] = "temp"

        # Common field names
        self.fields[0] = "text"
        self.fields[1] = "visible"
        self.fields[2] = "enabled"
        self.fields[3] = "tag"
        self.fields[4] = "width"
        self.fields[5] = "height"

        # Common method names
        self.methods[0] = "create"
        self.methods[1] = "destroy"
        self.methods[2] = "open"
        self.methods[3] = "close"
        self.methods[4] = "post"
        self.methods[5] = "trigger"

    def create_snapshot(self, offset: int, label: str = "") -> StackSnapshot:
        """Create a snapshot of current stack state."""
        snapshot = StackSnapshot(
            offset=offset,
            stack=list(self.stack),  # Shallow copy
            locals_context=self.locals.copy(),
            timestamp=label,
        )

        self.snapshots.append(snapshot)

        # Limit number of snapshots
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

        logger.debug(
            "Created stack snapshot at offset 0x%04x: %d items", offset, len(self.stack)
        )
        return snapshot

    def restore_snapshot(self, snapshot: StackSnapshot) -> None:
        """Restore stack state from a snapshot."""
        self.stack = list(snapshot.stack)
        self.locals.update(snapshot.locals_context)
        logger.info("Restored stack snapshot from offset 0x%04x", snapshot.offset)

    def push(self, value: StackValue) -> None:
        """Push a value onto the stack."""
        self.stack.append(value)
        logger.debug("Pushed %s (stack depth: %d)", value, len(self.stack))

    def pop(self, expected_type: StackValueType | None = None) -> StackValue | None:
        """Pop a value from the stack with optional type checking."""
        if not self.stack:
            self.underflow_count += 1
            if self.auto_recover:
                return self._recover_missing_value(expected_type)
            return None

        value = self.stack.pop()
        logger.debug("Popped %s (stack depth: %d)", value, len(self.stack))

        # Type checking
        if expected_type and value.value_type not in (
            expected_type,
            StackValueType.UNKNOWN,
        ):
            logger.warning(
                "Type mismatch: expected %s, got %s for value '%s'",
                expected_type.name,
                value.value_type.name,
                value.expression,
            )
            # Optionally adjust confidence
            value = value.with_confidence(value.confidence * 0.8)

        return value

    def peek(self, depth: int = 0) -> StackValue | None:
        """Peek at a stack value without popping it."""
        if len(self.stack) <= depth:
            return None
        return self.stack[-(depth + 1)]

    def depth(self) -> int:
        """Get current stack depth."""
        return len(self.stack)

    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return len(self.stack) == 0

    def clear(self) -> None:
        """Clear the stack."""
        self.stack.clear()
        logger.debug("Cleared stack")

    def _recover_missing_value(
        self, expected_type: StackValueType | None = None
    ) -> StackValue:
        """Recover from stack underflow by generating appropriate placeholder."""
        self.recovery_count += 1

        if expected_type:
            placeholder = self._generate_typed_placeholder(expected_type)
        else:
            placeholder = self._generate_generic_placeholder()

        logger.warning(
            "Stack underflow #%d - generated placeholder: %s",
            self.underflow_count,
            placeholder,
        )

        return placeholder

    def _generate_typed_placeholder(self, value_type: StackValueType) -> StackValue:
        """Generate a type-specific placeholder value."""
        placeholders = {
            StackValueType.INTEGER: ("0", "0"),
            StackValueType.LONG: ("0", "0L"),
            StackValueType.REAL: ("0.0", "0.0"),
            StackValueType.DOUBLE: ("0.0", "0.0D"),
            StackValueType.DECIMAL: ("0", "0.00"),
            StackValueType.STRING: ('""', '""'),
            StackValueType.BOOLEAN: ("FALSE", "FALSE"),
            StackValueType.DATE: ("Date(1900-01-01)", "Date(1900-01-01)"),
            StackValueType.TIME: ("Time(00:00:00)", "Time(00:00:00)"),
            StackValueType.DATETIME: (
                "DateTime(1900-01-01 00:00:00)",
                "DateTime(1900-01-01 00:00:00)",
            ),
            StackValueType.BLOB: ("Blob('')", "Blob('')"),
            StackValueType.OBJECT: ("", "/* missing object */"),
            StackValueType.ARRAY: ("", "/* missing array */"),
            StackValueType.NULL: ("", "/* null */"),
        }

        default_val, pb_val = placeholders.get(value_type, ("?", "/* unknown */"))

        return StackValue(
            expression=pb_val,
            value_type=value_type,
            origin=StackValueOrigin.PLACEHOLDER,
            confidence=0.1,  # Low confidence for placeholders
            metadata={
                "recovery_reason": "stack_underflow",
                "recovery_count": self.recovery_count,
            },
        )

    def _generate_generic_placeholder(self) -> StackValue:
        """Generate a generic placeholder when type is unknown."""
        return StackValue(
            expression=f"/* missing_value_{self.recovery_count} */",
            value_type=StackValueType.UNKNOWN,
            origin=StackValueOrigin.PLACEHOLDER,
            confidence=0.1,
            metadata={
                "recovery_reason": "stack_underflow",
                "recovery_count": self.recovery_count,
            },
        )

    def validate_stack_depth(self, required: int, operation: str) -> bool:
        """Validate that stack has enough items for an operation."""
        if len(self.stack) < required:
            logger.warning(
                "Stack validation failed for %s: required %d items, have %d",
                operation,
                required,
                len(self.stack),
            )
            return False
        return True

    def pop_multiple(
        self, count: int, expected_types: list[StackValueType] | None = None
    ) -> list[StackValue]:
        """Pop multiple values from the stack."""
        if not self.validate_stack_depth(count, f"pop_multiple({count})"):
            # Try to recover
            values = []
            for i in range(count):
                expected_type = (
                    expected_types[i]
                    if expected_types and i < len(expected_types)
                    else None
                )
                if i < len(self.stack):
                    values.append(self.stack.pop())
                else:
                    values.append(self._recover_missing_value(expected_type))
            return list(reversed(values))  # Maintain order

        values = []
        for i in range(count):
            expected_type = (
                expected_types[i]
                if expected_types and i < len(expected_types)
                else None
            )
            values.append(self.pop(expected_type))

        return list(reversed(values))  # Return in original push order

    def debug_state(self) -> str:
        """Get debug representation of current stack state."""
        lines = [f"Stack (depth {len(self.stack)}):"]
        for i, value in enumerate(reversed(self.stack)):
            lines.append(f"  [{len(self.stack) - i - 1}] {value}")

        lines.append(f"Snapshots: {len(self.snapshots)}")
        lines.append(f"Underflows: {self.underflow_count}")
        lines.append(f"Recoveries: {self.recovery_count}")

        return "\n".join(lines)

    def get_statistics(self) -> dict[str, Any]:
        """Get stack management statistics."""
        return {
            "current_depth": len(self.stack),
            "max_snapshots": len(self.snapshots),
            "underflow_count": self.underflow_count,
            "recovery_count": self.recovery_count,
            "recovery_strategy": self.recovery_strategy.name,
            "auto_recover": self.auto_recover,
        }
