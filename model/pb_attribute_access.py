"""PowerBuilder attribute access functionality."""

from dataclasses import dataclass, field


@dataclass
class PBAttributeAccess:
    """Represents access to an attribute or field of an object."""

    name: str
    identifier: str
    array_info: list[str] = field(default_factory=list)
    is_unchecked: bool = False

    @property
    def is_array_access(self) -> bool:
        """Check if this is an array access."""
        return bool(self.array_info)

    def __str__(self) -> str:
        """String representation of the attribute access."""
        result = self.identifier
        if self.array_info:
            for idx in self.array_info:
                result += f"[{idx}]"
        return result
