"""PowerBuilder type handling for parser."""

from enum import Enum

from parse.visitors.pb_function import PBType


class ParameterDirection(Enum):
    """Parameter direction enumeration."""

    IN = "in"
    OUT = "out"
    REF = "ref"
    READONLY = "readonly"


def create_pb_type(
    name: str, is_array: bool = False, array_bounds: list[int] | None = None
) -> PBType:
    """Create a PBType instance."""
    return PBType(
        name=name,
        is_array=is_array,
        array_bounds=array_bounds or [],
        is_custom=True,  # Can be refined based on name
    )


def parse_pb_type(type_str: str) -> PBType:
    """Parse a type string into a PBType."""
    # Basic implementation
    is_array = "[" in type_str
    if is_array:
        # Extract base type and dimensions
        base_type = type_str.split("[")[0].strip()
        return create_pb_type(base_type, is_array=True)
    return create_pb_type(type_str)
