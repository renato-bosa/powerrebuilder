"""PowerBuilder AST transformer.

This module provides the transformer class that converts parse trees into AST nodes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from lark import Token, Transformer, Tree, v_args

# Import new SQL parameter AST nodes
from model.ast.nodes import ColonParameter, QuestionMarkParameter
from model.datawindow.datawindow import DataWindow
from model.datawindow.datawindow_stubs import (
    ColumnDefinition,
    ComputeDefinition,
    DisplayElement,
    SummaryItem,
    TableDefinition,
)
from model.base.exception import (
    CatchBlock,
    ExceptionType,
    FinallyBlock,
    ThrowStatement,
    TryCatchStatement,
)
from model.constructs.global_vars import GlobalVariable, GlobalVariables
from model.library.library import (
    Export,
    Import,
    Library,
    LibraryObject,
)
from model.constructs.pcode import FunctionBlock
from model.transaction.transaction_stubs import (
    TransactionBlock,
    TransactionObject,
    TransactionStatement,
)
from model.ui.ui_elements import Control, Menu, MenuItem, UserObject, Window
from model.utils.base import PBNode

from .position_tracker import PositionMixin, SourceContext

TokenType = Union[str, int, bool]
ValueType = Union[str, int, bool, list[str], dict[str, str], None]
ExpressionType = Union[str, int, bool, list[str], dict[str, str], None]
ArgumentType = Union[str, int, bool, list[str], dict[str, str], None]


@v_args(inline=True)  # pass tokens as bare args
class PBTransformer(Transformer, PositionMixin):
    """Transforms PowerBuilder parse trees into AST nodes."""

    def __init__(
        self, source_text: str | None = None, filename: str | None = None
    ) -> None:
        """Initialize transformer with optional source context.

        Args:
            source_text: Source code text for position tracking
            filename: Source file name
        """
        super().__init__()

        # Set up source context if provided
        if source_text is not None:
            context = SourceContext.from_content(
                content=source_text,
                filename=filename or "<unknown>",
            )
            self.set_source_context(context)

    # Token transformations
    # These methods match token names from the grammar, so they are allowed to be
    # uppercase
    def IDENTIFIER(self, tok: Token) -> str:  # noqa: N802
        """Transform identifier token."""
        return str(tok.value)

    def STRING(self, tok: Token) -> str:  # noqa: N802
        """Transform string token."""
        return str(tok.value.strip('"'))

    def INT(self, tok: Token) -> int:  # noqa: N802
        """Transform integer token."""
        return int(tok.value)

    def HEX_INT(self, tok: Token) -> int:  # noqa: N802
        """Transform hexadecimal integer token."""
        return int(tok.value, 16)

    def DATE_LIT(self, tok: Token) -> str:  # noqa: N802
        """Transform date literal token."""
        return str(tok.value)

    def TIME_LIT(self, tok: Token) -> str:  # noqa: N802
        """Transform time literal token."""
        return str(tok.value)

    def CONTROL_TYPE(self, tok: Token) -> str:  # noqa: N802
        """Transform control type token."""
        return str(tok.value)

    def EVENT_TYPE(self, tok: Token) -> str:  # noqa: N802
        """Transform event type token."""
        return str(tok.value)

    def TYPE(self, tok: Token) -> str:  # noqa: N802
        """Transform type token."""
        return str(tok.value)

    def FROM(self, tok: Token) -> str:  # noqa: N802
        """Transform from token."""
        return str(tok.value)

    def WINDOW(self, tok: Token) -> str:  # noqa: N802
        """Transform window token."""
        return str(tok.value)

    def MENU(self, tok: Token) -> str:  # noqa: N802
        """Transform menu token."""
        return str(tok.value)

    def MENUITEM(self, tok: Token) -> str:  # noqa: N802
        """Transform menuitem token."""
        return str(tok.value)

    def SEPARATOR(self, tok: Token) -> str:  # noqa: N802
        """Transform separator token."""
        return str(tok.value)

    def TYPE_NAME(self, tok: Token) -> str:  # noqa: N802
        """Transform type name token."""
        return str(tok.value)

    def BOOLEAN(self, tok: Token) -> bool:  # noqa: N802
        """Transform boolean token."""
        return str(tok.value).lower() == "true"

    # SQL Parameter Tokens transformation
    def QUESTION_MARK_PARAM(self, tok: Token) -> QuestionMarkParameter:  # noqa: N802
        """Transforms a ? SQL parameter token into a QuestionMarkParameter AST node."""
        # Create node with position information
        return self.create_node(QuestionMarkParameter, tok)

    def COLON_PARAM(self, tok: Token) -> ColonParameter:  # noqa: N802
        """Transforms a :variable SQL parameter token into a ColonParameter AST node."""
        param_name = str(tok.value)[1:]  # Remove the leading colon
        return self.create_node(ColonParameter, tok, name=param_name)

    # Operators
    def GT(self, tok: Token) -> str:  # noqa: N802
        """Transform greater than operator."""
        return ">"

    def LT(self, tok: Token) -> str:  # noqa: N802
        """Transform less than operator."""
        return "<"

    def GE(self, tok: Token) -> str:  # noqa: N802
        """Transform greater than or equal operator."""
        return ">="

    def LE(self, tok: Token) -> str:  # noqa: N802
        """Transform less than or equal operator."""
        return "<="

    def EQ(self, tok: Token) -> str:  # noqa: N802
        """Transform equals operator."""
        return "="

    def NE(self, tok: Token) -> str:  # noqa: N802
        """Transform not equals operator."""
        return "<>"

    def PLUS(self, tok: Token) -> str:  # noqa: N802
        """Transform plus operator."""
        return "+"

    def MINUS(self, tok: Token) -> str:  # noqa: N802
        """Transform minus operator."""
        return "-"

    def MULT(self, tok: Token) -> str:  # noqa: N802
        """Transform multiply operator."""
        return "*"

    def DIV(self, tok: Token) -> str:  # noqa: N802
        """Transform divide operator."""
        return "/"

    def MOD(self, tok: Token) -> str:  # noqa: N802
        """Transform modulo operator."""
        return "%"

    def POWER(self, tok: Token) -> str:  # noqa: N802
        """Transform power operator."""
        return "^"

    # Keywords
    def GLOBAL(self, tok: Token) -> str:  # noqa: N802
        """Transform global keyword."""
        return str(tok.value)

    def VARIABLES(self, tok: Token) -> str:  # noqa: N802
        """Transform variables keyword."""
        return str(tok.value)

    def RETURN(self, tok: Token) -> str:  # noqa: N802
        """Transform return keyword."""
        return str(tok.value)

    def IF(self, tok: Token) -> str:  # noqa: N802
        """Transform if keyword."""
        return str(tok.value)

    def THEN(self, tok: Token) -> str:  # noqa: N802
        """Transform then keyword."""
        return str(tok.value)

    def ELSE(self, tok: Token) -> str:  # noqa: N802
        """Transform else keyword."""
        return str(tok.value)

    def END(self, tok: Token) -> str:  # noqa: N802
        """Transform end keyword."""
        return str(tok.value)

    def END_IF(self, tok: Token) -> str:  # noqa: N802
        """Transform end if keyword."""
        return str(tok.value)

    def TRY(self, tok: Token) -> str:  # noqa: N802
        """Transform try keyword."""
        return str(tok.value)

    def CATCH(self, tok: Token) -> str:  # noqa: N802
        """Transform catch keyword."""
        return str(tok.value)

    def FINALLY(self, tok: Token) -> str:  # noqa: N802
        """Transform finally keyword."""
        return str(tok.value)

    def THROW(self, tok: Token) -> str:  # noqa: N802
        """Transform throw keyword."""
        return str(tok.value)

    def USING(self, tok: Token) -> str:  # noqa: N802
        """Transform using keyword."""
        return str(tok.value)

    def TRANSACTION(self, tok: Token) -> str:  # noqa: N802
        """Transform transaction keyword."""
        return str(tok.value)

    def COMMIT(self, tok: Token) -> str:  # noqa: N802
        """Transform commit keyword."""
        return str(tok.value)

    def ROLLBACK(self, tok: Token) -> str:  # noqa: N802
        """Transform rollback keyword."""
        return str(tok.value)

    def CONNECT(self, tok: Token) -> str:  # noqa: N802
        """Transform connect keyword."""
        return str(tok.value)

    def DISCONNECT(self, tok: Token) -> str:  # noqa: N802
        """Transform disconnect keyword."""
        return str(tok.value)

    def LIBRARY(self, tok: Token) -> str:  # noqa: N802
        """Transform library keyword."""
        return str(tok.value)

    def IMPORT(self, tok: Token) -> str:  # noqa: N802
        """Transform import keyword."""
        return str(tok.value)

    def EXPORT(self, tok: Token) -> str:  # noqa: N802
        """Transform export keyword."""
        return str(tok.value)

    def SYSTEM(self, tok: Token) -> str:  # noqa: N802
        """Transform system keyword."""
        return str(tok.value)

    def DYNAMIC(self, tok: Token) -> str:  # noqa: N802
        """Transform dynamic keyword."""
        return str(tok.value)

    def INDIRECT(self, tok: Token) -> str:  # noqa: N802
        """Transform indirect keyword."""
        return str(tok.value)

    def start(self, *items: PBNode) -> list[PBNode]:
        """Transform start rule."""
        return list(items)

    # System function handling
    def system_function(
        self,
        func_type: str,
        name: str,
        params: list[tuple[str, str]] | None = None,
        return_type: str | None = None,
        throws: list[str] | None = None,
        forward: bool | None = None,
    ) -> dict[str, Any]:
        """Transform system function declaration."""
        return {
            "type": "system_function",
            "name": str(name),
            "parameters": params or [],
            "return_type": return_type,
            "throws": throws,
            "is_forward": bool(forward),
        }

    def system_service(
        self,
        service_type: str,
        name: str,
        params: list[tuple[str, str]] | None = None,
        throws: list[str] | None = None,
        forward: bool | None = None,
    ) -> dict[str, Any]:
        """Transform system service declaration."""
        return {
            "type": "system_service",
            "name": str(name),
            "parameters": params or [],
            "throws": throws,
            "is_forward": bool(forward),
        }

    # Library handling
    def library_def(
        self,
        lib_kw: str,
        name: str,
        system: str | None = None,
        lbrace: str | None = None,
        body: Tree | None = None,
        rbrace: str | None = None,
    ) -> Library:
        """Transform library definition."""
        body_parts = body.children if isinstance(body, Tree) else [body]
        imports = [p for p in body_parts if isinstance(p, Import)]
        exports = [p for p in body_parts if isinstance(p, Export)]
        objects = [p for p in body_parts if isinstance(p, LibraryObject)]

        return Library(
            name=str(name),
            path=Path(f"{name}.pbl"),
            is_system=bool(system),
            imports=imports,
            exports=exports,
            objects={obj.name: obj for obj in objects},
        )

    def import_stmt(
        self,
        import_kw: str,
        from_lib: str,
        dot: str,
        object_name: str,
        semicolon: str | None = None,
    ) -> Import:
        """Transform import statement."""
        return Import(
            from_library=str(from_lib),
            object_name=str(object_name),
        )

    def export_stmt(
        self,
        export_kw: str,
        object_name: str,
        to: str | None = None,
        to_lib: str | None = None,
        semicolon: str | None = None,
    ) -> Export:
        """Transform export statement."""
        return Export(
            object_name=str(object_name),
            to_library=str(to_lib) if to_lib else None,
        )

    # Enhanced DataWindow support
    def datawindow(
        self,
        type_kw: str,
        name: str,
        from_kw: str,
        dw_kw: str,
        lbrace: str,
        body: Tree,
        rbrace: str,
    ) -> DataWindow:
        """Transform DataWindow definition."""
        body_parts = body.children if isinstance(body, Tree) else [body]

        properties = []
        table = None
        columns = []
        computes = []
        displays = []
        summaries = []

        for part in body_parts:
            if isinstance(part, tuple):  # Property
                properties.append(part)
            elif isinstance(part, TableDefinition):
                table = part
            elif isinstance(part, ColumnDefinition):
                columns.append(part)
            elif isinstance(part, ComputeDefinition):
                computes.append(part)
            elif isinstance(part, DisplayElement):
                displays.append(part)
            elif isinstance(part, SummaryItem):
                summaries.append(part)

        return DataWindow(
            name=str(name),
            properties=properties,
            table=table,
            columns=columns,
            computes=computes,
            display_elements=displays,
            summary_items=summaries,
        )

    # Transaction handling
    def transaction_block(
        self,
        using_kw: str,
        trans_obj: TransactionObject,
        code_block: list[PBNode],
    ) -> TransactionBlock:
        """Transform transaction block."""
        return TransactionBlock(
            transaction=trans_obj,
            statements=code_block,
        )

    def transaction_stmt(
        self,
        stmt_type: str,
        trans_obj: TransactionObject | None = None,
        using_kw: str | None = None,
        savepoint: str | None = None,
        semicolon: str | None = None,
    ) -> TransactionStatement:
        """Transform transaction statement."""
        return TransactionStatement(
            type=str(stmt_type).upper(),
            transaction=trans_obj,
        )

    # Exception handling
    def try_catch(
        self,
        try_kw: str,
        try_block: list[PBNode],
        *rest: CatchBlock | FinallyBlock,
    ) -> TryCatchStatement:
        """Transform try-catch statement."""
        catch_blocks = []
        finally_block = None

        for item in rest:
            if isinstance(item, CatchBlock):
                catch_blocks.append(item)
            elif isinstance(item, FinallyBlock):
                finally_block = item

        return TryCatchStatement(
            try_statements=try_block,
            catch_blocks=catch_blocks,
            finally_block=finally_block,
        )

    def catch_block(
        self,
        catch_kw: str,
        lpar: str,
        exc_type: ExceptionType,
        var_name: str,
        rpar: str,
        block: list[PBNode],
    ) -> CatchBlock:
        """Transform catch block."""
        return CatchBlock(
            exception_type=exc_type,
            variable_name=str(var_name),
            statements=block,
        )

    def finally_block(
        self,
        finally_kw: str,
        block: list[PBNode],
    ) -> FinallyBlock:
        """Transform finally block."""
        return FinallyBlock(statements=block)

    def throw_stmt(
        self,
        throw_kw: str,
        expr: PBNode,
        semicolon: str | None = None,
    ) -> ThrowStatement:
        """Transform throw statement."""
        return ThrowStatement(expression=expr)

    # Dynamic calls
    def dynamic_call(
        self,
        dynamic_kw: str,
        obj_access: str,
        lpar: str,
        args: list[Any] | None = None,
        rpar: str | None = None,
    ) -> str:
        """Transform dynamic method call."""
        args_str = ", ".join(str(a) for a in (args or []))
        return f"dynamic {obj_access}({args_str})"

    def indirect_call(
        self,
        indirect_kw: str,
        obj_access: str,
        lpar: str,
        args: list[Any] | None = None,
        rpar: str | None = None,
    ) -> str:
        """Transform indirect method call."""
        args_str = ", ".join(str(a) for a in (args or []))
        return f"indirect {obj_access}({args_str})"

    # Enhanced expressions
    def binary_operation(
        self,
        left: PBNode,
        op: str,
        right: PBNode,
    ) -> str:
        """Transform binary operation."""
        return f"{left} {op} {right}"

    def unary_operation(
        self,
        op: str,
        expr: PBNode,
    ) -> str:
        """Transform unary operation."""
        return f"{op}{expr}"

    def boolean_expression(
        self,
        left: PBNode,
        op: str,
        right: PBNode,
    ) -> str:
        """Transform boolean expression."""
        return f"{left} {op} {right}"

    # Case statement
    def case_statement(
        self,
        choose_kw: str,
        case_kw: str,
        expr: PBNode,
        *items: tuple[Any, list[str]],
    ) -> dict[str, Any]:
        """Transform case statement."""
        cases = []
        for item in items:
            if isinstance(item, tuple):
                cases.append(item)
        return {
            "type": "case",
            "expression": expr,
            "cases": cases,
        }

    def case_item(
        self,
        case_kw: str,
        expr: PBNode,
        colon: str,
        *stmts: str,
    ) -> tuple[Any, list[str]]:
        """Transform case item."""
        return (expr, list(stmts))

    def window(
        self,
        type_kw: str,
        name: str,
        from_kw: str,
        window_kw: str,
        lbrace: str,
        body: Tree | PBNode,
        rbrace: str,
    ) -> Window:
        """Transform window definition into Window node.

        Args:
            type_kw: The 'type' keyword
            name: The name of the window
            from_kw: The 'from' keyword
            window_kw: The 'window' keyword
            lbrace: The opening brace
            body: The window body (Tree or Node)
            rbrace: The closing brace

        Returns:
            Window: The transformed Window node
        """
        # Extract body parts from the window_body Tree
        body_parts = body.children if isinstance(body, Tree) else [body]
        controls = [p for p in body_parts if isinstance(p, Control)]
        events = [p for p in body_parts if isinstance(p, FunctionBlock)]
        properties = []
        for p in body_parts:
            if isinstance(p, tuple) and len(p) == 2:
                properties.append(p)

        return Window(
            name=str(name),
            properties=properties,
            controls=controls,
            events=events,
        )

    def menu(
        self,
        type_kw: str,
        name: str,
        from_kw: str,
        menu_kw: str,
        lbrace: str,
        body: Tree | PBNode,
        rbrace: str,
    ) -> Menu:
        """Transform menu definition into Menu node.

        Args:
            type_kw: The 'type' keyword
            name: The name of the menu
            from_kw: The 'from' keyword
            menu_kw: The 'menu' keyword
            lbrace: The opening brace
            body: The menu body (Tree or Node)
            rbrace: The closing brace

        Returns:
            Menu: The transformed Menu node
        """
        return Menu(
            name=str(name),
            items=body if isinstance(body, list) else [body],
        )

    def menu_body(self, item_list: list[MenuItem]) -> list[MenuItem]:
        """Transform menu body into list of menu items.

        Args:
            item_list: List of menu items

        Returns:
            List[MenuItem]: The transformed list of menu items
        """
        return item_list

    def menu_item_list(self, *items: MenuItem) -> list[MenuItem]:
        """Transform menu item list into list of menu items.

        Args:
            *items: Variable length argument list of menu items

        Returns:
            List[MenuItem]: The transformed list of menu items
        """
        return list(items)

    def menu_item(self, item: MenuItem) -> MenuItem:
        """Transform menu item into MenuItem node.

        Args:
            item: The menu item to transform

        Returns:
            MenuItem: The transformed MenuItem node
        """
        return item

    def menu_entry(
        self,
        name: str,
        colon: str,
        menuitem: str,
        lbrace: str,
        body: Tree | PBNode,
        rbrace: str,
        semicolon: str | None = None,
    ) -> MenuItem:
        """Transform menu entry into MenuItem node.

        Args:
            name: The name of the menu item
            colon: The colon token
            menuitem: The 'menuitem' keyword
            lbrace: The opening brace
            body: The menu item body (Tree or Node)
            rbrace: The closing brace
            semicolon: Optional semicolon token

        Returns:
            MenuItem: The transformed MenuItem node
        """
        body_parts = body.children if isinstance(body, Tree) else [body]
        events = [p for p in body_parts if isinstance(p, FunctionBlock)]
        properties = []
        for p in body_parts:
            if isinstance(p, tuple) and len(p) == 2:
                properties.append(p)

        return MenuItem(
            name=str(name),
            type="item",
            properties=properties,
            click_handler=events[0] if events else None,
            items=[],
        )

    def menu_separator(
        self,
        separator: str,
        semicolon: str | None = None,
    ) -> MenuItem:
        """Transform menu separator into MenuItem node."""
        return MenuItem(
            name="",
            type="separator",
            properties=[],
            click_handler=None,
            items=[],
        )

    def menu_item_body(self, *parts: PBNode) -> Tree:
        """Transform menu item body into Tree node."""
        return Tree("menu_item_body", list(parts))

    def global_vars(
        self,
        global_kw: str,
        vars_kw: str,
        lbrace: str,
        *declarations: GlobalVariable,
    ) -> GlobalVariables:
        """Transform global variables declaration into GlobalVariables node."""
        variables = {}
        for decl in declarations:
            variables[decl.name] = decl
        return GlobalVariables(variables=variables)

    def var_declaration(
        self,
        name: str,
        colon: str,
        type_name: str,
        *rest: ValueType,
    ) -> GlobalVariable:
        """Transform variable declaration into GlobalVariable node."""
        initial_value = rest[1] if len(rest) > 1 else None
        return GlobalVariable(
            name=str(name),
            type=str(type_name),
            initial_value=initial_value,
        )

    def user_object(
        self,
        type_kw: str,
        name: str,
        from_kw: str,
        userobject_kw: str,
        lbrace: str,
        body: Tree | PBNode,
        rbrace: str,
    ) -> UserObject:
        """Transform user object definition into AST node."""
        body_parts = body.children if isinstance(body, Tree) else [body]
        controls = [p for p in body_parts if isinstance(p, Control)]
        events = [p for p in body_parts if isinstance(p, FunctionBlock)]
        properties = dict(p for p in body_parts if isinstance(p, tuple))

        inherits = properties.get("inherits")
        return UserObject(
            name=str(name),
            inherits=inherits,
            controls=controls,
            events=events,
            properties=properties,
        )

    def user_object_body(self, *parts: PBNode) -> Tree:
        """Transform user object body into Tree node."""
        return Tree("user_object_body", list(parts))

    def window_body(self, *parts: PBNode) -> Tree:
        """Transform window body into Tree node."""
        return Tree("window_body", list(parts))

    def control(self, *args: str | list[tuple[str, str]]) -> Control:
        """Transform control definition into Control node.

        Args:
            *args: Variable length argument list containing:
                - name: The name of the control
                - type: The type of the control
                - properties: List of property tuples
        """
        # Extract name, type and properties from args
        name = args[0]
        control_type = args[1]
        properties = args[2] if len(args) > 2 else []
        return Control(
            name=str(name),
            type=str(control_type),
            properties=properties,
        )

    def properties(
        self,
        *args: str | list[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        """Transform properties list into list of property tuples."""
        return args[1]

    def property_list(self, *props: tuple[str, str]) -> list[tuple[str, str]]:
        """Transform property list into list of property tuples."""
        return list(props)

    def property(
        self,
        name: str,
        equals: str,
        value: ValueType,
        semicolon: str | None = None,
    ) -> tuple[str, str]:
        """Transform property into name-value tuple."""
        return (str(name), str(value))

    def value(self, val: ValueType) -> ValueType:
        """Transform value into appropriate type."""
        return val

    def string_value(self, val: str) -> str:
        """Transform string value."""
        return str(val)

    def int_value(self, val: str | int) -> int:
        """Transform integer value."""
        return int(val)

    def identifier_value(self, val: str) -> str:
        """Transform identifier value."""
        return str(val)

    def boolean_value(self, val: str | bool) -> str:
        """Transform boolean value."""
        return str(val)

    def atom(self, val: ValueType) -> ValueType:
        """Transform atomic value."""
        return val

    def method(
        self,
        event_type: str,
        name: str,
        params: list[tuple[str, str]] | None = None,
        code: list[str] | None = None,
    ) -> FunctionBlock:
        """Transform method definition into FunctionBlock node."""
        return FunctionBlock(
            name=f"{event_type}_{name}",
            parameters=params or [],
            code=code or [],
        )

    def parameters(self, *params: tuple[str, str]) -> list[tuple[str, str]]:
        """Transform parameters list into list of parameter tuples."""
        return list(params)

    def parameter(self, name: str, type_name: str) -> tuple[str, str]:
        """Transform parameter into name-type tuple."""
        return (str(name), str(type_name))

    def code_block(self, *statements: str) -> list[str]:
        """Transform code block into list of statements."""
        return [str(s) for s in statements]

    def statement(self, stmt: str) -> str:
        """Transform statement into string."""
        return str(stmt)

    def simple_statement(self, stmt: str, semicolon: str | None = None) -> str:
        """Transform simple statement into string."""
        return str(stmt)

    def compound_statement(self, stmt: str) -> str:
        """Transform compound statement into string."""
        return str(stmt)

    def expression_statement(self, expr: str) -> str:
        """Transform expression statement into string."""
        return str(expr)

    def assignment_statement(
        self,
        target: str,
        equals: str,
        value: str,
    ) -> str:
        """Transform assignment statement into string."""
        return f"{target} = {value}"

    def return_statement(
        self,
        return_kw: str,
        expr: str | None = None,
    ) -> str:
        """Transform return statement into string."""
        if expr is None:
            return "return"
        return f"return {expr}"

    def expression(self, value: ExpressionType) -> ExpressionType:
        """Transform expression into appropriate type."""
        return value

    def func_call(self, name: str, *args: str) -> str:
        """Transform function call into string."""
        args_str = ", ".join(str(a) for a in args)
        return f"{name}({args_str})"

    def meth_call(self, obj_access: str, *args: str) -> str:
        """Transform method call into string."""
        args_str = ", ".join(str(a) for a in args)
        return f"{obj_access}({args_str})"

    def object_access(self, *args: str) -> str:
        """Transform object access into string.

        Args:
            *args: Variable length argument list containing:
                - Object name
                - Dot token
                - Method name
        """
        # Extract object and method, skip the dot token
        obj = args[0]
        method = args[2]
        return f"{obj}.{method}"

    def if_statement(
        self,
        if_kw: str,
        condition: str,
        then_kw: str,
        *body_parts: str | list[str],
    ) -> str:
        """Transform if statement into string.

        Args:
            if_kw: The 'if' keyword
            condition: The condition expression
            then_kw: The 'then' keyword
            *body_parts: Variable length argument list containing:
                - Then block statements
                - Optional else keyword
                - Optional else block statements
        """
        # Extract else part if present
        else_idx = -1
        for i, part in enumerate(body_parts):
            if isinstance(part, str) and part.lower() == "else":
                else_idx = i
                break

        if else_idx >= 0:
            then_block = "\n".join(str(s) for s in body_parts[:else_idx])
            else_block = "\n".join(str(s) for s in body_parts[else_idx + 1 :])
            return f"if {condition} then\n{then_block}\nelse\n{else_block}\nend if"
        then_block = "\n".join(str(s) for s in body_parts)
        return f"if {condition} then\n{then_block}\nend if"

    def condition(self, comp: str) -> str:
        """Transform condition into string."""
        return str(comp)

    def comparison(
        self,
        left: str,
        op: str,
        right: str,
    ) -> str:
        """Transform comparison into string."""
        return f"{left} {op} {right}"

    def argument_list(self, *args: ArgumentType) -> list[ArgumentType]:
        """Transform argument list into list."""
        return list(args)

    def argument(self, value: ArgumentType) -> ArgumentType:
        """Transform argument into appropriate type."""
        return value
