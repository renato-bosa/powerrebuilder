"""Model persistence service for saving and loading AST models.

This service handles the serialization and deserialization of model data
to and from JSON files, with support for different model formats.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ModelPersistenceService:
    """Service for persisting and loading model data."""

    def __init__(self):
        """Initialize the model persistence service."""
        self._save_count = 0
        self._load_count = 0

    def save_model(self, model: Dict[str, Any], file_path: Path) -> None:
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
            with file_path.open('w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)

            self._save_count += 1
            logger.debug("Saved model to %s", file_path)

        except Exception as e:
            logger.error("Failed to save model to %s: %s", file_path, e)
            raise

    def load_model(self, file_path: Path) -> Dict[str, Any]:
        """Load model from file.

        file_path: Model file path

        Loaded model
        """
        try:
            if not file_path.exists():
                logger.error("Model file not found: %s", file_path)
                return {}

            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            self._load_count += 1

            # Handle different formats
            if 'models' in data:
                # Standard format
                models = data.get('models', [])
                if models:
                    return models[0] if len(models) == 1 else {'models': models}
                else:
                    return {}
            else:
                # Legacy format - raw model
                return data

        except Exception as e:
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
        object_type: Type of object (e.g., 'window', 'nonvisualobject')
        object_name: Name of object

        Path to saved file
        """
        # Create type-specific subdirectory
        type_dir = output_dir / object_type
        type_dir.mkdir(parents=True, exist_ok=True)

        # Save model
        file_path = type_dir / f"{object_name}.model.json"
        self.save_model(model, file_path)

        return file_path

    def get_statistics(self) -> Dict[str, int]:
        """Get persistence statistics.

        Statistics dictionary
        """
        return {
            'models_saved': self._save_count,
            'models_loaded': self._load_count,
        }