"""Enhanced structured decompiler with dynamic indentation support.

This module provides an improved version of the structured decompiler that uses
dynamic indentation filters for better code generation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from generate.jinja_filters import register_filters

logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Represents a structured code block."""
    type: str  # 'if', 'while', 'for', 'try', 'function', etc.
    statements: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Control flow specific fields
    condition: str | None = None
    else_statements: list[Any] | None = None

    # Loop specific fields
    variable: str | None = None
    start: str | None = None
    end: str | None = None

    # Try-catch specific fields
    try_statements: list[Any] | None = None
    catch_blocks: list[dict[str, Any]] | None = None
    finally_statements: list[Any] | None = None

    # Function/event specific fields
    name: str | None = None
    parameters: list[str] | None = None
    return_type: str | None = None

    # Choose-case specific fields
    expression: str | None = None
    cases: list[dict[str, Any]] | None = None
    default_statements: list[Any] | None = None

    # Other fields
    label: str | None = None
    comment: str | None = None
    sql_statement: str | None = None
    operand: str | None = None


class StructuredDecompilerV2:
    """Enhanced structured decompiler with dynamic indentation."""

    def __init__(self, template_dir: Path | None = None):
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

    def decompile(self, blocks: list[CodeBlock],
                  base_indent: int = 0,
                  header_comment: str | None = None) -> str:
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
            'header_comment': header_comment,
        }

        return template.render(**context)

    def create_if_block(self, condition: str,
                       then_statements: list[Any],
                       else_statements: list[Any] | None = None) -> CodeBlock:
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
            else_statements=else_statements,
        )

    def create_while_block(self, condition: str,
                          body_statements: list[Any]) -> CodeBlock:
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
            statements=body_statements,
        )

    def create_for_block(self, variable: str, start: str, end: str,
                        body_statements: list[Any]) -> CodeBlock:
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
            statements=body_statements,
        )

    def create_try_block(self, try_statements: list[Any],
                        catch_blocks: list[dict[str, Any]],
                        finally_statements: list[Any] | None = None) -> CodeBlock:
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
            finally_statements=finally_statements,
        )

    def create_function_block(self, name: str,
                             parameters: list[str],
                             body_statements: list[Any],
                             return_type: str | None = None) -> CodeBlock:
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
            return_type=return_type,
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
            label=label_name,
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
            comment=comment_text,
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
                                "discount = discount + 50",
                            ],
                        ),
                    ],
                    else_statements=[
                        decompiler.create_if_block(
                            condition='customer_type == "Regular"',
                            then_statements=[
                                "discount = price * 0.10",
                            ],
                            else_statements=[
                                "discount = 0",
                            ],
                        ),
                    ],
                ),
                "return discount",
            ],
            return_type="decimal",
        ),
    ]

    # Generate the decompiled code
    header = """// Decompiled from PowerBuilder
// Original file: pricing_module.pbl"""

    code = decompiler.decompile(blocks, header_comment=header)
    print(code)


if __name__ == "__main__":
    example_usage()
