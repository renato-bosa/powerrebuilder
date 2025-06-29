"""Template validation system for code generation.

This module provides comprehensive validation for Jinja2 templates used in code generation,
ensuring syntax correctness, proper context usage, and valid output generation.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Tuple

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError, meta
from jinja2.exceptions import UndefinedError
from jinja2.nodes import Node

logger = logging.getLogger(__name__)


class TemplateValidationError(Exception):
    """Base exception for template validation errors."""

    def __init__(self, message: str, template_name: str, details: dict[str, Any | None] = None) -> None:
        super().__init__(message)
        self.template_name = template_name
        self.details = details or {}


class TemplateSyntaxValidator:
    """Validates Jinja2 template syntax."""

    def __init__(self, env: Environment) -> None:




        """Initialize the syntax validator.

        Args:
            env: Jinja2 environment
        """
        self.env = env

    def validate(self, template_name: str) -> tuple[bool, str | None]:




        """Validate template syntax.

        Args:
            template_name: Name of the template file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to compile the template
            source, _, _ = self.env.loader.get_source(self.env, template_name)
            self.env.compile(source, template_name)
            return True, None
        except TemplateSyntaxError as e:
            error_msg = f"Syntax error in {template_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error validating {template_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


class TemplateContextValidator:
    """Validates template context usage."""

    def __init__(self, env: Environment) -> None:




        """Initialize the context validator.

        Args:
            env: Jinja2 environment
        """
        self.env = env

    def extract_variables(self, template_name: str) -> set[str]:




        """Extract all variables used in a template.

        Args:
            template_name: Name of the template file

        Returns:
            Set of variable names used in the template
        """
        try:
            source, _, _ = self.env.loader.get_source(self.env, template_name)
            ast_tree = self.env.parse(source)
            return meta.find_undeclared_variables(ast_tree)
        except Exception as e:
            logger.error("Failed to extract variables from %s: %s", template_name, e)
            return set()

    def validate_context(self, template_name: str, expected_vars: set[str], provided_context: dict[str, Any]) -> tuple[bool, list[str]]:




        """Validate that template context matches expectations.

        Args:
            template_name: Name of the template file
            expected_vars: Expected variables the template should use
            provided_context: Context dictionary to validate

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Extract variables used in template
        used_vars = self.extract_variables(template_name)

        # Check for undefined variables
        undefined_vars = used_vars - set(provided_context.keys())
        if undefined_vars:
            issues.append(f"Undefined variables: {', '.join(sorted(undefined_vars))}")

        # Check for unused expected variables
        unused_expected = expected_vars - used_vars
        if unused_expected:
            issues.append(f"Expected but unused variables: {', '.join(sorted(unused_expected))}")

        # Check for unexpected variables in context
        unexpected_vars = set(provided_context.keys()) - expected_vars
        if unexpected_vars:
            issues.append(f"Unexpected context variables: {', '.join(sorted(unexpected_vars))}")

        return len(issues) == 0, issues


class TemplateOutputValidator:
    """Validates generated output from templates."""

    @staticmethod
    def validate_python_syntax(code: str) -> tuple[bool, str | None]:


        """Validate Python code syntax.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            error_msg = f"Python syntax error at line {e.lineno}: {e.msg}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error validating Python code: {str(e)}"
            return False, error_msg

    @staticmethod
    def validate_dart_syntax(code: str) -> tuple[bool, str | None]:


        """Basic validation for Dart code syntax.

        Args:
            code: Dart code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic checks for Dart syntax
        issues = []

        # Check for balanced braces
        brace_count = code.count('{') - code.count('}')
        if brace_count != 0:
            issues.append(f"Unbalanced braces: {brace_count} extra '{{' found")

        # Check for balanced parentheses
        paren_count = code.count('(') - code.count(')')
        if paren_count != 0:
            issues.append(f"Unbalanced parentheses: {paren_count} extra '(' found")

        # Check for balanced brackets
        bracket_count = code.count('[') - code.count(']')
        if bracket_count != 0:
            issues.append(f"Unbalanced brackets: {bracket_count} extra '[' found")

        # Check for semicolons at end of statements (simplified check)
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not any(stripped.endswith(char) for char in ['', '{', '}', ',', ':', ')']):
                # Check if it's not a comment or annotation
                if not stripped.startswith('//') and not stripped.startswith('@'):
                    # Check if it's not a control structure
                    if not any(stripped.startswith(kw) for kw in ['if', 'else', 'for', 'while', 'class', 'enum']):
                        issues.append(f"Line {i+1} might be missing semicolon: {stripped[:50]}...")

        if issues:
            return False, "; ".join(issues)
        return True, None


class TemplateConventionValidator:
    """Validates template conventions and standards."""

    def __init__(self, template_dir: Path) -> None:




        """Initialize the convention validator.

        Args:
            template_dir: Root template directory
        """
        self.template_dir = template_dir

    def validate_naming(self, template_name: str) -> tuple[bool, str | None]:




        """Validate template naming conventions.

        Args:
            template_name: Name of the template file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        if not template_name.endswith(('.jinja2', '.j2', '.jinja')):
            return False, f"Template {template_name} should have .jinja2 extension"

        # Check naming pattern (lowercase with underscores)
        # For templates that generate files with extensions (e.g., model.py.jinja2),
        # we need to handle the double extension case
        path = Path(template_name)
        base_name = path.stem

        # If the base name has an extension (e.g., model.py), check the part before the extension
        if '.' in base_name:
            name_to_check = base_name.split('.')[0]
        else:
            name_to_check = base_name

        if not re.match(r'^[a-z][a-z0-9_]*$', name_to_check):
            return False, f"Template {name_to_check} should use lowercase_underscore naming"

        return True, None

    def validate_structure(self, template_content: str) -> tuple[bool, list[str]]:




        """Validate template structure and required blocks.

        Args:
            template_content: Template content

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check for file header comment
        if not template_content.strip().startswith('{#'):
            issues.append("Template should start with a header comment {# ... #}")

        # Check for proper indentation (no tabs)
        if '\t' in template_content:
            issues.append("Template should use spaces, not tabs for indentation")

        # Check for trailing whitespace
        lines = template_content.split('\n')
        for i, line in enumerate(lines):
            if line.rstrip() != line:
                issues.append(f"Line {i+1} has trailing whitespace")

        return len(issues) == 0, issues


class TemplateValidator:
    """Main template validator orchestrating all validation types."""

    def __init__(self, template_dir: str) -> None:




        """Initialize the template validator.

        Args:
            template_dir: Directory containing templates
        """
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.syntax_validator = TemplateSyntaxValidator(self.env)
        self.context_validator = TemplateContextValidator(self.env)
        self.output_validator = TemplateOutputValidator()
        self.convention_validator = TemplateConventionValidator(self.template_dir)

    def validate_template(self, template_name: str, 
                         expected_context: dict[str, Any | None] = None,
                         sample_context: dict[str, Any | None] = None,
                         validate_output: bool = True) -> dict[str, Any]:




        """Perform comprehensive validation on a template.

        Args:
            template_name: Name of the template file
            expected_context: Expected context variables and types
            sample_context: Sample context for test rendering
            validate_output: Whether to validate the generated output

        Returns:
            Dictionary with validation results
        """
        results = {
            'template': template_name,
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # 1. Validate naming conventions
        valid, error = self.convention_validator.validate_naming(template_name)
        if not valid:
            results['errors'].append(f"Naming: {error}")
            results['valid'] = False

        # 2. Validate syntax
        valid, error = self.syntax_validator.validate(template_name)
        if not valid:
            results['errors'].append(f"Syntax: {error}")
            results['valid'] = False
            return results  # Can't continue if syntax is invalid

        # 3. Load template content for structure validation
        try:
            source, _, _ = self.env.loader.get_source(self.env, template_name)
            valid, issues = self.convention_validator.validate_structure(source)
            if not valid:
                results['warnings'].extend([f"Structure: {issue}" for issue in issues])
        except Exception as e:
            results['errors'].append(f"Failed to load template: {str(e)}")
            results['valid'] = False
            return results

        # 4. Validate context usage if expected context provided
        if expected_context:
            expected_vars = set(expected_context.keys())
            test_context = sample_context or expected_context
            valid, issues = self.context_validator.validate_context(
                template_name, expected_vars, test_context
            )
            if not valid:
                results['warnings'].extend([f"Context: {issue}" for issue in issues])

        # 5. Validate output if sample context provided
        if validate_output and sample_context:
            try:
                template = self.env.get_template(template_name)
                output = template.render(**sample_context)

                # Determine output type based on template name
                if template_name.endswith('.py.jinja2'):
                    valid, error = self.output_validator.validate_python_syntax(output)
                    if not valid:
                        results['errors'].append(f"Output: {error}")
                        results['valid'] = False
                elif template_name.endswith('.dart.jinja2'):
                    valid, error = self.output_validator.validate_dart_syntax(output)
                    if not valid:
                        results['warnings'].append(f"Output: {error}")

            except Exception as e:
                results['errors'].append(f"Render error: {str(e)}")
                results['valid'] = False

        return results

    def validate_all_templates(self) -> dict[str, list[dict[str, Any]]]:




        """Validate all templates in the template directory.

        Returns:
            Dictionary with validation results for all templates
        """
        results = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }

        # Find all template files
        template_files = list(self.template_dir.rglob('*.jinja2'))
        template_files.extend(list(self.template_dir.rglob('*.j2')))
        template_files.extend(list(self.template_dir.rglob('*.jinja')))

        for template_file in template_files:
            # Get relative path from template directory
            template_name = str(template_file.relative_to(self.template_dir))

            # Validate template
            validation_result = self.validate_template(template_name)

            if not validation_result['valid']:
                results['invalid'].append(validation_result)
            elif validation_result['warnings']:
                results['warnings'].append(validation_result)
            else:
                results['valid'].append(validation_result)

        return results