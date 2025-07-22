"""Relationship management service for PowerBuilder entities."""
import logging
from typing import Any, Dict, List, Set

from src.model.interfaces import IRelationshipManager

logger = logging.getLogger(__name__)


class RelationshipManager(IRelationshipManager):
    """Manages relationships between PowerBuilder entities."""
    
    def __init__(self):
        """Initialize the relationship manager."""
        # Entity relationships tracking (from -> to)
        self._entity_relationships: Dict[str, Set[str]] = {}
        # Entity dependencies (to -> from)
        self._entity_dependencies: Dict[str, Set[str]] = {}
        # Relationship types
        self._relationship_types: Dict[tuple[str, str], str] = {}
    
    def add_relationship(
        self, 
        from_entity: str, 
        to_entity: str, 
        relationship_type: str = "uses"
    ) -> None:
        """Add a relationship between entities.
        
        Args:
            from_entity: Source entity (format: "type:name")
            to_entity: Target entity (format: "type:name")
            relationship_type: Type of relationship
        """
        # Initialize sets if needed
        if from_entity not in self._entity_relationships:
            self._entity_relationships[from_entity] = set()
        if to_entity not in self._entity_dependencies:
            self._entity_dependencies[to_entity] = set()
        
        # Add relationship
        self._entity_relationships[from_entity].add(to_entity)
        self._entity_dependencies[to_entity].add(from_entity)
        
        # Store relationship type
        self._relationship_types[(from_entity, to_entity)] = relationship_type
        
        logger.debug("Added relationship: %s %s %s", from_entity, relationship_type, to_entity)
    
    def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity.
        
        Args:
            entity_name: Entity name (format: "type:name")
            
        Returns:
            List of relationships with type and target
        """
        relationships = []
        
        # Get outgoing relationships
        for target in self._entity_relationships.get(entity_name, set()):
            rel_type = self._relationship_types.get((entity_name, target), "uses")
            relationships.append({
            'from': entity_name,
                'to': target,
                'type': rel_type,
                'direction': 'outgoing'
            })
        
        # Get incoming relationships
        for source in self._entity_dependencies.get(entity_name, set()):
            rel_type = self._relationship_types.get((source, entity_name), "uses")
            relationships.append({
            'from': source,
                'to': entity_name,
                'type': rel_type,
                'direction': 'incoming'
            })
        
        return relationships
    
    def get_entity_dependencies(self, entity_name: str) -> List[str]:
        """Get entity dependencies.
        
        Args:
            entity_name: Entity name (format: "type:name")
            
        Returns:
            List of dependency names
        """
        # Get entities that this entity depends on
        dependencies = list(self._entity_relationships.get(entity_name, set()))
        return sorted(dependencies)
    
    def get_dependent_entities(self, entity_name: str) -> List[str]:
        """Get entities that depend on this entity.
        
        Args:
            entity_name: Entity name (format: "type:name")
            
        Returns:
            List of dependent entity names
        """
        dependents = list(self._entity_dependencies.get(entity_name, set()))
        return sorted(dependents)
    
    def validate_all_relationships(self) -> List[str]:
        """Validate all relationships.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for circular dependencies
        for entity_key in self._entity_relationships:
            cycle = self._find_cycle(entity_key)
            if cycle:
                errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")
        
        # Check for orphaned relationships (relationships to non-existent entities)
        all_entities = set(self._entity_relationships.keys()) | set(self._entity_dependencies.keys())
        
        for entity_key, relationships in self._entity_relationships.items():
            for related in relationships:
                if related not in all_entities:
                    errors.append(
                    f"Entity {entity_key} has relationship to non-existent entity {related}"
                    )
        
        return errors
    
    def _find_cycle(self, start_node: str) -> List[str] | None:
        """Find a cycle starting from the given node.
        
        Args:
            start_node: Node to start from
            
        Returns:
            List representing the cycle path, or None if no cycle
        """
        visited = set()
        stack = []
        
        def has_cycle(node: str) -> bool:
            if node in stack:
                # Found cycle - return the cycle path
                cycle_start = stack.index(node)
                self._cycle_path = stack[cycle_start:] + [node]
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            stack.append(node)
            
            for related in self._entity_relationships.get(node, set()):
                if has_cycle(related):
                    return True
            
            stack.pop()
            return False
        
        self._cycle_path = None
        if has_cycle(start_node):
            return self._cycle_path
        return None
    
    def remove_relationship(self, from_entity: str, to_entity: str) -> bool:
        """Remove a relationship between entities.
        
        Args:
            from_entity: Source entity
            to_entity: Target entity
            
        Returns:
            True if relationship was removed, False if it didn't exist
        """
        removed = False
        
        # Remove from relationships
        if from_entity in self._entity_relationships:
            if to_entity in self._entity_relationships[from_entity]:
                self._entity_relationships[from_entity].remove(to_entity)
                removed = True
        
        # Remove from dependencies
        if to_entity in self._entity_dependencies:
            if from_entity in self._entity_dependencies[to_entity]:
                self._entity_dependencies[to_entity].remove(from_entity)
        
        # Remove relationship type
        key = (from_entity, to_entity)
        if key in self._relationship_types:
            del self._relationship_types[key]
        
        if removed:
            logger.debug("Removed relationship: %s -> %s", from_entity, to_entity)
        
        return removed
    
    def clear_relationships(self) -> None:
        """Clear all relationships."""
        self._entity_relationships.clear()
        self._entity_dependencies.clear()
        self._relationship_types.clear()
        logger.debug("Cleared all relationships")
    
    def get_relationship_graph(self) -> Dict[str, List[str]]:
        """Get the entire relationship graph.
        
        Returns:
            Dictionary mapping entities to their relationships
        """
        graph = {}
        for entity, relationships in self._entity_relationships.items():
            graph[entity] = list(relationships)
        return graph
    
    def find_path(self, from_entity: str, to_entity: str) -> List[str] | None:
        """Find a path between two entities.
        
        Args:
            from_entity: Start entity
            to_entity: Target entity
            
        Returns:
            Path as list of entities, or None if no path exists
        """
        if from_entity == to_entity:
            return [from_entity]
        
        # BFS to find shortest path
        queue = [(from_entity, [from_entity])]
        visited = {from_entity}
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in self._entity_relationships.get(current, set()):
                if neighbor == to_entity:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None