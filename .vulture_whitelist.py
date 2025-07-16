"""Vulture whitelist for PowerRebuilder project.

This file contains dummy uses of names that are intentionally unused in the codebase
but should not be flagged by vulture.
"""

# Parser/Transformer method parameters that are part of framework contracts
_ = lambda items: None  # Common transformer parameter
_ = lambda children: None  # Common transformer parameter
_ = lambda args: None  # Common transformer parameter
_ = lambda meta: None  # Lark meta parameter

# Token parameters from parser framework
_ = lambda lparen: None
_ = lambda rparen: None
_ = lambda lbrace: None
_ = lambda rbrace: None
_ = lambda lsquare: None
_ = lambda rsquare: None
_ = lambda comma: None
_ = lambda semicolon: None
_ = lambda colon: None
_ = lambda dot: None
_ = lambda arrow: None
_ = lambda eq: None
_ = lambda ne: None
_ = lambda lt: None
_ = lambda gt: None
_ = lambda le: None
_ = lambda ge: None
_ = lambda plus: None
_ = lambda minus: None
_ = lambda star: None
_ = lambda slash: None
_ = lambda percent: None
_ = lambda ampersand: None
_ = lambda pipe: None
_ = lambda caret: None
_ = lambda tilde: None
_ = lambda lshift: None
_ = lambda rshift: None
_ = lambda at: None
_ = lambda dollar: None
_ = lambda question: None
_ = lambda exclamation: None
_ = lambda backslash: None

# Token keyword variants
_ = lambda lparen_token: None
_ = lambda rparen_token: None
_ = lambda comma_token: None
_ = lambda semicolon_token: None
_ = lambda colon_token: None
_ = lambda dot_token: None
_ = lambda eq_token: None

# Keyword tokens
_ = lambda if_kw: None
_ = lambda then_kw: None
_ = lambda else_kw: None
_ = lambda end_kw: None
_ = lambda for_kw: None
_ = lambda to_kw: None
_ = lambda next_kw: None
_ = lambda while_kw: None
_ = lambda loop_kw: None
_ = lambda case_kw: None
_ = lambda when_kw: None
_ = lambda return_kw: None
_ = lambda exit_kw: None
_ = lambda continue_kw: None
_ = lambda break_kw: None
_ = lambda try_kw: None
_ = lambda catch_kw: None
_ = lambda finally_kw: None
_ = lambda throw_kw: None
_ = lambda public_kw: None
_ = lambda private_kw: None
_ = lambda protected_kw: None
_ = lambda static_kw: None
_ = lambda const_kw: None
_ = lambda readonly_kw: None
_ = lambda global_kw: None
_ = lambda local_kw: None
_ = lambda ref_kw: None
_ = lambda function_kw: None
_ = lambda subroutine_kw: None
_ = lambda event_kw: None
_ = lambda trigger_kw: None
_ = lambda forward_kw: None
_ = lambda extends_kw: None
_ = lambda implements_kw: None
_ = lambda inherits_kw: None
_ = lambda from_kw: None
_ = lambda type_kw: None
_ = lambda choose_kw: None
_ = lambda is_kw: None
_ = lambda true_kw: None
_ = lambda false_kw: None
_ = lambda null_kw: None
_ = lambda this_kw: None
_ = lambda super_kw: None
_ = lambda create_kw: None
_ = lambda destroy_kw: None
_ = lambda using_kw: None
_ = lambda namespace_kw: None
_ = lambda library_kw: None

# SQL keywords
_ = lambda select_kw: None
_ = lambda from_kw: None
_ = lambda where_kw: None
_ = lambda group_kw: None
_ = lambda by_kw: None
_ = lambda having_kw: None
_ = lambda order_kw: None
_ = lambda asc_kw: None
_ = lambda desc_kw: None
_ = lambda insert_kw: None
_ = lambda into_kw: None
_ = lambda values_kw: None
_ = lambda update_kw: None
_ = lambda set_kw: None
_ = lambda delete_kw: None
_ = lambda join_kw: None
_ = lambda inner_kw: None
_ = lambda left_kw: None
_ = lambda right_kw: None
_ = lambda outer_kw: None
_ = lambda on_kw: None
_ = lambda and_kw: None
_ = lambda or_kw: None
_ = lambda not_kw: None
_ = lambda in_kw: None
_ = lambda exists_kw: None
_ = lambda between_kw: None
_ = lambda like_kw: None
_ = lambda as_kw: None
_ = lambda distinct_kw: None
_ = lambda all_kw: None
_ = lambda any_kw: None
_ = lambda some_kw: None
_ = lambda union_kw: None
_ = lambda intersect_kw: None
_ = lambda except_kw: None
_ = lambda limit_kw: None
_ = lambda offset_kw: None

# Visitor pattern parameters (for AST visitors)
_ = lambda node: None
_ = lambda ctx: None
_ = lambda context: None

# Interface/Protocol required parameters
_ = lambda self: None
_ = lambda cls: None
_ = lambda other: None
_ = lambda key: None
_ = lambda value: None
_ = lambda index: None
_ = lambda item: None
_ = lambda attr: None
_ = lambda name: None
_ = lambda args: None
_ = lambda kwargs: None
_ = lambda exc_type: None
_ = lambda exc_value: None
_ = lambda traceback: None
_ = lambda instance: None
_ = lambda owner: None

# Dataclass fields that might appear unused
class _DataclassWhitelist:
    # Model fields
    line: int
    column: int
    end_line: int
    end_column: int
    position: int
    length: int
    offset: int
    size: int
    version: str
    encoding: str
    metadata: dict
    attributes: dict
    properties: dict
    options: dict
    flags: int
    state: str
    status: str
    
    # Parser fields
    token_type: str
    token_value: str
    
    # AST Node fields
    kind: str
    parent: object
    children: list
    
    # Type system fields
    base_type: str
    is_array: bool
    is_nullable: bool
    dimensions: list
    
    # Error fields
    message: str
    code: str
    severity: str
    
# Method names that are called dynamically or via framework
class _DynamicMethods:
    def visit_default(self, node): pass
    def transform(self, tree): pass
    def preprocess(self, text): pass
    def postprocess(self, result): pass
    def on_error(self, error): pass
    def on_success(self, result): pass
    def before_parse(self): pass
    def after_parse(self): pass
    def setup(self): pass
    def teardown(self): pass
    def initialize(self): pass
    def finalize(self): pass
    def validate(self): pass
    def cleanup(self): pass
    
    # Transformer methods
    def error_node(self, items): pass
    def recovered_statement(self, children): pass
    def incomplete_statement(self, children): pass
    
    # Event handlers
    def on_click(self, event): pass
    def on_change(self, event): pass
    def on_submit(self, event): pass
    def on_load(self, event): pass
    def on_unload(self, event): pass
    
    # Lifecycle methods
    def __enter__(self): pass
    def __exit__(self, exc_type, exc_value, traceback): pass
    def __del__(self): pass
    def __init_subclass__(cls, **kwargs): pass
    
    # Protocol methods
    def __iter__(self): pass
    def __next__(self): pass
    def __getitem__(self, key): pass
    def __setitem__(self, key, value): pass
    def __delitem__(self, key): pass
    def __contains__(self, item): pass
    def __len__(self): pass
    def __repr__(self): pass
    def __str__(self): pass
    def __bool__(self): pass
    def __hash__(self): pass
    def __eq__(self, other): pass
    def __ne__(self, other): pass
    def __lt__(self, other): pass
    def __le__(self, other): pass
    def __gt__(self, other): pass
    def __ge__(self, other): pass
    
    # AST visitor methods specific to PowerBuilder AST
    def visit_all(self, nodes): pass
    def visit_access(self, node): pass
    def visit_access_modifier(self, node): pass
    def visit_access_modifier_definer(self, node): pass
    def visit_access_or_type(self, node): pass
    def visit_argument(self, node): pass
    def visit_argument_option(self, node): pass
    def visit_arguments(self, node): pass
    def visit_array(self, node): pass
    def visit_assignment(self, node): pass
    def visit_binary_expression(self, node): pass
    def visit_boolean_literal(self, node): pass
    def visit_case_statement(self, node): pass
    def visit_choose_statement(self, node): pass
    def visit_class_definition(self, node): pass
    def visit_constant(self, node): pass
    def visit_constructor(self, node): pass
    def visit_datawindow(self, node): pass
    def visit_declaration(self, node): pass
    def visit_destructor(self, node): pass
    def visit_do_while_statement(self, node): pass
    def visit_event_declaration(self, node): pass
    def visit_expression(self, node): pass
    def visit_for_statement(self, node): pass
    def visit_function_call(self, node): pass
    def visit_function_declaration(self, node): pass
    def visit_global_declaration(self, node): pass
    def visit_identifier(self, node): pass
    def visit_if_statement(self, node): pass
    def visit_import_statement(self, node): pass
    def visit_library_declaration(self, node): pass
    def visit_literal(self, node): pass
    def visit_member_access(self, node): pass
    def visit_method_declaration(self, node): pass
    def visit_null_literal(self, node): pass
    def visit_number_literal(self, node): pass
    def visit_parameter(self, node): pass
    def visit_property_declaration(self, node): pass
    def visit_return_statement(self, node): pass
    def visit_sql_statement(self, node): pass
    def visit_string_literal(self, node): pass
    def visit_switch_statement(self, node): pass
    def visit_throw_statement(self, node): pass
    def visit_try_statement(self, node): pass
    def visit_type_declaration(self, node): pass
    def visit_unary_expression(self, node): pass
    def visit_variable_declaration(self, node): pass
    def visit_while_statement(self, node): pass
    
    # PowerBuilder specific visitor methods
    def _visit_node(self, node, context): pass
    def visit_node(self, node): pass
    def visit_tokens(self): pass
    
    # Cache-related attributes
    def corruption_fix_cache(self): pass
    def position_stats(self): pass
    def corruption_patterns(self): pass
    def extraction_stats(self): pass
    def version_indicators(self): pass
    
    # Analyzer methods
    def analyze_corruption_patterns(self, text): pass
    def _fix_position_based_corruptions(self, text): pass
    
    # Click CLI decorators and handlers
    def handle_extract(self, ctx, param, value): pass
    def handle_parse(self, ctx, param, value): pass
    def handle_decompile(self, ctx, param, value): pass
    def handle_model(self, ctx, param, value): pass
    def handle_generate(self, ctx, param, value): pass
    
# Import references that might appear unused but are re-exported
import typing
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Type, TypeVar, Generic, Protocol

# Common decorators that might appear unused
from functools import lru_cache, cached_property, wraps
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from contextlib import contextmanager

# Click CLI framework
import click
from click import command, group, option, argument, pass_context, echo

# Testing framework
import pytest
from pytest import fixture, mark, raises, parametrize

# PowerBuilder specific imports that might appear unused
from lark import Lark, Tree, Token, Transformer, Visitor
from lark.visitors import Interpreter
from sqlalchemy import Column, String, Integer, ForeignKey, Table, MetaData
from pydantic import BaseModel, Field, validator

# Jinja2 template engine
from jinja2 import Environment, FileSystemLoader, Template

# Type checking related
from typing_extensions import Literal, TypedDict, NotRequired, Self

# Logging
import logging
from logging import Logger, getLogger, StreamHandler, FileHandler

# PowerBuilder-specific classes and constants
class _PowerBuilderWhitelist:
    # Common PowerBuilder prefixes and patterns
    pb_: str
    PB: str
    dw_: str
    tab_: str
    cb_: str
    st_: str
    em_: str
    ddlb_: str
    lb_: str
    rbtn_: str
    cbx_: str
    sle_: str
    mle_: str
    htb_: str
    vtb_: str
    hpb_: str
    vpb_: str
    gr_: str
    tv_: str
    
    # PowerBuilder specific methods
    def _map_event_type(self, pb_event): pass
    def get_decoder(self): pass
    def decode_pcode(self, data): pass
    def extract_datawindow(self, data): pass
    
# Opcode-related constants that might appear unused
OPCODE_MAP = {}
OPCODE_NAMES = {}
UNKNOWN_OPCODES = set()
VERIFIED_OPCODES = {}

# Pipeline stage names
EXTRACT_STAGE = "extract"
PARSE_STAGE = "parse"
DECOMPILE_STAGE = "decompile"
MODEL_STAGE = "model"
GENERATE_STAGE = "generate"

# Common test fixture names
@pytest.fixture
def pbd_file(): pass
@pytest.fixture
def pbl_file(): pass
@pytest.fixture
def sru_file(): pass
@pytest.fixture
def datawindow_definition(): pass
@pytest.fixture
def mock_coordinator(): pass
@pytest.fixture
def temp_output_dir(): pass

# Pydantic model validators
@validator
def validate_name(cls, v): pass
@validator
def validate_type(cls, v): pass

# SQLAlchemy declarative base
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Enum values that might appear unused
from enum import Enum, auto
class ObjectType(Enum):
    WINDOW = auto()
    DATAWINDOW = auto()
    MENU = auto()
    FUNCTION = auto()
    STRUCTURE = auto()
    USEROBJECT = auto()
    APPLICATION = auto()

class AccessModifier(Enum):
    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    GLOBAL = auto()
    LOCAL = auto()

# Dataclass fields that might appear unused in PowerBuilder models
from dataclasses import dataclass, field
@dataclass
class _DataclassFieldsWhitelist:
    object_type: str = field(default="")
    object_name: str = field(default="")
    library_name: str = field(default="")
    source_code: str = field(default="")
    compiled_code: bytes = field(default_factory=bytes)
    metadata: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
    exports: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    
# Common exception classes
class ExtractionError(Exception): pass
class DecompilationError(Exception): pass
class ParseError(Exception): pass
class ModelError(Exception): pass
class GenerationError(Exception): pass

# Coordinator method names
def coordinate_extraction(self): pass
def coordinate_parsing(self): pass
def coordinate_decompilation(self): pass
def coordinate_modeling(self): pass
def coordinate_generation(self): pass

# Template filter functions
def to_camel_case(value): pass
def to_snake_case(value): pass
def to_pascal_case(value): pass
def escape_dart_string(value): pass
def format_dart_type(value): pass