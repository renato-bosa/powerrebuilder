"""String utility functions."""

import re


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Args:
            name: camelCase string

    Returns:
            snake_case string
    """
    # Insert underscore before uppercase letters (except first)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters followed by lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase.

    Args:
            name: snake_case string

    Returns:
            camelCase string
    """
    components = name.split("_")
    # Capitalize all components except the first
    return components[0] + "".join(x.title() for x in components[1:])


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length, adding suffix if truncated.

    Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated

    Returns:
            Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def pluralize(word: str, count: int) -> str:
    """Simple pluralization (adds 's' if count != 1).

    Args:
            word: Word to pluralize
            count: Count for pluralization

    Returns:
            Pluralized word
    """
    return word if count == 1 else f"{word}s"
