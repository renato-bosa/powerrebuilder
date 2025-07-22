"""Custom Jinja2 filters for code generation."""

import logging
import re

logger = logging.getLogger(__name__)


def indent_filter(text: str, width: int = 4, first: bool = False) -> str:
    """Indent each line of text.

    Args:
        text: Text to indent
        width: Number of spaces to indent
        first: Whether to indent the first line

    Returns:
        Indented text
    """
    if not text:
        return text

    lines = text.split("\n")
    indent = " " * width

    if first:
        return "\n".join(indent + line if line else line for line in lines)
    # Don't indent first line
    result = []
    for i, line in enumerate(lines):
        if i == 0:
            result.append(line)
        else:
            result.append(indent + line if line else line)
    return "\n".join(result)


def indent_block_filter(text: str, width: int = 4) -> str:
    """Indent a block of text, preserving internal indentation.

    Args:
        text: Text block to indent
        width: Number of spaces to indent

    Returns:
        Indented text block
    """
    if not text:
        return text

    lines = text.split("\n")
    indent = " " * width
    return "\n".join(indent + line if line else line for line in lines)


def indent_nested_filter(text: str, level: int = 1, width: int = 4) -> str:
    """Indent text with nested level support.

    Args:
        text: Text to indent
        level: Nesting level
        width: Spaces per level

    Returns:
        Indented text
    """
    if not text:
        return text

    total_indent = " " * (level * width)
    lines = text.split("\n")
    return "\n".join(total_indent + line if line else line for line in lines)


def dedent_filter(text: str) -> str:
    """Remove common leading whitespace from all lines.

    This is useful for cleaning up multi-line strings in templates.

    Args:
        text: Text to dedent

    Returns:
        Dedented text
    """
    lines = text.split("\n")

    # Find minimum indentation (excluding empty lines)
    min_indent = float("inf")
    for line in lines:
        if line.strip():
            leading_spaces = len(line) - len(line.lstrip())
            min_indent = min(min_indent, leading_spaces)

    if min_indent == float("inf") or min_indent == 0:
        return text

    # Remove common indentation
    dedented_lines = []
    for line in lines:
        if line.strip():
            dedented_lines.append(line[min_indent:])
        else:
            dedented_lines.append(line)

    return "\n".join(dedented_lines)


def dedent_wrapper(text: str, _width: int | None = None) -> str:
    """Wrapper for dedent filter that accepts optional width parameter.

    The width parameter is ignored but accepted for template compatibility.
    """
    return dedent_filter(text)


def snake_case(text: str) -> str:
    """Convert text to snake_case.

    Args:
        text: Text to convert

    Returns:
        snake_case version of the text
    """
    # Replace spaces, hyphens with underscores
    text = re.sub(r"[\s\-]+", "_", text)
    # Insert underscores before capital letters
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    # Convert to lowercase and remove duplicate underscores
    return re.sub(r"_+", "_", text.lower()).strip("_")


def pascal_case(text: str) -> str:
    """Convert text to PascalCase.

    Args:
        text: Text to convert

    Returns:
        PascalCase version of the text
    """
    # Split by spaces, hyphens, underscores
    parts = re.split(r"[\s\-_]+", text)
    # Capitalize each part
    return "".join(part.capitalize() for part in parts if part)


def python_type(pb_type: str) -> str:
    """Convert PowerBuilder type to Python type.

    Args:
        pb_type: PowerBuilder type string

    Returns:
        Python type string
    """
    if not pb_type:
        return "Any"

    pb_type_lower = pb_type.lower()

    type_map = {
        "integer": "int",
        "long": "int",
        "decimal": "float",
        "real": "float",
        "double": "float",
        "string": "str",
        "char": "str",
        "boolean": "bool",
        "bool": "bool",
        "date": "datetime",
        "datetime": "datetime",
        "time": "datetime",
        "blob": "bytes",
        "any": "Any",
    }

    return type_map.get(pb_type_lower, "Any")


def humanize(text: str) -> str:
    """Convert function/method name to human readable form.

    Args:
        text: Text to humanize

    Returns:
        Human readable version
    """
    # Handle of_ prefix
    text = text.removeprefix("of_")
    # Split by underscores and capitalize
    parts = text.split("_")
    return " ".join(part.capitalize() for part in parts)


def register_filters(env) -> None:
    """Register all custom filters with a Jinja2 environment.

    Args:
        env: Jinja2 Environment instance
    """
    env.filters["indent"] = indent_filter
    env.filters["indent_block"] = indent_block_filter
    env.filters["indent_nested"] = indent_nested_filter
    env.filters["dedent"] = dedent_wrapper
    env.filters["snake_case"] = snake_case
    env.filters["pascal_case"] = pascal_case
    env.filters["python_type"] = python_type
    env.filters["humanize"] = humanize
