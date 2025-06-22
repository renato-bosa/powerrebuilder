"""Custom Jinja2 filters for code generation templates.

This module provides custom filters for handling dynamic indentation and
other formatting needs in code generation templates.
"""



def indent_filter(text: str | list[str], level: int = 0, width: int = 4) -> str:
    
    



    r"""Apply dynamic indentation to text.

    Args:
        text: Text to indent (string or list of lines)
        level: Indentation level (0 = no indent, 1 = one level, etc.)
        width: Number of spaces per indent level (default: 4)

    Returns:
        Indented text

    Examples:
        >>> indent_filter("hello", 1)
        '    hello'
        >>> indent_filter("hello\\nworld", 2, width=2)
        '    hello\\n    world'
    """
    if level <= 0:
        return text if isinstance(text, str) else "\n".join(text)

    indent = " " * (level * width)

    lines = text.split("\n") if isinstance(text, str) else list(text)

    # Apply indentation to each line, but not to empty lines
    indented_lines = []
    for line in lines:
        if line.strip():  # Non-empty line
            indented_lines.append(indent + line)
        else:
            indented_lines.append(line)

    return "\n".join(indented_lines)


def indent_block_filter(text: str, base_level: int = 0, width: int = 4) -> str:



    
    


    """Apply smart indentation to a code block, preserving relative indentation.

    This filter is useful for templates that generate nested code structures.
    It preserves the relative indentation within the block while applying
    a base indentation level.

    Args:
        text: Code block to indent
        base_level: Base indentation level to apply
        width: Number of spaces per indent level (default: 4)

    Returns:
        Indented code block

    Examples:
        >>> code = '''if x > 0:
        ...     print("positive")
        ... else:
        ...     print("negative")'''
        >>> print(indent_block_filter(code, 1))
            if x > 0:
                print("positive")
            else:
                print("negative")
    """
    if base_level <= 0:
        return text

    lines = text.split("\n")

    # Find the minimum indentation level (excluding empty lines)
    min_indent = float("inf")
    for line in lines:
        if line.strip():  # Non-empty line
            leading_spaces = len(line) - len(line.lstrip())
            min_indent = min(min_indent, leading_spaces)

    # If no non-empty lines, return as is
    if min_indent == float("inf"):
        return text

    # Apply base indentation while preserving relative indentation
    base_indent = " " * (base_level * width)
    indented_lines = []

    for line in lines:
        if line.strip():  # Non-empty line
            # Remove minimum indentation and apply base indentation
            relative_line = line[min_indent:]
            indented_lines.append(base_indent + relative_line)
        else:
            indented_lines.append(line)

    return "\n".join(indented_lines)


def indent_nested_filter(text: str, parent_level: int = 0, width: int = 4) -> str:



    
    


    """Apply indentation for nested structures, incrementing level by 1.

    This is a convenience filter for nested blocks that need to be indented
    one level deeper than their parent.

    Args:
        text: Text to indent
        parent_level: Parent's indentation level
        width: Number of spaces per indent level (default: 4)

    Returns:
        Text indented to parent_level + 1
    """
    return indent_filter(text, parent_level + 1, width)


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


def dedent_wrapper(text: str, width: int | None = None) -> str:



    
    


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
    import re
    # Replace spaces, hyphens with underscores
    text = re.sub(r'[\s\-]+', '_', text)
    # Insert underscores before capital letters
    text = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
    # Convert to lowercase and remove duplicate underscores
    return re.sub(r'_+', '_', text.lower()).strip('_')


def pascal_case(text: str) -> str:



    
    


    """Convert text to PascalCase.
    
    Args:
        text: Text to convert
        
    Returns:
        PascalCase version of the text
    """
    import re
    # Split by spaces, hyphens, underscores
    parts = re.split(r'[\s\-_]+', text)
    # Capitalize each part
    return ''.join(part.capitalize() for part in parts if part)


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