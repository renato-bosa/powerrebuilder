"""Interactive REPL for PowerBuilder and Pseudocode transpiler.

This module provides interactive features including:
- REPL interface
- Command history
- Code completion
- Help system
- Error reporting
"""

import atexit
import code
import contextlib
import json
import logging
import os
import readline
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Never

from .debug import Debugger, DebugLevel

logger = logging.getLogger(__name__)

class CommandType(Enum):
    """Command types for REPL."""

    HELP = auto()
    DEBUG = auto()
    HISTORY = auto()
    CLEAR = auto()
    SAVE = auto()
    LOAD = auto()
    QUIT = auto()
    EXEC = auto()


@dataclass
class Command:
    """REPL command."""

    type: CommandType
    name: str
    help: str
    handler: Callable[["REPL", list[str]], None]


@dataclass
class REPLState:
    """REPL state tracking."""

    history: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    history_file: str = os.path.expanduser("~/.pbhistory")
    start_time: datetime | None = None
    multiline_buffer: list[str] = field(default_factory=list)
    in_multiline: bool = False

    def __post_init__(self) -> None:




        """Initialize REPL state."""
        self.start_time = datetime.now()
        self.load_history()

    def load_history(self) -> None:




        """Load command history from file."""
        try:
            if os.path.exists(self.history_file):
                readline.read_history_file(self.history_file)
        except Exception:
            logger.debug("Generic exception caught")
            pass

    def save_history(self) -> None:




        """Save command history to file."""
        with contextlib.suppress(Exception):
            readline.write_history_file(self.history_file)

    def add_to_history(self, line: str) -> None:




        """Add line to history."""
        self.history.append(line)

    def clear_history(self) -> None:




        """Clear command history."""
        self.history.clear()
        with contextlib.suppress(Exception):
            os.remove(self.history_file)

    def update_variable(self, name: str, value: Any) -> None:




        """Update variable value."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any | None:




        """Get variable value."""
        return self.variables.get(name)

    def clear_variables(self) -> None:




        """Clear all variables."""
        self.variables.clear()


class REPL:
    """Interactive REPL implementation."""

    PROMPT = "pb> "
    MULTILINE_PROMPT = "... "

    def __init__(self, debugger: Debugger | None = None) -> None:


        self.state = REPLState()
        self.debugger = debugger or Debugger()
        self.commands = self._create_commands()
        self.interpreter = code.InteractiveInterpreter(self.state.variables)

        # Set up readline
        readline.parse_and_bind("tab: complete")
        atexit.register(self.state.save_history)

    def _create_commands(self) -> dict[str, Command]:




        """Create command handlers."""
        return {
            "help": Command(
                type=CommandType.HELP, name="help", help="Show help message", handler=self._handle_help, ), "debug": Command(
                type=CommandType.DEBUG, name="debug", help="Toggle debug mode", handler=self._handle_debug, ), "history": Command(
                type=CommandType.HISTORY, name="history", help="Show command history", handler=self._handle_history, ), "clear": Command(
                type=CommandType.CLEAR, name="clear", help="Clear screen", handler=self._handle_clear, ), "save": Command(
                type=CommandType.SAVE, name="save", help="Save variables to file", handler=self._handle_save, ), "load": Command(
                type=CommandType.LOAD, name="load", help="Load variables from file", handler=self._handle_load, ), "quit": Command(
                type=CommandType.QUIT, name="quit", help="Exit REPL", handler=self._handle_quit, ), }

    def run(self) -> None:




        """Run REPL loop."""
        self._print_welcome()
        while True:
            try:
                if self.state.in_multiline:
                    line = input(self.MULTILINE_PROMPT)
                else:
                    line = input(self.PROMPT)

                if not line.strip():
                    if self.state.in_multiline:
                        self._handle_multiline_end()
                    continue

                self.state.add_to_history(line)

                if line.startswith(":"):
                    self._handle_command(line[1:])
                else:
                    self._handle_code(line)

            except KeyboardInterrupt:
                self.state.in_multiline = False
                self.state.multiline_buffer.clear()
            except EOFError:
                break
            except Exception as e:
                if self.debugger.state.enabled:
                    self.debugger.handle_error(e)

    def _print_welcome(self) -> None:




        """Print welcome message."""

    def _handle_command(self, cmd_line: str) -> None:




        """Handle REPL command."""
        parts = cmd_line.strip().split()
        if not parts:
            return

        cmd_name = parts[0]
        args = parts[1:]

        if cmd_name in self.commands:
            self.commands[cmd_name].handler(self, args)
        else:
            pass

    def _handle_code(self, line: str) -> None:




        """Handle code input."""
        if line.endswith(":"):
            self.state.in_multiline = True
            self.state.multiline_buffer.append(line)
            return

        if self.state.in_multiline:
            self.state.multiline_buffer.append(line)
        else:
            self._execute_code(line)

    def _handle_multiline_end(self) -> None:




        """Handle end of multiline input."""
        if not self.state.multiline_buffer:
            return

        code = "\n".join(self.state.multiline_buffer)
        self.state.multiline_buffer.clear()
        self.state.in_multiline = False
        self._execute_code(code)

    def _execute_code(self, code: str) -> None:




        """Execute code in interpreter."""
        try:
            if self.debugger.state.enabled:
                self.debugger.step("<repl>", len(self.state.history))
            self.interpreter.runsource(code)
        except Exception as e:
            if self.debugger.state.enabled:
                self.debugger.handle_error(e)

    def _handle_help(self, args: list[str]) -> None:




        """Handle help command."""
        if not args:
            for _cmd in sorted(self.commands.values(), key=lambda c: c.name):
                pass
        else:
            cmd_name = args[0]
            if cmd_name in self.commands:
                self.commands[cmd_name]
            else:
                pass

    def _handle_debug(self, args: list[str]) -> None:




        """Handle debug command."""
        if not args:
            if self.debugger.state.enabled:
                self.debugger.disable()
            else:
                self.debugger.enable()
            return

        level_name = args[0].upper()
        try:
            level = DebugLevel[level_name]
            self.debugger.enable(level)
        except KeyError:
            pass

    def _handle_history(self, args: list[str]) -> None:




        """Handle history command."""
        if not args:
            for _i, _cmd in enumerate(self.state.history, 1):
                pass
        elif args[0] == "clear":
            self.state.clear_history()
        else:
            pass

    def _handle_clear(self, args: list[str]) -> None:




        """Handle clear command."""
        os.system("cls" if os.name == "nt" else "clear")

    def _handle_save(self, args: list[str]) -> None:




        """Handle save command."""
        if not args:
            return

        filename = args[0]
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.state.variables, f, indent=2)
        except Exception:
            logger.debug("Generic exception caught")
            pass

    def _handle_load(self, args: list[str]) -> None:




        """Handle load command."""
        if not args:
            return

        filename = args[0]
        try:
            with open(filename, encoding="utf-8") as f:
                variables = json.load(f)
            self.state.variables.update(variables)
        except Exception:
            logger.debug("Generic exception caught")
            pass

    def _handle_quit(self, args: list[str]) -> Never:




        """Handle quit command."""
        raise EOFError
