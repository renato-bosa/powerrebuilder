"""PowerBuilder AST transformer based on Moose PowerBuilder Parser."""

from typing import Any

from lark import Token, Transformer

from model.pb_behavioral import BehavioralOption as PBBehavioralOption
from parse.constants import PB_TYPE_MAP

from .pb_function import (
    PBFunction,
    PBParameter,
    PBSubroutine,
    create_pb_parameter,
)
from .pb_types import (
    ParameterDirection,
    PBType,
    create_pb_type,
    parse_pb_type,
)


class PowerBuilderTransformer(Transformer):
    """Transform PowerBuilder parse tree into AST nodes."""

    def __init__(self) -> None:
        super().__init__()
        self.current_scope = 'public'

    # Type handling
    def BASIC_TYPE(self, token: Token) -> PBType:
        """Transform basic type token into PBType."""
        return create_pb_type(str(token))

    def CUSTOM_TYPE(self, token: Token) -> PBType:
        """Transform custom type token into PBType."""
        return create_pb_type(str(token))

    def array_type(self, items: list[Any]) -> PBType:
        """Transform array type into PBType."""
        base_type = items[0]  # PBType
        bounds = [int(i) for i in items[1:] if isinstance(i, Token)]
        return create_pb_type(base_type.name, array_bounds=bounds)

    # Parameter handling
    def direction(self, items: list[Token]) -> str:
        """Transform parameter direction."""
        return str(items[0]).lower()

    def argument(self, items: list[Any]) -> PBParameter:
        """Transform function argument into PBParameter."""
        direction = 'in'
        pb_type = None
        name = None
        default_value = None

        for item in items:
            if isinstance(item, str) and item in {'ref', 'readonly', 'in', 'out'}:
                direction = item
            elif isinstance(item, PBType):
                pb_type = item
            elif isinstance(item, Token) and not pb_type:
                name = str(item)
            elif isinstance(item, Token):
                default_value = str(item)

        return create_pb_parameter(
            name=name,
            pb_type=pb_type,
            direction=direction,
            default_value=default_value,
        )

    def arguments(self, items: list[Any]) -> list[PBParameter]:
        """Transform argument list into parameter list."""
        return [item for item in items if isinstance(item, PBParameter)]

    # Function handling
    def access_modifier(self, items: list[Token]) -> str:
        """Transform access modifier."""
        access = str(items[0]).lower()
        self.current_scope = access
        return access

    def behavior_option(self, items: list[Any]) -> dict[str, str]:
        """Transform behavior option."""
        if items[0] == 'Alias':
            return {'alias': str(items[1])}
        return {'library': str(items[1])}

    def function_declaration(self, items):
        """Transform function declaration into PBFunction."""
        access = None
        return_type = None
        name = None
        parameters = []
        behavioral_options = []

        for item in items:
            if isinstance(item, Token):
                if item.type == 'ACCESS_MODIFIER':
                    access = str(item).lower()
                elif item.type == 'TYPE_NAME':
                    return_type = parse_pb_type(str(item))
                elif item.type == 'IDENTIFIER':
                    name = str(item)
            elif isinstance(item, list):
                if all(isinstance(p, PBParameter) for p in item):
                    parameters = item
                elif all(isinstance(o, PBBehavioralOption) for o in item):
                    behavioral_options = item

        return PBFunction(
            name=name,
            return_type=return_type or parse_pb_type('any'),
            parameters=parameters,
            access=access or 'public',
            behavioral_options=behavioral_options,
        )

    def parameter(self, items):
        """Transform parameter declaration into PBParameter."""
        direction = ParameterDirection.IN
        name = None
        pb_type = None
        default_value = None

        for item in items:
            if isinstance(item, Token):
                if item.type == 'DIRECTION_MODIFIER':
                    direction = ParameterDirection[str(item).upper()]
                elif item.type == 'IDENTIFIER':
                    name = str(item)
                elif item.type == 'TYPE_NAME':
                    pb_type = parse_pb_type(str(item))
            elif isinstance(item, str):  # Default value
                default_value = item

        return PBParameter(
            name=name,
            pb_type=pb_type or parse_pb_type('any'),
            direction=direction,
            default_value=default_value,
        )

    def behavioral_option(self, items):
        """Transform behavioral option into PBBehavioralOption."""
        option_type = None
        value = None

        for item in items:
            if isinstance(item, Token):
                if item.type == 'ALIAS':
                    option_type = 'alias'
                elif item.type == 'LIBRARY':
                    option_type = 'library'
                elif item.type == 'STRING':
                    value = str(item).strip('"')

        return PBBehavioralOption(
            option_type=option_type,
            value=value,
        )

    def type_declaration(self, items):
        """Transform type declaration into PBType."""
        is_array = False
        array_bounds = None
        name = None
        namespace = None

        for item in items:
            if isinstance(item, Token):
                if item.type == 'TYPE_NAME':
                    if '.' in str(item):
                        namespace, name = str(item).rsplit('.', 1)
                    else:
                        name = str(item)
            elif isinstance(item, list) and all(isinstance(x, int) for x in item):
                is_array = True
                array_bounds = item

        return PBType(
            name=name,
            is_array=is_array,
            array_bounds=array_bounds,
            namespace=namespace,
            is_custom=name.lower() not in PB_TYPE_MAP if name else True,
        )

    def array_bounds(self, items):
        """Transform array bounds into list of integers."""
        return [int(str(item)) for item in items if isinstance(item, Token) and item.type == 'INT']

    # File handling
    def file(self, items: list[Any]) -> list[PBFunction | PBSubroutine]:
        """Transform file content into list of functions and subroutines."""
        return [item for item in items if isinstance(item, PBFunction | PBSubroutine)]
