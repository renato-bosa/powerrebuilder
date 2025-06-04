"""PowerBuilder Data (PBD/PBL) Core Extraction Package."""

from . import (
    pcode_ir,  # Import the module to allow extract.pbd_core.pcode_ir.IrNode etc.
)
from .dat import (
    DataClass,
    extract_data_from_entry,
    get_binary_from_data,
    get_text_from_data,
)
from .entry import (
    PbEntryDefinition,
    extract_entry_def,
    extract_entry_def_mixed_mode,
    extract_entry_def_unicode,
    read_and_parse_entry_def,
)
from .exceptions import (  # Added PfcExcludedError
    DatError,
    EntryError,
    HeaderError,
    NodeError,
    PbdError,
    PfcExcludedError,
)
from .header import (
    PBD_SIGNATURE,
    PBD_SIGNATURE_EXT,
    PBL_SIGNATURE,
    PBL_SIGNATURE_EXT,
    HeaderClass,
    extract_pbl_header,
)
# Library import moved below with pfc utilities
from .node import NodeClass, extract_nod, extract_nods
from .opcodes import (
    CFGNode,
    FallbackResult,
    SymbolicStack,
    attempt_symbolic_fallback,
    get_opcode_info,
    load_opcodes,
    log_unknown_opcode,
)
from .pbd_object import PbdObject
from .pcode_ir import (
    AssignmentStatement,
    BinaryOperation,
    Constant,
    Expression,
    FunctionCall,
    IfStatement,
    IrNode,
    ReturnStatement,
    Script,
    Statement,
    VariableRef,
    WhileLoop,
)  # Direct imports for convenience
from .library import Library, calculate_content_hash, load_pfc_hashes  # Moved pfc utilities to library
from .symbol_table import (
    DefinitionLocation,
    ScopeNode,
    Symbol,
    SymbolScope,
    SymbolTable,
    SymbolType,
)

__all__ = [
    # Core Library and Object classes
    "Library",
    "PbdObject",

    # Data structures (Header, Node, Entry, Data blocks)
    "HeaderClass",
    "NodeClass",
    "PbEntryDefinition",
    "DataClass",

    # Component extractors (lower-level API)
    "extract_pbl_header",
    "extract_nods",
    "extract_nod",
    "extract_entry_def", "extract_entry_def_unicode", "extract_entry_def_mixed_mode", "read_and_parse_entry_def",
    "extract_data_from_entry",

    # Data processing helpers
    "get_text_from_data",
    "get_binary_from_data",

    # Exceptions
    "PbdError",
    "HeaderError",
    "NodeError",
    "EntryError",
    "DatError",
    "PfcExcludedError",

    # Signatures / Constants from header module
    "PBL_SIGNATURE", "PBL_SIGNATURE_EXT",
    "PBD_SIGNATURE", "PBD_SIGNATURE_EXT",

    # Opcode processing
    "load_opcodes",
    "get_opcode_info",
    "log_unknown_opcode",
    "attempt_symbolic_fallback",
    "SymbolicStack",
    "CFGNode",
    "FallbackResult",

    # P-Code Intermediate Representation (IR)
    "pcode_ir",  # Module access
    "IrNode", "Expression", "Statement", "Script",
    "Constant", "VariableRef", "BinaryOperation", "FunctionCall", "AssignmentStatement",
    "IfStatement", "WhileLoop", "ReturnStatement",

    # Symbol Table
    "Symbol", "SymbolType", "SymbolScope", "DefinitionLocation", "ScopeNode", "SymbolTable",

    # PFC Utilities
    "load_pfc_hashes",
    "calculate_content_hash",
]
