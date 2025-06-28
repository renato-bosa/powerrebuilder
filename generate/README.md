# Generate Module

## Overview

The Generate module is responsible for converting PowerBuilder AST into target languages (Python, Flutter/Dart). It provides template-based code generation with support for UI frameworks, business logic, and data handling.

## Structure

```
generate/
├── __init__.py
├── base_generator.py        # Base code generator class
├── converter_integration.py # Converter integration
├── generate_coordinator.py  # Generation orchestrator
├── documentation_generator.py
├── jinja_filters.py        # Custom Jinja2 filters
├── layout_converter.py     # UI layout conversion
├── python_ui_generator.py  # Python UI generation
├── template_schemas.py     # Template validation schemas
├── template_validator.py   # Template validation
├── converters/             # AST to IR converters
│   ├── ui/                # UI-related converters
│   │   ├── datawindow_converter.py
│   │   ├── design_system_converter.py
│   │   ├── menu_converter.py
│   │   └── ui_converter.py
│   ├── data/              # Data handling converters
│   │   ├── blob_converter.py
│   │   ├── database_operation_formatter.py
│   │   └── relationship_extractor.py
│   ├── logic/             # Business logic converters
│   │   ├── application_converter.py
│   │   ├── event_converter.py
│   │   ├── event_wiring.py
│   │   └── method_body_converter.py
│   └── utils/             # Utility converters
│       ├── ast_converter.py
│       ├── expression_converter.py
│       └── type_converter.py
├── flutter/               # Flutter-specific code
│   └── powerbuilder_flutter_mapping.json
├── python/                # Python-specific code
└── templates/             # Code generation templates
    ├── flutter/           # Flutter/Dart templates
    │   ├── main.dart.jinja2
    │   ├── widget.dart.jinja2
    │   ├── datawindow_widget.dart.jinja2
    │   └── ...
    └── python/            # Python templates
        ├── main.py.jinja2
        ├── tkinter_window.py.jinja2
        ├── datawindow_widget.py.jinja2
        └── ...
```

## Key Components

### Converters

Converters transform AST nodes into intermediate representations:

#### UI Converters
- **UIConverter**: Converts windows and controls
- **DataWindowConverter**: Handles DataWindow objects
- **MenuConverter**: Converts menu structures
- **DesignSystemConverter**: Creates consistent UI themes

#### Data Converters
- **BlobConverter**: Handles binary data
- **DatabaseOperationFormatter**: Formats SQL operations
- **RelationshipExtractor**: Extracts entity relationships

#### Logic Converters
- **EventConverter**: Converts event handlers
- **MethodBodyConverter**: Transforms method implementations
- **ApplicationConverter**: Handles application structure

### Templates

Jinja2 templates for code generation:

#### Python Templates
- Tkinter-based UI generation
- SQLModel for database models
- Event handling system
- Service layer architecture

#### Flutter Templates
- Material Design widgets
- State management
- Navigation system
- Responsive layouts

## Usage

```python
from generate.generate_coordinator import GenerateCoordinator
from model.core import Application

# Generate Python code
coordinator = GenerateCoordinator(target="python")
code_files = coordinator.generate(application_ast)

# Generate Flutter code
coordinator = GenerateCoordinator(target="flutter")
code_files = coordinator.generate(application_ast)
```

## Conversion Process

1. **AST Analysis**: Analyze the PowerBuilder AST
2. **Conversion**: Convert AST to intermediate representation
3. **Template Selection**: Choose appropriate templates
4. **Code Generation**: Generate target language code
5. **Post-processing**: Format and organize output

## Features

### UI Generation
- Window to Frame/Widget conversion
- Control mapping (Button, TextBox, etc.)
- Layout preservation
- Event handler wiring

### Business Logic
- Function conversion
- Expression translation
- Control flow mapping
- Error handling

### Data Handling
- Database model generation
- SQL operation conversion
- Transaction management
- Data validation

## Template System

The module uses Jinja2 templates with custom filters:

```jinja2
{{ function.name|snake_case }}
{{ control.type|map_control_type }}
{{ expression|convert_expression }}
```

## Layout Strategies

Multiple layout strategies for UI conversion:
- **Absolute**: Preserves exact positioning
- **Grid**: Converts to grid layout
- **Flex**: Uses flexible box layout
- **Responsive**: Creates responsive design

## Generated Code Structure

### Python Output
```
output/
├── main.py           # Application entry point
├── windows/          # Window classes
├── models/           # Data models
├── services/         # Business logic
└── utils/            # Utility functions
```

### Flutter Output
```
output/
├── lib/
│   ├── main.dart     # App entry point
│   ├── screens/      # Screen widgets
│   ├── widgets/      # Custom widgets
│   ├── models/       # Data models
│   └── services/     # Business logic
└── pubspec.yaml      # Dependencies
```

## Dependencies

- jinja2: Template engine
- Python 3.9+

## Related Modules

- **Model**: Provides AST for conversion
- **Parse**: Creates AST structure
- **Decompile**: Provides additional metadata