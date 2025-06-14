"""PowerBuilder code generation package.

This package provides functionality for generating modern web application code
from PowerBuilder models.

Key exports:
- FlutterGenerator: Generates Flutter widgets and screens from PowerBuilder UI
- generate_models: Generates SQLModel models from PowerBuilder database schema
- generate_services: Generates service layer from PowerBuilder business logic
- generate_flutter: Generates Flutter/Dart UI code from PowerBuilder windows and user objects

TODO: Missing Features
    - Comprehensive validation logic - Missing
    - Unit test generation - Missing
    - Documentation generation - Missing
"""

from .flutter import FlutterGenerator
from .generate_coordinator import generate_flutter, generate_models, generate_services

__all__ = [
    "FlutterGenerator",
    "generate_flutter",
    "generate_models",
    "generate_services",
]
