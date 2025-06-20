"""Documentation generation for PowerBuilder converted code.

This module generates comprehensive documentation for the converted Flutter/Dart 
and Python code based on the PowerBuilder models and conversion mappings.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DocumentationSection:
    """Represents a documentation section."""
    title: str
    content: List[str]
    subsections: List['DocumentationSection'] = None
    code_examples: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.code_examples is None:
            self.code_examples = []
    
    def to_markdown(self, level: int = 1) -> List[str]:
        """Convert section to markdown format."""
        lines = []
        
        # Add title
        lines.append(f"{'#' * level} {self.title}")
        lines.append("")
        
        # Add content
        lines.extend(self.content)
        lines.append("")
        
        # Add code examples
        for example in self.code_examples:
            lines.append(f"```{example.get('language', '')}")
            lines.append(example['code'])
            lines.append("```")
            lines.append("")
        
        # Add subsections
        for subsection in self.subsections:
            lines.extend(subsection.to_markdown(level + 1))
        
        return lines


class DocumentationGenerator:
    """Generates documentation from PowerBuilder models."""
    
    def __init__(self, output_dir: str):
        """Initialize the documentation generator.
        
        Args:
            output_dir: Directory for generated documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_project_documentation(self, project_info: Dict[str, Any]) -> str:
        """Generate overall project documentation.
        
        Args:
            project_info: Complete project information
            
        Returns:
            Path to generated documentation index
        """
        sections = []
        
        # Title section
        project_name = project_info.get('name', 'PowerBuilder Conversion Project')
        sections.append(DocumentationSection(
            title=project_name,
            content=[
                f"Generated from PowerBuilder on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "This documentation covers the converted Flutter/Dart and Python code generated from the original PowerBuilder application."
            ]
        ))
        
        # Overview section
        sections.append(self._create_overview_section(project_info))
        
        # Architecture section
        sections.append(self._create_architecture_section(project_info))
        
        # Models documentation
        if 'models' in project_info:
            sections.append(self._create_models_section(project_info['models']))
        
        # Services documentation
        if 'services' in project_info:
            sections.append(self._create_services_section(project_info['services']))
        
        # UI Components documentation
        if 'ui_components' in project_info:
            sections.append(self._create_ui_section(project_info['ui_components']))
        
        # API documentation
        if 'api_endpoints' in project_info:
            sections.append(self._create_api_section(project_info['api_endpoints']))
        
        # Migration guide
        sections.append(self._create_migration_guide(project_info))
        
        # Write main documentation file
        doc_path = self.output_dir / "README.md"
        self._write_documentation(doc_path, sections)
        
        # Generate additional documentation files
        self._generate_api_reference(project_info)
        self._generate_database_schema_docs(project_info)
        self._generate_ui_component_docs(project_info)
        
        return str(doc_path)
    
    def _create_overview_section(self, project_info: Dict[str, Any]) -> DocumentationSection:
        """Create project overview section."""
        stats = project_info.get('statistics', {})
        
        content = [
            "This project has been converted from PowerBuilder to modern web technologies:",
            "",
            "### Conversion Statistics",
            "",
            f"- **Total Windows/Forms**: {stats.get('total_windows', 0)}",
            f"- **Total User Objects**: {stats.get('total_user_objects', 0)}",
            f"- **Total DataWindows**: {stats.get('total_datawindows', 0)}",
            f"- **Total Database Tables**: {stats.get('total_tables', 0)}",
            f"- **Total Business Functions**: {stats.get('total_functions', 0)}",
            "",
            "### Technology Stack",
            "",
            "**Frontend**: Flutter/Dart",
            "- Material Design UI components",
            "- Reactive state management",
            "- Cross-platform support (iOS, Android, Web)",
            "",
            "**Backend**: Python with Litestar",
            "- RESTful API endpoints",
            "- SQLModel for database ORM",
            "- Pydantic for data validation",
            "",
            "**Database**: PostgreSQL (configurable)",
            "- Migrated from PowerBuilder embedded SQL",
            "- Full transaction support",
            "- Optimized queries"
        ]
        
        return DocumentationSection(
            title="Project Overview",
            content=content
        )
    
    def _create_architecture_section(self, project_info: Dict[str, Any]) -> DocumentationSection:
        """Create architecture documentation section."""
        content = [
            "The converted application follows a modern layered architecture:",
            "",
            "```",
            "┌─────────────────────────────────────┐",
            "│       Flutter Frontend              │",
            "│  ┌─────────────┬─────────────┐     │",
            "│  │   Screens   │   Widgets   │     │",
            "│  └─────────────┴─────────────┘     │",
            "│  ┌─────────────┬─────────────┐     │",
            "│  │   Services  │    Models   │     │",
            "│  └─────────────┴─────────────┘     │",
            "└─────────────────────────────────────┘",
            "                 ↕ HTTP/REST",
            "┌─────────────────────────────────────┐",
            "│       Python Backend                │",
            "│  ┌─────────────┬─────────────┐     │",
            "│  │     API     │   Services  │     │",
            "│  └─────────────┴─────────────┘     │",
            "│  ┌─────────────┬─────────────┐     │",
            "│  │    Models   │     ORM     │     │",
            "│  └─────────────┴─────────────┘     │",
            "└─────────────────────────────────────┘",
            "                 ↕ SQL",
            "┌─────────────────────────────────────┐",
            "│          PostgreSQL DB              │",
            "└─────────────────────────────────────┘",
            "```"
        ]
        
        subsections = [
            DocumentationSection(
                title="Frontend Architecture",
                content=[
                    "The Flutter frontend is organized into:",
                    "",
                    "- **Screens**: Full-page views corresponding to PowerBuilder windows",
                    "- **Widgets**: Reusable UI components from PowerBuilder user objects",
                    "- **Services**: Business logic and API communication",
                    "- **Models**: Data structures matching backend models",
                    "- **Providers**: State management using Provider pattern"
                ]
            ),
            DocumentationSection(
                title="Backend Architecture",
                content=[
                    "The Python backend follows clean architecture principles:",
                    "",
                    "- **API Layer**: RESTful endpoints using Litestar framework",
                    "- **Service Layer**: Business logic migrated from PowerBuilder",
                    "- **Repository Layer**: Database access using SQLModel",
                    "- **Model Layer**: Domain models with validation",
                    "- **Infrastructure**: Cross-cutting concerns (auth, logging, etc.)"
                ]
            )
        ]
        
        return DocumentationSection(
            title="Architecture",
            content=content,
            subsections=subsections
        )
    
    def _create_models_section(self, models: List[Dict[str, Any]]) -> DocumentationSection:
        """Create models documentation section."""
        content = [
            "Database models converted from PowerBuilder DataWindows and embedded SQL."
        ]
        
        subsections = []
        
        for model in models:
            model_content = [
                f"Table: `{model.get('table_name', model['name'].lower())}`",
                "",
                "**Fields:**",
                ""
            ]
            
            # Create fields table
            model_content.extend([
                "| Field | Type | Required | Description |",
                "|-------|------|----------|-------------|"
            ])
            
            for field in model.get('fields', []):
                required = "Yes" if field.get('required', False) else "No"
                description = field.get('description', '-')
                model_content.append(
                    f"| {field['name']} | {field['type']} | {required} | {description} |"
                )
            
            # Add relationships
            if model.get('relationships'):
                model_content.extend([
                    "",
                    "**Relationships:**",
                    ""
                ])
                for rel in model['relationships']:
                    model_content.append(f"- {rel['type']}: {rel['target_model']} via {rel['field']}")
            
            # Add code example
            code_example = {
                'language': 'python',
                'code': self._generate_model_example(model)
            }
            
            subsections.append(DocumentationSection(
                title=model['name'],
                content=model_content,
                code_examples=[code_example]
            ))
        
        return DocumentationSection(
            title="Data Models",
            content=content,
            subsections=subsections
        )
    
    def _create_services_section(self, services: List[Dict[str, Any]]) -> DocumentationSection:
        """Create services documentation section."""
        content = [
            "Business logic services converted from PowerBuilder functions and scripts."
        ]
        
        subsections = []
        
        for service in services:
            service_content = [
                service.get('description', 'Business logic service'),
                "",
                "**Methods:**",
                ""
            ]
            
            for method in service.get('methods', []):
                params = ', '.join([f"{p['name']}: {p['type']}" 
                                  for p in method.get('parameters', [])])
                service_content.append(
                    f"- `{method['name']}({params})` -> {method.get('return_type', 'None')}"
                )
                if method.get('description'):
                    service_content.append(f"  - {method['description']}")
            
            subsections.append(DocumentationSection(
                title=f"{service['name']} Service",
                content=service_content
            ))
        
        return DocumentationSection(
            title="Services",
            content=content,
            subsections=subsections
        )
    
    def _create_ui_section(self, ui_components: List[Dict[str, Any]]) -> DocumentationSection:
        """Create UI components documentation section."""
        content = [
            "UI components converted from PowerBuilder windows and user objects."
        ]
        
        subsections = []
        
        # Group by type
        screens = [c for c in ui_components if c.get('type') == 'screen']
        widgets = [c for c in ui_components if c.get('type') == 'widget']
        
        if screens:
            screen_content = ["Main application screens:"]
            for screen in screens:
                screen_content.append(f"- **{screen['name']}**: {screen.get('description', 'Application screen')}")
            
            subsections.append(DocumentationSection(
                title="Screens",
                content=screen_content
            ))
        
        if widgets:
            widget_content = ["Reusable UI components:"]
            for widget in widgets:
                widget_content.append(f"- **{widget['name']}**: {widget.get('description', 'UI widget')}")
            
            subsections.append(DocumentationSection(
                title="Widgets",
                content=widget_content
            ))
        
        return DocumentationSection(
            title="UI Components",
            content=content,
            subsections=subsections
        )
    
    def _create_api_section(self, endpoints: List[Dict[str, Any]]) -> DocumentationSection:
        """Create API documentation section."""
        content = [
            "RESTful API endpoints for client-server communication."
        ]
        
        subsections = []
        
        # Group endpoints by resource
        resources = {}
        for endpoint in endpoints:
            resource = endpoint.get('resource', 'general')
            if resource not in resources:
                resources[resource] = []
            resources[resource].append(endpoint)
        
        for resource, resource_endpoints in resources.items():
            resource_content = []
            
            for endpoint in resource_endpoints:
                resource_content.extend([
                    f"### {endpoint['method']} {endpoint['path']}",
                    "",
                    endpoint.get('description', 'API endpoint'),
                    ""
                ])
                
                if endpoint.get('request_body'):
                    resource_content.extend([
                        "**Request Body:**",
                        "```json",
                        json.dumps(endpoint['request_body'], indent=2),
                        "```",
                        ""
                    ])
                
                if endpoint.get('response'):
                    resource_content.extend([
                        "**Response:**",
                        "```json",
                        json.dumps(endpoint['response'], indent=2),
                        "```",
                        ""
                    ])
            
            subsections.append(DocumentationSection(
                title=f"{resource.title()} Endpoints",
                content=resource_content
            ))
        
        return DocumentationSection(
            title="API Reference",
            content=content,
            subsections=subsections
        )
    
    def _create_migration_guide(self, project_info: Dict[str, Any]) -> DocumentationSection:
        """Create migration guide section."""
        content = [
            "Guide for migrating from the PowerBuilder application to the new system."
        ]
        
        subsections = [
            DocumentationSection(
                title="Data Migration",
                content=[
                    "1. **Export existing data** from PowerBuilder database",
                    "2. **Run migration scripts** in `migrations/` directory",
                    "3. **Verify data integrity** using provided validation scripts",
                    "4. **Update sequences** for auto-increment fields"
                ]
            ),
            DocumentationSection(
                title="Configuration",
                content=[
                    "### Environment Variables",
                    "",
                    "```bash",
                    "# Backend configuration",
                    "DATABASE_URL=postgresql://user:pass@localhost/dbname",
                    "API_HOST=0.0.0.0",
                    "API_PORT=8000",
                    "",
                    "# Frontend configuration",
                    "API_BASE_URL=http://localhost:8000",
                    "```"
                ]
            ),
            DocumentationSection(
                title="Deployment",
                content=[
                    "### Backend Deployment",
                    "",
                    "```bash",
                    "# Install dependencies",
                    "pip install -r requirements.txt",
                    "",
                    "# Run migrations",
                    "alembic upgrade head",
                    "",
                    "# Start server",
                    "uvicorn main:app --reload",
                    "```",
                    "",
                    "### Frontend Deployment",
                    "",
                    "```bash",
                    "# Install dependencies",
                    "flutter pub get",
                    "",
                    "# Build for web",
                    "flutter build web",
                    "",
                    "# Build for mobile",
                    "flutter build apk  # Android",
                    "flutter build ios  # iOS",
                    "```"
                ]
            )
        ]
        
        return DocumentationSection(
            title="Migration Guide",
            content=content,
            subsections=subsections
        )
    
    def _generate_model_example(self, model: Dict[str, Any]) -> str:
        """Generate code example for a model."""
        example = f"""from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class {model['name']}(SQLModel, table=True):
    __tablename__ = "{model.get('table_name', model['name'].lower())}"
    
"""
        
        for field in model.get('fields', []):
            field_type = field['type']
            if not field.get('required', False):
                field_type = f"Optional[{field_type}]"
            
            if field.get('primary_key'):
                example += f"    {field['name']}: {field_type} = Field(primary_key=True)\n"
            elif field.get('foreign_key'):
                example += f"    {field['name']}: {field_type} = Field(foreign_key=\"{field['foreign_key']}\")\n"
            else:
                example += f"    {field['name']}: {field_type}\n"
        
        return example.strip()
    
    def _write_documentation(self, path: Path, sections: List[DocumentationSection]):
        """Write documentation sections to file."""
        lines = []
        
        for section in sections:
            lines.extend(section.to_markdown())
        
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Generated documentation: {path}")
    
    def _generate_api_reference(self, project_info: Dict[str, Any]):
        """Generate detailed API reference documentation."""
        if 'api_endpoints' not in project_info:
            return
        
        sections = [
            DocumentationSection(
                title="API Reference",
                content=["Complete API endpoint documentation"]
            )
        ]
        
        # Add detailed endpoint documentation
        endpoints_section = self._create_api_section(project_info['api_endpoints'])
        sections.append(endpoints_section)
        
        # Write API reference file
        api_path = self.output_dir / "API_REFERENCE.md"
        self._write_documentation(api_path, sections)
    
    def _generate_database_schema_docs(self, project_info: Dict[str, Any]):
        """Generate database schema documentation."""
        if 'models' not in project_info:
            return
        
        sections = [
            DocumentationSection(
                title="Database Schema",
                content=["Complete database schema documentation"]
            )
        ]
        
        # Add ERD diagram if available
        if project_info.get('erd_diagram'):
            sections.append(DocumentationSection(
                title="Entity Relationship Diagram",
                content=[
                    "```mermaid",
                    project_info['erd_diagram'],
                    "```"
                ]
            ))
        
        # Add detailed model documentation
        models_section = self._create_models_section(project_info['models'])
        sections.append(models_section)
        
        # Write schema documentation
        schema_path = self.output_dir / "DATABASE_SCHEMA.md"
        self._write_documentation(schema_path, sections)
    
    def _generate_ui_component_docs(self, project_info: Dict[str, Any]):
        """Generate UI component documentation."""
        if 'ui_components' not in project_info:
            return
        
        sections = [
            DocumentationSection(
                title="UI Component Library",
                content=["Flutter UI components reference"]
            )
        ]
        
        # Add component documentation
        ui_section = self._create_ui_section(project_info['ui_components'])
        sections.append(ui_section)
        
        # Write UI documentation
        ui_path = self.output_dir / "UI_COMPONENTS.md"
        self._write_documentation(ui_path, sections)


def generate_documentation(project_info: Dict[str, Any], output_dir: str) -> str:
    """Generate comprehensive project documentation.
    
    Args:
        project_info: Complete project information including models, services, UI, etc.
        output_dir: Output directory for documentation files
        
    Returns:
        Path to main documentation file
    """
    generator = DocumentationGenerator(output_dir)
    return generator.generate_project_documentation(project_info)