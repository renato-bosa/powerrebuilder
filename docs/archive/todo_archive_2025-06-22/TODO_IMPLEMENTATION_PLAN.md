# SIME Finch TODO Implementation Plan

## Overview

This document provides a detailed, phased implementation plan for completing all TODOs, stubs, and incomplete implementations in the SIME Finch project. The plan is organized by priority and dependencies to ensure a logical progression.

## Phase 1: Critical Infrastructure (Week 1)

### 1.1 Parse Module - GrammarManager Implementation

**Location**: `parse/grammar.py` (new file)
**Dependencies**: None
**Priority**: CRITICAL - Blocking multiple tests and parser functionality

**Implementation Steps**:
```python
# parse/grammar.py
from pathlib import Path
from typing import Dict, Optional, Union
from lark import Lark, Grammar
import logging

class GrammarManager:
    """Manages multiple Lark grammar files and their dependencies."""
    
    def __init__(self, grammar_dir: Path):
        self.grammar_dir = grammar_dir
        self._cache: Dict[str, Lark] = {}
        self._grammars: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
    
    def load_grammar(self, name: str, start: Optional[str] = None) -> Lark:
        """Load and cache a grammar by name."""
        # Implementation details:
        # 1. Check cache first
        # 2. Load grammar file from disk
        # 3. Resolve imports/dependencies
        # 4. Create Lark parser instance
        # 5. Cache and return
    
    def register_grammar(self, name: str, content: str) -> None:
        """Register a grammar string directly."""
        
    def get_parser(self, file_type: str) -> Lark:
        """Get appropriate parser for file type."""
        
    def clear_cache(self) -> None:
        """Clear grammar cache."""
```

**Test Coverage**:
- Unit tests for loading grammars
- Integration tests with actual grammar files
- Performance tests for caching

### 1.2 Extract Module - Progress Tracking Implementation

**Location**: `extract/pbd_io/progress.py`
**Dependencies**: None
**Priority**: HIGH - Breaking inheritance chain

**Implementation Steps**:
```python
# extract/pbd_io/progress.py
class BaseProgressHandler:
    """Base class for progress tracking."""
    
    def update(self, value: int, item_name: Optional[str] = None) -> None:
        """Update progress to specified value."""
        # Default implementation: log progress
        if hasattr(self, 'logger'):
            self.logger.debug(f"Progress: {value}% - {item_name or 'Processing'}")
    
    def finish(self) -> None:
        """Mark progress as complete."""
        # Default implementation: log completion
        if hasattr(self, 'logger'):
            self.logger.info("Progress: Complete")
        self.update(100, "Complete")
```

### 1.3 Model Module - Expression Evaluation

**Location**: `model/entities/expressions.py`
**Dependencies**: Type system
**Priority**: HIGH - Core functionality missing

**Implementation Steps**:
```python
# model/entities/expressions.py
class PBExpression:
    def evaluate(self) -> Any:
        """Evaluate the expression."""
        # Implementation strategy:
        # 1. Implement visitor pattern for expression evaluation
        # 2. Handle type coercion
        # 3. Support runtime context
        # 4. Error handling for invalid operations
        
class ExpressionEvaluator:
    """Visitor for evaluating expressions."""
    
    def visit_literal(self, node: Literal) -> Any:
        return node.value
    
    def visit_binary_expression(self, node: BinaryExpression) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self._apply_operator(node.operator, left, right)
    
    def visit_unary_expression(self, node: UnaryExpression) -> Any:
        operand = self.visit(node.operand)
        return self._apply_unary_operator(node.operator, operand)
```

### 1.4 SQL Transformer - Visitor Methods

**Location**: `parse/visitors/sql_transformer.py`
**Dependencies**: SQL grammar
**Priority**: HIGH - Blocking SQL parsing

**Implementation Steps**:
```python
# parse/visitors/sql_transformer.py
class SQLTransformer(Transformer):
    """Transform SQL parse tree to AST."""
    
    def select_statement(self, items):
        """Transform SELECT statement."""
        # Extract components: SELECT, FROM, WHERE, etc.
        # Build SQLSelectStatement AST node
        # Handle subqueries recursively
    
    def insert_statement(self, items):
        """Transform INSERT statement."""
        # Handle VALUES and SELECT variants
        # Build SQLInsertStatement AST node
    
    def update_statement(self, items):
        """Transform UPDATE statement."""
        # Handle SET clause and WHERE conditions
        # Build SQLUpdateStatement AST node
    
    def delete_statement(self, items):
        """Transform DELETE statement."""
        # Handle WHERE conditions
        # Build SQLDeleteStatement AST node
```

## Phase 2: Core Pipeline Completion (Week 2-3)

### 2.1 Parse Module - LibraryManager Implementation

**Location**: `parse/library.py` (new file)
**Dependencies**: GrammarManager
**Priority**: MEDIUM - Import resolution

**Implementation Steps**:
```python
# parse/library.py
class LibraryManager:
    """Manages PowerBuilder library imports and dependencies."""
    
    def __init__(self, library_paths: List[Path]):
        self.library_paths = library_paths
        self._cache: Dict[str, 'Library'] = {}
        self._import_graph: Dict[str, Set[str]] = {}
    
    def resolve_import(self, import_name: str) -> Optional['Library']:
        """Resolve an import to a library."""
        # Search strategy:
        # 1. Check cache
        # 2. Search in library paths
        # 3. Handle wildcards
        # 4. Build dependency graph
    
    def get_exported_symbols(self, library: 'Library') -> Dict[str, Any]:
        """Get all exported symbols from a library."""
        
    def check_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies."""
```

### 2.2 Generate Module - Code Generation Implementation

**Location**: `generate/generate_coordinator.py`
**Dependencies**: Template system
**Priority**: MEDIUM - End-to-end functionality

**Implementation Steps**:
```python
# Enhanced generate_coordinator.py
def generate_from_ast(ast_data: dict, output_dir: Path) -> Dict[str, Path]:
    """Generate code from AST data."""
    results = {}
    
    # 1. Extract metadata from AST
    metadata = extract_metadata(ast_data)
    
    # 2. Generate models
    if metadata.get('datawindows'):
        model_files = generate_sqlmodel_models(metadata['datawindows'], output_dir / 'models')
        results['models'] = model_files
    
    # 3. Generate services
    if metadata.get('business_logic'):
        service_files = generate_service_layer(metadata['business_logic'], output_dir / 'services')
        results['services'] = service_files
    
    # 4. Generate UI
    if metadata.get('ui_components'):
        ui_files = generate_flutter_ui(metadata['ui_components'], output_dir / 'flutter')
        results['ui'] = ui_files
    
    return results

def extract_relationships_from_sql(sql: str) -> List[Dict[str, Any]]:
    """Extract foreign key relationships from SQL."""
    # Parse JOIN clauses
    # Identify FK patterns
    # Return relationship metadata
```

### 2.3 Parse Module - Error Recovery

**Location**: `parse/error_recovery.py` (new file)
**Dependencies**: Parser infrastructure
**Priority**: MEDIUM - Robustness

**Implementation Steps**:
```python
# parse/error_recovery.py
class ErrorRecoveryStrategy:
    """Strategies for recovering from parse errors."""
    
    def sync_to_keyword(self, parser, keywords: Set[str]) -> bool:
        """Synchronize parser to next keyword."""
        
    def skip_to_delimiter(self, parser, delimiters: Set[str]) -> bool:
        """Skip tokens until delimiter found."""
        
    def insert_missing_token(self, parser, expected: str) -> bool:
        """Insert missing token and continue."""
        
    def remove_extra_token(self, parser) -> bool:
        """Remove unexpected token and continue."""

class RecoveringParser(PowerBuilderParser):
    """Parser with error recovery capabilities."""
    
    def parse_with_recovery(self, content: str) -> AST:
        """Parse with automatic error recovery."""
        try:
            return self.parse(content)
        except ParseError as e:
            # Apply recovery strategies
            # Collect errors for reporting
            # Return partial AST with error nodes
```

### 2.4 Model Module - Relationship Definitions

**Location**: `model/relationships.py` (new file)
**Dependencies**: Entity models
**Priority**: MEDIUM - Data modeling

**Implementation Steps**:
```python
# model/relationships.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class RelationshipType(Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"

@dataclass
class Relationship:
    """Represents a relationship between entities."""
    name: str
    source_entity: str
    target_entity: str
    relationship_type: RelationshipType
    source_key: str
    target_key: str
    cascade_delete: bool = False
    cascade_update: bool = False
    
class RelationshipManager:
    """Manages entity relationships."""
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship definition."""
        
    def get_relationships_for_entity(self, entity_name: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        
    def validate_relationships(self) -> List[str]:
        """Validate all relationships are consistent."""
```

## Phase 3: Advanced Features (Week 4)

### 3.1 Parse Module - Type and Enum Handling

**Location**: `parse/type_resolver.py` (new file)
**Dependencies**: Type system
**Priority**: LOW - Advanced feature

**Implementation Steps**:
```python
# parse/type_resolver.py
class TypeResolver:
    """Resolves custom types and enums."""
    
    def __init__(self):
        self._custom_types: Dict[str, TypeDefinition] = {}
        self._enums: Dict[str, EnumDefinition] = {}
    
    def register_type(self, name: str, definition: TypeDefinition) -> None:
        """Register a custom type."""
        
    def register_enum(self, name: str, values: List[str]) -> None:
        """Register an enum type."""
        
    def resolve_type(self, type_name: str) -> Optional[TypeDefinition]:
        """Resolve a type name to its definition."""
        
    def is_compatible(self, type1: str, type2: str) -> bool:
        """Check if two types are compatible."""
```

### 3.2 Generate Module - Validation Logic

**Location**: `generate/validators.py` (new file)
**Dependencies**: Model definitions
**Priority**: LOW - Enhancement

**Implementation Steps**:
```python
# generate/validators.py
class ValidationGenerator:
    """Generates validation logic from constraints."""
    
    def generate_field_validator(self, field: FieldDefinition) -> str:
        """Generate validation for a field."""
        validators = []
        
        if field.required:
            validators.append(self._required_validator(field))
        if field.min_length:
            validators.append(self._min_length_validator(field))
        if field.max_length:
            validators.append(self._max_length_validator(field))
        if field.pattern:
            validators.append(self._pattern_validator(field))
            
        return self._combine_validators(validators)
    
    def generate_model_validator(self, model: ModelDefinition) -> str:
        """Generate model-level validation."""
        # Cross-field validation
        # Business rule validation
        # Custom validation logic
```

### 3.3 Generate Module - Test Generation

**Location**: `generate/test_generator.py` (new file)
**Dependencies**: Code generation
**Priority**: LOW - Quality enhancement

**Implementation Steps**:
```python
# generate/test_generator.py
class TestGenerator:
    """Generates unit tests for generated code."""
    
    def generate_model_tests(self, model: ModelDefinition) -> str:
        """Generate tests for a model."""
        # Test creation
        # Test validation
        # Test relationships
        # Test business logic
    
    def generate_service_tests(self, service: ServiceDefinition) -> str:
        """Generate tests for a service."""
        # Test CRUD operations
        # Test business methods
        # Test error handling
        # Test authorization
    
    def generate_ui_tests(self, component: UIComponent) -> str:
        """Generate UI tests."""
        # Widget tests
        # Integration tests
        # User flow tests
```

### 3.4 Generate Module - Documentation Generation

**Location**: `generate/doc_generator.py` (new file)
**Dependencies**: AST analysis
**Priority**: LOW - Documentation

**Implementation Steps**:
```python
# generate/doc_generator.py
class DocumentationGenerator:
    """Generates documentation from code and comments."""
    
    def generate_api_docs(self, services: List[ServiceDefinition]) -> str:
        """Generate API documentation."""
        # OpenAPI/Swagger spec
        # Endpoint documentation
        # Request/response examples
    
    def generate_model_docs(self, models: List[ModelDefinition]) -> str:
        """Generate model documentation."""
        # Field descriptions
        # Relationship diagrams
        # Usage examples
    
    def generate_architecture_docs(self, project: ProjectDefinition) -> str:
        """Generate architecture documentation."""
        # Component diagrams
        # Sequence diagrams
        # Deployment guides
```

## Phase 4: Testing and Integration (Week 5)

### 4.1 Comprehensive Test Suite

**Priority**: CRITICAL - Quality assurance

**Test Categories**:
1. **Unit Tests**: Each new component
2. **Integration Tests**: Component interactions
3. **End-to-End Tests**: Full pipeline
4. **Performance Tests**: Large file handling
5. **Regression Tests**: Existing functionality

### 4.2 Performance Optimization

**Areas**:
1. Grammar caching optimization
2. Parallel processing for large projects
3. Memory optimization for AST handling
4. Template compilation caching

### 4.3 Documentation Updates

**Documents to Update**:
1. API documentation
2. User guides
3. Developer documentation
4. Architecture diagrams

## Implementation Order

### Week 1: Critical Infrastructure
1. GrammarManager (parse/grammar.py)
2. Progress tracking (extract/pbd_io/progress.py)
3. Expression evaluation (model/entities/expressions.py)
4. SQL transformer methods (parse/visitors/sql_transformer.py)

### Week 2: Core Pipeline
1. LibraryManager (parse/library.py)
2. Code generation from AST (generate/generate_coordinator.py)
3. Relationship extraction (generate/generate_coordinator.py)
4. Error recovery (parse/error_recovery.py)

### Week 3: Model Enhancements
1. Relationship definitions (model/relationships.py)
2. Type resolver (parse/type_resolver.py)
3. Enhanced templates (generate/templates/)

### Week 4: Advanced Features
1. Validation generation (generate/validators.py)
2. Test generation (generate/test_generator.py)
3. Documentation generation (generate/doc_generator.py)

### Week 5: Testing and Polish
1. Complete test coverage to 80%
2. Performance optimization
3. Documentation updates
4. Bug fixes and refinements

## Success Metrics

1. **Test Coverage**: Achieve 80% coverage
2. **End-to-End Success**: Full pipeline working for sample apps
3. **Performance**: Process typical PBD in <5 seconds
4. **Quality**: All linting/type checking passing
5. **Documentation**: Complete API docs and guides

## Risk Mitigation

1. **Incremental Implementation**: Each component independently testable
2. **Backward Compatibility**: Maintain existing interfaces
3. **Feature Flags**: New features behind flags initially
4. **Continuous Integration**: Test each commit
5. **Regular Reviews**: Code review after each phase

---

This plan provides a structured approach to completing all TODOs and stubs in the SIME Finch project, prioritizing critical infrastructure first and building toward advanced features.