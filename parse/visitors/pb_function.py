"""PowerBuilder function visitor module."""
from dataclasses import dataclass, field
from typing import Any

from lark import Tree


# Stub classes for imports
@dataclass
class PBType:
    """PowerBuilder type."""
    name: str
    is_array: bool = False
    array_bounds: list[int] = field(default_factory=list)
    namespace: str | None = None
    is_custom: bool = False


@dataclass
class PBParameter:
    """PowerBuilder parameter."""
    name: str
    pb_type: PBType
    direction: str = 'in'
    default_value: Any = None


@dataclass
class PBFunction:
    """PowerBuilder function."""
    name: str
    return_type: PBType
    parameters: list[PBParameter] = field(default_factory=list)
    access: str = 'public'
    behavioral_options: list[Any] = field(default_factory=list)


@dataclass
class PBSubroutine:
    """PowerBuilder subroutine."""
    name: str
    parameters: list[PBParameter] = field(default_factory=list)
    access: str = 'public'


def create_pb_parameter(name: str, pb_type: PBType, direction: str = 'in', default_value: Any = None) -> PBParameter:
    """Create a PBParameter instance."""
    return PBParameter(name=name, pb_type=pb_type, direction=direction, default_value=default_value)


def visit_function_definition(node: Tree) -> dict[str, Any]:
    """Visit function definition node.

    Args:
        node: Function definition AST node

    Returns:
        Function definition metadata
    """
    name = node.children[0].value
    params = []
    return_type = None
    body = []

    for child in node.children[1:]:
        if child.data == 'param_list':
            params = visit_param_list(child)
        elif child.data == 'type_spec':
            return_type = visit_type_spec(child)
        elif child.data == 'statement_list':
            body = visit_statement_list(child)

    return {
        'name': name,
        'params': params,
        'return_type': return_type,
        'body': body,
    }


def visit_param_list(node: Tree) -> list[dict[str, Any]]:
    """Visit parameter list node.

    Args:
        node: Parameter list AST node

    Returns:
        List of parameter metadata
    """
    params = []
    for child in node.children:
        if child.data == 'param':
            params.append(visit_param(child))
    return params


def visit_param(node: Tree) -> dict[str, Any]:
    """Visit parameter node.

    Args:
        node: Parameter AST node

    Returns:
        Parameter metadata
    """
    name = node.children[0].value
    type_spec = visit_type_spec(node.children[1])
    direction = None

    if len(node.children) > 2:
        direction = node.children[2].value

    return {
        'name': name,
        'type': type_spec,
        'direction': direction,
    }


def visit_type_spec(node: Tree) -> str:
    """Visit type specification node.

    Args:
        node: Type specification AST node

    Returns:
        Type name
    """
    if len(node.children) == 1:
        return node.children[0].value

    # Array type
    size = node.children[1].value
    elem_type = visit_type_spec(node.children[3])
    return f"ARRAY[{size}] OF {elem_type}"


def visit_statement_list(node: Tree) -> list[str]:
    """Visit statement list node.

    Args:
        node: Statement list AST node

    Returns:
        List of statement strings
    """
    statements = []
    for child in node.children:
        if hasattr(child, 'value'):
            statements.append(child.value)
        else:
            statements.append(str(child))
    return statements
