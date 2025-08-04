"""Collection utility functions."""

from typing import TypeVar

T = TypeVar("T")


def chunk_list[T](lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def find_duplicates[T](lst: list[T]) -> list[T]:
    """Find duplicate items in a list.

    Args:
        lst: List to check for duplicates

    Returns:
        List of duplicate items
    """
    seen = set()
    duplicates = []
    for item in lst:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return duplicates


def filter_dict[T](d: dict[str, T], keys: list[str]) -> dict[str, T]:
    """Filter dictionary to only include specified keys.

    Args:
        d: Dictionary to filter
        keys: Keys to include

    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in d.items() if k in keys}


def merge_dicts[T](*dicts: dict[str, T]) -> dict[str, T]:
    """Merge multiple dictionaries, later values override earlier ones.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
