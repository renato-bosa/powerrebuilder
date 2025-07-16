"""Core utilities with no domain dependencies.

This module contains utilities that can be used anywhere without creating
circular dependencies. Domain-specific utilities should be in their own modules.
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize filename for filesystem compatibility.
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid characters with
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove trailing dots and spaces (Windows)
    sanitized = sanitized.rstrip(". ")
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def calculate_hash(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """Calculate hash of data.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of hash
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def ensure_path(path: Union[str, Path], create_parents: bool = True) -> Path:
    """Ensure path exists and return as Path object.
    
    Args:
        path: Path to ensure
        create_parents: Whether to create parent directories
        
    Returns:
        Path object
    """
    path = Path(path)
    
    if path.is_file():
        parent = path.parent
    else:
        parent = path
    
    if create_parents and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    
    return path


def normalize_line_endings(text: str, target: str = "\n") -> str:
    """Normalize line endings in text.
    
    Args:
        text: Text to normalize
        target: Target line ending
        
    Returns:
        Text with normalized line endings
    """
    # Replace all types of line endings
    text = text.replace("\r\n", "\n")  # Windows
    text = text.replace("\r", "\n")    # Old Mac
    
    if target != "\n":
        text = text.replace("\n", target)
    
    return text


def split_qualified_name(name: str) -> List[str]:
    """Split qualified name into parts.
    
    Args:
        name: Qualified name (e.g., "namespace.class.member")
        
    Returns:
        List of name parts
    """
    return name.split(".")


def join_qualified_name(parts: List[str]) -> str:
    """Join name parts into qualified name.
    
    Args:
        parts: Name parts
        
    Returns:
        Qualified name
    """
    return ".".join(parts)


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase.
    
    Args:
        snake_str: Snake case string
        
    Returns:
        Camel case string
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase.
    
    Args:
        snake_str: Snake case string
        
    Returns:
        Pascal case string
    """
    return ''.join(x.title() for x in snake_str.split('_'))


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase or PascalCase to snake_case.
    
    Args:
        camel_str: Camel or Pascal case string
        
    Returns:
        Snake case string
    """
    # Insert underscore before uppercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def indent_text(text: str, indent: int = 4, indent_char: str = " ") -> str:
    """Indent text by specified amount.
    
    Args:
        text: Text to indent
        indent: Number of indent characters
        indent_char: Character to use for indentation
        
    Returns:
        Indented text
    """
    prefix = indent_char * indent
    lines = text.splitlines(True)
    return ''.join(prefix + line if line.strip() else line for line in lines)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    if max_length <= len(suffix):
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.
    
    Args:
        dictionary: Dictionary to search
        key_path: Dot-separated key path (e.g., "a.b.c")
        default: Default value if not found
        
    Returns:
        Value at key path or default
    """
    keys = key_path.split(".")
    value = dictionary
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def safe_set(dictionary: Dict[str, Any], key_path: str, value: Any) -> None:
    """Safely set nested dictionary value.
    
    Args:
        dictionary: Dictionary to update
        key_path: Dot-separated key path (e.g., "a.b.c")
        value: Value to set
    """
    keys = key_path.split(".")
    current = dictionary
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def merge_dicts(base: Dict[str, Any], *updates: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
    """Merge dictionaries.
    
    Args:
        base: Base dictionary
        *updates: Dictionaries to merge into base
        deep: Whether to do deep merge
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for update in updates:
        if deep:
            _deep_merge(result, update)
        else:
            result.update(update)
    
    return result


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """Deep merge update into base."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def is_valid_identifier(name: str) -> bool:
    """Check if string is valid identifier.
    
    Args:
        name: String to check
        
    Returns:
        True if valid identifier
    """
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))


def pluralize(word: str, count: int) -> str:
    """Simple pluralization.
    
    Args:
        word: Word to pluralize
        count: Count for determining plural
        
    Returns:
        Pluralized word if count != 1
    """
    if count == 1:
        return word
    
    # Simple rules
    if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
        return word[:-1] + 'ies'
    elif word.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z')):
        return word + 'es'
    else:
        return word + 's'


def format_bytes(num_bytes: int) -> str:
    """Format bytes as human-readable string.
    
    Args:
        num_bytes: Number of bytes
        
    Returns:
        Formatted string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"