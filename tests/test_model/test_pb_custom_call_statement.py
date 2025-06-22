"""Test cases for PowerBuilder custom call statement.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBCommonParserTest.class.st
"""

from model.entities.pb_expression import PBCustomCallStatement


def test_custom_call_statement_creation():






    """Test creating a custom call statement."""
    stmt = PBCustomCallStatement(
        identifier="my_custom_call", start_position=10, stop_position=20,
    )
    assert stmt.identifier == "my_custom_call"
    assert stmt.start_position == 10
    assert stmt.stop_position == 20


def test_custom_call_statement_str():






    """Test string representation of custom call statement."""
    stmt = PBCustomCallStatement(identifier="my_custom_call")
    assert str(stmt) == "my_custom_call"


def test_custom_call_statement_equality():






    """Test equality comparison of custom call statements."""
    stmt1 = PBCustomCallStatement(identifier="call1", start_position=1, stop_position=2)
    stmt2 = PBCustomCallStatement(identifier="call1", start_position=1, stop_position=2)
    stmt3 = PBCustomCallStatement(identifier="call2", start_position=1, stop_position=2)

    assert stmt1 == stmt2
    assert stmt1 != stmt3
    assert stmt1 != "call1"


def test_custom_call_statement_hash():






    """Test hashing of custom call statements."""
    stmt1 = PBCustomCallStatement(identifier="call1", start_position=1, stop_position=2)
    stmt2 = PBCustomCallStatement(identifier="call1", start_position=1, stop_position=2)

    # Same statements should have same hash
    assert hash(stmt1) == hash(stmt2)

    # Can be used as dictionary keys
    d = {stmt1: "value"}
    assert d[stmt2] == "value"
