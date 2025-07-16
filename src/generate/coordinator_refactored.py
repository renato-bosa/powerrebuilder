"""Refactored Generate Coordinator using dependency injection.

This coordinator delegates responsibilities to specialized services:
- AST extraction and analysis
- Generator factory for creating specific generators
- UI processing and layout generation
- Event processing and wiring
- Project scaffolding
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.contracts.generators import (
    IASTExtractor,
    IEventProcessor,
    IGeneratorFactory,
    IGeneratorCoordinator,
    IProjectScaffolder,
    IUIProcessor
)

logger = logging.getLogger(__name__)


class GenerateCoordinator(IGeneratorCoordinator):
    """Coordinates code generation using injected services."""
    
    def __init__(
        self,
        ast_extractor: IASTExtractor,
        generator_factory: IGeneratorFactory,
        ui_processor: IUIProcessor,
        event_processor: IEventProcessor,
        project_scaffolder: IProjectScaffolder
    ):
        """Initialize the coordinator with injected services.
        
        Args:
            ast_extractor: Service for extracting information from AST
            generator_factory: Factory for creating generators
            ui_processor: Service for processing UI elements
            event_processor: Service for processing events
            project_scaffolder: Service for creating project structure
        """
        self.ast_extractor = ast_extractor
        self.generator_factory = generator_factory
        self.ui_processor = ui_processor
        self.event_processor = event_processor
        self.project_scaffolder = project_scaffolder
        
        self._generators = {}
        self._stats = {
            "models_generated": 0,
            "services_generated": 0,
            "ui_components_generated": 0,
            "files_created": 0,
            "errors": []
        }
    
    def generate(
        self, 
        input_dir: Path, 
        output_dir: Path, 
        target: str = "flutter"
    ) -> Dict[str, Any]:
        """Coordinate the generation process.
        
        Args:
            input_dir: Directory containing model files
            output_dir: Directory for generated output
            target: Target framework
            
        Returns:
            Generation statistics
        """
        logger.info("Starting generation: %s -> %s (target: %s)", 
                   input_dir, output_dir, target)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize project structure
        project_name = input_dir.name.replace('_models', '')
        project_info = self._initialize_project(project_name, target, output_dir)
        
        # Process model files
        model_files = list(input_dir.glob("*.json"))
        logger.info("Found %d model files to process", len(model_files))
        
        # Collect all models first for relationship analysis
        all_models = {}
        for model_file in model_files:
            try:
                model_data = self._load_model_file(model_file)
                all_models[model_file.stem] = model_data
            except Exception as e:
                logger.error("Failed to load %s: %s", model_file, e)
                self._stats["errors"].append(str(e))
        
        # Generate code for each model
        for model_name, model_data in all_models.items():
            try:
                self._generate_for_model(
                    model_name, 
                    model_data, 
                    all_models,
                    project_info['project_root'],
                    target
                )
            except Exception as e:
                logger.error("Failed to generate %s: %s", model_name, e)
                self._stats["errors"].append(str(e))
        
        # Generate project-level files
        self._generate_project_files(
            project_info['project_root'],
            all_models,
            target
        )
        
        # Write generation report
        self._write_generation_report(output_dir)
        
        logger.info("Generation complete: %s", self._stats)
        return self._stats
    
    def register_generator(self, generator: Any) -> None:
        """Register a custom generator.
        
        Args:
            generator: Generator instance
        """
        target = generator.get_target_name()
        self._generators[target] = generator
        logger.debug("Registered generator for target: %s", target)
    
    def get_generators(self) -> List[Any]:
        """Get all registered generators.
        
        Returns:
            List of generators
        """
        return list(self._generators.values())
    
    def get_generator(self, target: str) -> Optional[Any]:
        """Get a specific generator by target.
        
        Args:
            target: Target framework
            
        Returns:
            Generator instance or None
        """
        return self._generators.get(target)
    
    # Private helper methods
    
    def _initialize_project(
        self, 
        project_name: str, 
        target: str, 
        output_dir: Path
    ) -> Dict[str, Any]:
        """Initialize project structure."""
        logger.info("Initializing %s project: %s", target, project_name)
        
        # Create project structure
        project_info = self.project_scaffolder.create_project_structure(
            project_name,
            target,
            output_dir
        )
        
        # Generate configuration files
        config = {
            'framework': target,
            'project_name': project_name,
            'dependencies': self._get_default_dependencies(target)
        }
        
        config_files = self.project_scaffolder.generate_config_files(
            Path(project_info['project_root']),
            config
        )
        
        project_info['config_files'] = config_files
        self._stats['files_created'] += len(project_info['files']) + len(config_files)
        
        return project_info
    
    def _load_model_file(self, model_file: Path) -> Dict[str, Any]:
        """Load and parse a model file."""
        with open(model_file, 'r') as f:
            return json.load(f)
    
    def _generate_for_model(
        self,
        model_name: str,
        model_data: Dict[str, Any],
        all_models: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for a single model."""
        logger.debug("Generating code for model: %s", model_name)
        
        # Determine model type
        model_type = self._determine_model_type(model_data)
        
        if model_type == 'datawindow':
            self._generate_datawindow(model_name, model_data, project_root, target)
        elif model_type == 'window':
            self._generate_window(model_name, model_data, project_root, target)
        elif model_type == 'application':
            self._generate_application(model_name, model_data, project_root, target)
        elif model_type == 'menu':
            self._generate_menu(model_name, model_data, project_root, target)
        elif model_type == 'userobject':
            self._generate_userobject(model_name, model_data, project_root, target)
        else:
            # Generate as generic model
            self._generate_generic_model(model_name, model_data, project_root, target)
    
    def _determine_model_type(self, model_data: Dict[str, Any]) -> str:
        """Determine the type of model."""
        # Check explicit type
        if 'type' in model_data:
            return model_data['type'].lower()
        
        # Check by properties
        if 'columns' in model_data or 'sql' in model_data:
            return 'datawindow'
        elif 'controls' in model_data or 'layout' in model_data:
            return 'window'
        elif 'windows' in model_data and 'libraries' in model_data:
            return 'application'
        elif 'menuitems' in model_data or 'items' in model_data:
            return 'menu'
        
        return 'unknown'
    
    def _generate_datawindow(
        self,
        name: str,
        model_data: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for a DataWindow."""
        # Extract DataWindow information
        dw_info = self.ast_extractor.extract_datawindow_from_ast(model_data)
        
        # Create model generator
        config = {'output_dir': project_root}
        model_generator = self.generator_factory.create_model_generator(config)
        
        # Generate data model
        model_path = Path(project_root) / 'src' / 'models' / f'{name}.py'
        model_generator.generate_model(dw_info, model_path)
        self._stats['models_generated'] += 1
        
        # Generate service
        service_generator = self.generator_factory.create_service_generator(config)
        service_path = Path(project_root) / 'src' / 'services' / f'{name}_service.py'
        service_generator.generate_service(dw_info, service_path)
        self._stats['services_generated'] += 1
        
        # Generate UI component if applicable
        if target in ['flutter', 'web', 'python']:
            ui_generator = self.generator_factory.create_ui_generator(target, config)
            ui_path = self._get_ui_path(project_root, target, f'{name}_view')
            ui_generator.generate_datawindow_ui(dw_info, ui_path)
            self._stats['ui_components_generated'] += 1
    
    def _generate_window(
        self,
        name: str,
        model_data: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for a Window."""
        # Extract window information
        window_info = self.ast_extractor.extract_window_from_ast(model_data)
        
        # Process controls
        controls = model_data.get('controls', [])
        processed_controls = self.ui_processor.process_controls(controls)
        
        # Generate layout
        layout = self.ui_processor.generate_layout(processed_controls)
        
        # Extract and process events
        events = model_data.get('events', [])
        processed_events = self.event_processor.process_events(events)
        
        # Extract event handlers
        event_handlers = self.event_processor.extract_event_handlers(model_data)
        
        # Wire events
        event_wiring = self.event_processor.wire_events(
            processed_controls,
            event_handlers
        )
        
        # Extract menus
        menus = self.ui_processor.extract_menus(model_data)
        
        # Generate UI component
        if target in ['flutter', 'web', 'python']:
            config = {'output_dir': project_root}
            ui_generator = self.generator_factory.create_ui_generator(target, config)
            
            window_context = {
                'name': name,
                'controls': processed_controls,
                'layout': layout,
                'events': processed_events,
                'event_wiring': event_wiring,
                'menus': menus,
                'params': window_info['params']
            }
            
            ui_path = self._get_ui_path(project_root, target, f'{name}_screen')
            ui_generator.generate_window_ui(window_context, ui_path)
            self._stats['ui_components_generated'] += 1
    
    def _generate_application(
        self,
        name: str,
        model_data: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for an Application."""
        # Generate main application file
        config = {'output_dir': project_root}
        
        if target == 'flutter':
            # Already generated in project scaffolding
            pass
        elif target == 'python':
            # Update main.py with application logic
            main_path = Path(project_root) / 'main.py'
            self._update_main_file(main_path, model_data)
        elif target == 'web':
            # Update index.js with application logic
            index_path = Path(project_root) / 'src' / 'index.js'
            self._update_index_file(index_path, model_data)
    
    def _generate_menu(
        self,
        name: str,
        model_data: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for a Menu."""
        # Process menu items
        menu_items = model_data.get('menuitems', model_data.get('items', []))
        
        if target in ['flutter', 'web', 'python']:
            config = {'output_dir': project_root}
            ui_generator = self.generator_factory.create_ui_generator(target, config)
            
            menu_context = {
                'name': name,
                'items': menu_items
            }
            
            ui_path = self._get_ui_path(project_root, target, f'{name}_menu')
            ui_generator.generate_menu_ui(menu_context, ui_path)
            self._stats['ui_components_generated'] += 1
    
    def _generate_userobject(
        self,
        name: str,
        model_data: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for a UserObject."""
        # UserObjects are custom components
        # Treat them similar to windows but as reusable widgets
        controls = model_data.get('controls', [])
        processed_controls = self.ui_processor.process_controls(controls)
        layout = self.ui_processor.generate_layout(processed_controls)
        
        if target in ['flutter', 'web', 'python']:
            config = {'output_dir': project_root}
            ui_generator = self.generator_factory.create_ui_generator(target, config)
            
            widget_context = {
                'name': name,
                'controls': processed_controls,
                'layout': layout,
                'properties': model_data.get('properties', {})
            }
            
            ui_path = self._get_ui_path(project_root, target, f'{name}_widget')
            ui_generator.generate_widget_ui(widget_context, ui_path)
            self._stats['ui_components_generated'] += 1
    
    def _generate_generic_model(
        self,
        name: str,
        model_data: Dict[str, Any],
        project_root: str,
        target: str
    ) -> None:
        """Generate code for a generic model."""
        # Extract methods
        methods = self.ast_extractor.extract_methods_from_ast(model_data)
        
        # Generate as a service class
        config = {'output_dir': project_root}
        service_generator = self.generator_factory.create_service_generator(config)
        
        service_context = {
            'name': name,
            'methods': methods,
            'properties': model_data.get('properties', {})
        }
        
        service_path = Path(project_root) / 'src' / 'services' / f'{name}.py'
        service_generator.generate_class(service_context, service_path)
        self._stats['services_generated'] += 1
    
    def _generate_project_files(
        self,
        project_root: str,
        all_models: Dict[str, Any],
        target: str
    ) -> None:
        """Generate project-level files."""
        # Extract module names
        modules = []
        for model_name, model_data in all_models.items():
            model_type = self._determine_model_type(model_data)
            if model_type == 'datawindow':
                modules.append(f'models/{model_name}')
                modules.append(f'services/{model_name}_service')
            elif model_type == 'window':
                modules.append(f'ui/{model_name}_screen')
            elif model_type == 'menu':
                modules.append(f'ui/{model_name}_menu')
        
        # Create boilerplate files
        boilerplate = self.project_scaffolder.create_boilerplate_files(
            Path(project_root),
            list(set(m.split('/')[0] for m in modules))
        )
        
        self._stats['files_created'] += len(boilerplate)
    
    def _get_ui_path(self, project_root: str, target: str, component_name: str) -> Path:
        """Get the appropriate UI path for the target framework."""
        if target == 'flutter':
            return Path(project_root) / 'lib' / 'screens' / f'{component_name}.dart'
        elif target == 'python':
            return Path(project_root) / 'src' / 'ui' / f'{component_name}.py'
        elif target == 'web':
            return Path(project_root) / 'src' / 'components' / f'{component_name}.js'
        else:
            return Path(project_root) / 'src' / 'ui' / f'{component_name}'
    
    def _get_default_dependencies(self, target: str) -> List[str]:
        """Get default dependencies for the target framework."""
        if target == 'python':
            return [
                'sqlmodel>=0.0.14',
                'pydantic>=2.0',
                'httpx>=0.25.0',
                'typer>=0.9.0',
                'rich>=13.0'
            ]
        elif target == 'flutter':
            return []  # Handled in pubspec.yaml
        elif target == 'web':
            return []  # Handled in package.json
        else:
            return []
    
    def _update_main_file(self, main_path: Path, app_data: Dict[str, Any]) -> None:
        """Update the main.py file with application logic."""
        # This would be implemented to update the main file
        # For now, just log
        logger.debug("Would update main file: %s", main_path)
    
    def _update_index_file(self, index_path: Path, app_data: Dict[str, Any]) -> None:
        """Update the index.js file with application logic."""
        # This would be implemented to update the index file
        # For now, just log
        logger.debug("Would update index file: %s", index_path)
    
    def _write_generation_report(self, output_dir: Path) -> None:
        """Write a generation report."""
        report_path = output_dir / 'generation_report.json'
        
        report = {
            'statistics': self._stats,
            'timestamp': str(Path.ctime(output_dir)),
            'errors': self._stats['errors']
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Generation report written to: %s", report_path)