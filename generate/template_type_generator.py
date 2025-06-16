"""
Generate type stubs and documentation for template contexts.

This module provides utilities to:
1. Generate TypedDict definitions from template schemas
2. Create type stub files for IDE support
3. Generate template documentation
"""

import ast
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from textwrap import dedent

from .template_schemas import (
    TEMPLATE_SCHEMAS, ModelSchema, ServiceSchema, ScreenSchema,
    DataWindowSchema, UIControlSchema, DartModelSchema
)


def generate_typed_dict_from_schema(schema_class: type) -> str:
    """
    Generate a TypedDict definition from a Pydantic schema.
    
    Args:
        schema_class: Pydantic model class
        
    Returns:
        TypedDict definition as string
    """
    class_name = f"{schema_class.__name__}Dict"
    fields = []
    
    from dataclasses import fields as get_fields, MISSING
    
    for field_info in get_fields(schema_class):
        field_name = field_info.name
        field_type = _get_type_string(field_info.type)
        has_default = field_info.default is not MISSING or field_info.default_factory is not MISSING
        if has_default:
            field_type = f"Optional[{field_type}]"
        fields.append(f"    {field_name}: {field_type}")
        
    typed_dict = f"""class {class_name}(TypedDict):
    \"\"\"Type definition for {schema_class.__name__} template context.\"\"\"
{chr(10).join(fields)}"""
    
    return typed_dict


def _get_type_string(annotation: Any) -> str:
    """Convert a type annotation to string representation."""
    if hasattr(annotation, '__name__'):
        return annotation.__name__
        
    # Handle generic types
    origin = getattr(annotation, '__origin__', None)
    if origin is not None:
        args = getattr(annotation, '__args__', ())
        if origin is list:
            if args:
                return f"List[{_get_type_string(args[0])}]"
            return "List[Any]"
        elif origin is dict:
            if len(args) == 2:
                return f"Dict[{_get_type_string(args[0])}, {_get_type_string(args[1])}]"
            return "Dict[str, Any]"
        elif origin is Union:
            types = [_get_type_string(arg) for arg in args]
            return f"Union[{', '.join(types)}]"
            
    # Handle string representation
    return str(annotation).replace('typing.', '')


def generate_template_types_module() -> str:
    """
    Generate a Python module with all template TypedDict definitions.
    
    Returns:
        Complete module content as string
    """
    imports = dedent("""
    \"\"\"
    Auto-generated type definitions for template contexts.
    
    This module provides TypedDict definitions for all template contexts,
    enabling type checking and IDE support when preparing template data.
    \"\"\"
    
    from typing import TypedDict, List, Dict, Optional, Any, Union, Literal
    
    """).strip()
    
    typed_dicts = []
    
    for template_name, schema_class in TEMPLATE_SCHEMAS.items():
        typed_dict = generate_typed_dict_from_schema(schema_class)
        typed_dicts.append(f"\n# Context for {template_name}\n{typed_dict}")
        
    # Add a mapping of template names to types
    mapping = "\n\n# Template name to context type mapping\nTEMPLATE_CONTEXT_TYPES = {"
    for template_name, schema_class in TEMPLATE_SCHEMAS.items():
        class_name = f"{schema_class.__name__}Dict"
        mapping += f'\n    "{template_name}": {class_name},'
    mapping += "\n}"
    
    return imports + "\n" + "\n\n".join(typed_dicts) + mapping


def generate_template_documentation() -> str:
    """
    Generate comprehensive documentation for all templates.
    
    Returns:
        Markdown documentation
    """
    docs = [
        "# Template Context Documentation",
        "",
        "This document describes the expected context structure for each template.",
        "",
        "## Table of Contents",
        ""
    ]
    
    # Generate TOC
    for template_name in sorted(TEMPLATE_SCHEMAS.keys()):
        anchor = template_name.replace('.', '').replace('_', '-').lower()
        docs.append(f"- [{template_name}](#{anchor})")
        
    docs.extend(["", "---", ""])
    
    # Generate detailed documentation for each template
    for template_name, schema_class in sorted(TEMPLATE_SCHEMAS.items()):
        anchor = template_name.replace('.', '').replace('_', '-').lower()
        docs.append(f"## {template_name} {{#{anchor}}}")
        docs.append("")
        docs.append(f"**Schema Class:** `{schema_class.__name__}`")
        docs.append("")
        docs.append("### Context Structure")
        docs.append("")
        docs.append("```python")
        docs.append(f"context = {{")
        
        from dataclasses import fields as get_fields, MISSING
        
        for field_info in get_fields(schema_class):
            field_name = field_info.name
            field_type = _get_type_string(field_info.type)
            has_default = field_info.default is not MISSING or field_info.default_factory is not MISSING
            required = " (required)" if not has_default else " (optional)"
            
            docs.append(f"    '{field_name}': {field_type},{required}")
            
        docs.append("}")
        docs.append("```")
        docs.append("")
        
        # Add example if available
        docs.append("### Example Usage")
        docs.append("")
        docs.append("```python")
        docs.append(f"from generate.template_schemas import {schema_class.__name__}")
        docs.append("")
        docs.append(f"# Create and validate context")
        docs.append(f"context_data = {{")
        
        # Generate example values
        example_values = _generate_example_values(schema_class)
        for field_name, value in example_values.items():
            docs.append(f"    '{field_name}': {repr(value)},")
            
        docs.append("}")
        docs.append("")
        docs.append(f"# Validate context")
        docs.append(f"validated = {schema_class.__name__}(**context_data)")
        docs.append("")
        docs.append(f"# Render template")
        docs.append(f"output = generator.render_template('{template_name}', validated.dict())")
        docs.append("```")
        docs.append("")
        docs.append("---")
        docs.append("")
        
    return "\n".join(docs)


def _generate_example_values(schema_class: type) -> Dict[str, Any]:
    """Generate example values for a schema."""
    from dataclasses import fields as get_fields, MISSING
    
    examples = {}
    
    for field_info in get_fields(schema_class):
        field_name = field_info.name
        field_type = field_info.type
        has_default = field_info.default is not MISSING or field_info.default_factory is not MISSING
        
        if has_default and field_info.default is None:
            continue
        
        # Generate appropriate example based on type
        if field_type == str:
            if 'name' in field_name:
                examples[field_name] = "ExampleName"
            elif 'path' in field_name:
                examples[field_name] = "/api/example"
            elif 'type' in field_name:
                examples[field_name] = "string"
            else:
                examples[field_name] = "example_value"
        elif field_type == int:
            examples[field_name] = 100
        elif field_type == bool:
            examples[field_name] = True
        elif hasattr(field_type, '__origin__'):
            origin = field_type.__origin__
            if origin is list:
                examples[field_name] = []
            elif origin is dict:
                examples[field_name] = {}
        else:
            # For complex types, provide minimal example
            examples[field_name] = f"<{field_type.__name__} instance>"
            
    return examples


def save_generated_types(output_dir: Path = Path("generate/types")) -> None:
    """
    Save generated type definitions and documentation.
    
    Args:
        output_dir: Directory to save generated files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save TypedDict definitions
    types_module = generate_template_types_module()
    types_file = output_dir / "template_types.py"
    types_file.write_text(types_module)
    
    # Save documentation
    docs = generate_template_documentation()
    docs_file = output_dir / "TEMPLATE_CONTEXTS.md"
    docs_file.write_text(docs)
    
    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text('"""Auto-generated template type definitions."""\n\nfrom .template_types import *\n')
    
    print(f"Generated type definitions saved to {output_dir}")
    print(f"- Type stubs: {types_file}")
    print(f"- Documentation: {docs_file}")


if __name__ == "__main__":
    # Generate types when run as script
    save_generated_types()