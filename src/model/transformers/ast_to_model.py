"""Convert AST nodes to model objects."""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from src.model.ast.nodes.base import (
    Block
)
from src.model.ast.nodes.declarations import (
    Type, BasicType, ArrayType, Structure, Field
)
from src.model.entities.application import PBApplication
from src.model.entities.function import (
    PBFunction, PBArgumentNode, PBVariableNode
)
from src.model.entities.event import (
    PBEventDeclarationNode
)
from src.model.entities.library import PBLibrary
from src.base import PBNode

logger = logging.getLogger(__name__)


@dataclass
class Window(PBNode):
    """PowerBuilder Window model."""
    name: str
    title: str = ""
    base_type: str = "window"
    variables: List[PBVariableNode] = field(default_factory=list)
    controls: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[PBFunction] = field(default_factory=list)
    events: List[PBEventDeclarationNode] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    menu_name: Optional[str] = None


@dataclass
class UserObject(PBNode):
    """PowerBuilder UserObject model."""
    name: str
    base_type: str = "userobject"
    parent_type: Optional[str] = None
    variables: List[PBVariableNode] = field(default_factory=list)
    controls: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[PBFunction] = field(default_factory=list)
    events: List[PBEventDeclarationNode] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    is_visual: bool = True
    is_autoinstantiate: bool = False


@dataclass
class DataWindow(PBNode):
    """PowerBuilder DataWindow model."""
    name: str
    sql_statement: Optional[str] = None
    presentation_style: str = "grid"
    columns: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    retrieval_arguments: List[Dict[str, Any]] = field(default_factory=list)
    sort_criteria: Optional[str] = None
    filter_criteria: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Menu(PBNode):
    """PowerBuilder Menu model."""
    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


class ASTToModelConverter:
    """Convert AST nodes to model objects."""

    def __init__(self):
        """Initialize the converter."""
        self.converted_count = 0
        self.failed_count = 0
        self.current_context = None  # Track current object being converted
        self.type_registry = {}  # Cache for custom types

    def convert(self, ast_node: Any) -> Any:
        """Convert an AST node to a model object.

        Args:
            ast_node: The AST node to convert

        Returns:
            The converted model object
        """
        if ast_node is None:
            return None

        # Determine node type and dispatch to appropriate converter
        node_type = type(ast_node).__name__

        # Handle dictionary-based AST nodes (from JSON)
        if isinstance(ast_node, dict):
            node_type = ast_node.get('type', ast_node.get('node_type', 'unknown'))

        converter_method = getattr(self, f'_convert_{node_type.lower()}', None)
        if converter_method:
            try:
                result = converter_method(ast_node)
                self.converted_count += 1
                return result
            except Exception as e:
                logger.error(f"Failed to convert {node_type}: {e}")
                self.failed_count += 1
                raise
        else:
            # Default conversion for unknown types
            logger.warning(f"No converter for node type: {node_type}")
            self.converted_count += 1
            return ast_node

    def convert_all(self, ast_nodes: list[Any]) -> list[Any]:
        """Convert multiple AST nodes to model objects.

        Args:
            ast_nodes: List of AST nodes to convert

        Returns:
            List of converted model objects
        """
        converted = []
        for node in ast_nodes:
            try:
                result = self.convert(node)
                if result is not None:
                    converted.append(result)
            except Exception as e:
                logger.error(f"Failed to convert AST node: {e}")
                self.failed_count += 1

        return converted

    # Window conversion
    def _convert_window(self, node: Any) -> Window:
        """Convert window AST node to Window model."""
        if isinstance(node, dict):
            return self._convert_window_dict(node)

        window = Window(name=getattr(node, 'name', 'unnamed_window'))
        self.current_context = window

        # Extract properties
        if hasattr(node, 'properties'):
            window.properties = self._extract_properties(node.properties)
            window.title = window.properties.get('title', window.name)

        # Extract variables
        if hasattr(node, 'variables'):
            for var in node.variables:
                window.variables.append(self._convert_variable(var))

        # Extract controls
        if hasattr(node, 'controls'):
            for control in node.controls:
                window.controls.append(self._convert_control(control))

        # Extract functions
        if hasattr(node, 'functions'):
            for func in node.functions:
                window.functions.append(self._convert_function(func))

        # Extract events
        if hasattr(node, 'events'):
            for event in node.events:
                window.events.append(self._convert_event(event))

        self.current_context = None
        return window

    def _convert_window_dict(self, node: dict) -> Window:
        """Convert window dictionary (from JSON) to Window model."""
        window = Window(name=node.get('name', 'unnamed_window'))
        self.current_context = window

        window.title = node.get('title', window.name)
        window.base_type = node.get('base_type', 'window')
        window.properties = node.get('properties', {})
        window.menu_name = node.get('menu_name')

        # Convert nested structures
        for var in node.get('variables', []):
            window.variables.append(self._convert_variable_dict(var))

        for control in node.get('controls', []):
            window.controls.append(control)  # Already in dict format

        for func in node.get('functions', []):
            window.functions.append(self._convert_function_dict(func))

        for event in node.get('events', []):
            window.events.append(self._convert_event_dict(event))

        self.current_context = None
        return window

    # UserObject conversion
    def _convert_userobject(self, node: Any) -> UserObject:
        """Convert UserObject AST node to UserObject model."""
        if isinstance(node, dict):
            return self._convert_userobject_dict(node)

        uo = UserObject(name=getattr(node, 'name', 'unnamed_userobject'))
        self.current_context = uo

        # Extract base type and parent
        if hasattr(node, 'base_type'):
            uo.base_type = node.base_type
        if hasattr(node, 'parent_type'):
            uo.parent_type = node.parent_type

        # Extract properties
        if hasattr(node, 'properties'):
            uo.properties = self._extract_properties(node.properties)
            uo.is_visual = uo.properties.get('visual', True)
            uo.is_autoinstantiate = uo.properties.get('autoinstantiate', False)

        # Extract variables, controls, functions, events (similar to window)
        if hasattr(node, 'variables'):
            for var in node.variables:
                uo.variables.append(self._convert_variable(var))

        if hasattr(node, 'controls'):
            for control in node.controls:
                uo.controls.append(self._convert_control(control))

        if hasattr(node, 'functions'):
            for func in node.functions:
                uo.functions.append(self._convert_function(func))

        if hasattr(node, 'events'):
            for event in node.events:
                uo.events.append(self._convert_event(event))

        self.current_context = None
        return uo

    def _convert_userobject_dict(self, node: dict) -> UserObject:
        """Convert UserObject dictionary to UserObject model."""
        uo = UserObject(name=node.get('name', 'unnamed_userobject'))
        self.current_context = uo

        uo.base_type = node.get('base_type', 'userobject')
        uo.parent_type = node.get('parent_type')
        uo.properties = node.get('properties', {})
        uo.is_visual = node.get('is_visual', True)
        uo.is_autoinstantiate = node.get('is_autoinstantiate', False)

        # Convert nested structures
        for var in node.get('variables', []):
            uo.variables.append(self._convert_variable_dict(var))

        for control in node.get('controls', []):
            uo.controls.append(control)

        for func in node.get('functions', []):
            uo.functions.append(self._convert_function_dict(func))

        for event in node.get('events', []):
            uo.events.append(self._convert_event_dict(event))

        self.current_context = None
        return uo

    # DataWindow conversion
    def _convert_datawindow(self, node: Any) -> DataWindow:
        """Convert DataWindow AST node to DataWindow model."""
        if isinstance(node, dict):
            return self._convert_datawindow_dict(node)

        dw = DataWindow(name=getattr(node, 'name', 'unnamed_datawindow'))

        if hasattr(node, 'sql_statement'):
            dw.sql_statement = node.sql_statement

        if hasattr(node, 'presentation_style'):
            dw.presentation_style = node.presentation_style

        if hasattr(node, 'columns'):
            for col in node.columns:
                dw.columns.append(self._convert_datawindow_column(col))

        if hasattr(node, 'tables'):
            dw.tables = list(node.tables)

        if hasattr(node, 'retrieval_arguments'):
            for arg in node.retrieval_arguments:
                dw.retrieval_arguments.append(self._convert_retrieval_argument(arg))

        if hasattr(node, 'properties'):
            dw.properties = self._extract_properties(node.properties)
            dw.sort_criteria = dw.properties.get('sort')
            dw.filter_criteria = dw.properties.get('filter')

        return dw

    def _convert_datawindow_dict(self, node: dict) -> DataWindow:
        """Convert DataWindow dictionary to DataWindow model."""
        dw = DataWindow(name=node.get('name', 'unnamed_datawindow'))

        dw.sql_statement = node.get('sql_statement')
        dw.presentation_style = node.get('presentation_style', 'grid')
        dw.columns = node.get('columns', [])
        dw.tables = node.get('tables', [])
        dw.retrieval_arguments = node.get('retrieval_arguments', [])
        dw.sort_criteria = node.get('sort_criteria')
        dw.filter_criteria = node.get('filter_criteria')
        dw.properties = node.get('properties', {})

        return dw

    # Function conversion
    def _convert_function(self, node: Any) -> PBFunction:
        """Convert function AST node to PBFunction model."""
        if isinstance(node, dict):
            return self._convert_function_dict(node)

        func = PBFunction(
            name=getattr(node, 'name', 'unnamed_function'),
            return_type=self._convert_type(getattr(node, 'return_type', None))
        )

        # Convert parameters
        if hasattr(node, 'parameters'):
            for param in node.parameters:
                func.arguments.arguments.append(self._convert_parameter(param))

        # Convert body
        if hasattr(node, 'body'):
            func.body = self._convert_statements(node.body)

        # Extract modifiers
        if hasattr(node, 'access_modifier'):
            func.access_level = node.access_modifier

        if hasattr(node, 'is_static'):
            func.is_static = node.is_static

        return func

    def _convert_function_dict(self, node: dict) -> PBFunction:
        """Convert function dictionary to PBFunction model."""
        func = PBFunction(
            name=node.get('name', 'unnamed_function'),
            return_type=node.get('return_type', 'void')
        )

        # Convert parameters
        for param in node.get('parameters', []):
            arg = PBArgumentNode(
                name=param.get('name', ''),
                type=param.get('type', 'any'),
                is_reference=param.get('is_reference', False),
                is_readonly=param.get('is_readonly', False),
                default_value=param.get('default_value')
            )
            func.arguments.arguments.append(arg)

        # Store body as string list for now
        func.body = node.get('body', [])
        func.access_level = node.get('access_modifier', 'public')
        func.is_static = node.get('is_static', False)

        return func

    # Event conversion
    def _convert_event(self, node: Any) -> PBEventDeclarationNode:
        """Convert event AST node to PBEventDeclarationNode model."""
        if isinstance(node, dict):
            return self._convert_event_dict(node)

        event = PBEventDeclarationNode(
            event_name=getattr(node, 'name', 'unnamed_event'),
            return_type=self._convert_type(getattr(node, 'return_type', None))
        )

        # Convert event body
        if hasattr(node, 'body'):
            event.statements = self._convert_statements(node.body)

        # Convert custom call if present
        if hasattr(node, 'custom_call'):
            event.custom_call_statement = node.custom_call

        return event

    def _convert_event_dict(self, node: dict) -> PBEventDeclarationNode:
        """Convert event dictionary to PBEventDeclarationNode model."""
        event = PBEventDeclarationNode(
            event_name=node.get('name', 'unnamed_event'),
            return_type=node.get('return_type', 'void')
        )

        event.statements = node.get('body', [])
        event.custom_call_statement = node.get('custom_call')

        return event

    # Application conversion
    def _convert_application(self, node: Any) -> PBApplication:
        """Convert application AST node to PBApplication model."""
        if isinstance(node, dict):
            return self._convert_application_dict(node)

        app = PBApplication(
            name=getattr(node, 'name', 'unnamed_application'),
            description=getattr(node, 'description', '')
        )

        # Extract application properties
        if hasattr(node, 'properties'):
            props = self._extract_properties(node.properties)
            app.app_name = props.get('appname', app.name)
            app.libraries = props.get('applibs', [])

        # Extract global variables
        if hasattr(node, 'global_variables'):
            for var in node.global_variables:
                app.global_variables.append(self._convert_variable(var))

        # Extract global functions
        if hasattr(node, 'global_functions'):
            for func in node.global_functions:
                app.global_functions.append(self._convert_function(func))

        # Extract open event
        if hasattr(node, 'open_event'):
            app.open_event = self._convert_event(node.open_event)

        return app

    def _convert_application_dict(self, node: dict) -> PBApplication:
        """Convert application dictionary to PBApplication model."""
        app = PBApplication(
            name=node.get('name', 'unnamed_application'),
            description=node.get('description', '')
        )

        app.app_name = node.get('app_name', app.name)
        app.libraries = node.get('libraries', [])
        app.global_variables = node.get('global_variables', [])
        app.global_functions = node.get('global_functions', [])
        app.open_event = node.get('open_event')

        return app

    # Helper conversion methods
    def _convert_variable(self, node: Any) -> PBVariableNode:
        """Convert variable AST node to PBVariableNode."""
        if isinstance(node, dict):
            return self._convert_variable_dict(node)

        var = PBVariableNode(
            name=getattr(node, 'name', 'unnamed_var'),
            type=self._convert_type(getattr(node, 'type', None))
        )

        if hasattr(node, 'initial_value'):
            var.initial_value = self._convert_expression(node.initial_value)

        if hasattr(node, 'is_constant'):
            var.is_constant = node.is_constant

        if hasattr(node, 'access_modifier'):
            var.access_level = node.access_modifier

        return var

    def _convert_variable_dict(self, node: dict) -> PBVariableNode:
        """Convert variable dictionary to PBVariableNode."""
        return PBVariableNode(
            name=node.get('name', 'unnamed_var'),
            type=node.get('type', 'any'),
            initial_value=node.get('initial_value'),
            is_constant=node.get('is_constant', False),
            access_level=node.get('access_modifier', 'private')
        )

    def _convert_parameter(self, node: Any) -> PBArgumentNode:
        """Convert parameter to PBArgumentNode."""
        if isinstance(node, dict):
            return PBArgumentNode(
                name=node.get('name', ''),
                type=node.get('type', 'any'),
                is_reference=node.get('is_reference', False),
                is_readonly=node.get('is_readonly', False),
                default_value=node.get('default_value')
            )

        return PBArgumentNode(
            name=getattr(node, 'name', ''),
            type=self._convert_type(getattr(node, 'type', None)),
            is_reference=getattr(node, 'is_reference', False),
            is_readonly=getattr(node, 'is_readonly', False),
            default_value=getattr(node, 'default_value', None)
        )

    def _convert_control(self, node: Any) -> Dict[str, Any]:
        """Convert control AST node to control dictionary."""
        if isinstance(node, dict):
            return node

        control = {
            'type': getattr(node, 'control_type', 'unknown'),
            'name': getattr(node, 'name', 'unnamed_control')
        }

        # Extract control properties
        if hasattr(node, 'properties'):
            control['properties'] = self._extract_properties(node.properties)

        # Extract position and size
        if hasattr(node, 'x'):
            control['x'] = node.x
        if hasattr(node, 'y'):
            control['y'] = node.y
        if hasattr(node, 'width'):
            control['width'] = node.width
        if hasattr(node, 'height'):
            control['height'] = node.height

        return control

    def _convert_datawindow_column(self, node: Any) -> Dict[str, Any]:
        """Convert DataWindow column."""
        if isinstance(node, dict):
            return node

        return {
            'name': getattr(node, 'name', ''),
            'type': getattr(node, 'type', 'string'),
            'db_name': getattr(node, 'db_name', ''),
            'display_format': getattr(node, 'display_format', ''),
            'edit_style': getattr(node, 'edit_style', 'edit'),
            'properties': self._extract_properties(getattr(node, 'properties', {}))
        }

    def _convert_retrieval_argument(self, node: Any) -> Dict[str, Any]:
        """Convert retrieval argument."""
        if isinstance(node, dict):
            return node

        return {
            'name': getattr(node, 'name', ''),
            'type': getattr(node, 'type', 'string'),
            'required': getattr(node, 'required', True)
        }

    def _convert_type(self, type_node: Any) -> str:
        """Convert type node to string representation."""
        if type_node is None:
            return 'any'

        if isinstance(type_node, str):
            return type_node

        if isinstance(type_node, dict):
            return type_node.get('name', 'any')

        if hasattr(type_node, 'name'):
            return type_node.name

        return str(type_node)

    def _convert_expression(self, expr: Any) -> Any:
        """Convert expression node."""
        if expr is None:
            return None

        if isinstance(expr, (str, int, float, bool)):
            return expr

        if isinstance(expr, dict):
            return expr.get('value', expr.get('text', str(expr)))

        # Handle specific expression types
        if hasattr(expr, 'value'):
            return expr.value

        if hasattr(expr, 'text'):
            return expr.text

        return str(expr)

    def _convert_statements(self, stmts: Any) -> List[Any]:
        """Convert statement nodes."""
        if not stmts:
            return []

        if isinstance(stmts, list):
            return [self._convert_statement(stmt) for stmt in stmts]

        if isinstance(stmts, Block):
            return self._convert_statements(stmts.statements)

        # Single statement
        return [self._convert_statement(stmts)]

    def _convert_statement(self, stmt: Any) -> Any:
        """Convert a single statement."""
        if isinstance(stmt, str):
            return stmt

        if isinstance(stmt, dict):
            return stmt

        # Convert statement to simplified representation
        return {
            'type': type(stmt).__name__,
            'content': str(stmt)
        }

    def _extract_properties(self, props: Any) -> Dict[str, Any]:
        """Extract properties from various formats."""
        if isinstance(props, dict):
            return props

        if hasattr(props, 'items'):
            return dict(props.items())

        # Try to extract from list of property nodes
        if isinstance(props, list):
            result = {}
            for prop in props:
                if hasattr(prop, 'name') and hasattr(prop, 'value'):
                    result[prop.name] = prop.value
                elif isinstance(prop, dict):
                    result.update(prop)
            return result

        return {}

    # Menu conversion
    def _convert_menu(self, node: Any) -> Menu:
        """Convert menu AST node to Menu model."""
        if isinstance(node, dict):
            return self._convert_menu_dict(node)

        menu = Menu(name=getattr(node, 'name', 'unnamed_menu'))

        # Extract properties
        if hasattr(node, 'properties'):
            menu.properties = self._extract_properties(node.properties)

        # Extract menu items
        if hasattr(node, 'items'):
            for item in node.items:
                menu.items.append(self._convert_menu_item(item))

        return menu

    def _convert_menu_dict(self, node: dict) -> Menu:
        """Convert menu dictionary to Menu model."""
        menu = Menu(name=node.get('name', 'unnamed_menu'))
        menu.properties = node.get('properties', {})
        menu.items = node.get('items', [])
        return menu

    def _convert_menu_item(self, node: Any) -> Dict[str, Any]:
        """Convert menu item."""
        if isinstance(node, dict):
            return node

        item = {
            'name': getattr(node, 'name', ''),
            'text': getattr(node, 'text', ''),
            'enabled': getattr(node, 'enabled', True),
            'visible': getattr(node, 'visible', True),
            'checked': getattr(node, 'checked', False),
            'shortcut': getattr(node, 'shortcut', None),
            'items': []  # Sub-items
        }

        # Handle sub-items
        if hasattr(node, 'items'):
            for sub_item in node.items:
                item['items'].append(self._convert_menu_item(sub_item))

        # Handle event handlers
        if hasattr(node, 'clicked_event'):
            item['clicked_event'] = self._convert_event(node.clicked_event)

        return item

    # Library conversion
    def _convert_library(self, node: Any) -> PBLibrary:
        """Convert library AST node to PBLibrary model."""
        if isinstance(node, dict):
            return self._convert_library_dict(node)

        lib = PBLibrary(
            name=getattr(node, 'name', 'unnamed_library'),
            file_path=getattr(node, 'file_path', '')
        )

        # Extract library contents
        if hasattr(node, 'objects'):
            for obj in node.objects:
                obj_type = type(obj).__name__.lower()
                if obj_type == 'window':
                    lib.windows.append(self._convert_window(obj))
                elif obj_type == 'userobject':
                    lib.user_objects.append(self._convert_userobject(obj))
                elif obj_type == 'datawindow':
                    lib.datawindows.append(self._convert_datawindow(obj))
                elif obj_type == 'menu':
                    lib.menus.append(self._convert_menu(obj))
                elif obj_type == 'function':
                    lib.global_functions.append(self._convert_function(obj))
                elif obj_type == 'structure':
                    lib.structures.append(self._convert_structure(obj))

        return lib

    def _convert_library_dict(self, node: dict) -> PBLibrary:
        """Convert library dictionary to PBLibrary model."""
        lib = PBLibrary(
            name=node.get('name', 'unnamed_library'),
            file_path=node.get('file_path', '')
        )

        # Convert each object type
        for window in node.get('windows', []):
            lib.windows.append(self._convert_window_dict(window))

        for uo in node.get('user_objects', []):
            lib.user_objects.append(self._convert_userobject_dict(uo))

        for dw in node.get('datawindows', []):
            lib.datawindows.append(self._convert_datawindow_dict(dw))

        for menu in node.get('menus', []):
            lib.menus.append(self._convert_menu_dict(menu))

        for func in node.get('global_functions', []):
            lib.global_functions.append(self._convert_function_dict(func))

        for struct in node.get('structures', []):
            lib.structures.append(self._convert_structure_dict(struct))

        return lib

    # Structure conversion
    def _convert_structure(self, node: Any) -> Structure:
        """Convert structure AST node to Structure model."""
        if isinstance(node, dict):
            return self._convert_structure_dict(node)

        struct = Structure(name=getattr(node, 'name', 'unnamed_structure'))

        # Extract fields
        if hasattr(node, 'fields'):
            for field in node.fields:
                struct.add_field(self._convert_field(field))

        # Extract properties
        if hasattr(node, 'is_global'):
            struct.is_global = node.is_global

        return struct

    def _convert_structure_dict(self, node: dict) -> Structure:
        """Convert structure dictionary to Structure model."""
        struct = Structure(name=node.get('name', 'unnamed_structure'))

        # Convert fields
        for field_data in node.get('fields', []):
            field = Field(
                name=field_data.get('name', ''),
                field_type=BasicType(name=field_data.get('type', 'any')),
                initial_value=field_data.get('initial_value'),
                is_nullable=field_data.get('is_nullable', True)
            )
            struct.add_field(field)

        struct.is_global = node.get('is_global', False)
        return struct

    def _convert_field(self, node: Any) -> Field:
        """Convert field node to Field model."""
        if isinstance(node, dict):
            return Field(
                name=node.get('name', ''),
                field_type=BasicType(name=node.get('type', 'any')),
                initial_value=node.get('initial_value'),
                is_nullable=node.get('is_nullable', True)
            )

        return Field(
            name=getattr(node, 'name', ''),
            field_type=self._convert_type_to_type_object(getattr(node, 'type', None)),
            initial_value=getattr(node, 'initial_value', None),
            is_nullable=getattr(node, 'is_nullable', True)
        )

    def _convert_type_to_type_object(self, type_node: Any) -> Type:
        """Convert type node to Type object."""
        if isinstance(type_node, Type):
            return type_node

        if isinstance(type_node, str):
            return BasicType(name=type_node)

        if isinstance(type_node, dict):
            type_name = type_node.get('name', 'any')
            if type_node.get('is_array'):
                return ArrayType(
                    name=type_name + '[]',
                    element_type=BasicType(name=type_name)
                )
            return BasicType(name=type_name)

        if hasattr(type_node, 'name'):
            return BasicType(name=type_node.name)

        return BasicType(name='any')