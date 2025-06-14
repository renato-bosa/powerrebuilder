"""PowerBuilder grammar tests using direct Lark grammar construction."""

import pytest
from lark import Lark, NonTerminal, Rule, Terminal


def create_simple_grammar():
    """Create a grammar programmatically to avoid EBNF parsing issues."""
    # Define terminals
    NAME = Terminal("NAME", r"[a-zA-Z][a-zA-Z0-9_]*")
    NUMBER = Terminal("NUMBER", r"[0-9]+")
    STRING = Terminal("STRING", r'"[^"]*"')

    # Define rules
    rules = [
        Rule("start", [NonTerminal("statement")]),
        Rule("statement", [NonTerminal("var_decl")]),
        Rule("statement", [NonTerminal("assignment")]),
        Rule("statement", [NonTerminal("if_stmt")]),
        Rule(
            "var_decl",
            [
                NAME,
                Terminal("COLON", ":"),
                NonTerminal("type"),
                Terminal("SEMICOLON", ";"),
            ],
        ),
        Rule("type", [Terminal("INTEGER", "integer")]),
        Rule("type", [Terminal("STRING_TYPE", "string")]),
        Rule("type", [Terminal("BOOLEAN", "boolean")]),
        Rule(
            "assignment",
            [
                NAME,
                Terminal("EQUALS", "="),
                NonTerminal("value"),
                Terminal("SEMICOLON", ";"),
            ],
        ),
        Rule("value", [NAME]),
        Rule("value", [NUMBER]),
        Rule("value", [STRING]),
        Rule(
            "if_stmt",
            [
                Terminal("IF", "if"),
                NonTerminal("condition"),
                Terminal("THEN", "then"),
                NonTerminal("statement"),
                Terminal("END_IF", "end if"),
            ],
        ),
        Rule("condition", [NAME, NonTerminal("compare"), NUMBER]),
        Rule("compare", [Terminal("GT", ">")]),
        Rule("compare", [Terminal("LT", "<")]),
        Rule("compare", [Terminal("GE", ">=")]),
        Rule("compare", [Terminal("LE", "<=")]),
        Rule("compare", [Terminal("EQ", "=")]),
        Rule("compare", [Terminal("NE", "<>")]),
    ]

    # Create a parser with these rules
    return Lark(
        start="start",
        rules=rules,
        parser="earley",
        lexer="contextual",
        import_paths=[],
        keep_all_tokens=False,
    )


@pytest.fixture
def simple_parser():
    """Return a simple parser for PowerBuilder."""
    return create_simple_grammar()


class TestDirectGrammar:
    """Test cases for a PowerBuilder grammar built directly."""

    def test_variable_declaration(self, simple_parser):
        """Test parsing of variable declarations."""
        code = "x: integer;"
        tree = simple_parser.parse(code)
        assert tree is not None

    def test_assignment(self, simple_parser):
        """Test parsing of assignment statements."""
        code = "x = 10;"
        tree = simple_parser.parse(code)
        assert tree is not None

        code = 'message = "Hello";'
        tree = simple_parser.parse(code)
        assert tree is not None

    def test_if_statement(self, simple_parser):
        """Test parsing of if statements."""
        code = """
        if x > 5 then
            y = 10;
        end if
        """
        tree = simple_parser.parse(code.strip())
        assert tree is not None
