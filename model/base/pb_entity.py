"""PowerBuilder entity base classes.

This module provides base entity classes for PowerBuilder models.
"""


from dataclasses import dataclass

from ..utils.base import PBNode


@dataclass
class PBSourcedEntity(PBNode):
    """Base class for PowerBuilder entities with source information.

    This class extends PBNode to provide entities with source tracking
    and a qualified name property.
    """

    name: str

    @property
    def qualified_name(self) -> str:

        
        """Get the qualified name of this entity.

        Subclasses can override this to provide namespace-qualified names.
        """
        return self.name