"""Base interfaces (protocols) to prevent circular dependencies.

These interfaces define contracts that can be implemented by concrete classes
without creating import cycles.
"""

from abc import abstractmethod
from typing import Any, Dict, Generic, Iterator, List, Optional, Protocol, TypeVar, Union

from .types import (
    Identifier,
    Metadata,
    NodeAttributes,
    NodeKind,
    Position,
    QualifiedName,
    SourceLocation,
    TypeReference,
    Visibility
)

T = TypeVar('T')
R = TypeVar('R')


class INode(Protocol):
    """Base interface for all AST nodes."""
    
    @property
    def kind(self) -> NodeKind:
        """Get node kind."""
        ...
    
    @property
    def location(self) -> Optional[SourceLocation]:
        """Get source location."""
        ...
    
    @property
    def parent(self) -> Optional["INode"]:
        """Get parent node."""
        ...
    
    @property
    def children(self) -> List["INode"]:
        """Get child nodes."""
        ...
    
    def accept(self, visitor: "IVisitor[T]") -> T:
        """Accept a visitor."""
        ...
    
    def transform(self, transformer: "ITransformer") -> "INode":
        """Transform this node."""
        ...


class ITyped(Protocol):
    """Interface for typed entities."""
    
    @property
    def type(self) -> Optional[TypeReference]:
        """Get type reference."""
        ...
    
    def set_type(self, type_ref: TypeReference) -> None:
        """Set type reference."""
        ...


class INamedEntity(Protocol):
    """Interface for named entities."""
    
    @property
    def name(self) -> Union[str, Identifier]:
        """Get entity name."""
        ...
    
    @property
    def qualified_name(self) -> Optional[QualifiedName]:
        """Get fully qualified name."""
        ...


class ISourced(Protocol):
    """Interface for entities with source information."""
    
    @property
    def source_file(self) -> Optional[str]:
        """Get source file path."""
        ...
    
    @property
    def source_text(self) -> Optional[str]:
        """Get original source text."""
        ...
    
    def get_source_line(self, line_number: int) -> Optional[str]:
        """Get specific source line."""
        ...


class IScoped(Protocol):
    """Interface for entities that define or use scopes."""
    
    @property
    def scope(self) -> "IScope":
        """Get associated scope."""
        ...
    
    def resolve(self, name: str) -> Optional["ISymbol"]:
        """Resolve a name in this scope."""
        ...


class IScope(Protocol):
    """Interface for symbol scopes."""
    
    @property
    def name(self) -> str:
        """Get scope name."""
        ...
    
    @property
    def parent(self) -> Optional["IScope"]:
        """Get parent scope."""
        ...
    
    def define(self, symbol: "ISymbol") -> None:
        """Define a symbol in this scope."""
        ...
    
    def resolve(self, name: str) -> Optional["ISymbol"]:
        """Resolve a symbol by name."""
        ...
    
    def get_symbols(self) -> Dict[str, "ISymbol"]:
        """Get all symbols in this scope."""
        ...


class ISymbol(Protocol):
    """Interface for symbols."""
    
    @property
    def name(self) -> str:
        """Get symbol name."""
        ...
    
    @property
    def type(self) -> Optional[TypeReference]:
        """Get symbol type."""
        ...
    
    @property
    def scope(self) -> Optional[IScope]:
        """Get defining scope."""
        ...
    
    @property
    def visibility(self) -> Optional[Visibility]:
        """Get visibility."""
        ...


class IVisitor(Protocol, Generic[T]):
    """Visitor interface for traversing nodes."""
    
    def visit(self, node: INode) -> T:
        """Visit a node."""
        ...
    
    def visit_children(self, node: INode) -> List[T]:
        """Visit all children of a node."""
        ...


class ITransformer(Protocol):
    """Transformer interface for modifying nodes."""
    
    def transform(self, node: INode) -> INode:
        """Transform a node."""
        ...
    
    def transform_children(self, node: INode) -> List[INode]:
        """Transform all children of a node."""
        ...


class IValidator(Protocol):
    """Validator interface for checking nodes."""
    
    def validate(self, node: INode) -> List["IValidationError"]:
        """Validate a node."""
        ...
    
    def is_valid(self, node: INode) -> bool:
        """Check if node is valid."""
        ...


class IValidationError(Protocol):
    """Interface for validation errors."""
    
    @property
    def message(self) -> str:
        """Get error message."""
        ...
    
    @property
    def node(self) -> INode:
        """Get node that caused the error."""
        ...
    
    @property
    def severity(self) -> str:
        """Get error severity."""
        ...


class IAnalyzer(Protocol):
    """Analyzer interface for analyzing nodes."""
    
    def analyze(self, node: INode) -> "IAnalysisResult":
        """Analyze a node."""
        ...


class IAnalysisResult(Protocol):
    """Interface for analysis results."""
    
    @property
    def node(self) -> INode:
        """Get analyzed node."""
        ...
    
    @property
    def findings(self) -> List[Dict[str, Any]]:
        """Get analysis findings."""
        ...


class IParser(Protocol):
    """Parser interface."""
    
    def parse(self, source: str, filename: Optional[str] = None) -> INode:
        """Parse source code."""
        ...
    
    def parse_file(self, file_path: str) -> INode:
        """Parse a file."""
        ...


class ICodeGenerator(Protocol):
    """Code generator interface."""
    
    def generate(self, node: INode) -> str:
        """Generate code from AST."""
        ...
    
    def generate_file(self, node: INode, file_path: str) -> None:
        """Generate code to file."""
        ...


class ICompilationUnit(Protocol):
    """Interface for compilation units."""
    
    @property
    def filename(self) -> str:
        """Get filename."""
        ...
    
    @property
    def root(self) -> INode:
        """Get root node."""
        ...
    
    @property
    def imports(self) -> List[str]:
        """Get imports."""
        ...
    
    @property
    def exports(self) -> List[ISymbol]:
        """Get exported symbols."""
        ...


class IDiagnostic(Protocol):
    """Interface for diagnostic messages."""
    
    @property
    def message(self) -> str:
        """Get diagnostic message."""
        ...
    
    @property
    def severity(self) -> str:
        """Get severity level."""
        ...
    
    @property
    def location(self) -> Optional[SourceLocation]:
        """Get location."""
        ...
    
    @property
    def code(self) -> Optional[str]:
        """Get diagnostic code."""
        ...


class ISemanticModel(Protocol):
    """Interface for semantic models."""
    
    def get_symbol_at(self, position: Position) -> Optional[ISymbol]:
        """Get symbol at position."""
        ...
    
    def get_type_at(self, position: Position) -> Optional[TypeReference]:
        """Get type at position."""
        ...
    
    def get_diagnostics(self) -> List[IDiagnostic]:
        """Get all diagnostics."""
        ...


# Factory interfaces to avoid direct construction

class INodeFactory(Protocol):
    """Factory for creating nodes without circular imports."""
    
    def create_identifier(self, name: str, location: Optional[SourceLocation] = None) -> INode:
        """Create identifier node."""
        ...
    
    def create_literal(self, value: Any, location: Optional[SourceLocation] = None) -> INode:
        """Create literal node."""
        ...
    
    def create_binary_expression(
        self,
        left: INode,
        operator: str,
        right: INode,
        location: Optional[SourceLocation] = None
    ) -> INode:
        """Create binary expression."""
        ...
    
    def create_call_expression(
        self,
        callee: INode,
        arguments: List[INode],
        location: Optional[SourceLocation] = None
    ) -> INode:
        """Create call expression."""
        ...
    
    def create_block(
        self,
        statements: List[INode],
        location: Optional[SourceLocation] = None
    ) -> INode:
        """Create block statement."""
        ...


class ITypeFactory(Protocol):
    """Factory for creating types without circular imports."""
    
    def create_primitive_type(self, name: str) -> TypeReference:
        """Create primitive type reference."""
        ...
    
    def create_array_type(self, element_type: TypeReference, dimensions: int = 1) -> TypeReference:
        """Create array type reference."""
        ...
    
    def create_object_type(self, name: Union[str, QualifiedName]) -> TypeReference:
        """Create object type reference."""
        ...
    
    def create_generic_type(
        self,
        base_type: TypeReference,
        type_arguments: List[TypeReference]
    ) -> TypeReference:
        """Create generic type reference."""
        ...