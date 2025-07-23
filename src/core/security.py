"""Security utilities for path validation and safe file operations."""

import os
import re
from pathlib import Path

from src.core.exceptions import SimeFinchError


class SecurityError(SimeFinchError):
    """Base exception for security-related errors."""


class PathTraversalError(SecurityError):
    """Raised when a path traversal attempt is detected."""


class PathValidator:
    """Validates file paths to prevent directory traversal attacks."""

    # Patterns that indicate potential path traversal
    DANGEROUS_PATTERNS = [
        r"\.\./",  # Parent directory reference
        r"\.\.\\",  # Windows parent directory
        r"\.\.(?:/|\\|$)",  # Parent directory at end
        r"^~",  # Home directory expansion
        r"^\$",  # Environment variable
        # Note: Absolute paths are allowed if they're within base_dir
        # r'^/',  # Absolute path on Unix
        # r'^[A-Za-z]:',  # Absolute path on Windows
        r"\\\\",  # UNC path
    ]

    # Characters that should not appear in safe filenames
    UNSAFE_CHARS = set('<>:"|?*\0')

    @classmethod
    def validate_path(cls, path: str | Path, base_dir: str | Path) -> Path:
        """Validate a path is safe and within the base directory.

        Args:
        path: The path to validate
        base_dir: The base directory that paths must be within

        Returns:
        The validated absolute path

        Raises:
        PathTraversalError: If the path is unsafe or outside base_dir
        """
        # Convert to Path objects
        path = Path(path)
        base_dir = Path(base_dir).resolve()

        # Check for dangerous patterns
        path_str = str(path)
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                raise PathTraversalError(f"Dangerous path pattern detected: {path_str}")

        # Check for unsafe characters
        for part in path.parts:
            if any(char in part for char in cls.UNSAFE_CHARS):
                raise PathTraversalError(f"Unsafe characters in path component: {part}")

        # Resolve the full path
        try:
            if path.is_absolute():
                full_path = path.resolve()
            else:
                full_path = (base_dir / path).resolve()
        except OSError as e:
            raise PathTraversalError(f"Cannot resolve path: {e}") from e
        except RuntimeError as e:
            raise PathTraversalError(f"Path resolution failed: {e}") from e

        # Ensure the resolved path is within base_dir
        try:
            full_path.relative_to(base_dir)
        except ValueError:
            raise PathTraversalError(
                f"Path {full_path} is outside base directory {base_dir}"
            )

        return full_path

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate a filename is safe.

        Args:
        filename: The filename to validate

        Returns:
        The validated filename

        Raises:
        PathTraversalError: If the filename is unsafe
        """
        # Strip any path components
        filename = os.path.basename(filename)

        # Check for empty or special names
        if not filename or filename in (".", ".."):
            raise PathTraversalError(f"Invalid filename: {filename}")

        # Check for unsafe characters
        if any(char in filename for char in cls.UNSAFE_CHARS):
            raise PathTraversalError(f"Unsafe characters in filename: {filename}")

        # Check for reserved Windows names
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        name_without_ext = filename.split(".")[0].upper()
        if name_without_ext in reserved_names:
            raise PathTraversalError(f"Reserved filename: {filename}")

        return filename


def safe_join_path(base_dir: str | Path, *parts: str) -> Path:
    """Safely join path components and validate the result.

    Args:
    base_dir: The base directory
    *parts: Path components to join

    Returns:
    The validated joined path

    Raises:
    PathTraversalError: If the resulting path is unsafe
    """
    base_dir = Path(base_dir).resolve()

    # Validate each part
    safe_parts = []
    for part in parts:
        if not part:
            continue
        # Remove any leading/trailing separators
        part = part.strip("/\\")
        if part:
            safe_parts.append(PathValidator.validate_filename(part))

    # Join and validate the full path
    if safe_parts:
        path = Path(*safe_parts)
        return PathValidator.validate_path(path, base_dir)
    return base_dir


def safe_create_directory(path: str | Path, base_dir: str | Path) -> Path:
    """Safely create a directory after validating the path.

    Args:
    path: The directory path to create
    base_dir: The base directory that paths must be within

    Returns:
    The created directory path

    Raises:
    PathTraversalError: If the path is unsafe
    OSError: If directory creation fails
    """
    safe_path = PathValidator.validate_path(path, base_dir)
    safe_path.mkdir(parents=True, exist_ok=True)
    return safe_path


def safe_write_file(
    path: str | Path,
    content: str | bytes,
    base_dir: str | Path,
    mode: str = "w",
) -> Path:
    """Safely write content to a file after validating the path.

    Args:
    path: The file path to write to
    content: The content to write
    base_dir: The base directory that paths must be within
    mode: The file open mode

    Returns:
    The path of the written file

    Raises:
    PathTraversalError: If the path is unsafe
    OSError: If file writing fails
    """
    safe_path = PathValidator.validate_path(path, base_dir)

    # Ensure parent directory exists
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    if isinstance(content, bytes) and "b" not in mode:
        mode += "b"

    with safe_path.open(mode) as f:
        f.write(content)

    return safe_path


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize a filename by replacing unsafe characters.

    Args:
    filename: The filename to sanitize
    replacement: Character to replace unsafe characters with

    Returns:
    The sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)

    # Replace unsafe characters
    sanitized = ""
    for char in filename:
        if char in PathValidator.UNSAFE_CHARS or ord(char) < 32:
            sanitized += replacement
        else:
            sanitized += char

    # Handle reserved names
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    name_parts = sanitized.split(".")
    if name_parts[0].upper() in reserved_names:
        name_parts[0] = f"{name_parts[0]}{replacement}"
        sanitized = ".".join(name_parts)

    # Ensure it's not empty
    if not sanitized or sanitized == ".":
        sanitized = "unnamed"

    return sanitized
