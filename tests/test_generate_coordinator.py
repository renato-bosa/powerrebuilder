"""Tests for the generate coordinator module."""

import pytest
from pathlib import Path
import tempfile
import shutil
import json
from unittest.mock import Mock, patch, MagicMock

from generate.generate_coordinator import generate_models, generate_services, generate_flutter


class TestGenerateCoordinator:
    """Test cases for the Generate module coordinator."""

    def setup_method(self):
        """Set up test instances."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = GenerateCoordinator()
        
    def teardown_method(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test coordinator initialization."""
        assert self.coordinator is not None
        assert hasattr(self.coordinator, 'type_converter')
        assert hasattr(self.coordinator, 'ui_converter')
        assert hasattr(self.coordinator, 'event_converter')
        assert hasattr(self.coordinator, 'datawindow_converter')
        assert hasattr(self.coordinator, 'template_env')

    def test_process_window_object(self):
        """Test processing a window object."""
        window_data = {
            "type": "window",
            "name": "w_customer_list",
            "title": "Customer List",
            "width": 800,
            "height": 600,
            "controls": [
                {
                    "type": "datawindow",
                    "name": "dw_list",
                    "x": 10,
                    "y": 50,
                    "width": 780,
                    "height": 400
                },
                {
                    "type": "commandbutton",
                    "name": "cb_retrieve",
                    "text": "Retrieve",
                    "x": 10,
                    "y": 460,
                    "width": 100,
                    "height": 30
                }
            ],
            "events": [
                {
                    "name": "open",
                    "body": "dw_list.settransobject(sqlca)\ndw_list.retrieve()"
                },
                {
                    "control": "cb_retrieve",
                    "name": "clicked",
                    "body": "dw_list.retrieve()"
                }
            ]
        }
        
        result = self.coordinator.process_window(window_data)
        
        assert result["type"] == "StatefulWidget"
        assert result["name"] == "WCustomerList"
        assert result["title"] == "Customer List"
        assert len(result["widgets"]) == 2
        assert result["widgets"][0]["type"] == "DataTable"
        assert result["widgets"][1]["type"] == "ElevatedButton"
        assert len(result["methods"]) == 2

    def test_process_userobject(self):
        """Test processing a user object."""
        uo_data = {
            "type": "userobject",
            "name": "u_customer_detail",
            "controls": [
                {
                    "type": "statictext",
                    "name": "st_name",
                    "text": "Name:",
                    "x": 10,
                    "y": 10
                },
                {
                    "type": "singlelineedit",
                    "name": "sle_name",
                    "x": 100,
                    "y": 10,
                    "width": 200
                }
            ]
        }
        
        result = self.coordinator.process_userobject(uo_data)
        
        assert result["type"] == "StatelessWidget"
        assert result["name"] == "UCustomerDetail"
        assert len(result["widgets"]) == 2
        assert result["widgets"][0]["type"] == "Text"
        assert result["widgets"][1]["type"] == "TextField"

    def test_process_datawindow_object(self):
        """Test processing a DataWindow object."""
        dw_data = {
            "type": "datawindow",
            "name": "d_customer_list",
            "sql": "SELECT id, name, balance FROM customer",
            "columns": [
                {"name": "id", "type": "number"},
                {"name": "name", "type": "char(100)"},
                {"name": "balance", "type": "decimal(2)"}
            ]
        }
        
        result = self.coordinator.process_datawindow(dw_data)
        
        assert result["model_name"] == "DCustomerListModel"
        assert result["widget_name"] == "DCustomerListWidget"
        assert result["repository_name"] == "DCustomerListRepository"
        assert len(result["columns"]) == 3

    def test_process_nonvisual_object(self):
        """Test processing a non-visual object."""
        nvo_data = {
            "type": "nonvisual",
            "name": "n_business_logic",
            "instance_variables": [
                {"name": "is_connection_string", "type": "string", "access": "private"},
                {"name": "ii_timeout", "type": "integer", "initial": "30"}
            ],
            "methods": [
                {
                    "name": "of_connect",
                    "returns": "integer",
                    "arguments": [{"name": "as_database", "type": "string"}],
                    "body": "// Connect logic"
                }
            ]
        }
        
        result = self.coordinator.process_nonvisual(nvo_data)
        
        assert result["type"] == "Service"
        assert result["name"] == "NBusinessLogic"
        assert len(result["properties"]) == 2
        assert result["properties"][0]["name"] == "isConnectionString"
        assert result["properties"][0]["type"] == "String"
        assert len(result["methods"]) == 1
        assert result["methods"][0]["name"] == "ofConnect"

    def test_generate_flutter_project(self):
        """Test Flutter project generation."""
        objects = [
            {
                "type": "window",
                "name": "w_main",
                "generated": {
                    "type": "StatefulWidget",
                    "name": "WMain",
                    "file": "screens/w_main.dart"
                }
            },
            {
                "type": "nonvisual",
                "name": "n_service",
                "generated": {
                    "type": "Service",
                    "name": "NService",
                    "file": "services/n_service.dart"
                }
            }
        ]
        
        output_dir = Path(self.temp_dir) / "flutter_app"
        self.coordinator.generate_flutter_project(objects, output_dir)
        
        # Check project structure
        assert (output_dir / "pubspec.yaml").exists()
        assert (output_dir / "lib" / "main.dart").exists()
        assert (output_dir / "lib" / "screens").is_dir()
        assert (output_dir / "lib" / "services").is_dir()
        assert (output_dir / "lib" / "models").is_dir()
        assert (output_dir / "lib" / "widgets").is_dir()

    def test_generate_pubspec(self):
        """Test pubspec.yaml generation."""
        project_info = {
            "name": "customer_app",
            "description": "Customer management application",
            "dependencies": ["http", "provider", "intl"]
        }
        
        pubspec_content = self.coordinator.generate_pubspec(project_info)
        
        assert "name: customer_app" in pubspec_content
        assert "description: Customer management application" in pubspec_content
        assert "sdk: flutter" in pubspec_content
        assert "http:" in pubspec_content
        assert "provider:" in pubspec_content
        assert "intl:" in pubspec_content

    def test_process_menu_object(self):
        """Test processing a menu object."""
        menu_data = {
            "type": "menu",
            "name": "m_main",
            "items": [
                {
                    "text": "File",
                    "name": "m_file",
                    "items": [
                        {"text": "New", "name": "m_new", "clicked": "// New logic"},
                        {"text": "Open", "name": "m_open", "clicked": "// Open logic"},
                        {"text": "-"},
                        {"text": "Exit", "name": "m_exit", "clicked": "close(parentwindow)"}
                    ]
                },
                {
                    "text": "Help",
                    "name": "m_help",
                    "items": [
                        {"text": "About", "name": "m_about", "clicked": "open(w_about)"}
                    ]
                }
            ]
        }
        
        result = self.coordinator.process_menu(menu_data)
        
        assert result["type"] == "AppBar"
        assert result["name"] == "MMain"
        assert len(result["actions"]) == 2
        assert result["actions"][0]["type"] == "PopupMenuButton"
        assert len(result["actions"][0]["items"]) == 4

    def test_generate_routes(self):
        """Test route generation for navigation."""
        windows = [
            {"name": "WMain", "route": "/"},
            {"name": "WCustomerList", "route": "/customers"},
            {"name": "WCustomerDetail", "route": "/customer/:id"}
        ]
        
        routes_code = self.coordinator.generate_routes(windows)
        
        assert "routes: {" in routes_code
        assert "'/': (context) => WMain()" in routes_code
        assert "'/customers': (context) => WCustomerList()" in routes_code
        assert "onGenerateRoute:" in routes_code  # For parameterized routes

    def test_process_global_functions(self):
        """Test processing global functions."""
        functions = [
            {
                "name": "gf_calculate_tax",
                "returns": "decimal",
                "arguments": [
                    {"name": "ad_amount", "type": "decimal"},
                    {"name": "ai_rate", "type": "integer"}
                ],
                "body": "return ad_amount * ai_rate / 100"
            }
        ]
        
        result = self.coordinator.process_global_functions(functions)
        
        assert len(result) == 1
        assert result[0]["name"] == "gfCalculateTax"
        assert result[0]["returnType"] == "double"
        assert len(result[0]["parameters"]) == 2
        assert result[0]["parameters"][0]["name"] == "adAmount"
        assert result[0]["parameters"][0]["type"] == "double"

    def test_generate_theme(self):
        """Test theme generation based on PowerBuilder styles."""
        pb_styles = {
            "window_background": "15790320",  # Light gray
            "button_color": "buttonface",
            "text_color": "windowtext",
            "font_family": "Arial",
            "font_size": "10"
        }
        
        theme_code = self.coordinator.generate_theme(pb_styles)
        
        assert "ThemeData(" in theme_code
        assert "primarySwatch:" in theme_code
        assert "fontFamily: 'Arial'" in theme_code
        assert "textTheme:" in theme_code

    def test_handle_inheritance(self):
        """Test handling object inheritance."""
        base_window = {
            "type": "window",
            "name": "w_base",
            "controls": [
                {"type": "commandbutton", "name": "cb_ok", "text": "OK"}
            ],
            "methods": [
                {"name": "wf_validate", "returns": "boolean"}
            ]
        }
        
        derived_window = {
            "type": "window",
            "name": "w_derived",
            "ancestor": "w_base",
            "controls": [
                {"type": "singlelineedit", "name": "sle_input"}
            ],
            "methods": [
                {"name": "wf_process", "returns": "integer"}
            ]
        }
        
        result = self.coordinator.process_inheritance(base_window, derived_window)
        
        assert result["extends"] == "WBase"
        assert len(result["controls"]) == 2  # Inherited + new
        assert len(result["methods"]) == 2  # Inherited + new

    def test_error_handling(self):
        """Test error handling in generation process."""
        # Invalid object type
        with pytest.raises(ValueError):
            self.coordinator.process_object({"type": "invalid_type", "name": "test"})
        
        # Missing required fields
        with pytest.raises(KeyError):
            self.coordinator.process_window({"type": "window"})  # Missing name

    @patch('generate.generate_coordinator.TemplateEnvironment')
    def test_template_rendering(self, mock_template_env):
        """Test template rendering functionality."""
        mock_template = MagicMock()
        mock_template.render.return_value = "Generated code"
        mock_template_env.get_template.return_value = mock_template
        
        self.coordinator.template_env = mock_template_env
        
        result = self.coordinator.render_template("window.dart.j2", {"name": "TestWindow"})
        
        assert result == "Generated code"
        mock_template_env.get_template.assert_called_with("window.dart.j2")
        mock_template.render.assert_called_with({"name": "TestWindow"})

    def test_batch_processing(self):
        """Test batch processing of multiple objects."""
        objects = [
            {"type": "window", "name": "w_1", "controls": []},
            {"type": "window", "name": "w_2", "controls": []},
            {"type": "nonvisual", "name": "n_1", "methods": []},
            {"type": "datawindow", "name": "d_1", "columns": []}
        ]
        
        results = self.coordinator.process_batch(objects)
        
        assert len(results) == 4
        assert results[0]["generated"]["name"] == "W1"
        assert results[1]["generated"]["name"] == "W2"
        assert results[2]["generated"]["name"] == "N1"
        assert results[3]["generated"]["model_name"] == "D1Model"

    def test_dependency_resolution(self):
        """Test dependency resolution between objects."""
        objects = [
            {
                "type": "window",
                "name": "w_main",
                "references": ["n_service", "w_child"]
            },
            {
                "type": "nonvisual",
                "name": "n_service",
                "references": []
            },
            {
                "type": "window",
                "name": "w_child",
                "references": ["n_service"]
            }
        ]
        
        ordered = self.coordinator.resolve_dependencies(objects)
        
        # n_service should come first as it has no dependencies
        assert ordered[0]["name"] == "n_service"
        # w_child and w_main can be in any order after n_service
        assert len(ordered) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])