"""AST processing service for converting AST to models."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class ASTProcessor:
    """Processes AST files and converts them to model objects."""

    def __init__(self):
        """Initialize the AST processor."""
        self._processed_files = 0
        self._failed_files = 0

    def process_ast_file(self, file_path: Path) -> Dict[str, Any]:
        """Process an AST file.

        file_path: Path to AST file

        Processed model dictionary
        """
        if not file_path.exists():
            logger.error("AST file not found: %s", file_path)
            self._failed_files += 1
            return {}

        try:
            # Load AST data
            with file_path.open('r', encoding='utf-8') as f:
                ast_data = json.load(f)

            # Process based on format
            if 'ast' in ast_data:
                # New format with metadata
                model = self._process_structured_ast(file_path, ast_data)
            else:
                # Legacy format - just the AST
                model = self._process_legacy_ast(file_path, ast_data)

            self._processed_files += 1
            return model

        except Exception as e:
            logger.error("Failed to process AST file %s: %s", file_path, e)
            self._failed_files += 1
            return {}

    def _extract_metadata(self, ast: Any) -> dict[str, Any]:
        """Extract metadata from AST.

        ast: Abstract syntax tree

        Extracted metadata
        """
        metadata = {
            'object_type': 'unknown',
            'object_name': '',
            'has_ast': 'ast' in ast if isinstance(ast, dict) else False,
            'format': 'structured' if isinstance(ast, dict) and 'ast' in ast else 'legacy'
        }

        # Extract from structured format
        if isinstance(ast, dict) and 'ast' in ast:
            metadata['object_type'] = ast.get('object_type', 'unknown')
            metadata['object_name'] = ast.get('object_name', '')
            metadata['file_path'] = ast.get('file', '')

            # Try to extract from AST structure
            if metadata['object_type'] == 'unknown':
                extracted_type, extracted_name = self._extract_type_from_ast(
                    ast.get('ast', ast)
                )
                if extracted_type:
                    metadata['object_type'] = extracted_type
                if extracted_name:
                    metadata['object_name'] = extracted_name

        return metadata

    def _process_structured_ast(self, ast_path: Path, ast_data: dict[str, Any]) -> dict[str, Any]:
        """Process AST data in structured format.

        ast_path: Path to the AST file
        ast_data: Loaded AST data with metadata

        Model dictionary
        """
        # Extract metadata
        file_path = ast_data.get('file', str(ast_path))
        object_type = ast_data.get('object_type', 'unknown')
        object_name = ast_data.get('object_name', ast_path.stem)

        # Get the AST
        ast_content = ast_data.get('ast')
        if not ast_content:
            logger.error("No AST content in %s", ast_path)
            return {}

        # Create base model
        model = {
            'file_path': file_path,
            'object_type': object_type,
            'object_name': object_name,
            'metadata': self._extract_metadata(ast_data),
            'content': ast_content
        }

        return model

    def _process_legacy_ast(self, ast_path: Path, ast_data: Any) -> dict[str, Any]:
        """Process AST data in legacy format.

        ast_path: Path to the AST file
        ast_data: Raw AST data

        Model dictionary
        """
        # Try to extract type and name from AST
        object_type, object_name = self._extract_type_from_ast(ast_data)
        
        if not object_name:
            object_name = ast_path.stem

        # Create model
        model = {
            'file_path': str(ast_path),
            'object_type': object_type or 'unknown',
            'object_name': object_name,
            'metadata': {
                'format': 'legacy',
                'extracted': True
            },
            'content': ast_data
        }

        return model

    def _extract_type_from_ast(self, ast: Any) -> Tuple[Optional[str], Optional[str]]:
        """Extract object type and name from AST structure.

        ast: AST data

        Tuple of (object_type, object_name)
        """
        object_type = None
        object_name = None

        if isinstance(ast, dict):
            # Check for type field
            if 'type' in ast:
                object_type = ast['type'].lower()
            
            # Check for name field
            if 'name' in ast:
                object_name = ast['name']
            
            # Check for class_definition
            if 'class_definition' in ast:
                object_type = 'class'
                if isinstance(ast['class_definition'], dict):
                    object_name = ast['class_definition'].get('name')
            
            # Check for window_definition
            elif 'window_definition' in ast:
                object_type = 'window'
                if isinstance(ast['window_definition'], dict):
                    object_name = ast['window_definition'].get('name')

        return object_type, object_name

    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics.

        Statistics dictionary
        """
        return {
            'processed_files': self._processed_files,
            'failed_files': self._failed_files,
        }