"""Flutter/Dart code generation for PowerBuilder conversion.

This module provides Flutter/Dart code generation capabilities for converting
PowerBuilder applications to Flutter mobile/web applications. The FlutterGenerator
class handles the generation of:

- Widgets from PowerBuilder user objects
- Screens from PowerBuilder windows
- Data models from PowerBuilder structures
- DataWindow widgets for data display

Templates are provided in the templates/ subdirectory for various Flutter
components using the Dart programming language.
"""

from ..generate_coordinator import FlutterGenerator

__all__ = ['FlutterGenerator']