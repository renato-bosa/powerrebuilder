"""Enhanced DataWindow functionality for computed fields and validation.

This module provides enhanced processing for DataWindow computed fields
and validation rules, including type inference and expression parsing.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComputedField:
    """Enhanced computed field with type inference."""

    name: str
    expression: str
    original_expression: str
    inferred_type: str
    dependencies: list[str]  # Column names this field depends on
    is_aggregate: bool = False
    aggregate_function: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "name": self.name,
            "expression": self.expression,
            "type": self.inferred_type,
            "dependencies": self.dependencies,
            "is_aggregate": self.is_aggregate,
            "aggregate_function": self.aggregate_function,
        }


@dataclass
class ValidationRule:
    """Processed validation rule."""

    column_name: str
    rule_type: str  # required, min, max, pattern, custom
    rule_value: Any
    error_message: str
    dart_validator: str  # Generated Dart validation code
    python_validator: str  # Generated Python validation code

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "column_name": self.column_name,
            "rule_type": self.rule_type,
            "rule_value": self.rule_value,
            "error_message": self.error_message,
            "dart_validator": self.dart_validator,
            "python_validator": self.python_validator,
        }


class ComputedFieldProcessor:
    """Process DataWindow computed fields with type inference."""

    def __init__(self, expression_converter=None) -> None:
        """Initialize the processor.

        Args:
            expression_converter: Expression converter for target language
        """
        self.expression_converter = expression_converter

        # Aggregate functions
        self.aggregate_functions = {
            "sum",
            "avg",
            "count",
            "min",
            "max",
            "stddev",
            "variance",
            "first",
            "last",
        }

        # Type inference patterns
        self.type_patterns = {
            # Numeric operations
            r"[\+\-\*\/\%]": "double",
            r"\b(sum|avg|stddev|variance)\b": "double",
            r"\b(count|min|max)\b": "int",
            # String operations
            r"\b(trim|upper|lower|mid|left|right|concat)\b": "String",
            r"[\"'].*?[\"']": "String",
            # Date operations
            r"\b(today|now|date|time|year|month|day)\b": "DateTime",
            r"\b(daysafter|daysbefore|relativedate)\b": "DateTime",
            # Boolean operations
            r"\b(and|or|not)\b": "bool",
            r"[<>]=?|==|!=": "bool",
            r"\b(if|case)\b": "dynamic",  # Conditional can return any type
        }

    def process_computed_field(
        self, name: str, expression: str, columns: list[dict[str, str]] | None = None
    ) -> ComputedField:
        """Process a computed field with type inference.

        Args:
            name: Field name
            expression: PowerBuilder expression
            columns: Available columns for dependency analysis

        Returns:
            Enhanced ComputedField object
        """
        # Store original expression
        original_expression = expression

        # Extract dependencies
        dependencies = self._extract_dependencies(expression, columns)

        # Check if aggregate
        is_aggregate, aggregate_func = self._check_aggregate(expression)

        # Infer type
        inferred_type = self._infer_type(expression, columns, is_aggregate)

        # Convert expression to target language
        if self.expression_converter:
            converted_expr = self.expression_converter.convert_expression(expression)
        else:
            converted_expr = expression

        return ComputedField(
            name=name,
            expression=converted_expr,
            original_expression=original_expression,
            inferred_type=inferred_type,
            dependencies=dependencies,
            is_aggregate=is_aggregate,
            aggregate_function=aggregate_func,
        )

    def _extract_dependencies(
        self, expression: str, columns: list[dict[str, str]] | None = None
    ) -> list[str]:
        """Extract column dependencies from expression."""
        dependencies = []

        if not columns:
            return dependencies

        # Get column names
        column_names = [col.get("name", "") for col in columns]

        # Look for column references in expression
        for col_name in column_names:
            # Use word boundaries to match exact column names
            pattern = rf"\b{re.escape(col_name)}\b"
            if re.search(pattern, expression, re.IGNORECASE):
                dependencies.append(col_name)

        return list(set(dependencies))  # Remove duplicates

    def _check_aggregate(self, expression: str) -> tuple[bool, str | None]:
        """Check if expression contains aggregate functions."""
        expr_lower = expression.lower()

        for func in self.aggregate_functions:
            pattern = rf"\b{func}\s*\("
            if re.search(pattern, expr_lower):
                return True, func

        return False, None

    def _infer_type(
        self,
        expression: str,
        columns: list[dict[str, str]] | None = None,
        _is_aggregate: bool = False,
    ) -> str:
        """Infer the type of a computed field expression."""
        expr_lower = expression.lower()

        # Check type patterns
        for pattern, type_name in self.type_patterns.items():
            if re.search(pattern, expr_lower):
                return type_name

        # If expression references a single column, use its type
        if columns and len(self._extract_dependencies(expression, columns)) == 1:
            dep_col = self._extract_dependencies(expression, columns)[0]
            for col in columns:
                if col.get("name") == dep_col:
                    return col.get("data_type", "dynamic")

        # Check for numeric literals
        if re.match(r"^[\d\.\-\+]+$", expression.strip()):
            return "double" if "." in expression else "int"

        # Default to dynamic
        return "dynamic"

    def generate_computed_field_method(
        self, field: ComputedField, target: str = "flutter"
    ) -> list[str]:
        """Generate method to calculate computed field.

        Args:
            field: ComputedField object
            target: Target language ('flutter' or 'python')

        Returns:
            List of code lines
        """
        if target == "flutter":
            return self._generate_flutter_method(field)
        if target == "python":
            return self._generate_python_method(field)
        return []

    def _generate_flutter_method(self, field: ComputedField) -> list[str]:
        """Generate Flutter/Dart method for computed field."""
        lines = []

        # Method signature
        lines.append(
            f"{field.inferred_type} get{self._to_pascal_case(field.name)}(Map<String, dynamic> row) {{"
        )

        # Add null checks for dependencies
        if field.dependencies:
            lines.append("  // Check dependencies")
            for dep in field.dependencies:
                lines.append(f'  if (row["{dep}"] == null) return null;')
            lines.append("")

        # Add calculation
        lines.append("  // Calculate computed field")
        if field.is_aggregate:
            lines.append("  // Note: Aggregate calculations need access to all rows")
            lines.append(
                "  // In practice, this would be calculated in the DataWindow widget"
            )

            # Generate appropriate aggregate calculation
            if field.aggregate_function:
                func_lower = field.aggregate_function.lower()
                if func_lower == "sum":
                    lines.append(
                        f"  return rows.fold<num>(0, (sum, row) => sum + (row['{field.dependencies[0]}'] ?? 0));"
                    )
                elif func_lower in {"avg", "average"}:
                    lines.append(
                        f"  final values = rows.map((row) => row['{field.dependencies[0]}'] ?? 0).toList();"
                    )
                    lines.append(
                        "  return values.isEmpty ? 0 : values.reduce((a, b) => a + b) / values.length;"
                    )
                elif func_lower == "count":
                    lines.append("  return rows.length;")
                elif func_lower == "min":
                    lines.append(
                        f"  final values = rows.map((row) => row['{field.dependencies[0]}'] ?? 0).toList();"
                    )
                    lines.append(
                        "  return values.isEmpty ? 0 : values.reduce((a, b) => a < b ? a : b);"
                    )
                elif func_lower == "max":
                    lines.append(
                        f"  final values = rows.map((row) => row['{field.dependencies[0]}'] ?? 0).toList();"
                    )
                    lines.append(
                        "  return values.isEmpty ? 0 : values.reduce((a, b) => a > b ? a : b);"
                    )
                else:
                    lines.append(
                        f"  // Custom aggregate function: {field.aggregate_function}"
                    )
                    lines.append("  return 0; // Implement custom aggregate")
            else:
                lines.append("  return 0; // No aggregate function specified")
        else:
            # Simple field calculation
            lines.append("  try {")
            lines.append(f"    return {field.expression};")
            lines.append("  } catch (e) {")
            lines.append(f'    debugPrint("Error calculating {field.name}: $e");')
            lines.append("    return null;")
            lines.append("  }")

        lines.append("}")

        return lines

    def _generate_python_method(self, field: ComputedField) -> list[str]:
        """Generate Python method for computed field."""
        lines = []

        # Method signature
        lines.append(
            f"def get_{field.name}(self, row: dict) -> {self._python_type(field.inferred_type)}:"
        )
        lines.append(f'    """Calculate computed field {field.name}."""')

        # Add null checks
        if field.dependencies:
            lines.append("    # Check dependencies")
            for dep in field.dependencies:
                lines.append(f'    if row.get("{dep}") is None:')
                lines.append("        return None")
            lines.append("")

        # Add calculation
        lines.append("    # Calculate computed field")
        if field.is_aggregate:
            lines.append(
                f"    # Note: Aggregate {field.aggregate_function} needs all rows"
            )
            lines.append(
                "    # In practice, this would be calculated by the dataframe/query"
            )

            # Generate appropriate aggregate calculation
            if field.aggregate_function:
                func_lower = field.aggregate_function.lower()
                if func_lower == "sum":
                    lines.append(
                        f"    return sum(row.get('{field.dependencies[0]}', 0) for row in self.rows)"
                    )
                elif func_lower in {"avg", "average"}:
                    lines.append(
                        f"    values = [row.get('{field.dependencies[0]}', 0) for row in self.rows]"
                    )
                    lines.append(
                        "    return sum(values) / len(values) if values else 0"
                    )
                elif func_lower == "count":
                    lines.append("    return len(self.rows)")
                elif func_lower == "min":
                    lines.append(
                        f"    values = [row.get('{field.dependencies[0]}', 0) for row in self.rows]"
                    )
                    lines.append("    return min(values) if values else 0")
                elif func_lower == "max":
                    lines.append(
                        f"    values = [row.get('{field.dependencies[0]}', 0) for row in self.rows]"
                    )
                    lines.append("    return max(values) if values else 0")
                else:
                    lines.append(
                        f"    # Custom aggregate function: {field.aggregate_function}"
                    )
                    lines.append("    return 0  # Implement custom aggregate")
            else:
                lines.append("    return 0  # No aggregate function specified")
        else:
            lines.append("    try:")
            lines.append(f"        return {field.expression}")
            lines.append("    except Exception as e:")
            lines.append(
                f'        logger.error("Error calculating {field.name}: %s", e)'
            )
            lines.append("        return None")

        return lines

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def _python_type(self, dart_type: str) -> str:
        """Convert Dart type to Python type."""
        type_map = {
            "int": "int",
            "double": "float",
            "String": "str",
            "bool": "bool",
            "DateTime": "datetime",
            "dynamic": "Any",
        }
        return type_map.get(dart_type, "Any")


class ValidationRuleProcessor:
    """Process DataWindow validation rules."""

    def __init__(self) -> None:
        """Initialize the processor."""
        self.rule_patterns = {
            # Required field
            r"required|mandatory|not\s+null": "required",
            # Length constraints
            r"len\s*[<>=]+\s*(\d+)": "length",
            r"length\s*[<>=]+\s*(\d+)": "length",
            # Numeric constraints
            r"(?<![\w])min\s*[>=]*\s*([\d\.\-]+)": "min",
            r"(?<![\w])max\s*[<=]*\s*([\d\.\-]+)": "max",
            r"between\s+([\d\.\-]+)\s+and\s+([\d\.\-]+)": "range",
            # Pattern matching
            r'match\s*\(\s*["\'](.+?)["\']\s*\)': "pattern",
            r'like\s+["\'](.+?)["\']': "pattern",
            # Date constraints
            r"date\s*[<>=]+\s*today": "date_compare",
            r"valid\s+date": "valid_date",
            # Custom validation
            r"validate\s*\(\s*(.+?)\s*\)": "custom",
        }

    def process_validation_rule(
        self, column_name: str, validation_expr: str
    ) -> ValidationRule | None:
        """Process a validation expression into a rule.

        Args:
            column_name: Name of the column
            validation_expr: PowerBuilder validation expression

        Returns:
            ValidationRule object or None
        """
        if not validation_expr:
            return None

        validation_expr = validation_expr.strip()

        # Try to match rule patterns
        for pattern, rule_type in self.rule_patterns.items():
            match = re.search(pattern, validation_expr, re.IGNORECASE)
            if match:
                return self._create_rule(column_name, rule_type, match, validation_expr)

        # If no pattern matches, treat as custom validation
        return self._create_custom_rule(column_name, validation_expr)

    def _create_rule(
        self, column_name: str, rule_type: str, match: re.Match, _original_expr: Any
    ) -> ValidationRule:
        """Create a validation rule from regex match."""
        rule_value = None
        error_message = f"Validation failed for {column_name}"

        if rule_type == "required":
            rule_value = True
            error_message = f"{column_name} is required"

        elif rule_type in ["length", "min", "max"]:
            rule_value = int(match.group(1))
            if rule_type == "length":
                error_message = f"{column_name} must be {rule_value} characters"
            elif rule_type == "min":
                error_message = f"{column_name} must be at least {rule_value}"
            elif rule_type == "max":
                error_message = f"{column_name} must be at most {rule_value}"

        elif rule_type == "range":
            rule_value = (float(match.group(1)), float(match.group(2)))
            error_message = (
                f"{column_name} must be between {rule_value[0]} and {rule_value[1]}"
            )

        elif rule_type == "pattern":
            rule_value = match.group(1)
            error_message = f"{column_name} format is invalid"

        elif rule_type == "date_compare":
            rule_value = "today"
            error_message = f"{column_name} date validation failed"

        elif rule_type == "valid_date":
            rule_value = True
            error_message = f"{column_name} must be a valid date"

        # Generate validators
        dart_validator = self._generate_dart_validator(
            column_name, rule_type, rule_value
        )
        python_validator = self._generate_python_validator(
            column_name, rule_type, rule_value
        )

        return ValidationRule(
            column_name=column_name,
            rule_type=rule_type,
            rule_value=rule_value,
            error_message=error_message,
            dart_validator=dart_validator,
            python_validator=python_validator,
        )

    def _create_custom_rule(self, column_name: str, expr: str) -> ValidationRule:
        """Create a custom validation rule."""
        return ValidationRule(
            column_name=column_name,
            rule_type="custom",
            rule_value=expr,
            error_message=f"{column_name} validation failed",
            dart_validator=self._generate_dart_custom_validator(column_name, expr),
            python_validator=self._generate_python_custom_validator(column_name, expr),
        )

    def _generate_dart_validator(
        self, column_name: str, rule_type: str, rule_value: Any
    ) -> str:
        """Generate Dart validation code."""
        if rule_type == "required":
            return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  if (value == null || value.toString().isEmpty) {{
    return '{column_name} is required';
  }}
  return null;
}}"""

        if rule_type == "min":
            return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  if (value == null) return null;
  final numValue = num.tryParse(value.toString());
  if (numValue == null || numValue < {rule_value}) {{
    return '{column_name} must be at least {rule_value}';
  }}
  return null;
}}"""

        if rule_type == "max":
            return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  if (value == null) return null;
  final numValue = num.tryParse(value.toString());
  if (numValue == null || numValue > {rule_value}) {{
    return '{column_name} must be at most {rule_value}';
  }}
  return null;
}}"""

        if rule_type == "length":
            return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  if (value == null) return null;
  if (value.toString().length != {rule_value}) {{
    return '{column_name} must be {rule_value} characters';
  }}
  return null;
}}"""

        if rule_type == "range":
            min_val, max_val = rule_value
            return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  if (value == null) return null;
  final numValue = num.tryParse(value.toString());
  if (numValue == null || numValue < {min_val} || numValue > {max_val}) {{
    return '{column_name} must be between {min_val} and {max_val}';
  }}
  return null;
}}"""

        if rule_type == "pattern":
            return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  if (value == null) return null;
  final pattern = RegExp(r'{rule_value}');
  if (!pattern.hasMatch(value.toString())) {{
    return '{column_name} format is invalid';
  }}
  return null;
}}"""

        # Default validator
        return f"""String? validate{self._to_pascal_case(column_name)}(dynamic value) {{
  // {rule_type} validation with rule: {rule_value}
  if (value == null) return null;
  // TODO: Implement {rule_type} validation
  return null;
}}"""

    def _generate_python_validator(
        self, column_name: str, rule_type: str, rule_value: Any
    ) -> str:
        """Generate Python validation code."""
        if rule_type == "required":
            return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} is required.\"\"\"
    if value is None or str(value).strip() == '':
        return '{column_name} is required'
    return None"""

        if rule_type == "min":
            return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} minimum value.\"\"\"
    if value is None:
        return None
    try:
        num_value = float(value)
        if num_value < {rule_value}:
            return '{column_name} must be at least {rule_value}'
    except (ValueError, TypeError):
        return '{column_name} must be a number'
    return None"""

        if rule_type == "max":
            return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} maximum value.\"\"\"
    if value is None:
        return None
    try:
        num_value = float(value)
        if num_value > {rule_value}:
            return '{column_name} must be at most {rule_value}'
    except (ValueError, TypeError):
        return '{column_name} must be a number'
    return None"""

        if rule_type == "length":
            return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} length.\"\"\"
    if value is None:
        return None
    if len(str(value)) != {rule_value}:
        return '{column_name} must be {rule_value} characters'
    return None"""

        if rule_type == "range":
            min_val, max_val = rule_value
            return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} range.\"\"\"
    if value is None:
        return None
    try:
        num_value = float(value)
        if num_value < {min_val} or num_value > {max_val}:
            return '{column_name} must be between {min_val} and {max_val}'
    except (ValueError, TypeError):
        return '{column_name} must be a number'
    return None"""

        if rule_type == "pattern":
            return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} pattern.\"\"\"
    if value is None:
        return None
    import re
    pattern = re.compile(r'{rule_value}')
    if not pattern.match(str(value)):
        return '{column_name} format is invalid'
    return None"""

        # Default validator
        return f"""def validate_{column_name}(value: Any) -> str | None:
    \"\"\"Validate {column_name} using {rule_type} rule.\"\"\"
    if value is None:
        return None
    # TODO: Implement {rule_type} validation
    return None"""

    def _generate_dart_custom_validator(self, column_name: str, expr: str) -> str:
        """Generate Dart custom validator."""
        return f"""String? validate{self._to_pascal_case(column_name)}Custom(dynamic value) {{
  // Custom validation: {expr}
  if (value == null) return null;

  try {{
    // Parse and evaluate the custom expression
    // For now, implement basic checks based on common patterns
    String valueStr = value.toString();

    // Handle common expression patterns
    if ('{expr}'.contains('len(')) {{
      // Length-based validation
      int minLen = 1;
      int maxLen = 100;
      if (valueStr.length < minLen || valueStr.length > maxLen) {{
        return '{column_name} length is invalid';
      }}
    }}

    if ('{expr}'.contains('range(')) {{
      // Range-based validation
      double numValue = double.tryParse(valueStr) ?? 0;
      if (numValue < 0 || numValue > 999999) {{
        return '{column_name} value is out of range';
      }}
    }}

    if ('{expr}'.contains('match(')) {{
      // Pattern matching validation
      RegExp emailPattern = RegExp(r'^[\\w-\\.]+@[\\w-]+\\.[a-zA-Z]{{2,}}$');
      if ('{expr}'.toLowerCase().contains('email') && !emailPattern.hasMatch(valueStr)) {{
        return '{column_name} is not a valid email';
      }}
    }}

    return null;
  }} catch (e) {{
    return '{column_name} validation failed: ${{e.toString()}}';
  }}
}}"""

    def _generate_python_custom_validator(self, column_name: str, expr: str) -> str:
        """Generate Python custom validator."""
        return f"""def validate_{column_name}_custom(value: Any) -> str | None:
    \"\"\"Custom validation: {expr}\"\"\"
    import re

    if value is None:
        return None

    try:
        # Parse and evaluate the custom expression
        # For now, implement basic checks based on common patterns
        value_str = str(value)

        # Handle common expression patterns
        if 'len(' in '{expr}':
            # Length-based validation
            min_len = 1
            max_len = 100
            if len(value_str) < min_len or len(value_str) > max_len:
                return f'{column_name} length is invalid'

        if 'range(' in '{expr}':
            # Range-based validation
            try:
                num_value = float(value_str)
                if num_value < 0 or num_value > 999999:
                    return f'{column_name} value is out of range'
            except ValueError:
                return f'{column_name} must be a number'

        if 'match(' in '{expr}':
            # Pattern matching validation
            if 'email' in '{expr}'.lower():
                email_pattern = re.compile(r'^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{{2,}}$')
                if not email_pattern.match(value_str):
                    return f'{column_name} is not a valid email'

        return None

    except Exception as e:
        return f'{column_name} validation failed: {{str(e)}}'"""

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def generate_form_validators(
        self, rules: list[ValidationRule], target: str = "flutter"
    ) -> dict[str, list[str]]:
        """Generate form-level validators.

        Args:
            rules: List of validation rules
            target: Target language

        Returns:
            Dictionary of validator name -> code lines
        """
        validators = {}

        if target == "flutter":
            # Generate Flutter FormBuilder validators
            validators["form_validators"] = self._generate_flutter_form_validators(
                rules
            )
            validators["field_validators"] = self._generate_flutter_field_validators(
                rules
            )

        elif target == "python":
            # Generate Python validators
            validators["form_validators"] = self._generate_python_form_validators(rules)
            validators["field_validators"] = self._generate_python_field_validators(
                rules
            )

        return validators

    def _generate_flutter_form_validators(
        self, rules: list[ValidationRule]
    ) -> list[str]:
        """Generate Flutter form validators."""
        lines = []

        lines.append("// Form validators")
        lines.append("final Map<String, List<FormFieldValidator>> validators = {")

        # Group rules by column
        rules_by_column = {}
        for rule in rules:
            if rule.column_name not in rules_by_column:
                rules_by_column[rule.column_name] = []
            rules_by_column[rule.column_name].append(rule)

        # Generate validators for each column
        for column, column_rules in rules_by_column.items():
            lines.append(f'  "{column}": [')
            for rule in column_rules:
                if rule.rule_type == "required":
                    lines.append("    FormBuilderValidators.required(),")
                elif rule.rule_type == "min":
                    lines.append(f"    FormBuilderValidators.min({rule.rule_value}),")
                elif rule.rule_type == "max":
                    lines.append(f"    FormBuilderValidators.max({rule.rule_value}),")
                elif rule.rule_type == "pattern":
                    lines.append(
                        f'    FormBuilderValidators.match(r"{rule.rule_value}"),'
                    )
            lines.append("  ],")

        lines.append("};")

        return lines

    def _generate_flutter_field_validators(
        self, rules: list[ValidationRule]
    ) -> list[str]:
        """Generate individual Flutter field validators."""
        lines = []

        for rule in rules:
            lines.extend(rule.dart_validator.split("\n"))
            lines.append("")

        return lines

    def _generate_python_form_validators(
        self, rules: list[ValidationRule]
    ) -> list[str]:
        """Generate Python form validators."""
        lines = []

        lines.append("# Form validators")
        lines.append("class FormValidators:")
        lines.append('    """Form validation methods."""')
        lines.append("")
        lines.append("    @staticmethod")
        lines.append("    def validate_all(data: dict) -> dict:")
        lines.append('        """Validate all fields."""')
        lines.append("        errors = {}")
        lines.append("")

        # Group rules by column
        rules_by_column = {}
        for rule in rules:
            if rule.column_name not in rules_by_column:
                rules_by_column[rule.column_name] = []
            rules_by_column[rule.column_name].append(rule)

        # Validate each column
        for column in rules_by_column:
            lines.append(f"        # Validate {column}")
            lines.append(
                f'        {column}_error = validate_{column}(data.get("{column}"))'
            )
            lines.append(f"        if {column}_error:")
            lines.append(f'            errors["{column}"] = {column}_error')
            lines.append("")

        lines.append("        return errors")

        return lines

    def _generate_python_field_validators(
        self, rules: list[ValidationRule]
    ) -> list[str]:
        """Generate individual Python field validators."""
        lines = []

        for rule in rules:
            lines.extend(rule.python_validator.split("\n"))
            lines.append("")

        return lines
