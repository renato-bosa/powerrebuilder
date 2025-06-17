"""Tests for CFG integration in the model module."""

import pytest
from pathlib import Path
from model.cfg_integration import (
    ModelCFGVisualizer,
    CFGGenerationResult,
    visualize_control_flow
)
from model.ast.functions import FunctionDefinition, Signature, Parameter
from model.ast.ast_nodes import Block
from model.entities.pb_event import PBEvent
from model.base.pb_behavioral import PBBehavioralNode
from decompile.visualization.cfg_visualizer import VisualizationOptions, VisualizationLevel


class TestModelCFGVisualizer:
    """Test cases for ModelCFGVisualizer."""
    
    def test_initialization(self):
        """Test CFG visualizer initialization."""
        visualizer = ModelCFGVisualizer()
        assert visualizer.options is not None
        assert visualizer.visualizer is not None
        
        # Test with custom options
        options = VisualizationOptions(
            level=VisualizationLevel.CLASS,
            show_instructions=False
        )
        visualizer = ModelCFGVisualizer(options)
        assert visualizer.options.level == VisualizationLevel.CLASS
        assert not visualizer.options.show_instructions
        
    def test_visualize_function_no_pcode(self):
        """Test function visualization without P-code."""
        visualizer = ModelCFGVisualizer()
        
        # Create a simple function
        function = FunctionDefinition(
            signature=Signature(name="test_function"),
            body=Block()
        )
        
        result = visualizer.visualize_function(function)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success
        assert "No P-code instructions" in result.error_message
        
    def test_visualize_event_no_pcode(self):
        """Test event visualization without P-code."""
        visualizer = ModelCFGVisualizer()
        
        # Create a simple event
        event = PBEvent(name="ue_clicked")
        
        result = visualizer.visualize_event(event)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success
        assert "No P-code instructions" in result.error_message
        
    def test_visualize_class_no_methods(self):
        """Test class visualization without methods."""
        visualizer = ModelCFGVisualizer()
        
        # Create an empty class
        class_node = PBBehavioralNode(name="n_test_class")
        
        result = visualizer.visualize_class(class_node)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success
        assert "No methods with P-code" in result.error_message
        
    def test_visualize_control_flow_function(self):
        """Test the convenience function with a function."""
        function = FunctionDefinition(
            signature=Signature(name="test_function"),
            body=Block()
        )
        
        result = visualize_control_flow(function)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success  # No P-code provided
        
    def test_visualize_control_flow_event(self):
        """Test the convenience function with an event."""
        event = PBEvent(name="ue_process")
        
        result = visualize_control_flow(event)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success  # No P-code provided
        
    def test_visualize_control_flow_class(self):
        """Test the convenience function with a class."""
        class_node = PBBehavioralNode(name="n_test_service")
        
        result = visualize_control_flow(class_node)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success  # No methods
        
    def test_visualize_control_flow_unsupported(self):
        """Test the convenience function with unsupported node type."""
        # Use any other node type
        from model.ast.ast_nodes import Statement
        node = Statement()
        
        result = visualize_control_flow(node)
        
        assert isinstance(result, CFGGenerationResult)
        assert not result.success
        assert "Unsupported node type" in result.error_message
        
    def test_cfg_result_structure(self):
        """Test CFGGenerationResult structure."""
        # Test successful result
        result = CFGGenerationResult(
            success=True,
            dot_content="digraph G { A -> B; }",
            output_path=Path("test.dot")
        )
        
        assert result.success
        assert result.dot_content == "digraph G { A -> B; }"
        assert result.output_path == Path("test.dot")
        assert result.error_message is None
        
        # Test failed result
        result = CFGGenerationResult(
            success=False,
            error_message="Test error"
        )
        
        assert not result.success
        assert result.error_message == "Test error"
        assert result.dot_content is None
        assert result.output_path is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])