"""Tests for PowerBuilder SQL nodes.

This module contains parametrized tests for all SQL-related AST nodes.
"""

import pytest

from model.ast import (
    SQLCommit,
    SQLCursor,
    SQLFromClause,
    SQLPrepare,
    SQLQuery,
    SQLRollback,
    SQLTransaction,
    SQLVariable,
)

# Test data for different SQL nodes
SQL_QUERY_CASES = [
    (
        SQLQuery,
        {
            "query": "SELECT * FROM users",
            "using_clause": None,
        },
    ),
    (
        SQLQuery,
        {
            "query": "INSERT INTO orders (id, total) VALUES (?, ?)",
            "using_clause": "SQLCA",
        },
    ),
    (
        SQLQuery,
        {
            "query": "UPDATE customers SET name = ? WHERE id = ?",
            "using_clause": None,
        },
    ),
    (
        SQLQuery,
        {
            "query": "DELETE FROM products WHERE category = ?",
            "using_clause": "SQLCA",
        },
    ),
]

SQL_CURSOR_CASES = [
    (
        SQLCursor,
        {
            "name": "cur_orders",
            "query": "SELECT id FROM orders",
            "is_dynamic": False,
        },
    ),
    (
        SQLCursor,
        {
            "name": "cur_products",
            "query": SQLQuery("SELECT * FROM products"),
            "is_dynamic": True,
        },
    ),
]

SQL_TRANSACTION_CASES = [
    (
        SQLTransaction,
        {
            "action": "commit",
            "using_clause": None,
        },
    ),
    (
        SQLTransaction,
        {
            "action": "rollback",
            "using_clause": "SQLCA",
        },
    ),
]


@pytest.mark.parametrize(("cls", "attrs"), SQL_QUERY_CASES)
def test_sql_query_creation(cls: type, attrs: dict) -> None:

    
    
    """Test SQL query node creation and attributes."""
    query = cls(**attrs)
    assert isinstance(query, SQLQuery)
    for key, value in attrs.items():
        assert getattr(query, key) == value


@pytest.mark.parametrize(("cls", "attrs"), SQL_CURSOR_CASES)
def test_sql_cursor_creation(cls: type, attrs: dict) -> None:

    
    
    """Test SQL cursor node creation and attributes."""
    cursor = cls(**attrs)
    assert isinstance(cursor, SQLCursor)
    for key, value in attrs.items():
        assert getattr(cursor, key) == value


@pytest.mark.parametrize(("cls", "attrs"), SQL_TRANSACTION_CASES)
def test_sql_transaction_creation(cls: type, attrs: dict) -> None:

    
    
    """Test SQL transaction node creation and attributes."""
    trans = cls(**attrs)
    assert isinstance(trans, SQLTransaction)
    for key, value in attrs.items():
        assert getattr(trans, key) == value


def test_sql_commit() -> None:



    
    


    """Test SQL commit statement."""
    commit = SQLCommit(using_clause="SQLCA")
    assert commit.using_clause == "SQLCA"


def test_sql_rollback() -> None:



    
    


    """Test SQL rollback statement."""
    rollback = SQLRollback(using_clause=None)
    assert rollback.using_clause is None


def test_sql_prepare() -> None:



    
    


    """Test SQL prepare statement."""
    prepare = SQLPrepare(
        "stmt1",
        "SELECT * FROM users WHERE id = ?",
    )
    assert prepare.name == "stmt1"
    assert "SELECT * FROM users" in prepare.query


def test_sql_variable() -> None:



    
    


    """Test SQL variable handling."""
    var = SQLVariable("total", "decimal")
    assert var.name == "total"
    assert var.type == "decimal"


def test_sql_from_clause() -> None:



    
    


    """Test SQL FROM clause handling."""
    clause = SQLFromClause("users u")
    assert clause.table == "users u"


def test_sql_query_parameters() -> None:



    
    


    """Test SQL query parameter handling."""
    query = SQLQuery(
        "SELECT * FROM users WHERE id = ? AND status = ?",
        using_clause="SQLCA",
    )
    assert "?" in query.query
    assert query.using_clause == "SQLCA"


def test_dynamic_cursor() -> None:



    
    


    """Test dynamic SQL cursor handling."""
    cursor = SQLCursor(
        "cur_dynamic",
        SQLQuery("SELECT * FROM ${table}"),
        is_dynamic=True,
    )
    assert cursor.is_dynamic
    assert isinstance(cursor.query, SQLQuery)
    assert "${table}" in cursor.query.query


def test_transaction_using_clause() -> None:



    
    


    """Test transaction USING clause handling."""
    # Default transaction
    trans1 = SQLTransaction("commit")
    assert trans1.using_clause is None

    # Named transaction
    trans2 = SQLTransaction("rollback", "SQLCA")
    assert trans2.using_clause == "SQLCA"
