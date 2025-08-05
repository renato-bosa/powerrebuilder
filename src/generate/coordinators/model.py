"""Model generation coordinator for database models."""

import logging
from pathlib import Path
from typing import Any

from src.contracts.interfaces import EventType, IEventBus
from src.generate.base import CodeGenerator
from src.generate.converters.data.relationships import RelationshipExtractor
from src.parse.parser.sql import SQLParser

from .base import BaseGenerationCoordinator

logger = logging.getLogger(__name__)


class ModelGenerationCoordinator(BaseGenerationCoordinator):
    """Coordinator for generating database models."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        template_dir: Path | None = None,
        event_bus: IEventBus | None = None,
    ) -> None:
        """Initialize model generation coordinator.

        Args:
            input_dir: Directory containing parsed AST files
            output_dir: Directory for generated models
            template_dir: Directory containing templates
            event_bus: Optional event bus
        """
        super().__init__(input_dir, output_dir, event_bus)

        # Set template directory
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates"

        # Initialize model generator
        self.generator = ModelGenerator(
            str(template_dir), str(self.output_dir), validate_templates=False
        )

        # Initialize helpers
        self.sql_parser = SQLParser()
        self.relationship_extractor = RelationshipExtractor()

    def get_generator_type(self) -> str:
        """Get the type of generator."""
        return "model"

    def generate(self, _config: dict[str, Any]) -> dict[str, Any]:
        """Generate database models from parsed DataWindow files.

        Args:
            config: Generation configuration

        Returns:
            Generation results
        """
        self.publish_event(EventType.STAGE_STARTED, {"stage": "model_generation"})

        try:
            # Find all DataWindow AST files
            datawindow_files = self.find_files("*.srd.ast.json")
            logger.info("Found %s DataWindow files", len(datawindow_files))

            # Extract tables from DataWindows
            tables = self._extract_tables(datawindow_files)

            # Generate models
            results = self._generate_models(tables)

            self.publish_event(
                EventType.STAGE_COMPLETED,
                {"stage": "model_generation", "results": results},
            )

            return results

        except Exception as e:
            self.publish_event(
                EventType.STAGE_FAILED,
                {"stage": "model_generation", "error": str(e)},
            )
            raise

    def _extract_tables(
        self, datawindow_files: list[Path]
    ) -> dict[str, dict[str, Any]]:
        """Extract table information from DataWindow files."""
        tables = {}

        def process_datawindow(dw_file: Path) -> None:
            ast_data = self.read_json_file(dw_file)
            table_name = self.extract_object_name(dw_file, ".srd.ast")

            if table_name not in tables:
                # Extract DataWindow information
                dw_data = self._extract_datawindow_from_ast(ast_data)
                if dw_data:
                    tables[table_name] = {
                        "name": table_name,
                        "columns": dw_data.get("columns", []),
                        "relationships": dw_data.get("relationships", []),
                        "sql": dw_data.get("sql", {}),
                        "primary_keys": dw_data.get("primary_keys", []),
                    }

        # Process all DataWindow files
        self.process_files(datawindow_files, process_datawindow, "datawindow")

        return tables

    def _generate_models(self, tables: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Generate model files for extracted tables."""
        results = {"models_generated": 0, "files": []}

        for table in tables.values():
            try:
                self.generator.generate_model(
                    table["name"], table["columns"], table.get("relationships")
                )

                model_file = f"models/{table['name'].lower()}.py"
                results["models_generated"] += 1
                results["files"].append(model_file)

                logger.info("Generated model for %s", table["name"])

            except Exception as e:
                logger.error("Failed to generate model for %s: %s", table["name"], e)

        return results

    def _extract_datawindow_from_ast(
        self, ast_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Extract DataWindow information from AST."""
        # Import the extraction function from the original coordinator
        from src.generate.coordinator import extract_datawindow_from_ast

        return extract_datawindow_from_ast(ast_data)


class ModelGenerator(CodeGenerator):
    """Generate SQLModel models from PowerBuilder schema."""

    def generate_model(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
        relationships: list[dict[str, Any]] | None = None,
    ) -> None:
        """Generate a SQLModel model for a table.

        Args:
            table_name: Name of the table
            columns: List of column definitions
            relationships: Optional list of relationship definitions
        """
        context = {
            "table_name": table_name,
            "columns": columns,
            "relationships": relationships or [],
        }
        content = self.render_template("sqlmodel_model.jinja2", context)
        self.write_file(f"models/{table_name.lower()}.py", content)
