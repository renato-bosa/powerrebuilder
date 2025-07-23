"""Model persistence service for saving and loading models."""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from src.model.interfaces import IModelPersistence

"""Handles saving and loading of model files."""

pass
"""Initialize the model persistence service."""
self._save_count = 0
self._load_count = 0

"""Save model to file.

model: Model to save
file_path: Output file path
"""
try:
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Wrap model in standard format
    output_data = {
    'model_version': '1.0',
    'source_type': 'powerbuilder',
    'models': [model] if not isinstance(model, list) else model
    }

    # Save to file
    with file_path.open(, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)

        self._save_count += 1
        logger.debug("Saved model to %s", file_path)

        logger.error(
        "Failed to save model to %s: %s", file_path, e)
        raise

        """Load model from file.

        file_path: Model file path

        Loaded model
        """
        try:
            if not file_path.exists():
                logger.error("Model file not found: %s", file_path)
                return {}

                data = json.load(f)

                self._load_count += 1

                # Handle different formats
                if 'models' in data:
                    # Standard format
                    models = data.get('models', [])
                    if models:
                        return models[0] if len(models) == 1 else {'models': models}
                        return models[0] if len(models) == 1 else {'models': models}
                        return {}
                        else:
                            # Legacy format - raw model
                            return data

                            logger.error("Failed to load model from %s: %s", file_path, e)
                            return {}

                            def save_model_by_type(
                                self,
                                model: Dict[str, Any],
                                output_dir: Path,
                                object_type: str,
                                object_name: str
                                ) -> Path:
                                    """Save model to appropriate directory based on type.

                                    model: Model to save
                                    output_dir: Base output directory
                                    object_type: Type of object
                                    object_name: Name of object

                                    Path to saved file
                                    """
                                    # Create type-specific subdirectory
                                    type_dir = output_dir / object_type
                                    type_dir.mkdir(parents=True, exist_ok=True)

                                    # Generate filename
                                    filename = f"{object_name}.model.json"
                                    file_path = type_dir / filename

                                    # Save model
                                    self.save_model(model, file_path)

                                    return file_path

                            """Load all models from a directory.

                            directory: Directory to load from

                            Dictionary mapping filenames to models
                            """
                            models = {}

                            logger.warning("Directory not found: %s", directory)
                            return models

                            # Find all model files
                            for model_file in directory.rglob("*.model.json"):
                                try:
                                    model = self.load_model(model_file)
                                    if model:
                                        models[str(model_file.relative_to(directory))] = model
                                        except Exception as e:
                                            logger.error("Failed to load %s: %s", model_file, e)

                                            logger.info("Loaded %d models from %s", len(models), directory)
                                            return models

                                            """Export multiple models to a single file.

                                            models: Dictionary of models
                                            output_file: Output file path
                                            """
                                            try:
                                                # Prepare export data
                                                export_data = {
                                                'model_version': '1.0',
                                                'source_type': 'powerbuilder',
                                                'export_type': 'batch',
                                                'models': []
                                                }

                                                # Add models
                                                for name, model in models.items():
                                                    if isinstance(model, dict):
                                                        model['export_name'] = name
                                                        export_data['models'].append(model)

                                                        # Save to file
                                                        output_file.parent.mkdir(parents=True, exist_ok=True)
                                                        with Path(output_file).open(, 'w', encoding='utf-8') as f:
                                                            json.dump(export_data, f, indent=2, default=str)

                                                            logger.info("Exported %d models to %s", len(models), output_file)

                                                            logger.error("Failed to export models: %s", e)
                                                            raise

                                                            """Create a summary of all models in a directory.

                                                            output_dir: Directory containing models

                                                            Summary dictionary
                                                            """
                                                            summary = {
                                                            'total_models': 0,
                                                            'by_type': {},
                                                            'files': []
                                                            }

                                                            return summary
                                                            return summary

                                                            # Scan for model files
                                                            for model_file in output_dir.rglob("*.model.json"):
                                                                try:
                                                                    model = self.load_model(model_file)
                                                                    if model:
                                                                        model_type = model.get('type', 'unknown')

                                                                        # Update counts
                                                                        summary['total_models'] += 1
                                                                        if model_type not in summary['by_type']:
                                                                            summary['by_type'][model_type] = 0
                                                                            summary['by_type'][model_type] += 1

                                                                            # Add file info
                                                                            summary['files'].append({
                                                                            'path': str(model_file.relative_to(output_dir)),
                                                                            'type': model_type,
                                                                            'name': model.get('name', ''),
                                                                            'size': model_file.stat().st_size
                                                                            })

                                                                            logger.debug("Error processing %s: %s", model_file, e)

                                                                            # Save summary
                                                                            summary_file = output_dir / 'model_summary.json'
                                                                            try:
                                                                                with Path(summary_file).open(, 'w', encoding='utf-8') as f:
                                                                                    json.dump(summary, f, indent=2)
                                                                                    logger.info("Created model summary with %d models", summary['total_models'])
                                                                                    except Exception as e:
                                                                                        logger.error("Failed to save summary: %s", e)

                                                                                        return summary

                                                                                        """Get persistence statistics.

                                                                                        Dictionary with save and load counts
                                                                                        """
                                                                                        return {
                                                                                        'saved': self._save_count,
                                                                                        'loaded': self._load_count
                                                                                        }

                                                                                        """Reset persistence statistics."""
                                                                                        self._save_count = 0
                                                                                        self._load_count = 0
