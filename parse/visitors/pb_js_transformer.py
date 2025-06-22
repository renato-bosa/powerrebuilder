
from lark import Token, Transformer, Tree, v_args


@v_args(inline=True)
class PowerBuilderJSTransformer(Transformer):
    """Transforms PowerBuilder AST into JavaScript/TypeScript code."""

    def __init__(self) -> None:


        super().__init__()
        self.record_types: dict[str, list[tuple[str, str]]] = {}
        self.type_map = {
            "INTEGER": "number", "STRING": "string", "BOOLEAN": "boolean", "DOUBLE": "number", "DATE": "Date", "DATETIME": "Date", "DECIMAL": "number", }

    def start(self, *statements) -> str:




        """Convert a sequence of statements into a JS/TS function body."""
        return "\n".join(str(stmt) for stmt in statements if stmt)

    def if_statement(self, if_token, condition, then_token, *statements) -> str:




        """Transform if statement to JS if."""
        then_statements = []
        else_statements = []

        # Split statements into then and else blocks
        found_else = False
        for stmt in statements:
            if isinstance(stmt, Token | str) and str(stmt).lower() == "else":
                found_else = True
                continue
            if found_else:
                # Don't add end_if to else block
                if isinstance(stmt, Token | str) and str(stmt).lower() == "end if":
                    continue
                else_statements.append(stmt)
            else:
                then_statements.append(stmt)

        # Remove the end_if token if it's the last statement
        if then_statements and str(then_statements[-1]).lower() == "end if":
            then_statements.pop()

        # Convert Tree objects to strings
        then_block = "\n  ".join(str(stmt) for stmt in then_statements if stmt)
        if else_statements:
            else_block = "\n  ".join(str(stmt) for stmt in else_statements if stmt)
            return (
                f"if ({condition}) {{\n  {then_block}\n}} else {{\n  {else_block}\n}}"
            )
        return f"if ({condition}) {{\n  {then_block}\n}}"

    def while_statement(self, do_token, while_token, condition, *statements) -> str:




        """Transform while statement to JS while."""
        # Remove the 'loop' token from statements
        statements = [stmt for stmt in statements if str(stmt).lower() != "loop"]
        body = "\n  ".join(str(stmt) for stmt in statements if stmt)
        return f"while ({condition}) {{\n  {body}\n}}"

    def for_statement(
        self, for_token, var, equal_token, start, to_token, end, *statements, ) -> str:




        """Transform for statement to JS for."""
        # Remove the 'next' token from statements
        statements = [stmt for stmt in statements if str(stmt).lower() != "next"]
        body = "\n  ".join(str(stmt) for stmt in statements if stmt)
        return f"for (let {var} = {start} {var} <= {end}; {var}++) {{\n  {body}\n}}"

    def repeat_statement(self, repeat_token, *statements) -> str:




        """Transform repeat-until statement to JS do-while."""
        # Last statement should be the until condition
        *body_statements, until_token, condition = statements
        body = "\n  ".join(str(stmt) for stmt in body_statements if stmt)
        return f"do {{\n  {body}\n}} while (!({condition}));"

    def case_statement(self, case_token, expr, of_token, *statements) -> str:




        """Transform case statement to JS switch."""
        for _i, stmt in enumerate(statements):
            if isinstance(stmt, Tree):
                pass

        # Find case blocks and otherwise block
        case_blocks = []
        otherwise_block = None

        in_otherwise = False

        for stmt in statements:
            if isinstance(stmt, tuple):
                # Handle case block tuple
                values_info, block = stmt
                if values_info[0] == "case_values":
                    values = [v for v in values_info[1] if v != ","]
                    case_blocks.append((values, block))
            elif isinstance(stmt, Tree):
                if stmt.data == "statement" and in_otherwise:
                    otherwise_block = [stmt.children[0]]
            elif str(stmt).lower() == "otherwise":
                in_otherwise = True
            elif str(stmt).lower() == "end case":
                continue
            elif in_otherwise:
                if otherwise_block is None:
                    otherwise_block = []
                otherwise_block.append(stmt)

        for values, block in case_blocks:
            pass

        # Build switch statement
        result = [f"switch ({expr}) {{"]
        for values, block in case_blocks:
            for value in values:
                result.append(f"  case {value}:")
            block_str = "\n    ".join(str(stmt) for stmt in block)
            result.append(f"    {block_str}")
            result.append("    break;")

        if otherwise_block:
            result.append("  default:")
            block_str = "\n    ".join(str(stmt) for stmt in otherwise_block)
            result.append(f"    {block_str}")

        result.append("}")
        return "\n".join(result)

    def case_block(self, expr_list, colon_token, *statements) -> tuple[str, list[str]]:




        """Handle case block with values and statements."""
        values = expr_list
        statements = [str(stmt) for stmt in statements]
        return ("case_values", values), statements

    def expression_list(self, *expressions) -> list[str]:




        """Handle list of expressions for case values."""
        result = []
        for expr in expressions:
            if isinstance(expr, list | tuple):
                result.extend(expr)
            else:
                result.append(str(expr))
        return result

    def array_access(self, name, lparen, expr, rparen) -> str:




        """Transform array access to JS array indexing."""
        return f"{name}[{expr}]"

    def record_access(self, record, dot, field) -> str:




        """Transform record field access."""
        return f"{record}.{field}"

    def record_declaration(self, record_token, name, *fields) -> str:




        """Transform record declaration to JS class."""
        field_list = []
        constructor_list = []
        self.record_types[str(name)] = []

        # Filter out the end_if token
        fields = [f for f in fields if not isinstance(f, Token) or f.type != "END_IF"]

        for field_type, field_name in fields:
            # Convert field type to lowercase for lookup
            type_key = str(field_type).upper()
            js_type = self.type_map.get(type_key, "any")
            field_list.append(f"  {field_name}: {js_type};")
            constructor_list.append(f"    this.{field_name} = null;")
            self.record_types[str(name)].append((str(field_name), js_type))

        return (
            f"class {name} {{\n"
            + "\n".join(field_list)
            + "\n\n"
            + "  constructor() {\n"
            + "\n".join(constructor_list)
            + "\n"
            + "  }\n"
            + "}"
        )

    def record_field(self, type_decl, name) -> tuple[str, str]:




        """Handle record field declaration."""
        return (str(type_decl), str(name))

    def function_call_stmt(self, expr) -> str:




        """Handle function call statement."""
        return str(expr) + ";"

    def function_call_expr(self, name, lparen, *args) -> str:




        """Transform function call to JS."""
        # Remove the right parenthesis from args
        args = [arg for arg in args if str(arg) != ")"]
        # Remove commas from args
        args = [arg for arg in args if str(arg) != ","]
        args_str = ", ".join(str(arg) for arg in args)

        # Handle built-in functions
        if str(name).lower() == "length":
            if args:
                return f"{args[0]}.length"
            return "length"
        if str(name).lower() == "asc":
            if args:
                return f"{args[0]}.charCodeAt(0)"
            return "asc"
        if str(name).lower() == "chr":
            if args:
                return f"String.fromCharCode({args[0]})"
            return "chr"
        # Single-argument identifier calls are array access
        if isinstance(name, Token) and name.type == "IDENTIFIER" and len(args) == 1:
            return f"{name}[{args[0]}]"

        # Otherwise, treat as a function call
        return f"{name}({args_str})"

    def variable_ref(self, name) -> str:




        """Handle variable reference."""
        return str(name)

    def primary_expression(self, expr) -> str:




        """Handle primary expression."""
        return str(expr)

    def condition(self, left, op, right) -> str:




        """Build a condition expression."""
        return f"{left} {op} {right}"

    def comparison_op(self, op) -> str:




        """Convert PB comparison operators to JS."""
        op_map = {
            "=": "===",
            "<>": "!==",
            "<": "<",
            ">": ">",
            "<=": "<=",
            ">=": ">=",
        }
        return op_map[str(op)]

    def expression(self, *terms) -> str:




        """Build an expression from terms and operators."""
        if len(terms) == 1:
            return str(terms[0])
        result = []
        for term in terms:
            result.append(str(term))
        return " ".join(result)

    def term(self, *factors) -> str:




        """Build a term from factors and operators."""
        if len(factors) == 1:
            return str(factors[0])
        result = []
        for factor in factors:
            result.append(str(factor))
        return " ".join(result)

    def factor(self, value) -> str:




        """Convert a factor to its string representation."""
        return str(value)

    def assignment(self, name, equal_token, value) -> str:




        """Transform assignment to JS."""
        return f"{name} = {value};"

    def return_statement(self, return_token, value=None) -> str:




        """Transform return statement to JS."""
        if value:
            return f"return {value};"
        return "return;"

    def declare_statement(
        self,
        local_token,
        type_decl,
        name,
        equal_token=None,
        value=None,
    ) -> str:




        """Transform variable declaration to JS."""
        # Determine JS type, handling array types specially
        if isinstance(type_decl, Tree) and type_decl.data == "array_type":
            # array_type: ARRAY LPAREN type_declaration RPAREN
            inner = type_decl.children[2]
            js_type = f"Array<{self.type_map[inner.type]}>"
        else:
            js_type = self.type_map[type_decl.type]

        if value:
            return f"let {name}: {js_type} = {value};"
        return f"let {name}: {js_type};"

    def type_declaration(self, type_token) -> Token:




        """Pass through type token."""
        return type_token

    def statement(self, stmt) -> str:




        """Handle statement nodes."""
        return str(stmt)

    def output_statement(self, output_token, expr) -> str:




        """Transform OUTPUT statement to console.log."""
        return f"console.log({expr});"
