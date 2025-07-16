"""Base types and interfaces to prevent circular dependencies.

This module provides foundational types that can be imported by any module
without creating circular dependencies.
"""

from .types import *
from .interfaces import *

__all__ = [
    # Base types
    'NodeKind',
    'Position',
    'SourceLocation',
    'Identifier',
    'QualifiedName',
    'SourceAnchor',
    'PBNode',
    'TypeReference',
    'Parameter',
    'Variable',
    'Metadata',
    'NodeAttributes',
    
    # Base interfaces
    'INode',
    'IVisitor',
    'ITransformer',
    'IValidator',
    'IAnalyzer',
    'ISourced',
    'ITyped',
    'IScoped',
    'IScope',
    'ISymbol',
    'INamedEntity',
    'IParser',
    'ICodeGenerator',
    'ISemanticModel',
    'INodeFactory',
    'ITypeFactory',
]