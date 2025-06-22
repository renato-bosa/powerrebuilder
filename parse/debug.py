"""Debug support for PowerBuilder and Pseudocode transpiler.

This module provides debugging features including:
- Variable inspection
- Step-by-step execution
- Call stack tracking
- Breakpoint management
- Debug output formatting
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any



logger = logging.getLogger(__name__)

class DebugLevel(Enum):
    """Debug output levels."""

    NONE = auto()
    BASIC = auto()
    DETAILED = auto()
    VERBOSE = auto()


@dataclass
class DebugState:
    """Debug state tracking."""

    enabled: bool = False
    level: DebugLevel = DebugLevel.NONE
    step_mode: bool = False
    break_on_error: bool = True
    output_indent: int = 0
    current_line: int = 0
    current_file: str = ""
    call_stack: list[str] = field(default_factory=list)
    breakpoints: set[str] = field(default_factory=set)  # Format: "file:line"
    variables: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None

    def __post_init__(self) -> None:


        

        """Initialize debug state."""
        self.start_time = datetime.now()

    def format_location(self) -> str:


        

        """Format current location for output."""
        return f"{self.current_file}:{self.current_line}"

    def add_breakpoint(self, file: str, line: int) -> None:


        

        """Add a breakpoint."""
        self.breakpoints.add(f"{file}:{line}")

    def remove_breakpoint(self, file: str, line: int) -> None:


        

        """Remove a breakpoint."""
        self.breakpoints.discard(f"{file}:{line}")

    def should_break(self) -> bool:


        

        """Check if should break at current location."""
        return self.enabled and (
            self.step_mode
            or f"{self.current_file}:{self.current_line}" in self.breakpoints
        )

    def push_call(self, func_name: str) -> None:


        

        """Push function call to stack."""
        self.call_stack.append(func_name)

    def pop_call(self) -> str | None:


        

        """Pop function call from stack."""
        return self.call_stack.pop() if self.call_stack else None

    def update_variable(self, name: str, value: Any) -> None:


        

        """Update variable value."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any | None:


        

        """Get variable value."""
        return self.variables.get(name)

    def clear(self) -> None:


        

        """Clear debug state."""
        self.call_stack.clear()
        self.variables.clear()
        self.start_time = datetime.now()


class DebugOutput:
    """Debug output formatting."""

    def __init__(self, state: DebugState) -> None:
        

        self.state = state
        self.logger = logging.getLogger("debug")

    def output(self, message: str) -> None:


        

        """Output debug message with indentation."""
        if not self.state.enabled:
            return
        indent = " " * self.state.output_indent
        self.logger.debug("%s%s", indent, message)

    def output_variables(self, variables: list[str] | None = None) -> None:


        

        """Output current variable values."""
        if not self.state.enabled:
            return
        if variables is None:
            variables = sorted(self.state.variables.keys())
        for var in variables:
            value = self.state.get_variable(var)
            self.output(f"{var} = {self._format_value(value)}")

    def output_call_stack(self) -> None:


        

        """Output current call stack."""
        if not self.state.enabled:
            return
        self.output("Call stack:")
        for i, func in enumerate(reversed(self.state.call_stack)):
            self.output(f"{i}: {func}")

    def output_location(self) -> None:


        

        """Output current location."""
        if not self.state.enabled:
            return
        self.output(f"At {self.state.format_location()}")

    def increase_indent(self) -> None:


        

        """Increase output indentation."""
        self.state.output_indent += 2

    def decrease_indent(self) -> None:


        

        """Decrease output indentation."""
        self.state.output_indent = max(0, self.state.output_indent - 2)

    def _format_value(self, value: Any) -> str:


        

        """Format value for output."""
        try:
            return json.dumps(value)
        except Exception as e:
            return str(value)


@dataclass
class Debugger:
    """Main debugger class."""

    state: DebugState = field(default_factory=DebugState)
    output: DebugOutput = field(init=False)

    def __post_init__(self) -> None:
        

        self.output = DebugOutput(self.state)

    def enable(self, level: DebugLevel = DebugLevel.BASIC) -> None:


        

        """Enable debugging."""
        self.state.enabled = True
        self.state.level = level
        self.state.clear()

    def disable(self) -> None:


        

        """Disable debugging."""
        self.state.enabled = False
        self.state.level = DebugLevel.NONE

    def step(self, file: str, line: int) -> None:


        

        """Step to next line."""
        if not self.state.enabled:
            return
        self.state.current_file = file
        self.state.current_line = line
        if self.state.should_break():
            self.output_debug_info()

    def enter_function(self, func_name: str) -> None:


        

        """Enter function."""
        if not self.state.enabled:
            return
        self.state.push_call(func_name)
        self.output.increase_indent()
        if self.state.level >= DebugLevel.DETAILED:
            self.output.output(f"Entering {func_name}")

    def exit_function(self) -> None:


        

        """Exit function."""
        if not self.state.enabled:
            return
        func_name = self.state.pop_call()
        self.output.decrease_indent()
        if self.state.level >= DebugLevel.DETAILED and func_name:
            self.output.output(f"Exiting {func_name}")

    def output_debug_info(self) -> None:


        

        """Output debug information at break."""
        self.output.output_location()
        if self.state.level >= DebugLevel.DETAILED:
            self.output.output_call_stack()
        if self.state.level >= DebugLevel.VERBOSE:
            self.output.output_variables()

    def handle_error(self, error: Exception) -> None:


        

        """Handle error during debugging."""
        if not self.state.enabled:
            return
        self.output.output(f"Error: {error}")
        if self.state.break_on_error:
            self.output_debug_info()