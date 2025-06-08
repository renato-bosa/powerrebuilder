"""PowerBuilder Parser to AST Transformer.

This module transforms Lark parse trees into PowerBuilder AST nodes.
"""


from lark import Token, Transformer

from model.ast import (
    ASTAssignment,
    BinaryExpression,
    Block,
    BooleanLiteral,
    CaseExpression,
    CaseStatement,
    CustomType,
    DoWhileLoop,
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


class PowerBuilderTransformer(Transformer):
    """Transform Lark parse tree to PowerBuilder AST."""

    def __init__(self):
        super().__init__()

    # File structure
    def powerbuilder_file(self, items):
        """Transform the root file node."""
        return {"type": "file", "elements": items}

    def file_element(self, items):
        """Pass through file elements."""
        return items[0] if items else None

    # Type declarations
    def type_declaration(self, items):
        """Transform type declaration."""
        # items: [global?, 'type', identifier, 'from', type_parent, type_body, 'end', 'type']
        is_global = False
        start_idx = 0

        # Find the actual elements by filtering out None values
        filtered_items = [item for item in items if item is not None]

        # Check if first item is 'global'
        if filtered_items and str(filtered_items[0]).lower() == 'global':
            is_global = True
            start_idx = 1

        # Extract name and parent type
        name = None
        parent_type = None

        # Find identifier (the type name) and parent
        for i, item in enumerate(filtered_items[start_idx:], start_idx):
            if hasattr(item, 'type') and item.type == 'IDENTIFIER':
                if name is None:
                    name = str(item)
            elif isinstance(item, dict) and item.get('type') == 'type_parent':
                parent_type = item.get('value')
            elif hasattr(item, 'data') and item.data == 'type_parent':
                # Extract the parent type string from the tree
                parent_type = str(item.children[0]) if item.children else None

        # Create a custom type with parent information
        custom_type = CustomType(
            name=name,
            category=TypeCategory.CUSTOM,
            parent_type=parent_type,
        )

        # Add the global flag
        custom_type.is_global = is_global

        return custom_type

    def type_parent(self, items):
        """Extract type parent."""
        # Return a dict to help identify this in type_declaration
        return {'type': 'type_parent', 'value': str(items[0])}

    def type_body(self, items):
        """Transform type body."""
        return items

    def type_member(self, items):
        """Pass through type members."""
        return items[0] if items else None

    # Function definitions
    def function_definition(self, items):
        """Transform function definition."""
        # items: [access?, 'function', return_type, identifier, parameters, semicolon?, statements, 'end', 'function']
        access_modifier = None

        # Filter out None items
        items = [item for item in items if item is not None]

        # Find indices of key elements
        idx = 0
        # Check if first item is an access modifier (could be a Tree or a string)
        first_item = items[idx]
        if hasattr(first_item, 'data') and first_item.data == 'access_modifier':
            # Extract the actual modifier from the tree
            access_modifier = str(first_item.children[0])
            idx += 1
        elif isinstance(first_item, str) and first_item in ['public', 'private', 'protected']:
            access_modifier = first_item
            idx += 1

        # Skip 'function' keyword
        if str(items[idx]).lower() == 'function':
            idx += 1

        return_type = items[idx]
        name = str(items[idx + 1])
        parameters = items[idx + 2]

        # Find statements (skip optional semicolon)
        statements_idx = idx + 3
        if statements_idx < len(items) and str(items[statements_idx]) == ';':
            statements_idx += 1
        statements = items[statements_idx] if statements_idx < len(items) and isinstance(items[statements_idx], list) else []

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
        if items[idx] in ['public', 'private', 'protected']:
            idx += 1
            
        # Skip 'event' keyword
        if str(items[idx]).lower() == 'event':
            idx += 1
            
        name = str(items[idx])
        parameters = items[idx + 1] if idx + 1 < len(items) else []
        
        # Find statements (skip optional semicolon)
        statements_idx = idx + 2
        if statements_idx < len(items) and str(items[statements_idx]) == ';':
            statements_idx += 1
        statements = items[statements_idx] if statements_idx < len(items) and isinstance(items[statements_idx], list) else []
        
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
        if items[idx] in ['public', 'private', 'protected']:
            idx += 1
            
        # Skip 'subroutine' keyword
        if str(items[idx]).lower() == 'subroutine':
            idx += 1
            
        name = str(items[idx])
        parameters = items[idx + 1] if idx + 1 < len(items) else []
        
        # Find statements
        statements_idx = idx + 2
        if statements_idx < len(items) and str(items[statements_idx]) == ';':
            statements_idx += 1
        statements = items[statements_idx] if statements_idx < len(items) and isinstance(items[statements_idx], list) else []
        
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

    def parameters(self, items):
        """Transform parameters."""
        # items: ['(', parameter_list?, ')']
        return items[1] if len(items) > 2 and items[1] else []

    def parameter_list(self, items):
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
            if items[0] is not None and str(items[0]) in ['ref', 'readonly']:
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
            is_ref=(modifier == 'ref'),
            is_readonly=(modifier == 'readonly'),
        )

    # Statements
    def statements(self, items):
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
            if item and str(item) != ';':
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

        # TODO: Handle suffixes (array access, property access)
        if len(items) > 1:
            # For now, just return the base identifier
            pass

        return base
    
    def expression_statement(self, items):
        """Transform expression statement."""
        # items: [expression, semicolon?]
        return items[0] if items else None
    
    def if_statement(self, items):
        """Transform if statement."""
        # items: ['if', expression, 'then', statements, elseif_parts*, else_part?, 'end', 'if']
        condition = items[1]
        then_statements = items[3] if len(items) > 3 else []
        
        # For now, create simple if without else/elseif handling
        # TODO: Handle elseif and else branches
        return IfStatement(
            condition=condition,
            then_branch=Block(statements=then_statements) if isinstance(then_statements, list) else Block(),
            else_branch=None,
        )
    
    def for_statement(self, items):
        """Transform for statement."""
        # items: ['for', identifier, '=', start_expr, 'to', end_expr, step?, statements, 'next', identifier?]
        variable = str(items[1])
        start = items[3]
        end = items[5]
        
        # Find where statements begin (after optional 'step')
        statements_idx = 6
        step = None
        if statements_idx < len(items) and str(items[statements_idx]).lower() == 'step':
            step = items[statements_idx + 1]
            statements_idx += 2
            
        statements = items[statements_idx] if statements_idx < len(items) and isinstance(items[statements_idx], list) else []
        
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
    
    def case_statement(self, items):
        """Transform case statement."""
        # items: ['case', expression, 'of', case_branches*, otherwise?, 'end', 'case']
        expression = items[1]
        
        # Extract case branches
        branches = []
        # TODO: Properly parse case branches
        
        return CaseStatement(
            expression=expression,
            cases=branches,
            default_body=None,
        )

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
            if item.type == 'IDENTIFIER':
                return Variable(name=str(item))
            if item.type == 'INT':
                return IntegerLiteral(value=int(item))
            if item.type == 'STRING':
                # Remove quotes
                value = str(item)[1:-1]
                return StringLiteral(value=value)
            if item.type == 'TRUE':
                return BooleanLiteral(value=True)
            if item.type == 'FALSE':
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

        # Map to BasicType
        type_mapping = {
            'integer': BasicType.INTEGER,
            'long': BasicType.LONG,
            'string': BasicType.STRING,
            'boolean': BasicType.BOOLEAN,
            'real': BasicType.REAL,
            'decimal': BasicType.DECIMAL,
            'date': BasicType.DATE,
            'time': BasicType.TIME,
            'blob': BasicType.BLOB,
            'any': BasicType.ANY,
        }

        basic_type = type_mapping.get(type_str)
        if basic_type:
            return Type(
                name=basic_type.type_name,
                category=basic_type.category,
            )
        # Return Type with CUSTOM category for unknown types
        return Type(
            name=type_str,
            category=TypeCategory.CUSTOM,
        )

    # Misc transformations
    def access_modifier(self, items):
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
