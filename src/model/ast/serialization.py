"""AST serialization and deserialization utilities.

This module provides functions to convert Lark Tree objects to and from
JSON-serializable dictionaries, enabling proper storage and retrieval
of parsed AST structures.
"""

import json
from typing import Any

from lark import Token, Tree


def tree_to_dict(tree: Tree) -> dict[str, Any]:








    """Convert a Lark Tree to a JSON-serializable dictionary.

    Args:
        tree: Lark Tree object to serialize

    Returns:
        Dictionary representation of the tree
    """
    # Handle tree.data - it might be a Token or a string
    if isinstance(tree.data, Token):
        data_value = tree.data.value
    else:
        data_value = str(tree.data)

    result = {
        "type": "tree", "data": data_value, "children": [],
    }

    for child in tree.children:
        if isinstance(child, Tree):
            result["children"].append(tree_to_dict(child))
        elif isinstance(child, Token):
            result["children"].append(token_to_dict(child))
        else:
            # Handle primitive values (str, int, etc.)
            # But first check if it's actually a Tree that wasn't caught
            if hasattr(child, 'data') and hasattr(child, 'children'):
                # It's likely a Tree object that wasn't recognized
                result["children"].append(tree_to_dict(child))
            else:
                # It's a primitive value
                result["children"].append({
                    "type": "value", "value": str(child) if child is not None else None,
                })

    # Preserve metadata if available
    if hasattr(tree, "meta"):
        result["meta"] = {
            "line": getattr(tree.meta, "line", None), "column": getattr(tree.meta, "column", None), "end_line": getattr(tree.meta, "end_line", None), "end_column": getattr(tree.meta, "end_column", None), }

    return result


def token_to_dict(token: Token) -> dict[str, Any]:








    """Convert a Lark Token to a JSON-serializable dictionary.

    Args:
        token: Lark Token object to serialize

    Returns:
        Dictionary representation of the token
    """
    result = {
        "type": "token", "type_": token.type, "value": token.value,
    }

    # Preserve position information
    if hasattr(token, "line"):
        result["line"] = token.line
    if hasattr(token, "column"):
        result["column"] = token.column
    if hasattr(token, "end_line"):
        result["end_line"] = token.end_line
    if hasattr(token, "end_column"):
        result["end_column"] = token.end_column

    return result


def dict_to_tree(data: dict[str, Any]) -> Tree | Token | Any:








    """Convert a dictionary back to a Lark Tree or Token.

    Args:
        data: Dictionary representation of a tree or token

    Returns:
        Reconstructed Tree, Token, or primitive value
    """
    if not isinstance(data, dict):
        return data

    obj_type = data.get("type")

    if obj_type == "tree":
        # Reconstruct children first
        children = []
        for child_data in data.get("children", []):
            children.append(dict_to_tree(child_data))

        # Create the tree
        tree = Tree(data["data"], children)

        # Restore metadata if available
        if "meta" in data and data["meta"]:
            # Try to set meta if the tree supports it
            try:
                # Create a simple metadata object
                class Meta:
                    pass

                meta = Meta()
                for key, value in data["meta"].items():
                    if value is not None:
                        setattr(meta, key, value)
                tree.meta = meta
            except AttributeError:
                # Tree doesn't support meta assignment, skip it
                pass

        return tree

    elif obj_type == "token":
        # Create token
        token = Token(data["type_"], data["value"])

        # Restore position information
        for attr in ["line", "column", "end_line", "end_column"]:
            if attr in data:
                setattr(token, attr, data[attr])

        return token

    elif obj_type == "value":
        # Return primitive value
        return data["value"]

    else:
        # Unknown type, return as-is
        return data


def serialize_ast(tree: Tree) -> dict[str, Any]:








    """Serialize an AST tree for JSON storage.

    This is the main entry point for AST serialization.

    Args:
        tree: Lark Tree object representing the AST

    Returns:
        JSON-serializable dictionary
    """
    if not isinstance(tree, Tree):
        raise ValueError(f"Expected Lark Tree, got {type(tree)}")

    return tree_to_dict(tree)


def deserialize_ast(data: dict[str, Any]) -> Tree:








    """Deserialize an AST from JSON storage.

    This is the main entry point for AST deserialization.

    Args:
        data: Dictionary representation of the AST

    Returns:
        Reconstructed Lark Tree object
    """
    result = dict_to_tree(data)

    if not isinstance(result, Tree):
        raise ValueError(f"Expected to deserialize a Tree, got {type(result)}")

    return result


def deserialize_ast_string(ast_string: str) -> Tree | dict[str, Any]:








    """Attempt to deserialize an AST from a pretty-printed string.

    This is a fallback for legacy AST files that were saved as pretty strings.
    Since we cannot fully reconstruct a Tree from a pretty string, we return
    a dictionary representation that can still be processed.

    Args:
        ast_string: Pretty-printed AST string

    Returns:
        Dictionary with parsed structure or original string if parsing fails
    """
    # For now, we return a structured dict that indicates this is a legacy format
    # In the future, we could implement a parser for the pretty format
    return {
        "type": "legacy_ast", "format": "pretty_string", "content": ast_string, "warning": "This AST was saved in legacy string format and cannot be fully deserialized",
    }


class ASTJSONEncoder(json.JSONEncoder):
    """JSON encoder for AST objects."""

    def default(self, obj):
        """Handle AST-specific objects during JSON encoding."""
        if isinstance(obj, Tree):
            return tree_to_dict(obj)
        elif isinstance(obj, Token):
            return token_to_dict(obj)
        elif hasattr(obj, "__dict__"):
            # Handle custom AST node classes
            return {
                "_type": obj.__class__.__name__,
                **obj.__dict__
            }
        return super().default(obj)


class ASTJSONDecoder(json.JSONDecoder):
    """JSON decoder for AST objects."""

    def __init__(self, *args, **kwargs):
        """Initialize decoder with custom object hook."""
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        """Handle AST-specific objects during JSON decoding."""
        if "type" in dct:
            if dct["type"] == "tree":
                return dict_to_tree(dct)
            elif dct["type"] == "token":
                return dict_to_tree(dct)
            elif dct["type"] == "value":
                return dct["value"]
        return dct
