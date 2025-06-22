"""PowerBuilder code generation package.

This package provides functionality for generating modern web application code
from PowerBuilder models.

Key exports:
- FlutterGenerator: Generates Flutter widgets and screens from PowerBuilder UI
- generate_models: Generates SQLModel models from PowerBuilder database schema
- generate_services: Generates service layer from PowerBuilder business logic
- generate_flutter: Generates Flutter/Dart UI code from PowerBuilder windows and user objects
- generate_tests: Generates unit tests for converted code
- generate_documentation: Generates comprehensive project documentation
"""

from .documentation_generator import generate_documentation
from .flutter import FlutterGenerator
from .generate_coordinator import generate_flutter, generate_models, generate_services
from .test_generator import generate_tests

__all__ = [
    "FlutterGenerator",
    "generate_flutter",
    "generate_models",
    "generate_services",
    "generate_tests",
    "generate_documentation",
]
