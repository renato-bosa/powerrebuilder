"""Centralized constants for PowerBuilder parsing.

This module contains constants used throughout the parsing process,
including grammar paths, token types, and common string literals.
"""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path

# Grammar file paths
GRAMMAR_DIR = Path(__file__).parent / "grammar"
POWERBUILDER_GRAMMAR = GRAMMAR_DIR / "powerbuilder.lark"
COMMON_GRAMMAR = GRAMMAR_DIR / "common_grammar.lark"
DATAWINDOW_GRAMMAR = GRAMMAR_DIR / "datawindow.lark"
SQL_GRAMMAR = GRAMMAR_DIR / "sql.lark"
PSEUDOCODE_GRAMMAR = GRAMMAR_DIR / "pseudocode.lark"
POWERBUILDER_CORE_GRAMMAR = GRAMMAR_DIR / "powerbuilder_core.lark"
POWERBUILDER_JS_GRAMMAR = GRAMMAR_DIR / "powerbuilder_js.lark"


# File extensions
class FileType(Enum):
    """PowerBuilder file types."""

    WINDOW = auto()  # .srw
    USER_OBJECT = auto()  # .sru
    FUNCTION = auto()  # .srf
    MENU = auto()  # .srm
    STRUCTURE = auto()  # .srs
    QUERY = auto()  # .srq
    APPLICATION = auto()  # .sra
    DATAWINDOW = auto()  # .srd
    PROJECT = auto()  # .pbt
    LIBRARY = auto()  # .pbl, .pbd
    UNKNOWN = auto()


# File extension mappings
FILE_EXTENSIONS: dict[str, FileType] = {
    "srw": FileType.WINDOW,
    "sru": FileType.USER_OBJECT,
    "srf": FileType.FUNCTION,
    "srm": FileType.MENU,
    "srs": FileType.STRUCTURE,
    "srq": FileType.QUERY,
    "sra": FileType.APPLICATION,
    "srd": FileType.DATAWINDOW,
    "pbt": FileType.PROJECT,
    "pbl": FileType.LIBRARY,
    "pbd": FileType.LIBRARY,
}

# PowerBuilder basic types
PB_BASIC_TYPES: set[str] = {
    "integer",
    "int",
    "long",
    "uint",
    "ulong",
    "string",
    "char",
    "character",
    "boolean",
    "bool",
    "date",
    "datetime",
    "time",
    "decimal",
    "dec",
    "real",
    "double",
    "blob",
    "any",
}

# PowerBuilder system types
PB_SYSTEM_TYPES: set[str] = {
    "powerobject",
    "window",
    "transaction",
    "dynamicdescriptionarea",
    "dynamicstagingarea",
    "error",
    "menu",
    "message",
    "connection",
    "datastore",
}

# PowerBuilder control types
PB_CONTROL_TYPES: set[str] = {
    # Text controls
    "statictext",
    "singlelineedit",
    "multilineedit",
    "editmask",
    "statichyperlink",
    
    # Button controls
    "commandbutton",
    "picturebutton",
    
    # Selection controls
    "checkbox",
    "radiobutton",
    
    # List controls
    "dropdownlistbox",
    "listbox",
    "combobox",
    
    # Container controls
    "groupbox",
    "tab",
    
    # Data controls
    "datawindow",
    
    # Shape controls
    "line",
    "rectangle",
    "roundrectangle",
    "oval",
    "drawobject",
    
    # Advanced controls
    "treeview",
    "listview",
    "richtextedit",
    "graph",
    "ole",
    "mdiclient",
    
    # Progress controls
    "progressbar",
    "hprogressbar",
    "vprogressbar",
    
    # Slider/Trackbar controls
    "htrackbar",
    "vtrackbar",
    
    # Scrollbar controls
    "vscrollbar",
    "hscrollbar",
    
    # Date/Time controls
    "datepicker",
    "monthcalendar",
    
    # Ink controls
    "inkpicture",
    "inkedit",
    
    # Other controls
    "picture",
    "animation",
    "spin",
    
    # Legacy/generic names
    "edit",  # Generic edit control
}

# PowerBuilder event types
PB_EVENT_TYPES: set[str] = {
    "clicked",
    "doubleclicked",
    "itemchanged",
    "itererror",
    "itemfocuschanged",
    "rbuttondown",
    "rowfocuschanged",
    "rowfocuschanging",
    "create",
    "destroy",
    "buttonclicked",
    "buttonclicking",
    "getfocus",
    "losefocus",
    "modified",
}

# PowerBuilder keywords
PB_KEYWORDS: set[str] = {
    "if",
    "then",
    "else",
    "elseif",
    "end",
    "case",
    "choose",
    "do",
    "loop",
    "while",
    "until",
    "for",
    "next",
    "step",
    "continue",
    "exit",
    "return",
    "try",
    "catch",
    "finally",
    "throw",
    "this",
    "super",
    "goto",
    "gosub",
    "call",
    "post",
    "trigger",
    "create",
    "destroy",
    "open",
    "close",
    "function",
    "subroutine",
    "event",
    "private",
    "public",
    "protected",
    "global",
    "shared",
    "on",
    "type",
    "constant",
    "variables",
    "forward",
    "from",
    "to",
    "ref",
    "autoinstantiate",
    "within",
    "of",
    "parent",
    "using",
    "dynamic",
    "indirect",
    "not",
    "and",
    "or",
    "xor",
    "true",
    "false",
}

# PowerBuilder operators
PB_OPERATORS: set[str] = {
    # Arithmetic operators
    "+",
    "-",
    "*",
    "/",
    "^",
    # Comparison operators
    "=",
    "<>",
    "<",
    ">",
    "<=",
    ">=",
    # Logical operators
    "and",
    "or",
    "not",
    # Assignment operators
    "+=",
    "-=",
    "*=",
    "/=",
}

# SQL keywords
SQL_KEYWORDS: set[str] = {
    "select",
    "insert",
    "update",
    "delete",
    "where",
    "from",
    "join",
    "inner",
    "outer",
    "left",
    "right",
    "full",
    "on",
    "group",
    "by",
    "having",
    "order",
    "asc",
    "desc",
    "distinct",
    "union",
    "all",
    "into",
    "values",
    "set",
    "null",
    "is",
    "not",
    "like",
    "in",
    "between",
    "exists",
    "create",
    "alter",
    "drop",
    "table",
    "view",
    "index",
    "procedure",
    "function",
    "constraint",
    "primary",
    "key",
    "foreign",
    "references",
    "default",
    "check",
    "unique",
    "identity",
}

# Map of all built-in PowerBuilder types for quick lookup
PB_TYPE_MAP: dict[str, bool] = dict.fromkeys(PB_BASIC_TYPES | PB_SYSTEM_TYPES, True)
