"""Test fixtures and helpers for PowerRebuilder integration tests.

This module provides realistic test data and helper functions for creating
PowerBuilder artifacts at each stage of the pipeline.
"""

import struct
from pathlib import Path
from typing import Any


class PowerBuilderTestData:
    """Factory for creating realistic PowerBuilder test data."""

    # Sample PowerBuilder opcodes (simplified)
    OPCODES = {
        "PUSH_CONST": 0x31,
        "PUSH_VAR": 0x32,
        "POP_VAR": 0x33,
        "ADD": 0x40,
        "SUB": 0x41,
        "MUL": 0x42,
        "DIV": 0x43,
        "CALL": 0x50,
        "RETURN": 0x20,
        "JUMP": 0x60,
        "JUMP_IF": 0x61,
    }

    @staticmethod
    def create_pbd_file(path: Path, objects: list[dict[str, Any]]) -> None:
        """Create a PBD file with specified objects.

        Args:
            path: Path to create PBD file
            objects: List of objects with 'name', 'type', and 'pcode' keys
        """
        with open(path, "wb") as f:
            # Write header
            f.write(b"HDR*")  # Magic
            f.write(struct.pack("<I", 6))  # Version
            f.write(b"PowerBuilder 6.0".ljust(32, b"\x00"))

            # Write node count
            f.write(b"NOD*")
            f.write(struct.pack("<I", len(objects)))

            # Calculate offsets
            header_size = f.tell() + 4
            node_size = 64  # Fixed size per node
            data_offset = header_size + (node_size * len(objects))

            f.write(struct.pack("<I", header_size))  # Offset to first node

            # Write nodes
            current_data_offset = data_offset
            for obj in objects:
                # Node entry
                f.write(b"ENT*")
                f.write(obj["name"].encode("utf-8").ljust(32, b"\x00"))
                f.write(obj["type"].encode("utf-8").ljust(16, b"\x00"))
                f.write(struct.pack("<I", current_data_offset))
                f.write(struct.pack("<I", len(obj.get("pcode", b""))))
                current_data_offset += (
                    len(obj.get("pcode", b"")) + 8
                )  # Include DAT header

            # Write data blocks
            for obj in objects:
                f.write(b"DAT*")
                f.write(struct.pack("<I", len(obj.get("pcode", b""))))
                f.write(obj.get("pcode", b""))

    @staticmethod
    def create_pcode_function(name: str, body: list[tuple]) -> bytes:
        """Create P-code for a simple function.

        Args:
            name: Function name
            body: List of (opcode, operand) tuples

        Returns:
            P-code bytes
        """
        pcode = bytearray()

        # Function header (simplified)
        pcode.extend(name.encode("utf-8")[:16].ljust(16, b"\x00"))
        pcode.extend(struct.pack("<I", len(body)))  # Instruction count

        # Function body
        for opcode, operand in body:
            if isinstance(opcode, str):
                opcode = PowerBuilderTestData.OPCODES.get(opcode, 0)
            pcode.append(opcode)
            pcode.append(0)  # Flags
            if operand is not None:
                pcode.extend(struct.pack("<H", operand))
            else:
                pcode.extend(b"\x00\x00")

        return bytes(pcode)

    @staticmethod
    def create_sru_window(name: str, controls: list[dict[str, Any]]) -> str:
        """Create a PowerBuilder window source file.

        Args:
            name: Window name
            controls: List of control definitions

        Returns:
            SRU file content
        """
        lines = [
            "forward",
            f"global type {name} from window",
        ]

        # Forward declare controls
        for ctrl in controls:
            lines.append(f"type {ctrl['name']} from {ctrl['type']} within {name}")
        lines.append("end type")
        lines.append("end forward")
        lines.append("")

        # Window definition
        lines.append(f"global type {name} from window")
        lines.append("    integer width = 2000")
        lines.append("    integer height = 1200")
        lines.append("    boolean titlebar = true")
        lines.append('    string title = "Test Window"')

        # Control declarations
        for ctrl in controls:
            lines.append(f"    {ctrl['name']} {ctrl['name']}")
        lines.append("end type")
        lines.append(f"global {name} {name}")
        lines.append("")

        # Control implementations
        for ctrl in controls:
            lines.append(f"type {ctrl['name']} from {ctrl['type']} within {name}")
            lines.append(f"    integer x = {ctrl.get('x', 10)}")
            lines.append(f"    integer y = {ctrl.get('y', 10)}")
            lines.append(f"    integer width = {ctrl.get('width', 400)}")
            lines.append(f"    integer height = {ctrl.get('height', 100)}")
            if ctrl["type"] == "commandbutton":
                lines.append(f'    string text = "{ctrl.get("text", "Button")}"')
            elif ctrl["type"] == "singlelineedit":
                lines.append("    integer textsize = -10")
                lines.append('    string facename = "Arial"')
            lines.append("end type")
            lines.append("")

            # Add events
            for event in ctrl.get("events", []):
                lines.append(f"event {ctrl['name']}::{event['name']};")
                for stmt in event.get("statements", []):
                    lines.append(f"    {stmt}")
                lines.append("end event")
                lines.append("")

        # Window events
        lines.append(f"on {name}.create")
        for ctrl in controls:
            lines.append(f"    this.{ctrl['name']}=create {ctrl['name']}")
        lines.append(
            "    this.Control[]={"
            + ",".join(f"this.{c['name']}" for c in controls)
            + "}"
        )
        lines.append("end on")
        lines.append("")
        lines.append(f"on {name}.destroy")
        for ctrl in controls:
            lines.append(f"    destroy(this.{ctrl['name']})")
        lines.append("end on")

        return "\n".join(lines)

    @staticmethod
    def create_sru_datawindow(
        name: str, sql: str, columns: list[dict[str, Any]]
    ) -> str:
        """Create a PowerBuilder DataWindow source file.

        Args:
            name: DataWindow name
            sql: SQL SELECT statement
            columns: List of column definitions

        Returns:
            SRU file content
        """
        lines = [
            "release 8;",
            'datawindow(units=0 timer_interval=0 color=1073741824 processing=1 HTMLDW=no print.printername="" print.documentname="" print.orientation = 0)',
            'header(height=72 color="536870912" )',
            'summary(height=0 color="536870912" )',
            'footer(height=0 color="536870912" )',
            'detail(height=84 color="536870912" )',
        ]

        # Table definition
        table_parts = []
        for col in columns:
            col_def = f'column=(type={col["type"]} updatewhereclause=yes name={col["name"]} dbname="{col["dbname"]}")'
            table_parts.append(col_def)

        lines.append("table(" + " ".join(table_parts))
        lines.append(f' retrieve="{sql}" )')

        # Column controls
        x_pos = 10
        for col in columns:
            lines.append(
                f'column(band=detail id={columns.index(col) + 1} alignment="0" tabsequence={columns.index(col) + 1}0 border="0" color="33554432" x="{x_pos}" y="4" height="76" width="{col.get("width", 274)}" format="[general]" html.valueishtml="0"  name={col["name"]} visible="1" edit.limit=0 edit.case=any edit.autoselect=yes edit.autohscroll=yes  font.face="Arial" font.height="-10" font.weight="400" font.pitch="2" font.charset="0" background.mode="1" background.color="536870912" )'
            )
            x_pos += col.get("width", 274) + 10

        return "\n".join(lines)

    @staticmethod
    def create_sru_nonvisual(
        name: str, variables: list[dict], methods: list[dict]
    ) -> str:
        """Create a PowerBuilder non-visual object source file.

        Args:
            name: Object name
            variables: List of variable definitions
            methods: List of method definitions

        Returns:
            SRU file content
        """
        lines = [
            "forward",
            f"global type {name} from nonvisualobject",
            "end type",
            "end forward",
            "",
            f"global type {name} from nonvisualobject",
            "end type",
            f"global {name} {name}",
            "",
        ]

        # Variables
        if variables:
            lines.append("type variables")
            for var in variables:
                visibility = var.get("visibility", "")
                if visibility:
                    visibility += " "
                init = ""
                if "initial_value" in var:
                    if var["type"] == "string":
                        init = f' = "{var["initial_value"]}"'
                    else:
                        init = f" = {var['initial_value']}"
                lines.append(f"    {visibility}{var['type']} {var['name']}{init}")
            lines.append("end variables")
            lines.append("")

        # Forward prototypes
        if methods:
            lines.append("forward prototypes")
            for method in methods:
                visibility = method.get("visibility", "public")
                return_type = method.get("return_type", "integer")
                params = ", ".join(
                    f"{p['type']} {p['name']}" for p in method.get("parameters", [])
                )
                if method.get("is_function", True):
                    lines.append(
                        f"{visibility} function {return_type} {method['name']} ({params})"
                    )
                else:
                    lines.append(f"{visibility} subroutine {method['name']} ({params})")
            lines.append("end prototypes")
            lines.append("")

        # Method implementations
        for method in methods:
            visibility = method.get("visibility", "public")
            return_type = method.get("return_type", "integer")
            params = ", ".join(
                f"{p['type']} {p['name']}" for p in method.get("parameters", [])
            )

            if method.get("is_function", True):
                lines.append(
                    f"{visibility} function {return_type} {method['name']} ({params});"
                )
            else:
                lines.append(f"{visibility} subroutine {method['name']} ({params});")

            # Method body
            for stmt in method.get("body", []):
                lines.append(f"    {stmt}")

            if method.get("is_function", True):
                lines.append("end function")
            else:
                lines.append("end subroutine")
            lines.append("")

        # Object events
        lines.append(f"on {name}.create")
        lines.append("    call super::create")
        lines.append('    TriggerEvent( this, "constructor" )')
        lines.append("end on")
        lines.append("")
        lines.append(f"on {name}.destroy")
        lines.append('    TriggerEvent( this, "destructor" )')
        lines.append("    call super::destroy")
        lines.append("end on")

        return "\n".join(lines)

    @staticmethod
    def create_ast_json(pb_type: str, name: str, **kwargs) -> dict[str, Any]:
        """Create an AST JSON structure for a PowerBuilder object.

        Args:
            pb_type: PowerBuilder object type (Window, DataWindow, etc.)
            name: Object name
            **kwargs: Additional properties for the AST

        Returns:
            AST dictionary
        """
        ast = {
            "type": pb_type,
            "name": name,
            "source_file": f"{name}.sru",
            "position": {"line": 1, "column": 1},
        }

        if pb_type == "Window":
            ast.update(
                {
                    "properties": kwargs.get(
                        "properties",
                        {"width": 2000, "height": 1200, "title": "Test Window"},
                    ),
                    "controls": kwargs.get("controls", []),
                    "events": kwargs.get("events", []),
                }
            )
        elif pb_type == "DataWindow":
            ast.update(
                {
                    "sql": kwargs.get("sql", {}),
                    "columns": kwargs.get("columns", []),
                    "controls": kwargs.get("controls", []),
                    "processing": kwargs.get("processing", 1),
                }
            )
        elif pb_type == "NonVisualObject":
            ast.update(
                {
                    "variables": kwargs.get("variables", []),
                    "methods": kwargs.get("methods", []),
                    "events": kwargs.get("events", []),
                }
            )

        return ast

    @staticmethod
    def create_model_json(ast: dict[str, Any]) -> dict[str, Any]:
        """Transform an AST into a semantic model.

        Args:
            ast: AST dictionary

        Returns:
            Model dictionary
        """
        model = {
            "type": ast["type"],
            "name": ast["name"],
            "namespace": "test",
            "source_file": ast.get("source_file"),
            "metadata": {"created": "2024-01-01T00:00:00Z", "version": "1.0"},
        }

        if ast["type"] == "Window":
            model["ui_definition"] = {
                "properties": ast.get("properties", {}),
                "controls": [],
            }

            # Transform controls
            for ctrl in ast.get("controls", []):
                model_ctrl = {
                    "type": ctrl["type"],
                    "name": ctrl["name"],
                    "properties": ctrl.get("properties", {}),
                    "events": [],
                }

                # Transform events
                for event in ctrl.get("events", []):
                    model_ctrl["events"].append(
                        {
                            "name": event["name"],
                            "handler": f"on_{ctrl['name']}_{event['name']}",
                        }
                    )

                model["ui_definition"]["controls"].append(model_ctrl)

        elif ast["type"] == "DataWindow":
            model["data_definition"] = {
                "sql": ast.get("sql", {}),
                "columns": ast.get("columns", []),
                "relationships": [],
            }

            # Infer relationships from foreign key columns
            for col in ast.get("columns", []):
                if col["name"].endswith("_id") and col["name"] != "id":
                    table_name = col["name"][:-3]  # Remove _id
                    model["data_definition"]["relationships"].append(
                        {
                            "type": "belongs_to",
                            "target": table_name,
                            "foreign_key": col["name"],
                        }
                    )

        elif ast["type"] == "NonVisualObject":
            model["attributes"] = []
            model["methods"] = []

            # Transform variables to attributes
            for var in ast.get("variables", []):
                model["attributes"].append(
                    {
                        "name": var["name"],
                        "type": var["datatype"],
                        "visibility": var.get("visibility", "private"),
                        "initial_value": var.get("initial_value"),
                    }
                )

            # Transform methods
            for method in ast.get("methods", []):
                model["methods"].append(
                    {
                        "name": method["name"],
                        "visibility": method.get("visibility", "public"),
                        "return_type": method.get("returns", "void"),
                        "parameters": method.get("parameters", []),
                        "implementation": {
                            "type": "powerbuilder",
                            "body": method.get("body", []),
                        },
                    }
                )

        return model


class TestDataGenerator:
    """Generate comprehensive test data sets for integration testing."""

    @staticmethod
    def create_simple_application(root_dir: Path) -> None:
        """Create a simple but complete PowerBuilder application structure."""
        # Create directories
        (root_dir / "pbls").mkdir(exist_ok=True)
        (root_dir / "source").mkdir(exist_ok=True)

        # Create application object
        app_sru = PowerBuilderTestData.create_sru_nonvisual(
            "test_app",
            variables=[
                {
                    "type": "string",
                    "name": "is_app_name",
                    "initial_value": "Test Application",
                }
            ],
            methods=[
                {
                    "name": "open",
                    "return_type": "integer",
                    "body": ["// Application startup", "Open(w_main)", "return 1"],
                }
            ],
        )
        (root_dir / "source" / "test_app.sra").write_text(app_sru)

        # Create main window
        window_sru = PowerBuilderTestData.create_sru_window(
            "w_main",
            controls=[
                {
                    "name": "cb_process",
                    "type": "commandbutton",
                    "x": 100,
                    "y": 100,
                    "text": "Process",
                    "events": [
                        {
                            "name": "clicked",
                            "statements": [
                                'MessageBox("Info", "Processing...")',
                                "n_processor ln_proc",
                                "ln_proc = CREATE n_processor",
                                "ln_proc.of_process()",
                                "DESTROY ln_proc",
                            ],
                        }
                    ],
                },
                {
                    "name": "sle_input",
                    "type": "singlelineedit",
                    "x": 100,
                    "y": 250,
                    "width": 600,
                },
            ],
        )
        (root_dir / "source" / "w_main.srw").write_text(window_sru)

        # Create business logic object
        processor_sru = PowerBuilderTestData.create_sru_nonvisual(
            "n_processor",
            variables=[
                {"type": "integer", "name": "ii_count", "visibility": "private"},
                {"type": "string", "name": "is_status", "visibility": "protected"},
            ],
            methods=[
                {
                    "name": "of_process",
                    "return_type": "integer",
                    "visibility": "public",
                    "body": [
                        "ii_count = ii_count + 1",
                        'is_status = "Processing"',
                        "return ii_count",
                    ],
                },
                {
                    "name": "of_reset",
                    "is_function": False,
                    "visibility": "public",
                    "body": ["ii_count = 0", 'is_status = "Ready"'],
                },
            ],
        )
        (root_dir / "source" / "n_processor.sru").write_text(processor_sru)

        # Create DataWindow
        dw_sru = PowerBuilderTestData.create_sru_datawindow(
            "d_employee_list",
            "SELECT emp_id, emp_name, dept_id, salary FROM employee WHERE status = 'A' ORDER BY emp_name",
            columns=[
                {"name": "emp_id", "type": "number", "dbname": "employee.emp_id"},
                {"name": "emp_name", "type": "char(50)", "dbname": "employee.emp_name"},
                {"name": "dept_id", "type": "number", "dbname": "employee.dept_id"},
                {
                    "name": "salary",
                    "type": "decimal(10,2)",
                    "dbname": "employee.salary",
                },
            ],
        )
        (root_dir / "source" / "d_employee_list.srd").write_text(dw_sru)

        # Create PBD with compiled objects
        objects = []
        for name in ["test_app", "w_main", "n_processor", "d_employee_list"]:
            # Create simple P-code
            if name == "n_processor":
                pcode = PowerBuilderTestData.create_pcode_function(
                    "of_process",
                    [
                        ("PUSH_VAR", 0),  # ii_count
                        ("PUSH_CONST", 1),
                        ("ADD", None),
                        ("POP_VAR", 0),  # ii_count = ii_count + 1
                        ("PUSH_VAR", 0),  # return ii_count
                        ("RETURN", None),
                    ],
                )
            else:
                pcode = PowerBuilderTestData.create_pcode_function(
                    "constructor", [("PUSH_CONST", 0), ("RETURN", None)]
                )

            objects.append({"name": name, "type": "compiled", "pcode": pcode})

        PowerBuilderTestData.create_pbd_file(
            root_dir / "pbls" / "test_app.pbd", objects
        )

    @staticmethod
    def create_complex_inheritance_test(root_dir: Path) -> None:
        """Create test data for inheritance and polymorphism testing."""
        source_dir = root_dir / "source"
        source_dir.mkdir(exist_ok=True)

        # Base class
        base_sru = PowerBuilderTestData.create_sru_nonvisual(
            "n_base",
            variables=[
                {
                    "type": "string",
                    "name": "is_type",
                    "visibility": "protected",
                    "initial_value": "base",
                }
            ],
            methods=[
                {
                    "name": "of_get_type",
                    "return_type": "string",
                    "visibility": "public",
                    "body": ["return is_type"],
                },
                {
                    "name": "of_process",
                    "return_type": "integer",
                    "visibility": "public",
                    "body": ["return 0"],
                },
            ],
        )
        (source_dir / "n_base.sru").write_text(base_sru)

        # Derived class
        derived_sru = """
forward
global type n_derived from n_base
end type
end forward

global type n_derived from n_base
end type
global n_derived n_derived

public function integer of_process();
    // Override parent method
    integer li_result
    li_result = super::of_process()
    return li_result + 10
end function

on n_derived.create
    call super::create
    is_type = "derived"
end on

on n_derived.destroy
    call super::destroy
end on
"""
        (source_dir / "n_derived.sru").write_text(derived_sru)


# Pipeline test scenarios
class PipelineScenarios:
    """Pre-defined test scenarios for pipeline testing."""

    @staticmethod
    def simple_crud_app() -> dict[str, Any]:
        """Scenario: Simple CRUD application."""
        return {
            "name": "Simple CRUD",
            "description": "Basic Create-Read-Update-Delete application",
            "objects": [
                {
                    "type": "DataWindow",
                    "name": "d_customer",
                    "sql": "SELECT * FROM customer",
                    "columns": [
                        {"name": "cust_id", "type": "number"},
                        {"name": "cust_name", "type": "string"},
                        {"name": "email", "type": "string"},
                    ],
                },
                {
                    "type": "Window",
                    "name": "w_customer_list",
                    "controls": [
                        {"type": "datawindow", "name": "dw_list"},
                        {"type": "commandbutton", "name": "cb_new"},
                        {"type": "commandbutton", "name": "cb_edit"},
                        {"type": "commandbutton", "name": "cb_delete"},
                    ],
                },
                {
                    "type": "NonVisualObject",
                    "name": "n_customer_service",
                    "methods": [
                        {"name": "of_retrieve", "return_type": "long"},
                        {"name": "of_save", "return_type": "integer"},
                        {"name": "of_delete", "return_type": "integer"},
                    ],
                },
            ],
        }

    @staticmethod
    def transaction_processing() -> dict[str, Any]:
        """Scenario: Transaction processing with rollback."""
        return {
            "name": "Transaction Processing",
            "description": "Complex transaction handling with error recovery",
            "objects": [
                {
                    "type": "NonVisualObject",
                    "name": "n_transaction_mgr",
                    "methods": [
                        {
                            "name": "of_begin_transaction",
                            "body": ["SQLCA.AutoCommit = FALSE"],
                        },
                        {
                            "name": "of_commit",
                            "body": ["COMMIT;", "return SQLCA.SQLCode"],
                        },
                        {
                            "name": "of_rollback",
                            "body": ["ROLLBACK;", "return SQLCA.SQLCode"],
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def event_driven_ui() -> dict[str, Any]:
        """Scenario: Complex event-driven UI."""
        return {
            "name": "Event-Driven UI",
            "description": "UI with custom events and inter-control communication",
            "objects": [
                {
                    "type": "Window",
                    "name": "w_event_test",
                    "custom_events": ["ue_data_changed", "ue_validation_failed"],
                    "controls": [
                        {
                            "type": "userobject",
                            "name": "uo_validator",
                            "events": [
                                {
                                    "name": "ue_validate",
                                    "triggers": "parent.ue_validation_failed",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
