"""Tests for PowerBuilder statement nodes.

This module contains parametrized tests for all statement-related AST nodes.
"""

import pytest
from model.ast import (
    Event,
    EventTrigger,
    ExecuteProcedure,
    ExitStatement,
    ForLoop,
    Function,
    GotoStatement,
    IfStatement,
    Parameter,
    ReturnStatement,
    SQLCommit,
    SQLCursor,
    SQLQuery,
    SQLRollback,
    SQLTransaction,
    Statement,
    TryCatch,
    Type,
)

# Test data for different statement types
STATEMENT_CASES = [
    (Event, {
        'name': 'clicked',
        'parameters': [],
        'body': [],
    }),
    (EventTrigger, {
        'event': Event('clicked'),
        'arguments': [],
    }),
    (Function, {
        'name': 'calculate',
        'return_type': Type('integer'),
        'parameters': [],
        'body': [],
    }),
    (IfStatement, {
        'condition': None,
        'then_statements': [],
        'else_statements': [],
    }),
    (ForLoop, {
        'variable': None,
        'start': None,
        'end': None,
        'step': None,
        'statements': [],
    }),
    (TryCatch, {
        'try_statements': [],
        'catch_statements': [],
        'finally_statements': [],
    }),
    (ReturnStatement, {
        'expression': None,
    }),
    (GotoStatement, {
        'label': 'error_handler',
    }),
    (ExitStatement, {
        'type': 'function',
    }),
    (ExecuteProcedure, {
        'name': 'sp_update',
        'arguments': [],
    }),
]

SQL_STATEMENT_CASES = [
    (SQLQuery, {
        'query': 'SELECT * FROM users',
        'using_clause': None,
    }),
    (SQLCursor, {
        'name': 'cur',
        'query': 'SELECT id FROM orders',
        'is_dynamic': False,
    }),
    (SQLTransaction, {
        'action': 'commit',
        'using_clause': None,
    }),
    (SQLCommit, {
        'using_clause': None,
    }),
    (SQLRollback, {
        'using_clause': None,
    }),
]

@pytest.mark.parametrize(("cls", "attrs"), STATEMENT_CASES)
def test_statement_creation(cls: type, attrs: dict) -> None:
    """Test statement node creation and attributes."""
    stmt = cls(**attrs)
    assert isinstance(stmt, Statement)
    for key, value in attrs.items():
        assert getattr(stmt, key) == value

@pytest.mark.parametrize(("cls", "attrs"), SQL_STATEMENT_CASES)
def test_sql_statement_creation(cls: type, attrs: dict) -> None:
    """Test SQL statement node creation and attributes."""
    stmt = cls(**attrs)
    assert isinstance(stmt, Statement)
    for key, value in attrs.items():
        assert getattr(stmt, key) == value

def test_if_statement_branches() -> None:
    """Test if statement branch handling."""
    if_stmt = IfStatement(
        condition=None,
        then_statements=[ReturnStatement(None)],
        else_statements=[ExitStatement('function')],
    )

    assert len(if_stmt.then_statements) == 1
    assert len(if_stmt.else_statements) == 1
    assert isinstance(if_stmt.then_statements[0], ReturnStatement)
    assert isinstance(if_stmt.else_statements[0], ExitStatement)

def test_try_catch_blocks() -> None:
    """Test try-catch block handling."""
    try_catch = TryCatch(
        try_statements=[SQLQuery('SELECT * FROM users')],
        catch_statements=[SQLRollback()],
        finally_statements=[SQLCommit()],
    )

    assert len(try_catch.try_statements) == 1
    assert len(try_catch.catch_statements) == 1
    assert len(try_catch.finally_statements) == 1
    assert isinstance(try_catch.try_statements[0], SQLQuery)
    assert isinstance(try_catch.catch_statements[0], SQLRollback)
    assert isinstance(try_catch.finally_statements[0], SQLCommit)

def test_for_loop_structure() -> None:
    """Test for loop structure handling."""
    loop = ForLoop(
        variable='i',
        start=1,
        end=10,
        step=1,
        statements=[ReturnStatement(None)],
    )

    assert loop.variable == 'i'
    assert loop.start == 1
    assert loop.end == 10
    assert loop.step == 1
    assert len(loop.statements) == 1
    assert isinstance(loop.statements[0], ReturnStatement)

def test_function_parameters() -> None:
    """Test function parameter handling."""
    func = Function(
        name='calculate',
        return_type=Type('integer'),
        parameters=[
            Parameter('x', Type('integer')),
            Parameter('y', Type('integer')),
        ],
        body=[ReturnStatement(None)],
    )

    assert len(func.parameters) == 2
    assert all(isinstance(p, Parameter) for p in func.parameters)
    assert func.parameters[0].name == 'x'
    assert func.parameters[1].name == 'y'
    assert len(func.body) == 1
    assert isinstance(func.body[0], ReturnStatement)
