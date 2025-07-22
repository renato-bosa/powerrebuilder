"""Flutter generation coordinator for UI components."""

import logging
from pathlib import Path
from typing import Any

from ...contracts.events import EventType, IEventBus
from ..base import CodeGenerator
from ..converters.flutter.layouts import LayoutConverter, LayoutStrategy
from ..converters.flutter.logic import MethodBodyConverter
from ..converters.flutter.models import TypeConverter
from ..converters.flutter.widgets import UIConverter
from ..converters.logic.wiring import EventWiringSystem
from .base import BaseGenerationCoordinator

logger = logging.getLogger(__name__)


class FlutterGenerationCoordinator(BaseGenerationCoordinator):
    """Coordinator for generating Flutter UI components."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        template_dir: Path | None = None,
        event_bus: IEventBus | None = None,
        design_theme: str = "liquid_glass",
    ) -> None:
        """Initialize Flutter generation coordinator.

        Args:
            input_dir: Directory containing parsed AST files
            output_dir: Directory for generated Flutter code
            template_dir: Directory containing templates
            event_bus: Optional event bus
            design_theme: Design theme to use
        """
        super().__init__(input_dir, output_dir, event_bus)

        # Set template directory
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates" / "flutter"

        # Initialize Flutter generator
        self.generator = FlutterGenerator(
            str(template_dir), str(self.output_dir), validate_templates=False
        )

        # Initialize converters
        self.type_converter = TypeConverter()
        self.ui_converter = UIConverter(design_theme=design_theme)
        self.method_body_converter = MethodBodyConverter()
        self.event_wiring_system = EventWiringSystem()

        # Initialize layout converter
        self.layout_converter = LayoutConverter(
            LayoutStrategy.ABSOLUTE,
            ui_converter=self.ui_converter,
            event_wiring_system=self.event_wiring_system,
        )

        # Configure generator
        self.generator.layout_converter = self.layout_converter
        self.generator.ui_converter = self.ui_converter
        self.generator.type_converter = self.type_converter
        self.generator.method_body_converter = self.method_body_converter
        self.generator.event_wiring_system = self.event_wiring_system

    def get_generator_type(self) -> str:
        """Get the type of generator."""
        return "flutter"

    def generate(self, config: dict[str, Any]) -> dict[str, Any]:
        """Generate Flutter code from parsed PowerBuilder files.

        Args:
            config: Generation configuration

        Returns:
            Generation results
        """
        self.publish_event(EventType.STAGE_STARTED, {"stage": "flutter_generation"})

        try:
            results = {
                "screens": self._generate_screens(),
                "widgets": self._generate_widgets(),
                "datawindows": self._generate_datawindow_widgets(),
                "project": self._generate_project_structure(config.get("app_info")),
            }

            self.publish_event(
                EventType.STAGE_COMPLETED,
                {"stage": "flutter_generation", "results": results},
            )

            return results

        except Exception as e:
            self.publish_event(
                EventType.STAGE_FAILED,
                {"stage": "flutter_generation", "error": str(e)},
            )
            raise

    def _generate_screens(self) -> dict[str, Any]:
        """Generate Flutter screens from window files."""
        window_files = self.find_files("*.srw.ast.json")
        logger.info("Found %s window files", len(window_files))

        results = {"generated": 0, "files": []}

        def process_window(window_file: Path) -> None:
            ast_data = self.read_json_file(window_file)
            window_name = self.extract_object_name(window_file, ".srw.ast")

            # Convert window to model
            window_model = self._convert_window_with_converters(ast_data, window_name)

            # Generate screen
            self.generator.generate_screen_from_model(window_model)

            screen_file = f"screens/{window_name.lower()}_screen.dart"
            results["generated"] += 1
            results["files"].append(screen_file)

        self.process_files(window_files, process_window, "window")

        return results

    def _generate_widgets(self) -> dict[str, Any]:
        """Generate Flutter widgets from user object files."""
        user_object_files = self.find_files("*.sru.ast.json")

        # Filter for UI objects
        ui_files = [
            f
            for f in user_object_files
            if any(prefix in f.stem.lower() for prefix in ["uo_", "u_"])
        ]

        logger.info("Found %s UI object files", len(ui_files))

        results = {"generated": 0, "files": []}

        def process_widget(uo_file: Path) -> None:
            ast_data = self.read_json_file(uo_file)
            widget_name = self.extract_object_name(uo_file, ".sru.ast")

            # Extract widget information
            widget_info = self._extract_widget_from_ast(ast_data)

            # Generate widget
            self.generator.generate_widget(
                name=widget_name,
                props=widget_info.get("props", {}),
                is_stateful=widget_info.get("is_stateful", True),
                children=widget_info.get("children", []),
            )

            widget_file = f"widgets/{widget_name.lower()}.dart"
            results["generated"] += 1
            results["files"].append(widget_file)

        self.process_files(ui_files, process_widget, "widget")

        return results

    def _generate_datawindow_widgets(self) -> dict[str, Any]:
        """Generate Flutter DataWindow widgets."""
        datawindow_files = self.find_files("*.srd.ast.json")
        logger.info("Found %s DataWindow files", len(datawindow_files))

        results = {"generated": 0, "files": []}

        def process_datawindow(dw_file: Path) -> None:
            ast_data = self.read_json_file(dw_file)
            dw_name = self.extract_object_name(dw_file, ".srd.ast")

            # Extract DataWindow information
            from src.generate.coordinator import extract_datawindow_from_ast

            dw_info = extract_datawindow_from_ast(ast_data)

            if dw_info:
                self.generator.generate_datawindow_widget(
                    name=dw_name,
                    columns=dw_info.get("columns", []),
                    data_source=f"api/{dw_name}",
                    presentation_style=dw_info.get("presentation_style", "grid"),
                )

                dw_file = f"widgets/{dw_name.lower()}_datawindow.dart"
                results["generated"] += 1
                results["files"].append(dw_file)

        self.process_files(datawindow_files, process_datawindow, "datawindow")

        return results

    def _generate_project_structure(
        self, app_info: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Generate Flutter project structure."""
        if app_info is None:
            app_info = {
                "name": "pb_app",
                "display_name": "PowerBuilder App",
                "description": "Flutter application converted from PowerBuilder",
            }

        self.generator.generate_project_structure(app_info)

        return {"success": True, "project_path": str(self.output_dir)}

    def _convert_window_with_converters(
        self, ast_data: dict[str, Any], object_name: str
    ) -> dict[str, Any]:
        """Convert window AST data using converters."""
        # Import the conversion function from the original coordinator
        from src.generate.coordinator import GenerateCoordinator

        # Create temporary coordinator instance to reuse conversion logic
        temp_coord = GenerateCoordinator(str(self.input_dir), str(self.output_dir))
        temp_coord.type_converter = self.type_converter
        temp_coord.ui_converter = self.ui_converter

        return temp_coord._convert_window_with_converters(ast_data, object_name)

    def _extract_widget_from_ast(self, ast_data: dict[str, Any]) -> dict[str, Any]:
        """Extract widget information from AST."""
        from src.generate.coordinator import extract_widget_from_ast

        return extract_widget_from_ast(ast_data)


class FlutterGenerator(CodeGenerator):
    """Generate Flutter widgets and screens from PowerBuilder UI."""

    def __init__(
        self, template_dir: str, output_dir: str, validate_templates: bool = True
    ) -> None:
        """Initialize Flutter generator."""
        super().__init__(template_dir, output_dir, validate_templates)
        self.layout_converter = None
        self.ui_converter = None
        self.method_body_converter = None
        self.event_wiring_system = None
        self.type_converter = None

    def generate_widget(
        self,
        name: str,
        props: list[dict[str, Any]],
        is_stateful: bool = False,
        children: list[dict[str, Any]] | None = None,
    ) -> None:
        """Generate a Flutter widget."""
        use_glassmorphism = (
            hasattr(self, "ui_converter")
            and self.ui_converter
            and self.ui_converter.design_system.design_theme == "liquid_glass"
        )

        context = {
            "widget": {
                "name": name,
                "props": props,
                "has_state": is_stateful,
                "children": children or [],
                "use_glassmorphism": use_glassmorphism,
                "controls": [],
                "state": [],
                "controllers": [],
                "methods": [],
                "imports": [],
            }
        }
        content = self.render_template("widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}.dart", content)

    def generate_screen_from_model(self, window_model: dict[str, Any]) -> None:
        """Generate a Flutter screen from a converted window model."""
        # Import the implementation from original coordinator
        from src.generate.coordinator import FlutterGenerator as OriginalGenerator

        # Create temporary instance and copy our dependencies
        temp = OriginalGenerator(self.template_dir, self.output_dir, False)
        temp.layout_converter = self.layout_converter
        temp.ui_converter = self.ui_converter
        temp.method_body_converter = self.method_body_converter
        temp.event_wiring_system = self.event_wiring_system
        temp.env = self.env

        # Use the original implementation
        temp.generate_screen_from_model(window_model)

    def generate_datawindow_widget(
        self,
        name: str,
        columns: list[dict[str, Any]],
        data_source: str,
        presentation_style: str = "grid",
        row_type: str = "Map<String, dynamic>",
    ) -> None:
        """Generate a Flutter widget for PowerBuilder DataWindow."""
        context = {
            "datawindow": {
                "name": name,
                "columns": columns,
                "presentation_style": presentation_style,
                "row_type": row_type,
                "imports": [],
            },
            "widget_name": name,
            "columns": columns,
            "data_source": data_source,
        }
        content = self.render_template("datawindow_widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}_datawindow.dart", content)

    def generate_project_structure(self, app_info: dict[str, Any]) -> None:
        """Generate the complete Flutter project structure."""
        # Generate pubspec.yaml
        pubspec_context = {
            "app": {
                "name": app_info.get("name", "pb_app"),
                "description": app_info.get(
                    "description", "Flutter app converted from PowerBuilder"
                ),
                "has_database": app_info.get("has_database", False),
                "has_charts": app_info.get("has_charts", False),
                "has_file_operations": app_info.get("has_file_operations", False),
                "has_printing": app_info.get("has_printing", False),
                "assets": app_info.get("assets", []),
            },
            "generate_tests": app_info.get("generate_tests", False),
        }
        content = self.render_template("pubspec.yaml.jinja2", pubspec_context)
        self.write_file("pubspec.yaml", content)

        # Generate main.dart
        main_context = {"app": app_info}
        content = self.render_template("main.dart.jinja2", main_context)
        self.write_file("lib/main.dart", content)

        # Create directories
        directories = [
            "lib/screens",
            "lib/widgets",
            "lib/models",
            "lib/services",
            "lib/theme",
            "lib/core",
            "assets/images",
            "assets/fonts",
        ]

        for directory in directories:
            dir_path = self.output_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info("Generated Flutter project structure")
