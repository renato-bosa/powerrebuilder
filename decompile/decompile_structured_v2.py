"""Enhanced structured decompiler with dynamic indentation support.

This module provides an improved version of the structured decompiler that uses
dynamic indentation filters for better code generation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from jinja2 import Environment, FileSystemLoader
from generate.jinja_filters import register_filters

logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Represents a structured code block."""
    type: str  # 'if', 'while', 'for', 'try', 'function', etc.
    statements: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Control flow specific fields
    condition: Optional[str] = None
    else_statements: Optional[List[Any]] = None
    
    # Loop specific fields
    variable: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    
    # Try-catch specific fields
    try_statements: Optional[List[Any]] = None
    catch_blocks: Optional[List[Dict[str, Any]]] = None
    finally_statements: Optional[List[Any]] = None
    
    # Function/event specific fields
    name: Optional[str] = None
    parameters: Optional[List[str]] = None
    return_type: Optional[str] = None
    
    # Choose-case specific fields
    expression: Optional[str] = None
    cases: Optional[List[Dict[str, Any]]] = None
    default_statements: Optional[List[Any]] = None
    
    # Other fields
    label: Optional[str] = None
    comment: Optional[str] = None
    sql_statement: Optional[str] = None
    operand: Optional[str] = None


class StructuredDecompilerV2:
    """Enhanced structured decompiler with dynamic indentation."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the decompiler.
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        register_filters(self.env)
        
    def decompile(self, blocks: List[CodeBlock], 
                  base_indent: int = 0,
                  header_comment: Optional[str] = None) -> str:
        """Decompile a list of code blocks into structured code.
        
        Args:
            blocks: List of CodeBlock objects representing the program structure
            base_indent: Base indentation level (0 for top-level)
            header_comment: Optional header comment for the file
            
        Returns:
            Decompiled code as a string
        """
        template = self.env.get_template("structured_v2.py.jinja2")
        
        context = {
            'blocks': blocks,
            'base_indent': base_indent,
            'header_comment': header_comment
        }
        
        return template.render(**context)
    
    def create_if_block(self, condition: str, 
                       then_statements: List[Any],
                       else_statements: Optional[List[Any]] = None) -> CodeBlock:
        """Create an if-then-else block.
        
        Args:
            condition: The if condition expression
            then_statements: Statements in the then branch
            else_statements: Optional statements in the else branch
            
        Returns:
            CodeBlock representing the if statement
        """
        return CodeBlock(
            type='if',
            condition=condition,
            statements=then_statements,
            else_statements=else_statements
        )
    
    def create_while_block(self, condition: str, 
                          body_statements: List[Any]) -> CodeBlock:
        """Create a while loop block.
        
        Args:
            condition: The loop condition
            body_statements: Statements in the loop body
            
        Returns:
            CodeBlock representing the while loop
        """
        return CodeBlock(
            type='while',
            condition=condition,
            statements=body_statements
        )
    
    def create_for_block(self, variable: str, start: str, end: str,
                        body_statements: List[Any]) -> CodeBlock:
        """Create a for loop block.
        
        Args:
            variable: Loop variable name
            start: Start value expression
            end: End value expression
            body_statements: Statements in the loop body
            
        Returns:
            CodeBlock representing the for loop
        """
        return CodeBlock(
            type='for',
            variable=variable,
            start=start,
            end=end,
            statements=body_statements
        )
    
    def create_try_block(self, try_statements: List[Any],
                        catch_blocks: List[Dict[str, Any]],
                        finally_statements: Optional[List[Any]] = None) -> CodeBlock:
        """Create a try-catch-finally block.
        
        Args:
            try_statements: Statements in the try block
            catch_blocks: List of catch blocks, each with 'exception_type', 
                         'variable', and 'statements'
            finally_statements: Optional statements in the finally block
            
        Returns:
            CodeBlock representing the try-catch-finally structure
        """
        return CodeBlock(
            type='try',
            try_statements=try_statements,
            catch_blocks=catch_blocks,
            finally_statements=finally_statements
        )
    
    def create_function_block(self, name: str, 
                             parameters: List[str],
                             body_statements: List[Any],
                             return_type: Optional[str] = None) -> CodeBlock:
        """Create a function block.
        
        Args:
            name: Function name
            parameters: List of parameter names
            body_statements: Statements in the function body
            return_type: Optional return type
            
        Returns:
            CodeBlock representing the function
        """
        return CodeBlock(
            type='function',
            name=name,
            parameters=parameters,
            statements=body_statements,
            return_type=return_type
        )
    
    def create_label(self, label_name: str) -> CodeBlock:
        """Create a label block.
        
        Args:
            label_name: Name of the label (without colon)
            
        Returns:
            CodeBlock representing the label
        """
        return CodeBlock(
            type='label',
            label=label_name
        )
    
    def create_comment(self, comment_text: str) -> CodeBlock:
        """Create a comment block.
        
        Args:
            comment_text: Comment text (without // prefix)
            
        Returns:
            CodeBlock representing the comment
        """
        return CodeBlock(
            type='comment',
            comment=comment_text
        )


def example_usage():
    """Example of using the enhanced structured decompiler."""
    decompiler = StructuredDecompilerV2()
    
    # Create a sample function with nested structures
    blocks = [
        decompiler.create_function_block(
            name="calculate_discount",
            parameters=["price", "customer_type"],
            body_statements=[
                "// Calculate discount based on customer type",
                decompiler.create_if_block(
                    condition='customer_type == "VIP"',
                    then_statements=[
                        "discount = price * 0.20",
                        decompiler.create_if_block(
                            condition="price > 1000",
                            then_statements=[
                                "discount = discount + 50"
                            ]
                        )
                    ],
                    else_statements=[
                        decompiler.create_if_block(
                            condition='customer_type == "Regular"',
                            then_statements=[
                                "discount = price * 0.10"
                            ],
                            else_statements=[
                                "discount = 0"
                            ]
                        )
                    ]
                ),
                "return discount"
            ],
            return_type="decimal"
        )
    ]
    
    # Generate the decompiled code
    header = """// Decompiled from PowerBuilder
// Original file: pricing_module.pbl"""
    
    code = decompiler.decompile(blocks, header_comment=header)
    print(code)


if __name__ == "__main__":
    example_usage()