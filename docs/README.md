# Sime-Finch Documentation

## Overview

Sime-Finch is a PowerBuilder model and parser tool that helps analyze and transform PowerBuilder code. This documentation provides comprehensive information about the project's architecture, usage, and development.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture](#architecture)
3. [Usage Guide](#usage-guide)
4. [Development](#development)
5. [API Reference](#api-reference)
6. [Contributing](#contributing)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

```bash
pip install -r requirements.txt
```

### Quick Start

```python
from parse import Parser
from model import PowerBuilderModel

# Parse PowerBuilder code
parser = Parser()
model = parser.parse_file("example.pbl")

# Analyze the model
print(model.get_functions())
```

## Architecture

The project is organized into several main components:

- `parse/`: PowerBuilder code parsing
- `model/`: Abstract Syntax Tree (AST) and model definitions
- `extract/`: Code extraction utilities
- `decompile/`: Decompilation tools
- `generate/`: Code generation

See [architecture.md](architecture.md) for detailed design documentation.

## Usage Guide

### Basic Usage

1. Initialize the parser
2. Parse PowerBuilder files
3. Analyze the resulting model
4. Generate reports or transformed code

### Advanced Features

- Custom rule definitions
- Code transformation pipelines
- Integration with other tools

## DataWindow Extraction

### Overview

The Sime-Finch decompiler includes advanced DataWindow extraction capabilities that can extract SQL syntax and DataWindow definitions from compiled binary PBD files.

### Features

- Extracts PBSELECT statements with full SQL syntax
- Handles UTF-16 encoded DataWindow definitions
- Supports multiple DataWindow formats (binary and text-based)
- Generates .sql files for successfully extracted syntax
- Provides metadata files for DataWindows that cannot be fully extracted

### Usage

```bash
# Extract DataWindows from a PBD file
python -m decompile.main_decompiler input.pbd -o output_dir

# DataWindow files will be saved as:
# - .sql files for extracted syntax
# - .txt files for metadata when syntax cannot be extracted
```

### Example Output

```sql
// DataWindow: d_customer_list.dwo
// From: myapp.pbd
// Type: DataWindow
// Successfully extracted DataWindow syntax

PBSELECT( VERSION(400) 
  TABLE(NAME="customers" ) 
  COLUMN(NAME="customers.customer_id") 
  COLUMN(NAME="customers.customer_name") 
  COLUMN(NAME="customers.email")
  WHERE( 
    EXP1 ="customers.active" 
    OP ="=" 
    EXP2 ="'Y'" 
  ) 
) 
```

## Development

### Setting Up Development Environment

1. Clone the repository
2. Install development dependencies
3. Set up pre-commit hooks

### Running Tests

```bash
pytest
```

### Code Style

We use:

- Ruff for linting and formatting
- MyPy for type checking
- Black for code formatting

### Error Handling

All errors inherit from `SimeFinchError`. See [errors.py](../parse/errors.py) for details.

## API Reference

### Parser API

```python
class Parser:
    def parse_file(self, file_path: str) -> PowerBuilderModel:
        """Parse a PowerBuilder file."""
        pass
```

### Model API

```python
class PowerBuilderModel:
    def get_functions(self) -> List[Function]:
        """Get all functions in the model."""
        pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

# sime_finch

Reverse-engineer PowerBuilder .pbd files and recreate their important elements into a modern, modular codebase.

## Project Structure

```
sime_finch/
│
├── config.py                # Central config, constants, paths, etc.
├── pbd_reader.py            # Main entry for reading/extracting .pbd files
├── binary_utils.py          # All low-level byte/struct helpers
│
├── parsers/
│   ├── ui.py                # Parse .win, .udo, .menu, .srw, .sru to UI metadata
│   ├── schema.py            # Parse .dwo, .qry, .schema to DB schema
│   ├── pcode.py             # Disassembler, symbol resolution, stack-based decompiler
│
├── codegen/
│   ├── react_gen.py         # Generate React components from UI metadata
│   ├── models_gen.py        # Generate SQLAlchemy models from schema
│   └── templates/
│       ├── react_component.jinja2
│       ├── sqlalchemy_model.jinja2
│
└── tests/
    ├── test_pbd_reader.py
    ├── test_binary_utils.py
    ├── parsers/
    │   ├── test_ui.py
    │   ├── test_schema.py
    │   ├── test_pcode.py
    ├── codegen/
    │   ├── test_react_gen.py
    │   ├── test_models_gen.py
```

## Module Purposes

- **config.py**: Centralizes configuration, file type lists, and paths.
- **binary_utils.py**: Byte/struct parsing, decoding, and low-level helpers.
- **pbd_reader.py**: Handles reading and extracting raw objects from `.pbd` files.
- **parsers/**: Parse UI, schema, and pcode files into normalized metadata.
- **codegen/**: Generate code (React, SQLAlchemy) from metadata using Jinja2 templates.
- **tests/**: Unit tests for each module (pytest).

## Running Tests

```sh
pytest sime_finch/tests/
```

## Next Steps

- Fill in actual extraction, parsing, and codegen logic in each module.
- Expand tests for real PowerBuilder files and templates.
- Add a CLI or orchestrator script to wire the pipeline together.
- Add documentation and developer guides.

+--------------------------------------------------------------+
I PBL File Format                                  2003 - 2012 I
+--------------------------------------------------------------+
Dear PB Fans out there,

these are the results of the analysis I did, written down as
a short ASCII text description (valid thru PB5-11.5).

With this knowledge you can write your own LibraryDirectory
or Export Function for PowerBuilder PBL/PBD/DLL/EXE files.

Think about the possibility; including files via PBR assignment
and extracting them during runtime. That is a nice gimmick.

Most of the terms used are the results and presumptions of my
analysis.

Thanks to:

- Kevin Cai for Bytes 17-18 of the Node-Block
- Jeremy Lakeman for Bytes 19-20, 23-24 of the Node-Block

Regards

Arnd Schmidt                                          April 2011

<arnd.schmidt@dwox.com>

+--------------------------------------------------------------+
I PBL File Format                                              I
+--------------------------------------------------------------+

Rules and facts:

1.) A PBL is always made out of blocks of 512, except the Node
Block (NOD*), that has a size of 6 blocks, meaning 3072 Bytes.

2.) There is always one Header (HDR*) block,
followed by a free/used blocks bitmap (FRE*).
Then follows the first 'NOD*' block .
Theoretically this first 'NOD*' block might(!) point to a
parent node, but I have never seen that.

3.) Object Data (also SCC Informations) are always
stored in single forward linked/chained of 'DAT*'-Blocks.

The information about the offset and the length is stored in
the Header (HDR*).

4.) A PBD is a PBL.

5.) DLL and EXE files have a 'TRL*' at the end of the file.
This is pointing to the one and only 'HDR*'-Block.
Attention:
For signed DLLs (like PowerBuilder's signed DLLs in Version 11.5)
you have to recalculate the offset to the 'TRL*' Block.

+--------------------------------------------------------------+
I Library Header Block (512 Byte)                              I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'HDR*'                              I
I   5 - 18  I String     I 'PowerBuilder' + 0x00 + 0x00        I
I  19 - 22  I Char(4)    I PBL Format Version? (0400/0500/0600)I
I  23 - 26  I Long       I Creation/Optimization Datetime      I
I  29 - xx  I String     I Library Comment                     I
I 285 - 288 I Long       I Offset of first SCC data block      I
I 289 - 292 I Long       I Size (Net size of SCC data)         I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I Library Header Block - Unicode (1024 Byte)                   I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'HDR*'                              I
I   5 - 32  I StringW    I 'PowerBuilder' + 0x00 + 0x00        I
I  33 - 40  I CharW(4)   I PBL Format Version? (0400/0500/0600)I
I  41 - 44  I Long       I Creation/Optimization Datetime      I
I  47 - xx  I StringW    I Library Comment                     I
I 559 - 562 I Long       I Offset of first SCC data block      I
I 563 - 566 I Long       I Size (Net size of SCC data)         I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I  Bitmap Block (512 Byte)                                     I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I  1 - 4    I Char(4)    I 'FRE*'                              I
I  5 - 8    I Long       I Offset of next block or 0           I
I  9 - 512  I Bit(504)   I Bitmap, each Bit represents a block I
+-----------+------------+-------------------------------------+
(512 - 8)* 8 = 4032 Blocks are referenced

+--------------------------------------------------------------+
I Node Block (3072 Byte)                                       I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'NOD*'                              I
I   5 - 8   I Long       I Offset of next (left ) block or 0   I
I   9 - 12  I Long       I Offset of parent block or 0         I
I  13 - 16  I Long       I Offset of next (right) block or 0   I
I  17 - 18  I Integer    I Space left in block, initial = 3040 I
I  19 - 20  I Integer    I Position of alphabetically          I
I           I            I first Objectname in this block      I
I  21 - 22  I Integer    I Count of entries in that node       I
I  23 - 24  I Integer    I Position of alphabetically          I
I           I            I last Objectname in this block       I
I  33 - xx  I Chunks     I 'ENT*'-Chunks                       I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I Entry Chunk (Variable Length)                                I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'ENT*'                              I
I   5 - 8   I Char(4)    I PBL version? (0400/0500/0600)       I
I   9 - 12  I Long       I Offset of first data block          I
I  13 - 16  I Long       I Objectsize (Net size of data)       I
I  17 - 20  I Long       I Unix datetime                       I
I  21 - 22  I Integer    I Length of Comment                   I
I  23 - 24  I Integer    I Length of Objectname                I
I  25 - xx  I String     I Objectname                          I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I Entry Chunk - Unicode (Variable Length)                      I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'ENT*'                              I
I   5 - 12  I CharW(4)   I PBL version? (0400/0500/0600)       I
I  13 - 16  I Long       I Offset of first data block          I
I  17 - 20  I Long       I Objectsize (Net size of data)       I
I  21 - 24  I Long       I Unix datetime                       I
I  25 - 26  I Integer    I Length of Comment                   I
I  27 - 28  I Integer    I Length of Objectname                I
I  29 - xx  I StringW    I Objectname                          I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I Data Block (512 Byte)                                        I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'DAT*'                              I
I   5 - 8   I Long       I Offset of next data block or 0      I
I   9 - 10  I Integer    I Length of data in block             I
I  11 - XXX I Blob{}     I Data (maximum Length is 502         I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I Trailer Block (in DLL/EXE) always last block (512 Byte)      I
+-----------+------------+-------------------------------------+
I Pos.      I Type       I Information                         I
+-----------+------------+-------------------------------------+
I   1 - 4   I Char(4)    I 'TRL*'                              I
I   5 - 8   I Long       I Offset of Library Header ('HDR*')   I
+-----------+------------+-------------------------------------+

+--------------------------------------------------------------+
I SCC DATA                                                     I
I     Structure of status information chunks                   I
I     in DAT*-blocks (Variable Length)                         I
+---------+----------------------------------------------------I
I Type    I Information                                        I
+---------+----------------------------------------------------I
I String  I Libraryname (the opposite!)                        I
I String  I Objectname                                         I
I String  I Developername                                      I
I Char(1) I Flag                                               I
+---------+----------------------------------------------------I

+--------------------------------------------------------------+
I PB6/7 Status Flags                                           I
+------+------+------------------------------------------------+
I Icon I Flag I Meaning                                        I
+------+------+------------------------------------------------+
I      I  r   I Object is registered                           I
I      I  d   I Object is Checked Out (locked)                 I
I      I  s   I Object (Working Copy) to be checked in         I
I      I  u   I Unknown?! After an Error occurred.             I
I      I      I (Checked out by user <Unknown>                 I
I      I      I  Could be set to 'r' with an Hex-Editor.)      I
+------+------+------------------------------------------------+

+--------------------------------------------------------------+
I SCC DATA chunk                                               I
I In newer PB Versions the DAT*-blocks content starts with the I
I ansi-encoded String 'SCC*'.                                  I
I Objectname and Version Informations are stored as            I
I 0-Byte (Word) separated strings.                             I
+----------+---------------------------------------------------I
I Type     I Information                                       I
+----------+------------+--------------------------------------+
I  1 - 4   I Char(4)    I 'SCC*'                               I
I  5 - xxx I Blob       I Objectname (string) followed by      I
I          I            I Null-Byte 0x00 (Word in Unicode)     I
I          I            I indicating the string end            I
I          I            I Version (String) followed by         I
I          I            I Null-Byte 0x00 (Word in Unicode)     I
I          I            I indicating the string end            I
I          I            I Next Objectname und Versioninfo      I
I          I            I repeatedly until the end             I
+----------+------------+--------------------------------------+

DateTimes are stored in Long format in Unix representation.
Timezone is always GMT (+/- 0:00), so the datetime has to be
converted to LocalDateTime via LocalTimeZone conversation.

In the compiled object data blocks, there are at least 2 more
datetimes, starting at byte 23 and the other one at 27!
Looks like these are the modification and regeneration date...
