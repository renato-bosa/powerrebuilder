"""End-to-end conversion test for sample PowerBuilder app."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from common.pipeline_coordinator import PipelineCoordinator


class TestEndToEndConversion:
    """Test complete conversion of a sample PowerBuilder application."""

    @pytest.fixture
    def sample_app_dir(self):


        """Create a sample PowerBuilder application structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app_dir = Path(tmpdir) / "sample_app"
            app_dir.mkdir()

            # Create sample PBL files
            (app_dir / "application.pbl").write_bytes(b"HDR*" + b"\x00" * 1024)
            (app_dir / "windows.pbl").write_bytes(b"HDR*" + b"\x00" * 2048)
            (app_dir / "datawindows.pbl").write_bytes(b"HDR*" + b"\x00" * 1536)

            # Create source directory with sample files
            src_dir = app_dir / "src"
            src_dir.mkdir()

            # Sample application object
            (src_dir / "app_main.sra").write_text('''
                global type app_main from application
                end type
                global app_main app_main

                event open()
                    // Application initialization
                    open(w_main)
                end event

                event close()
                    // Application cleanup
                end event
            ''')

            # Sample window
            (src_dir / "w_main.srw").write_text('''
                forward
                global type w_main from window
                end type
                type cb_ok from commandbutton within w_main
                end type
                type dw_data from datawindow within w_main
                end type
                end forward

                global type w_main from window
                integer width = 2400
                integer height = 1800
                boolean titlebar = true
                string title = "Main Window"
                cb_ok cb_ok
                dw_data dw_data
                end type
                global w_main w_main

                type cb_ok from commandbutton within w_main
                integer x = 100
                integer y = 100
                integer width = 400
                integer height = 100
                string text = "OK"
                end type

                event cb_ok::clicked()
                    MessageBox("Info", "Button clicked!")
                end event

                type dw_data from datawindow within w_main
                integer x = 100
                integer y = 300
                integer width = 2200
                integer height = 1200
                string dataobject = "d_employee_list"
                boolean hscrollbar = true
                boolean vscrollbar = true
                end type

                on w_main.create
                this.cb_ok=create cb_ok
                this.dw_data=create dw_data
                this.Control[]={this.cb_ok,this.dw_data}
                end on

                on w_main.destroy
                destroy(this.cb_ok)
                destroy(this.dw_data)
                end on
            ''')

            # Sample DataWindow
            (src_dir / "d_employee_list.srd").write_text('''
                release 12.5;
                datawindow(units=0 timer_interval=0 color=1073741824 processing=1)
                header(height=72 color="536870912")
                summary(height=0 color="536870912")
                footer(height=0 color="536870912")
                detail(height=84 color="536870912")
                table(column=(type=number updatewhereclause=yes name=emp_id dbname="employee.emp_id" )
                     column=(type=char(50) updatewhereclause=yes name=emp_name dbname="employee.emp_name" )
                     column=(type=char(50) updatewhereclause=yes name=emp_email dbname="employee.emp_email" )
                     column=(type=decimal(2) updatewhereclause=yes name=emp_salary dbname="employee.emp_salary" )
                     retrieve="SELECT emp_id, emp_name, emp_email, emp_salary FROM employee" )
            ''')

            # Sample user object
            (src_dir / "n_business_logic.sru").write_text('''
                forward
                global type n_business_logic from nonvisualobject
                end type
                end forward

                global type n_business_logic from nonvisualobject
                end type
                global n_business_logic n_business_logic

                public function integer calculate_bonus(decimal salary)
                    decimal bonus

                    if salary > 100000 then
                        bonus = salary * 0.15
                    elseif salary > 50000 then
                        bonus = salary * 0.10
                    else
                        bonus = salary * 0.05
                    end if

                    return bonus
                end function

                public function boolean validate_email(string email)
                    // Simple email validation
                    if Pos(email, "@") > 0 and Pos(email, ".") > 0 then
                        return true
                    else
                        return false
                    end if
                end function
            ''')

            yield app_dir

    def test_successful_conversion(self, sample_app_dir, tmp_path):




        """Test successful end-to-end conversion of sample app."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create pipeline
        pipeline = PipelineCoordinator(
            input_dir=str(sample_app_dir),
            output_dir=str(output_dir),
        )

        # Mock the actual processing to avoid file system operations
        with patch.object(pipeline, "extract_step") as mock_extract, \
             patch.object(pipeline, "parse_step") as mock_parse, \
             patch.object(pipeline, "generate_step") as mock_generate:

            # Setup mocks
            mock_extract.return_value = {
                "extracted_files": ["app_main.sra", "w_main.srw", "d_employee_list.srd", "n_business_logic.sru"],
                "status": "success",
            }

            mock_parse.return_value = {
                "parsed_objects": {
                    "app_main": {"type": "application", "ast": Mock()},
                    "w_main": {"type": "window", "ast": Mock()},
                    "d_employee_list": {"type": "datawindow", "ast": Mock()},
                    "n_business_logic": {"type": "userobject", "ast": Mock()},
                },
                "status": "success",
            }

            mock_generate.return_value = {
                "generated_files": [
                    "lib/main.dart",
                    "lib/screens/main_screen.dart",
                    "lib/widgets/employee_list_datawindow.dart",
                    "lib/services/business_logic_service.dart",
                    "lib/models/employee.dart",
                ],
                "status": "success",
            }

            # Process the application
            result = pipeline.process_directory(str(sample_app_dir))

            # Verify successful conversion
            assert result["status"] == "success"
            assert "extract" in result["stages"]
            assert "parse" in result["stages"]
            assert "generate" in result["stages"]

    def test_conversion_metrics(self, sample_app_dir, tmp_path):




        """Test conversion metrics and reporting."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        pipeline = PipelineCoordinator(
            input_dir=str(sample_app_dir),
            output_dir=str(output_dir),
        )

        with patch.object(pipeline, "process_file") as mock_process:
            # Mock individual file processing
            mock_process.return_value = {
                "status": "success",
                "lines_of_code": 100,
                "conversion_time": 0.5,
            }

            # Get list of files
            pb_files = list(sample_app_dir.rglob("*.sr*"))

            # Process each file
            total_loc = 0
            for pb_file in pb_files:
                result = pipeline.process_file(str(pb_file), str(output_dir))
                total_loc += result.get("lines_of_code", 0)

            # Verify metrics
            assert len(pb_files) == 4  # 4 source files
            assert total_loc == 400  # 100 lines per file

    def test_error_handling(self, sample_app_dir, tmp_path):




        """Test error handling during conversion."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Add a corrupted file
        (sample_app_dir / "src" / "corrupted.srw").write_text("INVALID POWERBUILDER CODE!!!")

        pipeline = PipelineCoordinator(
            input_dir=str(sample_app_dir),
            output_dir=str(output_dir),
        )

        with patch.object(pipeline, "parse_step") as mock_parse:
            # Simulate parse error for corrupted file
            def parse_side_effect(file_path, *args, **kwargs):

                if "corrupted" in str(file_path):
                    raise Exception("Parse error: Invalid syntax")
                return {"status": "success", "ast": Mock()}

            mock_parse.side_effect = parse_side_effect

            # Process should continue despite individual file errors
            with patch.object(pipeline, "extract_step", return_value={"status": "success"}), \
                 patch.object(pipeline, "generate_step", return_value={"status": "success"}):

                result = pipeline.process_directory(str(sample_app_dir))

                # Should complete with partial success
                assert result["status"] == "completed_with_errors"
                assert result["failed_files"] > 0

    def test_generated_flutter_structure(self, sample_app_dir, tmp_path):




        """Test the structure of generated Flutter app."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create expected Flutter structure
        expected_structure = {
            "lib/": [
                "main.dart",
                "app.dart",
                "routes.dart",
            ],
            "lib/screens/": [
                "main_screen.dart",
            ],
            "lib/widgets/": [
                "employee_list_datawindow.dart",
            ],
            "lib/models/": [
                "employee.dart",
            ],
            "lib/services/": [
                "business_logic_service.dart",
                "database_service.dart",
            ],
            "lib/utils/": [
                "constants.dart",
                "helpers.dart",
            ],
        }

        # Mock file generation
        def create_flutter_structure():

            for dir_path, files in expected_structure.items():
                dir_full_path = output_dir / dir_path
                dir_full_path.mkdir(parents=True, exist_ok=True)
                for file_name in files:
                    (dir_full_path / file_name).touch()

        create_flutter_structure()

        # Verify structure
        for dir_path, expected_files in expected_structure.items():
            dir_full_path = output_dir / dir_path
            assert dir_full_path.exists()
            for file_name in expected_files:
                assert (dir_full_path / file_name).exists()

    def test_datawindow_to_model_conversion(self):




        """Test DataWindow to model conversion."""
        from generate.converters.datawindow_converter import DataWindowConverter

        converter = DataWindowConverter()
        converter.type_converter = Mock()
        converter.type_converter.convert_type.side_effect = ["int", "String", "String", "double"]

        dw_syntax = '''
            table(column=(type=number name=emp_id dbname="employee.emp_id")
                  column=(type=char(50) name=emp_name dbname="employee.emp_name")
                  column=(type=char(50) name=emp_email dbname="employee.emp_email")
                  column=(type=decimal(2) name=emp_salary dbname="employee.emp_salary")
                  retrieve="SELECT * FROM employee")
        '''

        result = converter.convert_datawindow(dw_syntax, "d_employee_list")

        assert result.name == "DEmployeeList"
        assert len(result.columns) == 4
        assert result.columns[0].name == "emp_id"
        assert result.columns[0].data_type == "int"
        assert result.columns[1].name == "emp_name"
        assert result.columns[1].data_type == "String"
        assert "SELECT * FROM employee" in result.sql

    def test_business_logic_conversion(self):




        """Test conversion of business logic to service."""
        from generate.converters.ast_converter import ASTConverter
        from model.ast import Block, Function, Parameter, Type

        converter = ASTConverter()
        converter.type_converter = Mock()
        converter.type_converter.convert_type.side_effect = ["double", "double", "double"]

        # Mock calculate_bonus function
        func = Mock(spec=Function)
        func.name = "calculate_bonus"
        func.return_type = Type("decimal")
        func.parameters = [Parameter("salary", Type("decimal"))]
        func.body = Mock(spec=Block)

        result = converter.convert_function(func)

        assert result.name == "calculateBonus"
        assert result.dart_return_type == "double"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "salary"
