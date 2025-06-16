"""
Template context schemas for type validation.

This module defines type schemas for validating template contexts
before rendering. Each template has a corresponding schema that defines
the expected structure and types of the context data.
"""

from typing import List, Optional, Dict, Any, Union, Literal, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import re


class ColumnType(str, Enum):
    """PowerBuilder to Python/Dart type mappings."""
    INTEGER = "integer"
    STRING = "string"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    BLOB = "blob"
    TEXT = "text"
    JSON = "json"


class RelationshipType(str, Enum):
    """Database relationship types."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class WidgetType(str, Enum):
    """Flutter widget types."""
    TEXT_FIELD = "TextField"
    DROPDOWN = "DropdownButton"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
    BUTTON = "ElevatedButton"
    DATE_PICKER = "DatePicker"
    TIME_PICKER = "TimePicker"
    DATA_GRID = "DataGrid"
    CUSTOM = "Custom"


@dataclass
class ValidationRule:
    """Validation rule for a field."""
    type: Literal["required", "min", "max", "pattern", "custom"]
    value: Optional[Union[str, int, float]] = None
    message: Optional[str] = None


@dataclass
class ColumnSchema:
    """Schema for database column definition."""
    name: str
    type: ColumnType
    python_type: str
    dart_type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default: Optional[Any] = None
    max_length: Optional[int] = None
    validators: List[ValidationRule] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate column name."""
        if not self.name or not self.name.strip():
            raise ValueError("Column name cannot be empty")
        if not self.name.replace('_', '').isalnum():
            raise ValueError("Column name must be alphanumeric with underscores")
        self.name = self.name.lower()


@dataclass
class RelationshipSchema:
    """Schema for model relationships."""
    name: str
    type: RelationshipType
    target_model: str
    foreign_key: str
    back_populates: Optional[str] = None
    cascade: Optional[str] = None
    lazy: bool = True


@dataclass
class ModelSchema:
    """Schema for SQLModel template context."""
    name: str
    table_name: str
    columns: List[ColumnSchema]
    relationships: List[RelationshipSchema] = field(default_factory=list)
    indexes: List[List[str]] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate model name is PascalCase."""
        if not self.name or not self.name[0].isupper():
            raise ValueError("Model name must be PascalCase")


@dataclass
class MethodParameterSchema:
    """Schema for method parameters."""
    name: str
    type: str
    default: Optional[Any] = None
    required: bool = True


@dataclass
class MethodSchema:
    """Schema for service method definition."""
    name: str
    path: str
    return_type: str
    http_method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    parameters: List[MethodParameterSchema] = field(default_factory=list)
    description: Optional[str] = None
    requires_auth: bool = True
    
    def __post_init__(self):
        """Validate method name is snake_case."""
        if not self.name or not self.name.replace('_', '').isalnum():
            raise ValueError("Method name must be snake_case")
        self.name = self.name.lower()


@dataclass
class ServiceSchema:
    """Schema for service template context."""
    name: str
    model_name: str
    methods: List[MethodSchema]
    imports: List[str] = field(default_factory=list)
    base_path: str = "/api"


@dataclass
class EventHandlerSchema:
    """Schema for event handler definition."""
    name: str
    event_type: str
    parameters: List[MethodParameterSchema] = field(default_factory=list)
    body: Optional[str] = None
    return_type: str = "void"


@dataclass
class ControlPropertySchema:
    """Schema for UI control properties."""
    name: str
    value: Any
    type: str
    is_expression: bool = False


@dataclass
class UIControlSchema:
    """Schema for UI control definition."""
    name: str
    type: WidgetType
    properties: Dict[str, Any] = field(default_factory=dict)
    events: List[EventHandlerSchema] = field(default_factory=list)
    children: List['UIControlSchema'] = field(default_factory=list)
    data_binding: Optional[str] = None
    visibility_condition: Optional[str] = None
    validation_rules: List[ValidationRule] = field(default_factory=list)


@dataclass
class DataWindowColumnSchema:
    """Schema for DataWindow column definition."""
    name: str
    display_name: str
    type: ColumnType
    width: int = 100
    editable: bool = True
    visible: bool = True
    format: Optional[str] = None
    alignment: Literal["left", "center", "right"] = "left"
    sort_enabled: bool = True
    filter_enabled: bool = True
    
    def __post_init__(self):
        """Validate width."""
        if self.width < 0:
            raise ValueError("Column width must be non-negative")


@dataclass
class DataWindowSchema:
    """Schema for DataWindow widget template context."""
    name: str
    title: str
    data_source: str
    columns: List[DataWindowColumnSchema]
    controls: List[UIControlSchema] = field(default_factory=list)
    events: List[EventHandlerSchema] = field(default_factory=list)
    retrieve_params: List[MethodParameterSchema] = field(default_factory=list)
    allow_add: bool = True
    allow_edit: bool = True
    allow_delete: bool = True
    page_size: int = 20
    
    def __post_init__(self):
        """Validate page size."""
        if self.page_size < 1:
            raise ValueError("Page size must be at least 1")


@dataclass
class ScreenSchema:
    """Schema for screen/window template context."""
    name: str
    title: str
    route_path: str
    controls: List[UIControlSchema]
    data_windows: List[DataWindowSchema] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    state_variables: Dict[str, str] = field(default_factory=dict)
    lifecycle_methods: Dict[str, str] = field(default_factory=dict)
    is_stateful: bool = True


@dataclass
class DartModelFieldSchema:
    """Schema for Dart model field."""
    name: str
    type: str
    is_nullable: bool = False
    default_value: Optional[Any] = None
    json_key: Optional[str] = None
    validators: List[str] = field(default_factory=list)


@dataclass
class DartModelSchema:
    """Schema for Dart model template context."""
    name: str
    fields: List[DartModelFieldSchema]
    imports: List[str] = field(default_factory=list)
    use_freezed: bool = True
    use_json_serializable: bool = True
    custom_methods: List[MethodSchema] = field(default_factory=list)


# Template name to schema mapping
TEMPLATE_SCHEMAS = {
    "sqlmodel_model.jinja2": ModelSchema,
    "service.py.jinja2": ServiceSchema,
    "datawindow_widget.dart.jinja2": DataWindowSchema,
    "model.dart.jinja2": DartModelSchema,
    "screen.dart.jinja2": ScreenSchema,
    "widget.dart.jinja2": UIControlSchema,
}


def get_schema_for_template(template_name: str) -> Optional[type]:
    """Get the schema class for a template."""
    return TEMPLATE_SCHEMAS.get(template_name)


def validate_template_context(template_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate template context against its schema.
    
    Args:
        template_name: Name of the template
        context: Context dictionary to validate
        
    Returns:
        Validated context dictionary
        
    Raises:
        ValueError: If validation fails
    """
    schema_class = get_schema_for_template(template_name)
    if not schema_class:
        # No schema defined, return context as-is
        return context
        
    try:
        # Validate using dataclass
        validated = schema_class(**context)
        # Convert back to dict
        return _dataclass_to_dict(validated)
    except Exception as e:
        raise ValueError(f"Template context validation failed for {template_name}: {e}")


def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert a dataclass instance to a dictionary."""
    from dataclasses import asdict, is_dataclass
    
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _dataclass_to_dict(value) for key, value in obj.items()}
    else:
        return obj


def generate_template_docs():
    """Generate documentation for all template schemas."""
    docs = []
    for template_name, schema_class in TEMPLATE_SCHEMAS.items():
        docs.append(f"## {template_name}")
        docs.append(f"\nSchema: `{schema_class.__name__}`\n")
        docs.append("### Fields:")
        
        from dataclasses import fields
        for field_info in fields(schema_class):
            field_name = field_info.name
            field_type = field_info.type
            has_default = field_info.default is not field_info.default_factory
            default = field_info.default if has_default else None
            
            docs.append(f"- **{field_name}** ({field_type})")
            docs.append(f"  - Required: {not has_default}")
            if has_default and default is not None:
                docs.append(f"  - Default: {default}")
                
        docs.append("\n")
        
    return "\n".join(docs)