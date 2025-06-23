"""Benchmarks for code generation performance."""

from unittest.mock import Mock

import pytest

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET
from generate.converters.ast_converter import ASTConverter
from generate.converters.datawindow_converter import DataWindowConverter
from generate.flutter import FlutterGenerator
from model.ast import Control, Function, Variable, Window


class TestGenerationPerformance:
    """Benchmark code generation operations."""

    @pytest.fixture
    def flutter_generator(self, tmp_path):


        """Create Flutter generator instance."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return FlutterGenerator(str(template_dir), str(output_dir))

    @pytest.fixture
    def ast_converter(self):


        """Create AST converter instance."""
        converter = ASTConverter()
        # Mock sub-converters
        converter.type_converter = Mock()
        converter.expression_converter = Mock()
        converter.ui_converter = Mock()
        converter.event_converter = Mock()
        converter.datawindow_converter = Mock()
        return converter

    @pytest.fixture
    def sample_window_ast(self):


        """Create sample window AST."""
        window = Mock(spec=Window)
        window.name = "w_test"
        window.properties = {"title": "Test", "width": 800, "height": 600}
        window.variables = [Mock(spec=Variable) for _ in range(5)]
        window.controls = [Mock(spec=Control) for _ in range(10)]
        window.events = []
        window.methods = [Mock(spec=Function) for _ in range(3)]
        return window

    def test_simple_widget_generation(self, benchmark, flutter_generator):




        """Benchmark simple widget generation."""
        context = {
            "widget": {
                "name": "TestWidget",
                "is_stateful": False,
            },
            "properties": [],
            "build_content": "Container()",
        }

        # Mock template rendering
        flutter_generator.env = Mock()
        flutter_generator.env.get_template = Mock(return_value=Mock(
            render=Mock(return_value="class TestWidget extends StatelessWidget {}"),
        ))

        def generate():
            """Generate.
            """


            return flutter_generator.render_template("widget.dart.jinja2", context)

        result = benchmark(generate)
        assert benchmark.stats["mean"] < 0.001  # Under 1ms

    def test_complex_screen_generation(self, benchmark, flutter_generator):




        """Benchmark complex screen generation."""
        context = {
            "screen": {
                "name": "MainScreen",
                "title": "Main",
                "route_name": "/main",
            },
            "parameters": [
                {"name": f"param{i}", "type": "String", "required": True}
                for i in range(10)
            ],
            "controllers": [
                {"name": f"controller{i}", "type": "TextEditingController"}
                for i in range(5)
            ],
            "state_variables": [
                {"name": f"state{i}", "dart_type": "int"}
                for i in range(10)
            ],
            "methods": [
                {"name": f"method{i}", "return_type": "void", "body": ["// Method"]}
                for i in range(20)
            ],
        }

        # Mock template
        flutter_generator.env = Mock()
        template = Mock()
        template.render = Mock(return_value="Generated Flutter code " * 100)
        flutter_generator.env.get_template = Mock(return_value=template)

        def generate():
            """Generate.
            """


            return flutter_generator.render_template("screen.dart.jinja2", context)

        result = benchmark(generate)
        assert benchmark.stats["mean"] < 0.01  # Under 10ms

    def test_ast_conversion_performance(self, benchmark, ast_converter, sample_window_ast):




        """Benchmark AST to Flutter conversion."""
        # Setup mocks
        ast_converter.type_converter.convert_type.return_value = "String"
        ast_converter.ui_converter.convert_control.return_value = {
            "type": "button", "widget": "ElevatedButton",
        }

        def convert():
            """Convert.
            """


            return ast_converter.convert_window(sample_window_ast)

        result = benchmark(convert)
        assert benchmark.stats["mean"] < 0.05  # Under 50ms

    def test_datawindow_conversion(self, benchmark):




        """Benchmark DataWindow conversion."""
        converter = DataWindowConverter()
        converter.type_converter = Mock()
        converter.type_converter.convert_type.return_value = "String"

        dw_syntax = """
        table(column=(type=char(MAX_NAME_LENGTH) name=name)
              column=(type=number name=id)
              column=(type=decimal(2) name=salary))
        """ * 20  # 60 columns

        def convert():
            """Convert.
            """


            return converter.convert_datawindow(dw_syntax, "dw_test")

        result = benchmark(convert)
        assert benchmark.stats["mean"] < 0.1  # Under 100ms for large DataWindow

    def test_batch_file_generation(self, benchmark, flutter_generator, tmp_path) -> None:




        """Benchmark batch file generation."""
        # Prepare multiple files to generate
        files_to_generate = []
        for i in range(20):
            files_to_generate.append({
                "path": f"widgets/widget_{i}.dart",
                "content": f"class Widget{i} extends StatelessWidget {{}}",
            })

        def generate_batch() -> None:
            """Generate batch.
            """


            for file_info in files_to_generate:
                flutter_generator.write_file(
                    file_info["path"],
                    file_info["content"],
                )

        result = benchmark(generate_batch)
        assert benchmark.stats["mean"] < 0.1  # Under 100ms for 20 files

    def test_template_compilation_cache(self, benchmark, flutter_generator):




        """Benchmark template compilation caching."""
        # Mock template environment
        flutter_generator.env = Mock()
        compiled_template = Mock(render=Mock(return_value="output"))
        flutter_generator.env.get_template = Mock(return_value=compiled_template)

        context = {"widget": {"name": "Test"}}

        # First call - template compilation
        flutter_generator.render_template("widget.dart.jinja2", context)

        # Benchmark subsequent calls (should use cache)
        def render_cached():
            """Render cached.
            """

            return flutter_generator.render_template("widget.dart.jinja2", context)

        result = benchmark(render_cached)
        # Cached rendering should be very fast
        assert benchmark.stats["mean"] < 0.0001  # Under 0.1ms

    def test_large_project_generation(self, benchmark, flutter_generator, ast_converter):




        """Benchmark generation of a large project."""
        # Simulate a project with many files
        project_structure = {
            "screens": 10,
            "widgets": 50,
            "models": 20,
            "services": 5,
        }

        # Mock all operations
        flutter_generator.env = Mock()
        flutter_generator.env.get_template = Mock(
            return_value=Mock(render=Mock(return_value="code")),
        )

        def generate_project():
            """Generate project.
            """


            generated_files = 0
            for _ in range(project_structure["screens"]):
                flutter_generator.render_template("screen.dart.jinja2", {})
                generated_files += 1
            for _ in range(project_structure["widgets"]):
                flutter_generator.render_template("widget.dart.jinja2", {})
                generated_files += 1
            for _ in range(project_structure["models"]):
                flutter_generator.render_template("model.dart.jinja2", {})
                generated_files += 1
            for _ in range(project_structure["services"]):
                flutter_generator.render_template("service.dart.jinja2", {})
                generated_files += 1
            return generated_files

        result = benchmark(generate_project)
        # Should handle large projects efficiently
        assert benchmark.stats["mean"] < 0.5  # Under 500ms for 85 files
