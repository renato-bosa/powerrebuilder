"""PowerBuilder type model compatibility layer.

This module provides backward compatibility aliases for type classes.
New code should use model.ast.types directly.
"""

from ..ast.types import Type as PBBasicTypeNode
from ..ast.types import CustomType as PBCustomTypeNode
from ..ast.types import Type as PBBasicType
from ..ast.types import ArrayType as PBArrayType

# For backward compatibility, map the old field names
class PBBasicTypeNode(PBBasicTypeNode):
    """Basic type node - compatibility wrapper."""
    
    def __init__(self, basic_type: str = "integer", **kwargs):
        super().__init__(name=basic_type, category=None, **kwargs)
        self.basic_type = self.name


class PBCustomTypeNode(PBCustomTypeNode):
    """Custom type node - compatibility wrapper."""
    
    def __init__(self, identifier: str = None, **kwargs):
        super().__init__(name=identifier or "custom", category=None, namespace=None, **kwargs)
        self.identifier = self.name
