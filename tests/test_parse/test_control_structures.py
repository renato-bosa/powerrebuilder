"""Tests for control structure AST nodes."""

import pytest

from model.ast import (
    Block,
    BooleanOperation,
    BreakStatement,
    CaseItem,
    CaseStatement,
    Condition,
    ContinueStatement,
    Expression,
    ForLoop,
    GotoStatement,
    IfStatement,
    LabelStatement,
    RepeatUntilLoop,
    ReturnStatement,
    TypeRegistry,
    WhileLoop,
)
from model.utils.validators import ASTValidator


@pytest.fixture
def type_registry():
    """Create a type registry for testing."""
    return TypeRegistry()


@pytest.fixture
def validator(type_registry):
    """Create a control flow validator."""
    return ASTValidator(type_registry)


def test_if_statement(validator):
    """Test IF statement validation."""
    # Create a simple IF statement
    if_stmt = IfStatement(
        condition=Condition(
            left=Expression(),
            operator="=",
            right=Expression(),
        ),
        then_block=Block(
            [
                ReturnStatement(),
            ]
        ),
        else_block=Block(
            [
                ReturnStatement(),
            ]
        ),
    )
    assert validator.validate_block(Block([if_stmt]))


def test_while_loop(validator):
    """Test WHILE loop validation."""
    # Create a WHILE loop
    while_loop = WhileLoop(
        condition=Condition(
            left=Expression(),
            operator="<",
            right=Expression(),
        ),
        body=Block(
            [
                ContinueStatement(),
            ]
        ),
    )
    assert validator.validate_block(Block([while_loop]))
    assert validator.current_loop_depth == 0  # Loop depth properly restored


def test_repeat_until_loop(validator):
    """Test REPEAT-UNTIL loop validation."""
    # Create a REPEAT-UNTIL loop
    repeat_loop = RepeatUntilLoop(
        body=Block(
            [
                BreakStatement(),
            ]
        ),
        condition=Condition(
            left=Expression(),
            operator=">",
            right=Expression(),
        ),
    )
    assert validator.validate_block(Block([repeat_loop]))
    assert validator.current_loop_depth == 0


def test_for_loop(validator):
    """Test FOR loop validation."""
    # Create a FOR loop
    for_loop = ForLoop(
        variable="i",
        start=Expression(),
        end=Expression(),
        step=Expression(),
        body=Block(
            [
                ContinueStatement(),
            ]
        ),
    )
    assert validator.validate_block(Block([for_loop]))
    assert validator.current_loop_depth == 0


def test_case_statement(validator):
    """Test CASE statement validation."""
    # Create a CASE statement
    case_stmt = CaseStatement(
        expression=Expression(),
        cases=[
            CaseItem(Expression(), ReturnStatement()),
            CaseItem(Expression(), ReturnStatement()),
        ],
        otherwise=ReturnStatement(),
    )
    assert validator.validate_block(Block([case_stmt]))


def test_break_continue_validation(validator):
    """Test BREAK and CONTINUE validation."""
    # BREAK/CONTINUE outside loop should fail
    block = Block(
        [
            BreakStatement(),
            ContinueStatement(),
        ]
    )
    assert not validator.validate_block(block)

    # BREAK/CONTINUE inside loop should succeed
    loop = WhileLoop(
        condition=Expression(),
        body=Block(
            [
                BreakStatement(),
                ContinueStatement(),
            ]
        ),
    )
    assert validator.validate_block(Block([loop]))


def test_goto_validation(validator):
    """Test GOTO validation."""
    # Create label and GOTO
    label = LabelStatement("target")
    goto = GotoStatement("target")

    # GOTO before label should fail
    assert not validator.validate_block(Block([goto]))

    # GOTO after label should succeed
    assert validator.validate_block(Block([label, goto]))


def test_nested_control_structures(validator):
    """Test nested control structures."""
    # Create complex nested structure
    nested_block = Block(
        [
            ForLoop(
                variable="i",
                start=Expression(),
                end=Expression(),
                body=Block(
                    [
                        IfStatement(
                            condition=Expression(),
                            then_block=Block(
                                [
                                    WhileLoop(
                                        condition=Expression(),
                                        body=Block(
                                            [
                                                BreakStatement(),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                            else_block=Block(
                                [
                                    ContinueStatement(),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    assert validator.validate_block(nested_block)
    assert validator.current_loop_depth == 0


def test_return_validation(validator, type_registry):
    """Test return statement validation."""
    # Return without value in void context
    assert ReturnStatement().validate(
        {"type_registry": type_registry, "expected_type": None}
    )

    # Return with value in non-void context
    int_type = type_registry.get_type("INTEGER")
    return_stmt = ReturnStatement(Expression())
    assert return_stmt.validate(
        {"type_registry": type_registry, "expected_type": int_type}
    )

    # Return with value in void context should fail
    assert not return_stmt.validate(
        {"type_registry": type_registry, "expected_type": None}
    )

    # Return without value in non-void context should fail
    assert not ReturnStatement().validate(
        {"type_registry": type_registry, "expected_type": int_type}
    )


def test_boolean_operations(validator):
    """Test boolean operations in conditions."""
    # Test AND operation
    and_op = BooleanOperation(
        operator="AND",
        operands=[
            Condition(Expression(), "=", Expression()),
            Condition(Expression(), "<", Expression()),
        ],
    )
    if_stmt = IfStatement(and_op, Block())
    assert validator.validate_block(Block([if_stmt]))

    # Test OR operation
    or_op = BooleanOperation(
        operator="OR",
        operands=[
            Condition(Expression(), ">", Expression()),
            Condition(Expression(), "=", Expression()),
        ],
    )
    if_stmt = IfStatement(or_op, Block())
    assert validator.validate_block(Block([if_stmt]))


def test_empty_blocks(validator):
    """Test empty block validation."""
    assert validator.validate_block(Block([]))

    # Empty blocks in control structures
    assert validator.validate_block(
        Block(
            [
                IfStatement(Expression(), Block()),
                WhileLoop(Expression(), Block()),
                RepeatUntilLoop(Block(), Expression()),
                ForLoop("i", Expression(), Expression(), body=Block()),
            ]
        )
    )


def test_invalid_control_flow(validator):
    """Test invalid control flow patterns."""
    # BREAK in IF statement (not in loop)
    if_stmt = IfStatement(
        condition=Expression(),
        then_block=Block([BreakStatement()]),
    )
    assert not validator.validate_block(Block([if_stmt]))

    # Undefined label
    goto = GotoStatement("nonexistent")
    assert not validator.validate_block(Block([goto]))

    # Multiple labels with same name
    Block(
        [
            LabelStatement("label"),
            LabelStatement("label"),  # Duplicate
            GotoStatement("label"),
        ]
    )
    # This should fail once we implement duplicate label checking
    # assert not validator.validate_block(block)


def test_example1_arithmetic_operations(validator):
    """Test arithmetic operations from Example1.txt."""
    # Create a block of arithmetic operations
    block = Block(
        [
            # a <- 1
            # OUTPUT(a*2)
            # OUTPUT(a+3)
            # OUTPUT(a-2)
            # OUTPUT(a^4)
            # OUTPUT(a/3)
            Expression(),  # Placeholder for actual arithmetic expressions
            Expression(),
            Expression(),
            Expression(),
            Expression(),
        ]
    )
    assert validator.validate_block(block)


def test_example2_loop_combinations(validator):
    """Test loop combinations from Example2.txt."""
    # FOR loop with STEP
    for_loop = ForLoop(
        variable="i",
        start=Expression(),  # 0
        end=Expression(),  # 100
        step=Expression(),  # 3
        body=Block(
            [
                Expression(),  # a <- a + 1
            ]
        ),
    )

    # WHILE loop
    while_loop = WhileLoop(
        condition=Condition(
            left=Expression(),  # b
            operator="<",
            right=Expression(),  # 45
        ),
        body=Block(
            [
                Expression(),  # b <- b + 4
            ]
        ),
    )

    # REPEAT-UNTIL loop
    repeat_loop = RepeatUntilLoop(
        body=Block(
            [
                Expression(),  # c <- c * 2
            ]
        ),
        condition=Condition(
            left=Expression(),  # c
            operator=">=",
            right=Expression(),  # 500
        ),
    )

    block = Block([for_loop, while_loop, repeat_loop])
    assert validator.validate_block(block)
    assert validator.current_loop_depth == 0


def test_example3_function_procedure(validator, type_registry):
    """Test function and procedure from Example3.txt."""
    # Function with parameters and return
    function_block = Block(
        [
            Expression(),  # a <- a + 1
            Expression(),  # OUTPUT(b)
            ReturnStatement(Expression()),  # RETURN a
        ]
    )

    # We need to provide an expected_type for the return statement
    assert validator.validate_block(function_block, type_registry.get_type("INTEGER"))

    # Procedure with parameters
    procedure_block = Block(
        [
            Expression(),  # OUTPUT(a)
            Expression(),  # OUTPUT(b)
        ]
    )
    assert validator.validate_block(procedure_block)


def test_example4_if_case(validator):
    """Test IF and CASE statements from Example4.txt."""
    # IF statement
    if_stmt = IfStatement(
        condition=Condition(
            left=Expression(),  # a
            operator="=",
            right=Expression(),  # 'hi'
        ),
        then_block=Block(
            [
                Expression(),  # OUTPUT("hi")
            ]
        ),
        else_block=Block(
            [
                Expression(),  # OUTPUT("BYE")
            ]
        ),
    )

    # CASE statement
    case_stmt = CaseStatement(
        expression=Expression(),  # a
        cases=[
            CaseItem(Expression(), Expression()),  # "38": OUTPUT(38)
            CaseItem(Expression(), Expression()),  # "BYE": OUTPUT("BYE")
            CaseItem(Expression(), Expression()),  # "hi": OUTPUT("HI")
        ],
    )

    block = Block([if_stmt, case_stmt])
    assert validator.validate_block(block)


def test_nested_loops_with_break(validator):
    """Test nested loops with break statements."""
    inner_loop = WhileLoop(
        condition=Expression(),
        body=Block(
            [
                IfStatement(
                    condition=Expression(),
                    then_block=Block(
                        [
                            BreakStatement(),
                        ]
                    ),
                ),
            ]
        ),
    )

    outer_loop = ForLoop(
        variable="i",
        start=Expression(),
        end=Expression(),
        body=Block([inner_loop]),
    )

    assert validator.validate_block(Block([outer_loop]))
    assert validator.current_loop_depth == 0


def test_case_with_multiple_actions(validator):
    """Test CASE statement with multiple actions per case."""
    case_stmt = CaseStatement(
        expression=Expression(),
        cases=[
            CaseItem(
                Expression(),
                Block(
                    [
                        Expression(),
                        Expression(),
                        IfStatement(
                            condition=Expression(),
                            then_block=Block([Expression()]),
                        ),
                    ]
                ),
            ),
            CaseItem(
                Expression(),
                Block(
                    [
                        WhileLoop(
                            condition=Expression(),
                            body=Block([Expression()]),
                        ),
                    ]
                ),
            ),
        ],
        otherwise=Block(
            [
                Expression(),
                Expression(),
            ]
        ),
    )

    assert validator.validate_block(Block([case_stmt]))


def test_loop_with_continue_conditions(validator):
    """Test loops with conditional continue statements."""
    loop = WhileLoop(
        condition=Expression(),
        body=Block(
            [
                IfStatement(
                    condition=Expression(),
                    then_block=Block(
                        [
                            ContinueStatement(),
                        ]
                    ),
                    else_block=Block(
                        [
                            Expression(),
                        ]
                    ),
                ),
                Expression(),
            ]
        ),
    )

    assert validator.validate_block(Block([loop]))
    assert validator.current_loop_depth == 0


def test_mixed_control_flow(validator):
    """Test mixed control flow structures."""
    block = Block(
        [
            IfStatement(
                condition=Expression(),
                then_block=Block(
                    [
                        WhileLoop(
                            condition=Expression(),
                            body=Block(
                                [
                                    CaseStatement(
                                        expression=Expression(),
                                        cases=[
                                            CaseItem(
                                                Expression(),
                                                RepeatUntilLoop(
                                                    body=Block([Expression()]),
                                                    condition=Expression(),
                                                ),
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )

    assert validator.validate_block(block)
    assert validator.current_loop_depth == 0


def test_control_flow_type_checking(validator, type_registry):
    """Test type checking in control structures."""
    # TODO: Implement once type checking is added to validation
