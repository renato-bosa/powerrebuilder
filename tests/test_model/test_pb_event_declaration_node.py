"""Test cases for the PBEventDeclarationNode class.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Tests/PWBASTVisitorTest.class.st
"""

from model.entities.pb_expression import PBEventDeclarationNode


def test_event_declaration_node_creation():



    


    """Test creating an event declaration node."""
    return_type = "integer"
    event_reference_name = "clicked"
    custom_call_statement = "call super::clicked"
    statements = ["a = a + 1", "print(a)"]
    node = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    assert node.return_type == return_type
    assert node.event_reference_name == event_reference_name
    assert node.custom_call_statement == custom_call_statement
    assert node.statements == statements
    assert node.start_position == 10
    assert node.stop_position == 20


def test_event_declaration_node_str():



    


    """Test string representation of event declaration node."""
    node = PBEventDeclarationNode(
        return_type="integer",
        event_reference_name="clicked",
        custom_call_statement="call super::clicked",
        statements=["stmt1", "stmt2"],
    )
    assert str(node) == "integer event clicked\ncall super::clicked\nstmt1\nstmt2"


def test_event_declaration_node_str_without_custom_call():



    


    """Test string representation of event declaration node without custom call."""
    node = PBEventDeclarationNode(
        return_type="integer",
        event_reference_name="clicked",
        statements=["stmt1", "stmt2"],
    )
    assert str(node) == "integer event clicked\nstmt1\nstmt2"


def test_event_declaration_node_str_without_statements():



    


    """Test string representation of event declaration node without statements."""
    node = PBEventDeclarationNode(
        return_type="integer",
        event_reference_name="clicked",
        custom_call_statement="call super::clicked",
    )
    assert str(node) == "integer event clicked\ncall super::clicked"


def test_event_declaration_node_equality():



    


    """Test event declaration node equality comparison."""
    return_type = "integer"
    event_reference_name = "clicked"
    custom_call_statement = "call super::clicked"
    statements = ["a = a + 1", "print(a)"]
    node1 = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements.copy(),
        start_position=10,
        stop_position=20,
    )
    node3 = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements,
        start_position=15,
        stop_position=25,
    )
    node4 = PBEventDeclarationNode(
        return_type="long",
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements,
        start_position=10,
        stop_position=20,
    )

    assert node1 == node2  # Same values
    assert node1 != node3  # Different positions
    assert node1 != node4  # Different return type
    assert node1 != "not a node"  # Different type


def test_event_declaration_node_hash():



    


    """Test event declaration node hashing."""
    return_type = "integer"
    event_reference_name = "clicked"
    custom_call_statement = "call super::clicked"
    statements = ["a = a + 1", "print(a)"]
    node1 = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    node2 = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements.copy(),
        start_position=10,
        stop_position=20,
    )

    assert hash(node1) == hash(node2)


def test_event_declaration_node_visitor():



    


    """Test event declaration node visitor pattern."""

    class TestVisitor:
        def visit_event_declaration_node(self, node) -> str:
            
            return "visited"

    return_type = "integer"
    event_reference_name = "clicked"
    custom_call_statement = "call super::clicked"
    statements = ["a = a + 1", "print(a)"]
    node = PBEventDeclarationNode(
        return_type=return_type,
        event_reference_name=event_reference_name,
        custom_call_statement=custom_call_statement,
        statements=statements,
        start_position=10,
        stop_position=20,
    )
    visitor = TestVisitor()

    assert node.accept_visitor(visitor) == "visited"
