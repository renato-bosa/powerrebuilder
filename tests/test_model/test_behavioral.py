"""Test PowerBuilder behavioral model functionality."""

from pathlib import Path

from model.constructs.pb_access import AccessType, PBAccess
from model.base.pb_behavioral import (
    AccessModifier,
    BehavioralOption,
    PBBehavioral,
    PBBehavioralAlias,
    PBBehaviorSignature,
    PBFunctionReturn,
    PBInvocation,
    PBParameter,
    PBVariable,
)
from model.base.pb_behavioral_library import PBBehavioralLibrary
from model.base.pb_type import PBBasicType


def test_behavioral_basic():
    """Test basic behavioral functionality."""
    func = PBBehavioral(name="test_func")
    assert func.name == "test_func"
    assert func.access_modifier == AccessModifier.PUBLIC
    assert func.is_behavioral
    assert not func.is_global
    assert not func.is_private
    assert func.cyclomatic_complexity == 1


def test_behavioral_parameters():
    """Test behavioral parameter handling."""
    func = PBBehavioral(name="test_func")

    # Add parameters
    param1 = PBParameter(
        name="p1",
        parameter_type=PBBasicType(name="integer"),
    )
    param2 = PBParameter(
        name="p2",
        parameter_type=PBBasicType(name="string"),
    )

    func.add_parameter(param1)
    func.add_parameter(param2)

    # Test parameter linking
    assert len(func.parameters) == 2
    assert func.parameters[0].behavioral == func
    assert func.parameters[1].behavioral == func

    # Test parameter string representation
    assert param1.to_string() == "p1: integer"
    assert param2.to_string() == "p2: string"


def test_behavioral_returns():
    """Test behavioral return handling."""
    func = PBBehavioral(name="test_func")

    # Add returns
    ret1 = PBFunctionReturn(behavioral=func, value=42)
    ret2 = PBFunctionReturn(behavioral=func, value="success")

    func.add_return(ret1)
    func.add_return(ret2)

    # Test return linking
    assert len(func.returns) == 2
    assert func.returns[0].behavioral == func
    assert func.returns[1].behavioral == func
    assert func.returns[0].value == 42
    assert func.returns[1].value == "success"


def test_behavioral_variables():
    """Test behavioral variable handling."""
    func = PBBehavioral(name="test_func")

    # Add variables
    var1 = PBVariable(
        name="counter",
        behavioral=func,
        variable_type=PBBasicType(name="integer"),
        initial_value=0,
    )
    var2 = PBVariable(
        name="name",
        behavioral=func,
        variable_type=PBBasicType(name="string"),
    )

    func.add_variable(var1)
    func.add_variable(var2)

    # Test variable linking
    assert len(func.variables) == 2
    assert func.variables[0].behavioral == func
    assert func.variables[1].behavioral == func

    # Test variable string representation
    assert var1.to_string() == "counter: integer = 0"
    assert var2.to_string() == "name: string"


def test_behavioral_access():
    """Test behavioral access tracking."""
    func = PBBehavioral(name="test_func")

    # Add accesses
    access1 = PBAccess(
        name="read_access",
        variable_name="m_data",
        access_type=AccessType.READ,
        is_instance_access=True,
    )
    access2 = PBAccess(
        name="write_access",
        variable_name="m_data",
        access_type=AccessType.WRITE,
        is_instance_access=True,
    )

    func.add_access(access1)
    func.add_access(access2)

    # Test access tracking
    assert len(func.accesses) == 2
    assert len(func.get_accessed_attributes()) == 2


def test_behavioral_invocations():
    """Test behavioral invocation tracking."""
    func1 = PBBehavioral(name="caller")
    func2 = PBBehavioral(name="callee")

    # Create invocation
    invocation = PBInvocation(
        name="test_invocation",
        source=func1,
        target=func2,
    )

    func1.add_invocation(invocation)
    func2.add_invocation(invocation)

    # Test invocation tracking
    assert len(func1.get_outgoing_invocations()) == 1
    assert len(func1.get_incoming_invocations()) == 0
    assert len(func2.get_outgoing_invocations()) == 0
    assert len(func2.get_incoming_invocations()) == 1


def test_behavioral_complexity():
    """Test behavioral complexity tracking."""
    func = PBBehavioral(name="test_func")
    assert func.cyclomatic_complexity == 1

    # Increase complexity
    func.increase_complexity()
    func.increase_complexity()
    assert func.cyclomatic_complexity == 3


def test_behavioral_predefined():
    """Test predefined method detection."""
    # Regular method
    func1 = PBBehavioral(name="custom_func")
    assert not func1.is_predefined_method()

    # Predefined method
    func2 = PBBehavioral(name="sort")
    assert func2.is_predefined_method()

    # Case insensitive
    func3 = PBBehavioral(name="SORT")
    assert func3.is_predefined_method()


def test_behavioral_string():
    """Test behavioral string representation."""
    func = PBBehavioral(name="test_func")

    # Add parameter
    param = PBParameter(
        name="p1",
        parameter_type=PBBasicType(name="integer"),
    )
    func.add_parameter(param)

    # Add signature
    sig = PBBehaviorSignature(
        name="test_func_sig",
        behavioral=func,
        return_type=PBBasicType(name="integer"),
    )
    func.signature = sig

    # Test string representation
    expected = "public test_func (p1: integer) returns integer"
    assert func.to_string() == expected


def test_behavioral_reachable_entities() -> None:
    """Test behavioral reachable entities."""
    func = PBBehavioral(name="test_func")

    # Create type with reachable entities
    class ReachableType(PBBasicType):
        def get_reachable_entities(self) -> set:
            return {self}

    # Add variable with reachable type
    var = PBVariable(
        name="obj",
        behavioral=func,
        variable_type=ReachableType(name="custom_type"),
    )
    func.add_variable(var)

    # Test reachable entities
    entities = func.get_reachable_entities()
    assert func in entities
    assert var.variable_type in entities


def test_behavior_signature():
    """Test behavior signature functionality."""
    # Create signature
    sig = PBBehaviorSignature(
        name="test_sig",
        return_type=PBBasicType(name="integer"),
    )

    # Add parameters
    param1 = PBParameter(
        name="p1",
        parameter_type=PBBasicType(name="integer"),
    )
    param2 = PBParameter(
        name="p2",
        parameter_type=PBBasicType(name="string"),
    )
    sig.parameters.extend([param1, param2])

    # Test string representation
    expected = "returns integer (p1: integer, p2: string)"
    assert str(sig) == expected


def test_behavior_signature_linking():
    """Test behavior signature linking."""
    # Create behavioral and signature
    func = PBBehavioral(name="test_func")
    sig = PBBehaviorSignature(
        name="test_sig",
        return_type=PBBasicType(name="integer"),
    )

    # Link signature to behavioral
    func.signature = sig
    assert sig.behavioral == func

    # Add parameter through behavioral
    param = PBParameter(
        name="p1",
        parameter_type=PBBasicType(name="integer"),
    )
    func.add_parameter(param)

    # Verify parameter is added to signature
    assert len(sig.parameters) == 1
    assert sig.parameters[0] == param


def test_access_modifiers():
    """Test access modifier functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTAccessModifier.class.st
    """
    # Test basic access modifier assignment
    func = PBBehavioral(name="test_func")
    assert func.access_modifier == AccessModifier.PUBLIC  # Default

    func.access_modifier = AccessModifier.PRIVATE
    assert func.access_modifier == AccessModifier.PRIVATE
    assert func.is_private

    func.access_modifier = AccessModifier.GLOBAL
    assert func.access_modifier == AccessModifier.GLOBAL
    assert func.is_global

    # Test access modifier in string representation
    assert func.to_string().startswith("global")

    func.access_modifier = AccessModifier.PROTECTED
    assert func.to_string().startswith("protected")


def test_behavioral_alias():
    """Test behavioral alias functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTBehaviouralAlias.class.st
    """
    # Create behavioral and alias
    func = PBBehavioral(name="test_func")
    alias = PBBehavioralAlias(
        name="test_alias",
        alias_name="alias_func",
    )

    # Test adding alias
    func.add_alias(alias)
    assert len(func.get_aliases()) == 1
    assert func.get_aliases()[0] == alias
    assert alias.target == func

    # Test getting alias by name
    assert func.get_alias("alias_func") == alias
    assert func.get_alias("nonexistent") is None

    # Test string representation
    assert str(alias) == "alias alias_func"
    assert func.to_string() == "public test_func() [alias alias_func]"

    # Test multiple aliases
    alias2 = PBBehavioralAlias(
        name="test_alias2",
        alias_name="another_alias",
    )
    func.add_alias(alias2)
    assert len(func.get_aliases()) == 2
    assert func.to_string() == "public test_func() [alias alias_func, alias another_alias]"


def test_behavioral_library():
    """Test behavioral library functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTBehaviouralLibrary.class.st
    """
    # Create library
    lib = PBBehavioralLibrary(
        name="test_lib",
        library_path=Path("test.pbl"),
    )
    assert str(lib) == "library test.pbl"

    # Test system library
    sys_lib = PBBehavioralLibrary(
        name="sys_lib",
        library_path=Path("system.pbl"),
        is_system=True,
    )
    assert str(sys_lib) == "system library system.pbl"

    # Test behavioral with library
    func = PBBehavioral(name="test_func")
    func.set_library(lib)
    assert func.get_library() == lib
    assert not func.is_system_library
    assert func.to_string() == "public library test.pbl test_func()"

    # Test behavioral with system library
    sys_func = PBBehavioral(name="sys_func")
    sys_func.set_library(sys_lib)
    assert sys_func.get_library() == sys_lib
    assert sys_func.is_system_library
    assert sys_func.to_string() == "public system library system.pbl sys_func()"


def test_behavioral_options():
    """Test behavioral options functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTBehaviouralOption.class.st
    """
    # Create behavioral
    func = PBBehavioral(name="test_func")

    # Test adding options
    func.add_option(BehavioralOption.FORWARD)
    assert func.has_option(BehavioralOption.FORWARD)
    assert func.is_forward
    assert func.to_string() == "public forward test_func()"

    # Test multiple options
    func.add_option(BehavioralOption.RPCFUNC)
    assert func.has_option(BehavioralOption.RPCFUNC)
    assert func.is_rpcfunc
    assert func.to_string() == "public forward rpcfunc test_func()"

    # Test removing options
    func.remove_option(BehavioralOption.FORWARD)
    assert not func.has_option(BehavioralOption.FORWARD)
    assert not func.is_forward
    assert func.to_string() == "public rpcfunc test_func()"

    # Test all option types
    func = PBBehavioral(name="test_func")

    func.add_option(BehavioralOption.DYNAMIC)
    assert func.is_dynamic

    func.add_option(BehavioralOption.INDIRECT)
    assert func.is_indirect

    func.add_option(BehavioralOption.STATIC)
    assert func.is_static

    assert func.to_string() == "public dynamic indirect static test_func()"
