"""Control Flow Graph integration for the model layer.

This module provides integration between the model AST representation
and the decompile module's CFG visualization capabilities.
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass

from model.utils.base import PBNode
from model.ast.ast_nodes import Statement, Expression
from model.ast.functions import FunctionDefinition, ProcedureDefinition
from model.entities.pb_event import PBEvent
from model.base.pb_behavioral import PBBehavioralNode
# Lazy imports to avoid circular dependencies
# These will be imported in the functions that use them

logger = logging.getLogger(__name__)


@dataclass
class CFGGenerationResult:
    """Result of CFG generation."""
    success: bool
    dot_content: Optional[str] = None
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    

class ModelCFGVisualizer:
    """Integrates CFG visualization with the model layer."""
    
    def __init__(self, options: Optional['VisualizationOptions'] = None):
        """Initialize the model CFG visualizer.
        
        Args:
            options: Visualization options
        """
        # Lazy import to avoid circular dependency
        from decompile.visualization.cfg_visualizer import (
            CFGVisualizer, VisualizationOptions
        )
        self.options = options or VisualizationOptions()
        self.visualizer = CFGVisualizer(self.options)
        
    def visualize_function(
        self, 
        function: Union[FunctionDefinition, ProcedureDefinition],
        pcode_data: Optional[bytes] = None,
        output_path: Optional[Path] = None
    ) -> CFGGenerationResult:
        """Generate CFG visualization for a function or procedure.
        
        Args:
            function: Function/procedure definition from the model
            pcode_data: Optional P-code data (if not provided, will try to extract)
            output_path: Optional path to save the DOT file
            
        Returns:
            CFGGenerationResult with the visualization
        """
        try:
            function_name = function.signature.name if function.signature else "unnamed_function"
            
            # Get P-code instructions
            instructions = self._get_pcode_instructions(function, pcode_data)
            if not instructions:
                return CFGGenerationResult(
                    success=False,
                    error_message=f"No P-code instructions found for {function_name}"
                )
                
            # Generate visualization
            dot_content = self.visualizer.visualize_method(
                function_name,
                instructions,
                output_path
            )
            
            return CFGGenerationResult(
                success=True,
                dot_content=dot_content,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error("Failed to visualize function: %s", e)
            return CFGGenerationResult(
                success=False,
                error_message=str(e)
            )
            
    def visualize_event(
        self,
        event: PBEvent,
        pcode_data: Optional[bytes] = None,
        output_path: Optional[Path] = None
    ) -> CFGGenerationResult:
        """Generate CFG visualization for an event handler.
        
        Args:
            event: Event definition from the model
            pcode_data: Optional P-code data
            output_path: Optional path to save the DOT file
            
        Returns:
            CFGGenerationResult with the visualization
        """
        try:
            event_name = event.name or "unnamed_event"
            
            # Get P-code instructions
            instructions = self._get_pcode_instructions(event, pcode_data)
            if not instructions:
                return CFGGenerationResult(
                    success=False,
                    error_message=f"No P-code instructions found for {event_name}"
                )
                
            # Generate visualization
            dot_content = self.visualizer.visualize_method(
                event_name,
                instructions,
                output_path
            )
            
            return CFGGenerationResult(
                success=True,
                dot_content=dot_content,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error("Failed to visualize event: %s", e)
            return CFGGenerationResult(
                success=False,
                error_message=str(e)
            )
            
    def visualize_class(
        self,
        class_node: PBBehavioralNode,
        pcode_map: Optional[Dict[str, bytes]] = None,
        output_path: Optional[Path] = None
    ) -> CFGGenerationResult:
        """Generate CFG visualization for an entire class.
        
        Args:
            class_node: Class/object definition from the model
            pcode_map: Optional map of method names to P-code data
            output_path: Optional path to save the DOT file
            
        Returns:
            CFGGenerationResult with the visualization
        """
        try:
            class_name = class_node.name or "unnamed_class"
            
            # Collect all methods and their instructions
            methods_instructions: Dict[str, List['PCodeInstruction']] = {}
            
            # Process functions if they exist
            if hasattr(class_node, 'functions'):
                for function in class_node.functions:
                    func_name = function.signature.name if hasattr(function, 'signature') else function.name
                    pcode_data = pcode_map.get(func_name) if pcode_map else None
                    instructions = self._get_pcode_instructions(function, pcode_data)
                    if instructions:
                        methods_instructions[func_name] = instructions
                        
            # Process methods if they exist
            if hasattr(class_node, 'methods'):
                for method in class_node.methods:
                    method_name = method.name if hasattr(method, 'name') else str(method)
                    pcode_data = pcode_map.get(method_name) if pcode_map else None
                    instructions = self._get_pcode_instructions(method, pcode_data)
                    if instructions:
                        methods_instructions[method_name] = instructions
                    
            # Process events if they exist
            if hasattr(class_node, 'events'):
                for event in class_node.events:
                    event_name = event.name if hasattr(event, 'name') else str(event)
                    pcode_data = pcode_map.get(event_name) if pcode_map else None
                    instructions = self._get_pcode_instructions(event, pcode_data)
                    if instructions:
                        methods_instructions[event_name] = instructions
                    
            if not methods_instructions:
                return CFGGenerationResult(
                    success=False,
                    error_message=f"No methods with P-code found in {class_name}"
                )
                
            # Generate visualization
            dot_content = self.visualizer.visualize_class(
                class_name,
                methods_instructions,
                output_path
            )
            
            return CFGGenerationResult(
                success=True,
                dot_content=dot_content,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error("Failed to visualize class: %s", e)
            return CFGGenerationResult(
                success=False,
                error_message=str(e)
            )
            
    def _get_pcode_instructions(
        self,
        node: PBNode,
        pcode_data: Optional[bytes] = None
    ) -> List['PCodeInstruction']:
        """Extract P-code instructions from a node.
        
        Args:
            node: AST node (function, event, etc.)
            pcode_data: Optional P-code data
            
        Returns:
            List of P-code instructions
        """
        instructions = []
        
        # If P-code data provided, decode it
        if pcode_data:
            try:
                # Lazy import to avoid circular dependency
                from decompile.core.pcode_decoder import PCodeDecoderV2
                decoder = PCodeDecoderV2()
                instructions = decoder.decode(pcode_data)
            except Exception as e:
                logger.warning("Failed to decode P-code: %s", e)
                
        # Try to extract from node attributes
        elif hasattr(node, 'pcode_instructions'):
            instructions = node.pcode_instructions
        elif hasattr(node, 'body') and hasattr(node.body, 'pcode_instructions'):
            instructions = node.body.pcode_instructions
            
        return instructions
        
    def generate_module_cfg(
        self,
        module_path: Path,
        output_dir: Optional[Path] = None
    ) -> List[CFGGenerationResult]:
        """Generate CFG visualizations for all functions in a module.
        
        Args:
            module_path: Path to the PowerBuilder module
            output_dir: Optional directory to save visualizations
            
        Returns:
            List of CFGGenerationResult for each function/method
        """
        results = []
        
        # This would require parsing the module and extracting all functions
        # For now, this is a placeholder for the full implementation
        logger.warning("Module-level CFG generation not yet fully implemented")
        
        return results


def visualize_control_flow(
    node: Union[FunctionDefinition, ProcedureDefinition, PBEvent, PBBehavioralNode],
    pcode_data: Optional[Union[bytes, Dict[str, bytes]]] = None,
    output_path: Optional[Path] = None,
    options: Optional['VisualizationOptions'] = None
) -> CFGGenerationResult:
    """Convenience function to visualize control flow for various node types.
    
    Args:
        node: AST node to visualize
        pcode_data: P-code data (bytes for single method, dict for class)
        output_path: Optional output path for DOT file
        options: Visualization options
        
    Returns:
        CFGGenerationResult
    """
    visualizer = ModelCFGVisualizer(options)
    
    if isinstance(node, (FunctionDefinition, ProcedureDefinition)):
        return visualizer.visualize_function(node, pcode_data, output_path)
    elif isinstance(node, PBEvent):
        return visualizer.visualize_event(node, pcode_data, output_path)
    elif isinstance(node, PBBehavioralNode):
        return visualizer.visualize_class(node, pcode_data, output_path)
    else:
        return CFGGenerationResult(
            success=False,
            error_message=f"Unsupported node type: {type(node).__name__}"
        )