from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FunctionBlock:
    name: str
    instructions: list[tuple[int, str, str]]  # (address, opcode, operand)
    pseudocode: list[str]  # populated later
