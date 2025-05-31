"""Tests for PowerBuilder behavioral model."""

import pytest

from model.pb_behavioral import (
    PBBehavioral,
    PBBehavioralDeclaration,
    PBBehavioralImplementation,
    PBBehavioralNode,
    PBBehavioralScope,
    PBBehavioralType,
    PBEvent,
    PBEventHandler,
    PBEventTrigger,
    PBFunction,
    PBFunctionSignature,
    PBMethod,
    PBScript,
)


class TestPBBehavioralNode:
    """Test PBBehavioralNode class."""

    def test_behavioral_node_creation(self):
        """Test creating a behavioral node."""
        node = PBBehavioralNode(name="test_node")
        assert node.name == "test_node"

    def test_behavioral_node_with_type(self):
        """Test behavioral node with type."""
        node = PBBehavioralNode(name="typed_node", behavioral_type="function")
        assert node.name == "typed_node"
        assert node.behavioral_type == "function"


class TestPBBehavioral:
    """Test PBBehavioral class."""

    def test_behavioral_creation(self):
        """Test creating a behavioral element."""
        behavioral = PBBehavioral(
            name="test_behavioral",
            access_level="public",
            is_static=False,
        )
        assert behavioral.name == "test_behavioral"
        assert behavioral.access_level == "public"
        assert behavioral.is_static is False


class TestPBFunction:
    """Test PBFunction class."""

    def test_function_creation(self):
        """Test creating a function."""
        func = PBFunction(
            name="calculate",
            return_type="integer",
            parameters=[],
            body=[],
        )
        assert func.name == "calculate"
        assert func.return_type == "integer"
        assert func.parameters == []
        assert func.body == []

    def test_function_with_parameters(self):
        """Test function with parameters."""
        params = [
            {"name": "x", "type": "integer"},
            {"name": "y", "type": "integer"},
        ]
        func = PBFunction(
            name="add",
            return_type="integer",
            parameters=params,
            body=["return x + y"],
        )
        assert len(func.parameters) == 2
        assert func.parameters[0]["name"] == "x"
        assert func.parameters[1]["type"] == "integer"


class TestPBEvent:
    """Test PBEvent class."""

    def test_event_creation(self):
        """Test creating an event."""
        event = PBEvent(
            name="clicked",
            event_type="pbm_btnclicked",
            parameters=[],
        )
        assert event.name == "clicked"
        assert event.event_type == "pbm_btnclicked"

    def test_event_with_handler(self):
        """Test event with handler code."""
        event = PBEvent(
            name="itemchanged",
            event_type="pbm_itemchanged",
            parameters=[{"name": "row", "type": "long"}],
            body=["MessageBox('Changed', 'Item changed')"],
        )
        assert len(event.parameters) == 1
        assert event.body[0] == "MessageBox('Changed', 'Item changed')"


class TestPBEventHandler:
    """Test PBEventHandler class."""

    def test_event_handler_creation(self):
        """Test creating an event handler."""
        handler = PBEventHandler(
            event_name="clicked",
            object_name="cb_ok",
            script=["Close(Parent)"],
        )
        assert handler.event_name == "clicked"
        assert handler.object_name == "cb_ok"
        assert handler.script[0] == "Close(Parent)"


class TestPBMethod:
    """Test PBMethod class."""

    def test_method_creation(self):
        """Test creating a method."""
        method = PBMethod(
            name="process_data",
            return_type="boolean",
            access_level="protected",
            is_virtual=True,
        )
        assert method.name == "process_data"
        assert method.return_type == "boolean"
        assert method.access_level == "protected"
        assert method.is_virtual is True


class TestPBScript:
    """Test PBScript class."""

    def test_script_creation(self):
        """Test creating a script."""
        script = PBScript(
            name="initialization_script",
            code=["integer li_count", "li_count = 0"],
        )
        assert script.name == "initialization_script"
        assert len(script.code) == 2


class TestPBBehavioralDeclaration:
    """Test PBBehavioralDeclaration class."""

    def test_declaration_creation(self):
        """Test creating a behavioral declaration."""
        decl = PBBehavioralDeclaration(
            name="get_value",
            type="function",
            signature="integer get_value(string as_key)",
        )
        assert decl.name == "get_value"
        assert decl.type == "function"
        assert "as_key" in decl.signature


class TestPBBehavioralImplementation:
    """Test PBBehavioralImplementation class."""

    def test_implementation_creation(self):
        """Test creating a behavioral implementation."""
        impl = PBBehavioralImplementation(
            declaration="get_value",
            body=["return instance_variable"],
        )
        assert impl.declaration == "get_value"
        assert impl.body[0] == "return instance_variable"


class TestPBBehavioralScope:
    """Test PBBehavioralScope class."""

    @pytest.mark.parametrize(("scope", "expected"), [
        ("PUBLIC", "PUBLIC"),
        ("PRIVATE", "PRIVATE"),
        ("PROTECTED", "PROTECTED"),
        ("GLOBAL", "GLOBAL"),
        ("LOCAL", "LOCAL"),
    ])
    def test_scope_values(self, scope, expected):
        """Test behavioral scope values."""
        behavioral_scope = PBBehavioralScope(value=scope)
        assert behavioral_scope.value == expected


class TestPBBehavioralType:
    """Test PBBehavioralType class."""

    @pytest.mark.parametrize(("type_name", "expected"), [
        ("FUNCTION", "FUNCTION"),
        ("SUBROUTINE", "SUBROUTINE"),
        ("EVENT", "EVENT"),
        ("EXTERNAL", "EXTERNAL"),
    ])
    def test_behavioral_types(self, type_name, expected):
        """Test behavioral type values."""
        behavioral_type = PBBehavioralType(value=type_name)
        assert behavioral_type.value == expected


class TestPBFunctionSignature:
    """Test PBFunctionSignature class."""

    def test_signature_creation(self):
        """Test creating a function signature."""
        sig = PBFunctionSignature(
            name="calculate_total",
            return_type="decimal",
            parameters=[
                {"name": "amount", "type": "decimal"},
                {"name": "tax_rate", "type": "decimal"},
            ],
        )
        assert sig.name == "calculate_total"
        assert sig.return_type == "decimal"
        assert len(sig.parameters) == 2


class TestPBEventTrigger:
    """Test PBEventTrigger class."""

    def test_event_trigger_creation(self):
        """Test creating an event trigger."""
        trigger = PBEventTrigger(
            event="clicked",
            target="cb_save",
            arguments=[],
        )
        assert trigger.event == "clicked"
        assert trigger.target == "cb_save"

    def test_event_trigger_with_args(self):
        """Test event trigger with arguments."""
        trigger = PBEventTrigger(
            event="custom_event",
            target="parent",
            arguments=["100", "true"],
        )
        assert len(trigger.arguments) == 2
        assert trigger.arguments[0] == "100"
