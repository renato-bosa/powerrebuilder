"""Domain models - Pure data structures with no external dependencies.

This module contains all the data structures used throughout the PowerRebuilder
pipeline. These are pure Python/Pydantic models with no I/O or external dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

# ============= Enums =============


class ObjectType(str, Enum):
    """PowerBuilder object types."""

    APPLICATION = "application"
    WINDOW = "window"
    USER_OBJECT = "user_object"
    MENU = "menu"
    FUNCTION = "function"
    DATAWINDOW = "datawindow"
    STRUCTURE = "structure"
    GLOBAL = "global"
    QUERY = "query"


class PipelineStage(str, Enum):
    """Pipeline processing stages."""

    EXTRACT = "extract"
    DECOMPILE = "decompile"
    PARSE = "parse"
    MODEL = "model"
    GENERATE = "generate"
    ALL = "all"


class TargetLanguage(str, Enum):
    """Target generation languages."""

    FLUTTER = "flutter"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    REACT = "react"
    REACT_TYPESCRIPT = "react_typescript"
    RUST = "rust"
    TAURI = "tauri"
    DIOXUS = "dioxus"


# ============= Value Objects =============


@dataclass(frozen=True)
class FilePath:
    """Immutable file path value object."""

    path: Path

    def __post_init__(self):
        if not isinstance(self.path, Path):
            object.__setattr__(self, "path", Path(self.path))

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def extension(self) -> str:
        return self.path.suffix

    @property
    def stem(self) -> str:
        return self.path.stem

    def __str__(self) -> str:
        return str(self.path)


# ============= Input Models =============


class PBLFile(BaseModel):
    """PowerBuilder Library file."""

    path: str
    size: int
    entries: list[str] = Field(default_factory=list)
    version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PCodeData(BaseModel):
    """Raw P-code bytecode data."""

    object_name: str
    object_type: ObjectType
    bytecode: bytes
    version: str | None = None
    size: int = 0
    checksum: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.size == 0 and self.bytecode:
            self.size = len(self.bytecode)


# ============= Intermediate Models =============


class SourceCode(BaseModel):
    """Decompiled PowerBuilder source code."""

    object_name: str
    object_type: ObjectType
    source: str
    imports: list[str] = Field(default_factory=list)
    exports: list[str] = Field(default_factory=list)
    line_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        if self.line_count == 0 and self.source:
            self.line_count = len(self.source.splitlines())


class ASTNode(BaseModel):
    """Abstract Syntax Tree node."""

    node_type: str
    value: Any | None = None
    children: list["ASTNode"] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    line_number: int | None = None
    column: int | None = None

    def get_child(self, node_type: str) -> Optional["ASTNode"]:
        """Get first child of specific type."""
        for child in self.children:
            if child.node_type == node_type:
                return child
        return None

    def find_all(self, node_type: str) -> list["ASTNode"]:
        """Find all descendants of specific type."""
        results = []
        if self.node_type == node_type:
            results.append(self)
        for child in self.children:
            results.extend(child.find_all(node_type))
        return results


class ParsedObject(BaseModel):
    """Parsed PowerBuilder object with AST."""

    object_name: str
    object_type: ObjectType
    ast: ASTNode
    dependencies: list[str] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============= Semantic Models =============


class Property(BaseModel):
    """Object property definition."""

    name: str
    type: str
    access: str = "public"
    default_value: Any | None = None
    is_required: bool = False
    is_array: bool = False
    documentation: str | None = None


class Parameter(BaseModel):
    """Method/Event parameter."""

    name: str
    type: str
    is_optional: bool = False
    default_value: Any | None = None
    is_ref: bool = False
    is_array: bool = False


class Method(BaseModel):
    """Object method definition."""

    name: str
    return_type: str | None = None
    parameters: list[Parameter] = Field(default_factory=list)
    access: str = "public"
    body: str | None = None
    is_abstract: bool = False
    is_static: bool = False
    is_override: bool = False
    documentation: str | None = None


class Event(BaseModel):
    """Object event definition."""

    name: str
    parameters: list[Parameter] = Field(default_factory=list)
    body: str | None = None
    triggers: list[str] = Field(default_factory=list)
    documentation: str | None = None


class SemanticObject(BaseModel):
    """High-level semantic model of a PowerBuilder object."""

    name: str
    type: ObjectType
    parent: str | None = None
    interfaces: list[str] = Field(default_factory=list)
    properties: list[Property] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============= PowerBuilder AST Models =============


class PBControl(BaseModel):
    """PowerBuilder UI control definition."""

    name: str
    type: str  # commandbutton, datawindow, tab, etc.
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    properties: dict[str, Any] = Field(default_factory=dict)
    events: dict[str, str] = Field(default_factory=dict)  # event_name -> handler_name
    children: list["PBControl"] = Field(
        default_factory=list
    )  # for containers like tabs

    model_config = ConfigDict(populate_by_name=True)


class PBDataWindow(BaseModel):
    """PowerBuilder DataWindow definition."""

    name: str
    dataobject: str
    sql_query: str | None = None
    columns: list[dict[str, Any]] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    bands: dict[str, dict[str, Any]] = Field(
        default_factory=dict
    )  # header, detail, footer
    computed_fields: list[dict[str, Any]] = Field(default_factory=list)


class PBWindow(BaseModel):
    """PowerBuilder window definition."""

    name: str
    title: str = ""
    width: int = 0
    height: int = 0
    properties: dict[str, Any] = Field(default_factory=dict)
    controls: list[PBControl] = Field(default_factory=list)
    events: dict[str, str] = Field(default_factory=dict)
    inherits_from: str | None = None


class PBUserObject(BaseModel):
    """PowerBuilder user object definition."""

    name: str
    type: str = "userobject"
    properties: dict[str, Any] = Field(default_factory=dict)
    controls: list[PBControl] = Field(default_factory=list)
    events: dict[str, str] = Field(default_factory=dict)
    inherits_from: str | None = None


class PowerBuilderAST(BaseModel):
    """Complete PowerBuilder file AST representation."""

    file_type: ObjectType
    forward_declarations: list[str] = Field(default_factory=list)
    type_definitions: list[dict[str, Any]] = Field(default_factory=list)
    global_declarations: dict[str, Any] = Field(default_factory=dict)
    main_object: Any | None = None  # PBWindow, PBUserObject, PBDataWindow
    events: list[dict[str, Any]] = Field(default_factory=list)
    methods: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============= DataWindow IR Models =============


class DataWindowColumn(BaseModel):
    """DataWindow column definition."""

    name: str
    db_name: str
    data_type: str
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    nullable: bool = True
    default_value: Any | None = None
    is_key: bool = False
    is_computed: bool = False
    expression: str | None = None  # for computed columns
    validation_rules: list[str] = Field(default_factory=list)


class DataWindowBand(BaseModel):
    """DataWindow band (header, detail, footer, etc.)."""

    name: str  # header, detail, footer, summary, group_header_1, etc.
    height: int
    color: str | None = None
    visible: bool = True
    elements: list[dict[str, Any]] = Field(
        default_factory=list
    )  # text, column, computed elements


class DataWindowQuery(BaseModel):
    """DataWindow SQL query definition."""

    sql: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    sort_order: list[str] = Field(default_factory=list)
    where_clause: str | None = None


class DataWindowIR(BaseModel):
    """Complete DataWindow Intermediate Representation."""

    name: str
    version: str = "1.0"

    # Data layer
    query: DataWindowQuery
    columns: list[DataWindowColumn] = Field(default_factory=list)

    # Layout layer
    presentation_style: str = "grid"  # grid, freeform, tabular, crosstab, graph
    bands: list[DataWindowBand] = Field(default_factory=list)

    # Behavior layer
    properties: dict[str, Any] = Field(default_factory=dict)
    validation_rules: list[dict[str, Any]] = Field(default_factory=list)
    computed_fields: list[dict[str, Any]] = Field(default_factory=list)

    # Metadata
    creation_info: dict[str, Any] = Field(default_factory=dict)
    target_hints: dict[str, Any] = Field(
        default_factory=dict
    )  # hints for specific target frameworks

    def get_property(self, name: str) -> Property | None:
        """Get property by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None

    def get_method(self, name: str) -> Method | None:
        """Get method by name."""
        for method in self.methods:
            if method.name == name:
                return method
        return None


class DatabaseTable(BaseModel):
    """Database table definition."""

    name: str
    columns: dict[str, str] = Field(default_factory=dict)  # name -> type
    primary_key: list[str] = Field(default_factory=list)
    foreign_keys: dict[str, str] = Field(default_factory=dict)  # column -> reference
    indexes: list[str] = Field(default_factory=list)


class ApplicationModel(BaseModel):
    """Complete application model."""

    name: str
    version: str = "1.0.0"
    objects: dict[str, SemanticObject] = Field(default_factory=dict)
    entry_point: str | None = None
    global_functions: list[Method] = Field(default_factory=list)
    global_variables: list[Property] = Field(default_factory=list)
    database_schema: dict[str, DatabaseTable] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_object(self, name: str) -> SemanticObject | None:
        """Get object by name."""
        return self.objects.get(name)

    def get_windows(self) -> list[SemanticObject]:
        """Get all window objects."""
        return [obj for obj in self.objects.values() if obj.type == ObjectType.WINDOW]

    def get_datawindows(self) -> list[SemanticObject]:
        """Get all datawindow objects."""
        return [
            obj for obj in self.objects.values() if obj.type == ObjectType.DATAWINDOW
        ]


# ============= Output Models =============


class GeneratedFile(BaseModel):
    """Generated source file."""

    path: str
    content: str
    language: TargetLanguage
    file_type: str = "source"  # source, config, asset, test
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedProject(BaseModel):
    """Complete generated project."""

    name: str
    target: TargetLanguage
    files: list[GeneratedFile] = Field(default_factory=list)
    structure: dict[str, Any] = Field(default_factory=dict)
    dependencies: dict[str, str] = Field(default_factory=dict)
    build_config: dict[str, Any] = Field(default_factory=dict)
    commands: dict[str, str] = Field(default_factory=dict)

    def get_source_files(self) -> list[GeneratedFile]:
        """Get all source files."""
        return [f for f in self.files if f.file_type == "source"]

    def get_config_files(self) -> list[GeneratedFile]:
        """Get all config files."""
        return [f for f in self.files if f.file_type == "config"]


# ============= Pipeline Models =============


class PipelineConfig(BaseModel):
    """Pipeline configuration."""

    stages: list[PipelineStage] = Field(default_factory=lambda: list(PipelineStage))
    target: TargetLanguage = TargetLanguage.FLUTTER
    parallel: bool = False
    cache_enabled: bool = True
    debug: bool = False
    dry_run: bool = False
    max_workers: int = 4
    chunk_size: int = 1000
    options: dict[str, Any] = Field(default_factory=dict)


class StageResult(BaseModel):
    """Result from a single pipeline stage."""

    stage: PipelineStage
    success: bool
    files_processed: int = 0
    files_failed: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Pipeline execution result."""

    success: bool
    stages_completed: list[PipelineStage] = Field(default_factory=list)
    stage_results: dict[str, StageResult] = Field(default_factory=dict)
    total_files_processed: int = 0
    total_files_failed: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    output_path: str | None = None

    def add_stage_result(self, result: StageResult):
        """Add a stage result."""
        self.stage_results[result.stage.value] = result
        self.stages_completed.append(result.stage)
        self.total_files_processed += result.files_processed
        self.total_files_failed += result.files_failed
        self.errors.extend(result.errors)
        self.warnings.extend(result.warnings)


# ============= Validation Models =============


class ValidationResult(BaseModel):
    """Validation result for extracted data."""

    is_valid: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExtractionMetrics(BaseModel):
    """Metrics from extraction validation."""

    empty_blocks: list[tuple[int, int]] = Field(default_factory=list)
    false_cjk_count: int = 0
    actual_cjk_count: int = 0
    utf16_strings: int = 0
    file_size: int = 0
    signature: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Enable forward references
ASTNode.model_rebuild()
