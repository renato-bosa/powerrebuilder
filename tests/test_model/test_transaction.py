"""Test PowerBuilder transaction handling."""

from model.pb_transaction import (
    PBSavepoint,
    PBStatementType,
    PBTransaction,
    PBTransactionObject,
    PBTransactionState,
    PBTransactionStatement,
)
from parse.transaction_parser import Parser


# Tests for the model objects
def test_transaction_object():
    """Test creation of transaction object."""
    txn_obj = PBTransactionObject(
        name="sqlca",
        dbms="ODBC",
        database="MyDB",
        userid="user1",
        dbpass="pass1",
    )
    assert txn_obj.name == "sqlca"
    assert txn_obj.dbms == "ODBC"
    assert txn_obj.database == "MyDB"


def test_transaction_statement():
    """Test creation of transaction statement."""
    stmt = PBTransactionStatement(
        statement_type=PBStatementType.CONNECT,
        transaction_object="sqlca",
    )
    assert stmt.statement_type == PBStatementType.CONNECT
    assert stmt.transaction_object == "sqlca"

    # Test with string statement type
    stmt2 = PBTransactionStatement(
        statement_type="COMMIT",
        transaction_object="sqlca",
    )
    assert stmt2.statement_type == PBStatementType.COMMIT

    # Test SQL statement
    sql_stmt = PBTransactionStatement(
        statement_type=PBStatementType.INSERT,
        transaction_object="sqlca",
        sql_text="INSERT INTO customers (name) VALUES ('John')",
    )
    assert sql_stmt.statement_type == PBStatementType.INSERT
    assert "customers" in sql_stmt.sql_text


def test_transaction_with_statements():
    """Test transaction with statements."""
    txn = PBTransaction(transaction_object="sqlca")

    stmt1 = PBTransactionStatement(
        statement_type=PBStatementType.INSERT,
        transaction_object="sqlca",
        sql_text="INSERT INTO customers (name) VALUES ('John')",
    )

    stmt2 = PBTransactionStatement(
        statement_type=PBStatementType.COMMIT,
        transaction_object="sqlca",
    )

    txn.add_statement(stmt1)
    txn.add_statement(stmt2)

    assert len(txn.statements) == 2
    assert txn.statements[0].sql_text == "INSERT INTO customers (name) VALUES ('John')"
    assert txn.statements[1].statement_type == PBStatementType.COMMIT


def test_transaction_with_savepoint():
    """Test transaction with savepoint."""
    txn = PBTransaction(transaction_object="sqlca")

    savepoint = PBSavepoint(
        name="sp1",
        transaction_object="sqlca",
    )

    txn.add_savepoint(savepoint)

    assert len(txn.savepoints) == 1
    assert txn.savepoints[0].name == "sp1"
    assert "sp1" in txn.state.savepoints


def test_transaction_state():
    """Test transaction state tracking."""
    state = PBTransactionState(
        is_connected=True,
        in_progress=True,
    )

    assert state.is_connected
    assert state.in_progress
    assert not state.distributed

    # Test with distributed transaction
    state.distributed = True
    state.coordinator = "tx_coord1"

    assert state.distributed
    assert state.coordinator == "tx_coord1"


# Tests for parsing functionality
def test_parse_transaction_object():
    """Test parsing of transaction object declaration."""
    code = """transaction sqlca"""
    parser = Parser()
    result = parser.parse_transaction(code)
    assert isinstance(result, PBTransactionObject)
    assert result.name == "sqlca"


def test_parse_connect_statement():
    """Test parsing of CONNECT statement."""
    code = """CONNECT USING sqlca;"""
    parser = Parser()
    result = parser.parse_transaction_statement(code)
    assert isinstance(result, PBTransactionStatement)
    assert result.statement_type == PBStatementType.CONNECT
    assert result.transaction_object == "sqlca"


def test_parse_commit_statement():
    """Test parsing of COMMIT statement."""
    code = """COMMIT USING sqlca;"""
    parser = Parser()
    result = parser.parse_transaction_statement(code)
    assert isinstance(result, PBTransactionStatement)
    assert result.statement_type == PBStatementType.COMMIT
    assert result.transaction_object == "sqlca"


def test_parse_rollback_statement():
    """Test parsing of ROLLBACK statement."""
    code = """ROLLBACK USING sqlca;"""
    parser = Parser()
    result = parser.parse_transaction_statement(code)
    assert isinstance(result, PBTransactionStatement)
    assert result.statement_type == PBStatementType.ROLLBACK
    assert result.transaction_object == "sqlca"


def test_parse_disconnect_statement():
    """Test parsing of DISCONNECT statement."""
    code = """DISCONNECT USING sqlca;"""
    parser = Parser()
    result = parser.parse_transaction_statement(code)
    assert isinstance(result, PBTransactionStatement)
    assert result.statement_type == PBStatementType.DISCONNECT
    assert result.transaction_object == "sqlca"


def test_parse_transaction_block():
    """Test parsing of transaction block."""
    code = """
    USING sqlca;
    INSERT INTO customers (name) VALUES ('John');
    UPDATE orders SET status = 'shipped' WHERE order_id = 123;
    COMMIT USING sqlca;
    """
    parser = Parser()
    result = parser.parse_transaction_block(code)
    assert isinstance(result, PBTransaction)
    assert result.transaction_object == "sqlca"
    assert len(result.statements) >= 3  # At least INSERT, UPDATE, COMMIT

    # Check if there's a COMMIT statement (it should be one of the statements)
    has_commit = False
    for stmt in result.statements:
        if stmt.statement_type == PBStatementType.COMMIT:
            has_commit = True
            break
    assert has_commit


def test_parse_transaction_with_error_handling():
    """Test parsing of transaction with error handling."""
    code = """
    USING sqlca;
    TRY
        INSERT INTO customers (name) VALUES ('John');
        UPDATE orders SET status = 'shipped' WHERE order_id = 123;
        COMMIT USING sqlca;
    CATCH (SQLException e)
        ROLLBACK USING sqlca;
    END TRY;
    """
    parser = Parser()
    result = parser.parse_transaction_block(code)
    assert isinstance(result, PBTransaction)
    assert result.has_error_handling

    # Check that both COMMIT and ROLLBACK statements are recognized
    has_commit = has_rollback = False
    for stmt in result.statements:
        if stmt.statement_type == PBStatementType.COMMIT:
            has_commit = True
        elif stmt.statement_type == PBStatementType.ROLLBACK:
            has_rollback = True
    assert has_commit
    assert has_rollback


def test_parse_transaction_with_savepoint():
    """Test parsing of transaction with savepoint."""
    code = """
    USING sqlca;
    SAVEPOINT sp1;
    INSERT INTO customers (name) VALUES ('John');
    IF error_occurred THEN
        ROLLBACK TO SAVEPOINT sp1;
    ELSE
        COMMIT USING sqlca;
    END IF;
    """
    parser = Parser()
    result = parser.parse_transaction_block(code)
    assert isinstance(result, PBTransaction)
    assert len(result.savepoints) == 1
    assert result.savepoints[0].name == "sp1"
