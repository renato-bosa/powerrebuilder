"""Service generation coordinator for business logic."""

import logging
from pathlib import Path
from typing import Any

from ...contracts.events import EventType, IEventBus
from ..base import CodeGenerator
from .base import BaseGenerationCoordinator

logger = logging.getLogger(__name__)


class ServiceGenerationCoordinator(BaseGenerationCoordinator):
    """Coordinator for generating service layer code."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        template_dir: Path | None = None,
        event_bus: IEventBus | None = None,
        decompiled_dir: Path | None = None,
    ) -> None:
        """Initialize service generation coordinator.

        Args:
            input_dir: Directory containing parsed AST files
            output_dir: Directory for generated services
            template_dir: Directory containing templates
            event_bus: Optional event bus
            decompiled_dir: Optional directory containing decompiled functions
        """
        super().__init__(input_dir, output_dir, event_bus)

        # Set template directory
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates"

        # Initialize service generator
        self.generator = ServiceGenerator(
            str(template_dir), str(self.output_dir), validate_templates=False
        )

        # Set decompiled directory
        self.decompiled_dir = Path(decompiled_dir) if decompiled_dir else None

    def get_generator_type(self) -> str:
        """Get the type of generator."""
        return "service"

    def generate(self, _config: dict[str, Any]) -> dict[str, Any]:
        """Generate services from parsed user objects.

        Args:
            config: Generation configuration

        Returns:
            Generation results
        """
        self.publish_event(EventType.STAGE_STARTED, {"stage": "service_generation"})

        try:
            # Find all user object files
            user_object_files = self.find_files("*.sru.ast.json")

            # Filter for non-UI objects
            service_files = [
                f
                for f in user_object_files
                if not any(prefix in f.stem.lower() for prefix in ["w_", "dw_", "uo_"])
            ]

            logger.info("Found %s service object files", len(service_files))

            # Extract services
            services = self._extract_services(service_files)

            # Generate service files
            results = self._generate_services(services)

            self.publish_event(
                EventType.STAGE_COMPLETED,
                {"stage": "service_generation", "results": results},
            )

            return results

        except Exception as e:
            self.publish_event(
                EventType.STAGE_FAILED,
                {"stage": "service_generation", "error": str(e)},
            )
            raise

    def _extract_services(self, service_files: list[Path]) -> dict[str, dict[str, Any]]:
        """Extract service information from user object files."""
        services = {}

        def process_service(uo_file: Path) -> None:
            ast_data = self.read_json_file(uo_file)
            service_name = self.extract_object_name(uo_file, ".sru.ast")

            if service_name not in services:
                # Extract methods from AST
                methods = self._extract_methods_from_ast(ast_data)

                services[service_name] = {"name": service_name, "methods": methods}

                # Look for decompiled functions if available
                if self.decompiled_dir:
                    fun_file = self.decompiled_dir / f"{service_name}.fun"
                    if fun_file.exists():
                        logger.debug("Found decompiled functions for %s", service_name)
                        decompiled_methods = self._parse_decompiled_functions(fun_file)

                        # Merge with AST methods
                        for method in services[service_name]["methods"]:
                            if method["name"] in decompiled_methods:
                                method["implementation"] = decompiled_methods[
                                    method["name"]
                                ]

        self.process_files(service_files, process_service, "service")

        return services

    def _generate_services(self, services: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Generate service files."""
        results = {"services_generated": 0, "files": []}

        for service in services.values():
            try:
                self.generator.generate_service(service["name"], service["methods"])

                service_file = f"services/{service['name'].lower()}_service.py"
                results["services_generated"] += 1
                results["files"].append(service_file)

                logger.info("Generated service %s", service["name"])

            except Exception as e:
                logger.error("Failed to generate service %s: %s", service["name"], e)

        return results

    def _extract_methods_from_ast(
        self, ast_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract method information from AST."""
        from src.generate.coordinator import extract_methods_from_ast

        return extract_methods_from_ast(ast_data)

    def _parse_decompiled_functions(self, fun_file: Path) -> dict[str, str]:
        """Parse decompiled function file."""
        from src.generate.coordinator import parse_decompiled_functions

        return parse_decompiled_functions(fun_file)


class ServiceGenerator(CodeGenerator):
    """Generate service layer from PowerBuilder business logic."""

    def generate_service(self, name: str, methods: list[dict[str, Any]]) -> None:
        """Generate a service class.

        Args:
            name: Service name
            methods: List of method definitions
        """
        context = {"service_name": name, "methods": methods}
        content = self.render_template("service.jinja2", context)
        self.write_file(f"services/{name.lower()}_service.py", content)
