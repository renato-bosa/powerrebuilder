"""Tests for the ASTValidator."""

from model.utils.validators import ASTValidator
from model.ast import (
    Block,
    BreakStatement,
    ContinueStatement,
    FunctionCall,
    FunctionDefinition,
    IfStatement,
    Parameter,
    Signature,
    Type,
    TypeCategory,
    TypeRegistry,
    WhileLoop,
)

def test_ast_validator_initialization():
    """Test ASTValidator initialization."""
    type_registry = TypeRegistry()
    validator = ASTValidator(type_registry)

    assert validator.type_registry == type_registry
    assert validator.current_loop_depth == 0
    assert validator.labels == {}
    assert validator.current_scope is not None
    assert validator.current_scope.parent is None

def test_enter_exit_scope():
    """Test entering and exiting scopes."""
    validator = ASTValidator(TypeRegistry())

    # Get reference to global scope
    global_scope = validator.current_scope

    # Enter a new scope
    validator.enter_scope()
    assert validator.current_scope.parent == global_scope

    # Exit back to global scope
    validator.exit_scope()
    assert validator.current_scope == global_scope

def test_enter_exit_loop():
    """Test entering and exiting loops."""
    validator = ASTValidator(TypeRegistry())

    assert validator.current_loop_depth == 0

    # Enter a loop
    validator.enter_loop()
    assert validator.current_loop_depth == 1

    # Enter a nested loop
    validator.enter_loop()
    assert validator.current_loop_depth == 2

    # Exit loops
    validator.exit_loop()
    assert validator.current_loop_depth == 1
    validator.exit_loop()
    assert validator.current_loop_depth == 0

def test_validate_break_continue():
    """Test validation of break and continue statements."""
    validator = ASTValidator(TypeRegistry())

    # Break and continue outside of loops should fail
    assert not validator.validate_break(BreakStatement())
    assert not validator.validate_continue(ContinueStatement())

    # Enter a loop
    validator.enter_loop()

    # Break and continue inside loops should succeed
    assert validator.validate_break(BreakStatement())
    assert validator.validate_continue(ContinueStatement())

    # Exit loop
    validator.exit_loop()

def test_function_validation():
    """Test function validation."""
    type_registry = TypeRegistry()
    validator = ASTValidator(type_registry)

    # Create a simple function
    int_type = Type(name="INTEGER", category=TypeCategory.NUMERIC)
    signature = Signature(
        name="test_func",
        parameters=[
            Parameter(name="x", type=int_type),
            Parameter(name="y", type=int_type),
        ],
        return_type=int_type,
    )

    func_def = FunctionDefinition(
        signature=signature,
        body=Block(statements=[]),
    )

    # Validate function
    assert validator.validate_function(func_def)

    # The function should be registered in the global scope
    assert validator.current_scope.get_function("test_func") == func_def

def test_standardized_validation_interface():
    """Test the standardized validation interface for node types."""
    type_registry = TypeRegistry()
    validator = ASTValidator(type_registry)

    # Test validation with empty context
    block = Block(statements=[])
    assert block.validate()

    # Test validation with proper context
    context = {'validator': validator}
    assert block.validate(context)

    # Test validation of break statement
    break_stmt = BreakStatement()

    # Without validator in context, it should pass (no context for validation)
    assert break_stmt.validate({})

    # With validator in context but outside a loop, it should fail
    assert not break_stmt.validate(context)

    # With validator in context and inside a loop, it should pass
    validator.enter_loop()
    assert break_stmt.validate(context)
    validator.exit_loop()

    # Test if statement validation
    # First, define a test function for the condition
    bool_type = Type(name="BOOLEAN", category=TypeCategory.LOGICAL)
    is_valid_func = FunctionDefinition(
        signature=Signature(
            name="is_valid",
            parameters=[],
            return_type=bool_type,
        ),
        body=Block(statements=[]),
    )

    # Register the function in the validator's scope
    validator.current_scope.declare_function(is_valid_func)

    # Now create an if statement using this function
    if_stmt = IfStatement(
        condition=FunctionCall(function_name="is_valid"),
        then_block=Block(statements=[]),
        else_block=Block(statements=[]),
    )

    # This should now pass since the function is registered
    assert if_stmt.validate(context)

def test_nested_validation():
    """Test validation of nested structures."""
    type_registry = TypeRegistry()
    validator = ASTValidator(type_registry)

    # Create and register a test condition function
    bool_type = Type(name="BOOLEAN", category=TypeCategory.LOGICAL)
    test_condition_func = FunctionDefinition(
        signature=Signature(
            name="test_condition",
            parameters=[],
            return_type=bool_type,
        ),
        body=Block(statements=[]),
    )
    validator.current_scope.declare_function(test_condition_func)

    # Create a block with nested if statements
    if_stmt = IfStatement(
        condition=FunctionCall(function_name="test_condition"),
        then_block=Block(statements=[
            BreakStatement(),  # This should fail when inside an if but outside a loop
        ]),
    )

    block = Block(statements=[if_stmt])

    # Validate with context
    context = {
        'validator': validator,
        'type_registry': type_registry,
    }

    # Should fail because the break is outside a loop
    assert not block.validate(context)

    # Now try with a loop
    loop = WhileLoop(
        condition=FunctionCall(function_name="test_condition"),
        body=Block(statements=[if_stmt]),
    )

    # This should pass because the break is inside a loop
    validator.enter_loop()
    assert loop.validate(context)
    validator.exit_loop()
