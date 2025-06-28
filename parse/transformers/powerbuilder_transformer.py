"""PowerBuilder Parser to AST Transformer.

This module transforms Lark parse trees into PowerBuilder AST nodes.
"""


from lark import Token, Transformer

from model.ast import (
    ArrayAccess,
    ASTAssignment,
    BinaryExpression,
    Block,
    BooleanLiteral,
    CaseStatement,
    CustomType,
    Event,
    ForLoop,
    FunctionDefinition,
    IfStatement,
    IntegerLiteral,
    Parameter,
    ReturnStatement,
    StringLiteral,
    Type,
    Variable,
    WhileLoop,
)
from model.ast.functions import Signature
from model.ast.types import BasicType, TypeCategory
from parse.transformers.enhanced_type_transformer import EnhancedTypeTransformer


class PowerBuilderTransformer(EnhancedTypeTransformer, Transformer):
    """Transform Lark parse tree to PowerBuilder AST."""

    def __init__(self) -> None:




        """Initialize the transformer."""
        super().__init__()

    # Error recovery nodes
    def error_node(self, items) -> None:


        """Handle error nodes from error recovery."""
        # Create a special AST node for errors
        return {
            "type": "error", "error_type": "parse_error", "content": items, "message": "Failed to parse this section",
        }

    def recovered_statement(self, items) -> dict:




        """Handle recovered statements."""
        # Return the recovered statement with a marker
        if items:
            stmt = items[0] if len(items) == 1 else items
            if isinstance(stmt, dict):
                stmt["recovered"] = True
            return stmt
        return {"type": "empty_statement", "recovered": True}

    def incomplete_statement(self, items) -> dict:




        """Handle incomplete statements."""
        return {
            "type": "incomplete_statement", "content": items, "message": "Statement appears to be incomplete",
        }

    def statement_list(self, items) -> dict:




        """Handle statement lists from error recovery."""
        return {
            "type": "statement_list", "statements": items, "node_type": "statement_list",
        }

    def file_with_recovery(self, items) -> dict:




        """Handle file with error recovery nodes."""
        # Filter out None items and flatten
        elements = []
        for item in items:
            if item is not None:
                if isinstance(item, list):
                    elements.extend(item)
                else:
                    elements.append(item)
        return {"type": "file", "elements": elements, "has_errors": any(
            el.get("type") == "error" or el.get("recovered", False) 
            for el in elements if isinstance(el, dict)
        ),}

    # File structure
    def powerbuilder_file(self, items) -> dict:


        """Transform the root file node."""
        return {"type": "file", "elements": items}

    def file_element(self, items):




        """Pass through file elements."""
        return items[0] if items else None

    # Import handling
    def import_statement(self, items) -> None:


        """Transform import statement."""
        # items: ['import', identifier, ('.', identifier)*, ''?]
        # Extract the library path (skip 'import' keyword and semicolon)
        path_parts = []

        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                path_parts.append(str(item))

        if path_parts:
            # PowerBuilder imports typically have format: library.object
            # For simple imports, we'll use the whole path as both library and object
            library_path = ".".join(path_parts)

            # Split into library and object
            if len(path_parts) > 1:
                # Last part is the object, rest is library
                from_library = ".".join(path_parts[:-1])
                object_name = path_parts[-1]
            else:
                # Single identifier - use as both library and object
                from_library = path_parts[0]
                object_name = path_parts[0]

            # Create an Import object from model.library
            from model.core.library import Import
            return Import(from_library=from_library, object_name=object_name)

        return None

    # Type declarations
    # The type_declaration method is now inherited from EnhancedTypeTransformer
    # which provides full support for enums and structures

    def type_parent(self, items) -> dict:




        """Extract type parent."""
        # Return a dict to help identify this in type_declaration
        return {"type": "type_parent", "value": str(items[0])}

    # Override type_member to handle our enum_value_declaration
    def type_member(self, items):


        """Transform type member - handle enum values."""
        # Check if this is an enum value declaration
        if items and len(items) == 1:
            item = items[0]
            if isinstance(item, dict) and item.get("type") == "enum_value":
                return item

        # Otherwise defer to parent implementation
        return super().type_member(items) if hasattr(super(), "type_member") else None

    # The type_body method is inherited from EnhancedTypeTransformer
    # which provides full parsing of enum values and structure fields

    # Function definitions
    def function_definition(self, items) -> None:


        """Transform function definition."""
        # items: [access?, 'function', return_type, identifier, parameters, semicolon?, statements, 'end', 'function']

        # Filter out None items
        items = [item for item in items if item is not None]

        # Find indices of key elements
        idx = 0
        # Check if first item is an access modifier (could be a Tree or a string)
        first_item = items[idx]
        if hasattr(first_item, "data") and first_item.data == "access_modifier":
            # Extract the actual modifier from the tree
            str(first_item.children[0])
            idx += 1
        elif isinstance(first_item, str) and first_item in [
            "public",
            "private",
            "protected",
        ]:
            idx += 1

        # Skip 'function' keyword
        if str(items[idx]).lower() == "function":
            idx += 1

        return_type = items[idx]
        name = str(items[idx + 1])
        parameters = items[idx + 2]

        # Find statements (skip optional semicolon)
        statements_idx = idx + 3
        if statements_idx < len(items) and str(items[statements_idx]) == ";":
            statements_idx += 1
        statements = (
            items[statements_idx]
            if statements_idx < len(items) and isinstance(items[statements_idx], list)
            else []
        )

        # Create signature
        sig = Signature(
            name=name,
            return_type=self._convert_type(return_type),
            parameters=parameters if isinstance(parameters, list) else [],
        )

        # Create function definition
        return FunctionDefinition(
            signature=sig,
            body=Block(statements=statements) if statements else Block(),
        )

    def return_type(self, items):




        """Extract return type."""
        return items[0]

    def event_definition(self, items):




        """Transform event definition."""
        # items: [access?, 'event', identifier, parameters, semicolon?, statements, 'end', 'event']
        # Filter out None items
        items = [item for item in items if item is not None]

        # Parse similar to function_definition
        idx = 0
        # Check for access modifier
        if items[idx] in ["public", "private", "protected"]:
            idx += 1

        # Skip 'event' keyword
        if str(items[idx]).lower() == "event":
            idx += 1

        name = str(items[idx])
        parameters = items[idx + 1] if idx + 1 < len(items) else []

        # Find statements (skip optional semicolon)
        statements_idx = idx + 2
        if statements_idx < len(items) and str(items[statements_idx]) == ";":
            statements_idx += 1
        statements = (
            items[statements_idx]
            if statements_idx < len(items) and isinstance(items[statements_idx], list)
            else []
        )

        # Create Event node
        return Event(
            name=name,
            parameters=parameters if isinstance(parameters, list) else [],
            body=Block(statements=statements) if statements else None,
        )

    def subroutine_definition(self, items):




        """Transform subroutine definition."""
        # Subroutines are like functions without return type
        # items: [access?, 'subroutine', identifier, parameters, semicolon?, statements, 'end', 'subroutine']
        # Filter out None items
        items = [item for item in items if item is not None]

        idx = 0
        # Check for access modifier
        if items[idx] in ["public", "private", "protected"]:
            idx += 1

        # Skip 'subroutine' keyword
        if str(items[idx]).lower() == "subroutine":
            idx += 1

        name = str(items[idx])
        parameters = items[idx + 1] if idx + 1 < len(items) else []

        # Find statements
        statements_idx = idx + 2
        if statements_idx < len(items) and str(items[statements_idx]) == ";":
            statements_idx += 1
        statements = (
            items[statements_idx]
            if statements_idx < len(items) and isinstance(items[statements_idx], list)
            else []
        )

        # Create FunctionDefinition with void return type
        sig = Signature(
            name=name,
            return_type=Type(name="void", category=TypeCategory.BASIC),
            parameters=parameters if isinstance(parameters, list) else [],
        )

        return FunctionDefinition(
            signature=sig,
            body=Block(statements=statements) if statements else Block(),
        )

    def parameters(self, items) -> list:




        """Transform parameters."""
        # items: ['(', parameter_list?, ')']
        return items[1] if len(items) > 2 and items[1] else []

    def parameter_list(self, items) -> list:




        """Transform parameter list."""
        # Extract odd items (parameters, skipping commas)
        return [items[i] for i in range(0, len(items), 2)]

    def parameter(self, items):




        """Transform a single parameter."""
        # items: [ref?, type_name, identifier, array_bounds?]
        # The items list has 4 elements, with None for missing optional parts
        modifier = None
        type_name = None
        name = None

        # Parse based on position
        if len(items) >= 4:
            # Check first item for modifier
            if items[0] is not None and str(items[0]) in ["ref", "readonly"]:
                modifier = str(items[0])

            # Second item is type
            type_name = str(items[1]) if items[1] is not None else None

            # Third item is identifier
            name = str(items[2]) if items[2] is not None else None

            # Fourth item would be array bounds (not handled yet)
        elif len(items) == 3:
            # No modifier case
            type_name = str(items[0]) if items[0] is not None else None
            name = str(items[1]) if items[1] is not None else None

        # Create Parameter object
        return Parameter(
            name=name,
            type=self._convert_type(type_name) if type_name else None,
            is_ref=(modifier == "ref"),
            is_readonly=(modifier == "readonly"),
        )

    # Statements
    def statements(self, items) -> list:


        """Transform statement list."""
        return [item for item in items if item is not None]

    def statement(self, items):




        """Pass through statements."""
        return items[0] if items else None

    def return_statement(self, items):




        """Transform return statement."""
        # items: ['return', expression?, semicolon?]
        # Find the expression (skip 'return' keyword and semicolon)
        value = None
        for item in items[1:]:
            if item and str(item) != ";":
                value = item
                break
        return ReturnStatement(value=value)

    def assignment_statement(self, items):




        """Transform assignment statement."""
        # items: [lvalue, '=', expression, semicolon?]
        target = items[0]
        value = items[2]
        return ASTAssignment(target=target, value=value)

    def lvalue(self, items):




        """Transform lvalue."""
        # items: [identifier, lvalue_suffix*]
        base = Variable(name=str(items[0]))
        result = base

        # Handle suffixes (array access, property access)
        for i in range(1, len(items)):
            suffix = items[i]
            if isinstance(suffix, list) and suffix:
                # Array access: [expression, ...] (supports multi-dimensional)
                # Filter out just the expressions (skip brackets and commas)
                indices = []
                for item in suffix:
                    if hasattr(item, "__class__") and item.__class__.__name__ in ["Expression", "BinaryExpression", "UnaryExpression", "Literal", "Variable"]:
                        indices.append(item)

                if indices:
                    # For multi-dimensional arrays, chain ArrayAccess nodes
                    for index in indices:
                        result = ArrayAccess(
                            array=result,
                            index=index,
                        )
            elif isinstance(suffix, str) and suffix.startswith("."):
                # Property access: .property_name
                # Use Variable with dotted name to represent member access
                member_name = suffix[1:] if suffix.startswith(".") else suffix
                full_name = f"{result.name if hasattr(result, "name") else str(result)}.{member_name}"
                result = Variable(name=full_name)

        return result

    def expression_statement(self, items):




        """Transform expression statement."""
        # items: [expression, semicolon?]
        return items[0] if items else None

    def if_statement(self, items) -> None:




        """Transform if statement."""
        # Grammar: IF expression THEN statements (ELSEIF expression THEN statements)* [ELSE statements] END IF

        # Parse the structure
        i = 0
        main_condition = None
        main_then_statements = []
        elseif_branches = []
        else_statements = []

        # Skip 'if' keyword
        while i < len(items) and str(items[i]).lower() == "if":
            i += 1

        # Get main condition
        if i < len(items) and self._is_expression(items[i]):
            main_condition = items[i]
            i += 1

        # Skip 'then' keyword
        while i < len(items) and str(items[i]).lower() == "then":
            i += 1

        # Collect statements until we hit 'elseif', 'else', or 'end'
        while i < len(items):
            item_str = str(items[i]).lower() if isinstance(items[i], str) else ""

            if item_str == "elseif":
                # Start of elseif branch
                i += 1
                elseif_condition = None
                elseif_then_statements = []

                # Get elseif condition
                if i < len(items) and self._is_expression(items[i]):
                    elseif_condition = items[i]
                    i += 1

                # Skip 'then'
                while i < len(items) and str(items[i]).lower() == "then":
                    i += 1

                # Collect elseif statements
                while i < len(items):
                    next_item_str = str(items[i]).lower() if isinstance(items[i], str) else ""
                    if next_item_str in ["elseif", "else", "end"]:
                        break
                    if isinstance(items[i], list):
                        elseif_then_statements.extend(items[i])
                    elif self._is_statement(items[i]):
                        elseif_then_statements.append(items[i])
                    i += 1

                if elseif_condition:
                    elseif_branches.append((elseif_condition, elseif_then_statements))

            elif item_str == "else":
                # Start of else branch
                i += 1
                while i < len(items):
                    next_item_str = str(items[i]).lower() if isinstance(items[i], str) else ""
                    if next_item_str == "end":
                        break
                    if isinstance(items[i], list):
                        else_statements.extend(items[i])
                    elif self._is_statement(items[i]):
                        else_statements.append(items[i])
                    i += 1

            elif item_str == "end":
                # End of if statement
                break

            else:
                # Collect main then statements
                if isinstance(items[i], list):
                    main_then_statements.extend(items[i])
                elif self._is_statement(items[i]):
                    main_then_statements.append(items[i])
                i += 1

        # Build the if statement
        # If we have elseif branches, we need to chain them
        if elseif_branches:
            # Build else branch by chaining elseifs
            current_else = Block(statements=else_statements) if else_statements else None

            # Process elseifs in reverse order to build the chain
            for elseif_condition, elseif_stmts in reversed(elseif_branches):
                current_else = IfStatement(
                    condition=elseif_condition,
                    then_branch=Block(statements=elseif_stmts),
                    else_branch=current_else,
                )

            return IfStatement(
                condition=main_condition or Literal(value=True),
                then_branch=Block(statements=main_then_statements),
                else_branch=current_else,
            )
        else:
            # Simple if-else
            return IfStatement(
                condition=main_condition or Literal(value=True),
                then_branch=Block(statements=main_then_statements),
                else_branch=Block(statements=else_statements) if else_statements else None,
            )

    def _is_expression(self, item) -> bool:




        """Check if item is an expression."""
        return hasattr(item, "__class__") and item.__class__.__name__ in [
            "Expression", "BinaryExpression", "UnaryExpression", "Literal", "Variable",
        ]

    def _is_statement(self, item) -> bool:




        """Check if item is a statement."""
        return hasattr(item, "__class__") and "Statement" in item.__class__.__name__

    def for_statement(self, items):




        """Transform for statement."""
        # items: ['for', identifier, '=', start_expr, 'to', end_expr, step?, statements, 'next', identifier?]
        variable = str(items[1])
        start = items[3]
        end = items[5]

        # Find where statements begin (after optional 'step')
        statements_idx = 6
        step = None
        if statements_idx < len(items) and str(items[statements_idx]).lower() == "step":
            step = items[statements_idx + 1]
            statements_idx += 2

        statements = (
            items[statements_idx]
            if statements_idx < len(items) and isinstance(items[statements_idx], list)
            else []
        )

        return ForLoop(
            variable=variable,
            start=start,
            end=end,
            step=step,
            body=Block(statements=statements) if statements else Block(),
        )

    def do_while_statement(self, items):




        """Transform do-while statement."""
        # items: ['do', 'while', expression, statements, 'loop']
        condition = items[2]
        statements = items[3] if len(items) > 3 and isinstance(items[3], list) else []

        return WhileLoop(
            condition=condition,
            body=Block(statements=statements) if statements else Block(),
        )

    def do_until_statement(self, items):




        """Transform do-until statement."""
        # items: ['do', 'until', expression, statements, 'loop']
        # Convert UNTIL to NOT WHILE
        condition = items[2]
        statements = items[3] if len(items) > 3 and isinstance(items[3], list) else []

        # Create a NOT expression for the condition
        negated_condition = UnaryExpression(operator="not", operand=condition)

        return WhileLoop(
            condition=negated_condition,
            body=Block(statements=statements) if statements else Block(),
        )

    def case_statement(self, items) -> None:




        """Transform case statement."""
        # Grammar: CASE expression OF case_branch* [OTHERWISE COLON statements] END CASE
        expression = None
        branches = []
        default_body = None

        # Parse items to extract expression, branches, and default
        i = 0
        while i < len(items):
            item_str = str(items[i]).lower() if isinstance(items[i], str) else ""

            if item_str == "case":
                i += 1
                continue
            elif item_str == "of":
                i += 1
                continue
            elif item_str == "otherwise":
                # Found OTHERWISE clause
                i += 1
                # Skip colon if present
                if i < len(items) and str(items[i]) == ":":
                    i += 1
                # Collect default statements
                default_statements = []
                while i < len(items):
                    next_str = str(items[i]).lower() if isinstance(items[i], str) else ""
                    if next_str == "end":
                        break
                    if isinstance(items[i], list):
                        default_statements.extend(items[i])
                    elif self._is_statement(items[i]):
                        default_statements.append(items[i])
                    i += 1
                default_body = Block(statements=default_statements) if default_statements else None
            elif item_str == "end":
                break
            elif self._is_expression(items[i]) and expression is None:
                # This is the case expression
                expression = items[i]
            elif isinstance(items[i], tuple) and len(items[i]) == 2:
                # This is a case branch (case_values, statements)
                branches.append(items[i])
            elif hasattr(items[i], "__class__") and hasattr(items[i], "condition"):
                # Another form of case branch
                branches.append(items[i])
            i += 1

        return CaseStatement(
            expression=expression or Literal(value=0),
            cases=branches,
            default_body=default_body,
        )

    def case_branch(self, items) -> tuple:




        """Transform case branch."""
        # Grammar: case_values COLON statements
        case_values = None
        statements = []

        i = 0
        while i < len(items):
            if str(items[i]) == ":":
                i += 1
                # Collect statements after colon
                while i < len(items):
                    if isinstance(items[i], list):
                        statements.extend(items[i])
                    elif self._is_statement(items[i]):
                        statements.append(items[i])
                    i += 1
            elif case_values is None:
                # This should be case_values
                case_values = items[i]
                i += 1
            else:
                i += 1

        # Return tuple (case_values, statements)
        return (
            case_values,
            Block(statements=statements) if statements else Block(),
        )

    def case_values(self, items) -> list:




        """Transform case values (comma-separated values)."""
        # Grammar: case_value (COMMA case_value)*
        values = []
        for item in items:
            if str(item) != ",":  # Skip commas
                values.append(item)

        # If only one value, return it directly
        # Otherwise, return list of values
        return values[0] if len(values) == 1 else values

    def case_value(self, items) -> dict:




        """Transform case value (single value or range)."""
        # Grammar: expression [TO expression]
        if len(items) == 1:
            # Single value
            return items[0]
        elif len(items) >= 3 and str(items[1]).lower() == "to":
            # Range: expression TO expression
            return {
                "type": "range",
                "start": items[0],
                "end": items[2],
            }
        else:
            # Fallback to first item
            return items[0]

    # Expressions
    def expression(self, items):


        """Pass through expressions."""
        return items[0] if len(items) == 1 else items

    def logical_or(self, items):




        """Transform logical OR expression."""
        if len(items) == 1:
            return items[0]
        # Build left-associative tree
        result = items[0]
        for i in range(1, len(items), 2):
            result = BinaryExpression(
                left=result,
                operator="or",
                right=items[i + 1],
            )
        return result

    def logical_and(self, items):




        """Transform logical AND expression."""
        if len(items) == 1:
            return items[0]
        result = items[0]
        for i in range(1, len(items), 2):
            result = BinaryExpression(
                left=result,
                operator="and",
                right=items[i + 1],
            )
        return result

    def comparison(self, items):




        """Transform comparison expression."""
        if len(items) == 1:
            return items[0]
        return BinaryExpression(
            left=items[0],
            operator=str(items[1]),
            right=items[2],
        )

    def additive(self, items):




        """Transform additive expression."""
        if len(items) == 1:
            return items[0]
        result = items[0]
        for i in range(1, len(items), 2):
            result = BinaryExpression(
                left=result,
                operator=str(items[i]),
                right=items[i + 1],
            )
        return result

    def multiplicative(self, items):




        """Transform multiplicative expression."""
        if len(items) == 1:
            return items[0]
        result = items[0]
        for i in range(1, len(items), 2):
            result = BinaryExpression(
                left=result,
                operator=str(items[i]),
                right=items[i + 1],
            )
        return result

    def primary(self, items):




        """Transform primary expression."""
        item = items[0]

        if isinstance(item, Token):
            if item.type == "IDENTIFIER":
                return Variable(name=str(item))
            if item.type == "INT":
                return IntegerLiteral(value=int(item))
            if item.type == "STRING":
                # Remove quotes
                value = str(item)[1:-1]
                return StringLiteral(value=value)
            if item.type == "TRUE":
                return BooleanLiteral(value=True)
            if item.type == "FALSE":
                return BooleanLiteral(value=False)

        return item

    # Literals
    def literal(self, items):


        """Transform literal values."""
        return self.primary(items)

    # Utility methods
    def _convert_type(self, type_name: str | Token) -> Type:


        """Convert type name to Type object."""
        type_str = str(type_name).lower()

        # Map PowerBuilder types to categories
        basic_types = {
            "integer": TypeCategory.NUMERIC,
            "long": TypeCategory.NUMERIC,
            "decimal": TypeCategory.NUMERIC,
            "real": TypeCategory.NUMERIC,
            "double": TypeCategory.NUMERIC,
            "string": TypeCategory.TEXT,
            "char": TypeCategory.TEXT,
            "character": TypeCategory.TEXT,
            "boolean": TypeCategory.LOGICAL,
            "date": TypeCategory.BASIC,
            "time": TypeCategory.BASIC,
            "datetime": TypeCategory.BASIC,
            "blob": TypeCategory.BASIC,
            "any": TypeCategory.BASIC,
        }

        # Check if it's a basic type
        if type_str in basic_types:
            return BasicType(
                name=type_str,
                category=basic_types[type_str],
            )

        # Return CustomType for unknown types
        return CustomType(
            name=type_str,
            category=TypeCategory.CUSTOM,
        )

    # Enum value handling
    def enum_value_declaration(self, items) -> dict:


        """Transform enum value declaration."""
        # items: [IDENTIFIER, [EQUALS, [MINUS], INT]]
        name = str(items[0])
        value = None

        # Check if there's a value assignment
        if len(items) > 1:
            for i, item in enumerate(items):
                if item and str(item) == "=":
                    # Look for the value after equals
                    j = i + 1
                    while j < len(items) and items[j] is None:
                        j += 1

                    if j < len(items):
                        # Check for negative sign
                        if str(items[j]) == "-" and j + 1 < len(items):
                            value = -int(items[j + 1])
                        else:
                            value = int(items[j])
                    break

        return {
            "type": "enum_value",
            "name": name,
            "value": value,
        }

    # Misc transformations
    def access_modifier(self, items) -> str:


        """Extract access modifier."""
        return str(items[0])

    # Token transformations
    def IDENTIFIER(self, token):


        """Pass through identifier tokens."""
        return token

    def INT(self, token):




        """Pass through integer token."""
        return token

    def STRING(self, token):




        """Pass through string token."""
        return token
