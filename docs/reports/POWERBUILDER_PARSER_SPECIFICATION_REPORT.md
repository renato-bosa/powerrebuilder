# PowerBuilder Parser Specification Report

This report provides a comprehensive analysis of the PowerBuilder language support in the parser module, based on examination of grammar files, parsers, and transformers.

## Overview

The PowerBuilder parser module implements a comprehensive parsing system using the Lark parsing library with modular grammar design. The parser supports multiple PowerBuilder file types and language constructs through:

1. **Modular Grammar Architecture**
2. **Specialized Parsers for Different Constructs**
3. **AST Transformation Pipeline**
4. **Error Recovery Mechanisms**

## Grammar Architecture

### 1. Common Grammar (`common_grammar.lark`)
**Purpose**: Provides shared tokens, operators, and basic language constructs used across all PowerBuilder file types.

**Key Features Implemented**:
- **Basic Tokens**: Identifiers, integers, strings (including escaped strings), dates, times, hexadecimal numbers
- **Operators**: Arithmetic (+, -, *, /, %, ^), comparison (>, <, >=, <=, =, <>), logical (AND, OR)
- **Common Keywords**: type, from, global, return, if/then/else, try/catch/finally, public/private/protected
- **Type System**: Basic types (INTEGER, STRING, BOOLEAN, etc.) and PowerBuilder-specific types (powerobject, transaction, blob)
- **Expressions**: Full expression grammar with proper precedence for arithmetic, logical, and comparison operations
- **Control Flow**: if statements, conditions, comparisons
- **Exception Handling**: try/catch/finally blocks with typed exceptions
- **Function Calls**: Support for both standalone functions and method calls with arguments
- **Arrays**: Array access syntax with bracket notation
- **Value Types**: Literals for strings, integers, booleans, dates, times, and parameter placeholders

### 2. PowerBuilder Grammar (`powerbuilder.lark`)
**Purpose**: Main grammar for PowerBuilder source files (.sru, .srw, etc.)

**Key Features Implemented**:
- **File Structure**: Header parsing for exported files ($PBExportHeader$)
- **Object Types**: window, datawindow, userobject, application, menu
- **Type Declarations**: 
  - Custom types with inheritance (TYPE...FROM...WITHIN)
  - Global types
  - Forward declarations
- **Variable Declarations**:
  - Instance, shared, and global variables
  - Array declarations with bounds
  - Initial value assignments
- **Function/Subroutine Definitions**:
  - Access modifiers (public, private, protected)
  - Return types including arrays
  - Parameter lists with ref/readonly modifiers
  - Default parameter values
  - Library clauses for external functions
- **Event Handlers**:
  - Event declarations with parameter lists
  - System events (create, destroy, clicked, etc.)
  - Event posting and triggering
- **Control Structures**:
  - Loops: for/next, do/while, do/loop until
  - Choose/case statements
  - Exit and continue statements
- **SQL Integration**: Embedded SQL statements (SELECT, INSERT, UPDATE, DELETE)
- **Transaction Blocks**: USING blocks with transaction management
- **DataWindow Definitions**: Simplified support for DataWindow object syntax
- **Object Initialization**: on...create and on...destroy blocks

### 3. SQL Grammar (`sql.lark`)
**Purpose**: Minimal SQL grammar for parsing embedded SQL statements

**Key Features**:
- Basic SELECT statements with WHERE and ORDER BY clauses
- Table and column references
- Simple expressions and comparisons
- String and number literals

## Specialized Parsers

### 1. Pseudocode Parser (`pseudocode_parser.py`)
**Purpose**: Parse PowerBuilder pseudocode syntax (typically found in documentation)

**Key Features**:
- Extends base parser functionality
- Provides transformation to Python code
- AST summary generation
- Syntax validation

**Note**: Currently has missing dependencies (transformers, grammar loader)

### 2. SQL Parser (`sql_parser.py`)
**Purpose**: Advanced SQL parsing for PowerBuilder embedded SQL

**Key Features**:
- Full SQL statement support (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER)
- Transaction commands (BEGIN, COMMIT, ROLLBACK)
- Cursor operations (DECLARE, OPEN, FETCH, CLOSE)
- Statement type detection
- Multiple statement parsing
- Legacy parser fallback for compatibility
- Integration with SQL optimizer
- AST node generation for SQL constructs

### 3. Transaction Parser (`transaction_parser.py`)
**Purpose**: Specialized parsing for PowerBuilder transaction and event code

**Key Features**:
- Transaction object parsing
- Transaction statement parsing (CONNECT, COMMIT, ROLLBACK, DISCONNECT)
- Savepoint support
- Transaction block parsing with error handling detection
- Simplified string-based parsing (doesn't rely on grammar files)

### 4. Type Parser (`type_parser.py`)
**Purpose**: Enhanced parsing for custom types and enumerations

**Key Features**:
- **Enumerated Types**:
  - Enum value declarations with explicit or implicit values
  - Expression evaluation for enum values
  - Value validation
- **Structure Types**:
  - Field declarations with types and visibility
  - Initial value support
  - Array field support
- **Type Registry**: Maintains registry of parsed custom types
- **Inheritance Support**: Handles type inheritance chains

## Main Parser Implementation

### PowerBuilder Parser (`powerbuilder.py`)
**Purpose**: Unified parser that handles all PowerBuilder file types

**Key Features**:
- **File Type Support**: .sra, .srw, .sru, .srf, .srm, .srs, .srq, .srd, .dwo, .sql
- **Error Recovery**:
  - Enhanced error recovery with Earley parser
  - EOF recovery by completing incomplete constructs
  - Token recovery for encoding issues
  - Partial parsing with section-based recovery
  - Line skipping for unrecoverable errors
- **Environment Configuration**:
  - PB_PARSER_ERROR_RECOVERY: Enable/disable error recovery
  - PB_PARSER_TYPE: Parser type selection (earley/lalr)
  - PB_PARSER_MAX_ERRORS: Maximum errors to collect
- **Grammar Management**: Uses GrammarManager for loading and caching grammars
- **Preprocessing**: Integration with PowerBuilderPreprocessor
- **Type Resolution**: Integration with TypeResolver
- **Library Management**: Integration with LibraryManager

## AST Transformation

### 1. AST Builder (`ast_builder.py`)
**Purpose**: Transform Lark parse trees into PowerBuilder AST nodes

**Key Features**:
- **Error Recovery Nodes**: Special handling for parse errors and incomplete statements
- **Import Handling**: Creates Import objects from import statements
- **Type Transformations**: Inherits enhanced type transformation capabilities
- **Function Definitions**: Full support for function signatures and bodies
- **Statement Transformations**: All PowerBuilder statement types
- **Expression Building**: Complex expression tree construction

### 2. Enhanced Type Transformer (`enhanced_type_transformer.py`)
**Purpose**: Specialized transformation for custom types and enums

**Key Features**:
- **Type Declaration Processing**:
  - Global type handling
  - Enumerated type detection
  - Structure type detection
  - Inheritance chain processing
- **Enum Body Parsing**: 
  - Sequential value assignment
  - Explicit value handling
  - Expression evaluation for complex values
- **Structure Body Parsing**:
  - Field extraction with visibility
  - Type and array bound handling
  - Initial value processing

### 3. SQL Transformer (`sql_transformer.py`)
**Purpose**: Transform SQL parse trees into detailed SQL AST nodes

**Key Features**:
- **Literal Creation**: Type-aware literal node creation
- **Name Handling**: Simple and fully-qualified name support
- **SQL Constructs**:
  - Column and table references
  - FROM, WHERE, GROUP BY, HAVING, ORDER BY clauses
  - JOIN operations
  - Subqueries and CTEs
  - Set operations
  - Parameters (?, :name formats)

## Grammar Loading and Management

### GrammarManager (`loader.py`)
**Purpose**: Centralized grammar file management

**Key Features**:
- **Grammar Caching**: Parser instance caching with configuration
- **Import Resolution**: Handles %import directives
- **File Type Mapping**: Maps PowerBuilder file types to appropriate grammars
- **Dynamic Grammar Registration**: Support for runtime grammar registration
- **Circular Dependency Detection**: Checks for circular grammar imports
- **Parser Configuration**: Automatic parser type and lexer selection

## Pipeline Integration

The parser module is designed to work as part of the PowerBuilder conversion pipeline:

1. **Input**: Receives .sru files from the Decompile stage
2. **Processing**: 
   - Preprocesses source files (macros, includes)
   - Parses using appropriate grammar
   - Transforms to AST nodes
   - Resolves types and dependencies
3. **Output**: Produces AST JSON files for the Model stage

## Error Handling and Recovery

The parser implements sophisticated error recovery:

1. **Grammar-Level Recovery**: Error recovery rules in grammar
2. **Parser-Level Recovery**: 
   - EOF completion
   - Character encoding fixes
   - Section-based parsing
   - Line skipping
3. **Error Collection**: Configurable error collection with limits
4. **Context-Aware Messages**: Detailed error messages with source location

## Known Limitations and Issues

1. **Pseudocode Parser**: Has unresolved dependencies (missing transformer and grammar loader imports)
2. **Complex SQL**: Some advanced SQL features may fall back to legacy parser
3. **DataWindow Syntax**: Simplified DataWindow parsing (full syntax not implemented)
4. **Grammar Conflicts**: Some grammar rules are commented out to avoid conflicts (e.g., MULT token)

## Summary

The PowerBuilder parser module provides comprehensive language support through:

- **Modular grammar design** allowing reuse of common constructs
- **Specialized parsers** for different aspects of the language
- **Robust error recovery** for handling malformed input
- **Extensible architecture** supporting new constructs and file types
- **Full AST generation** for downstream processing

The parser successfully handles the core PowerBuilder language features needed for code conversion, including object-oriented constructs, SQL integration, event handling, and custom type definitions.