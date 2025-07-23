"""AST processing service for converting AST to models."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from src.model.interfaces import IASTProcessor
import re

"""Processes AST files and converts them to model objects."""

pass
"""Initialize the AST processor."""
self._processed_files = 0
self._failed_files = 0

"""Process an AST file.

file_path: Path to AST file

Processed model dictionary
"""
if not file_path.exists():
    logger.error("AST file not found: %s", file_path)
    self._failed_files += 1
    return {}

    # Load AST data
    with file_path.open(, 'r', encoding='utf-8') as f:
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

                logger.error("Failed to process AST file %s: %s", file_path, e)
                self._failed_files += 1
                return {}

                """Extract metadata from AST.

                ast: Abstract syntax tree

                Extracted metadata
                """
                metadata = {
                'object_type': 'unknown',
                'object_name': '',
                'has_ast': 'ast' in ast,
                'format': 'structured' if 'ast' in ast else 'legacy'
                }

                # Extract from structured format
                if 'ast' in ast:
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

                                    # Handle different AST formats
                                    if isinstance(ast_content, dict):
                                        # Already a dictionary - could be serialized Tree or model
                                        ast = ast_content
                                        elif isinstance(ast_content, str):
                                            # Pretty-printed string format (legacy)
                                            ast = {'type': 'legacy_ast', 'content': ast_content}
                                            else:
                                                logger.error("Unknown AST format in %s", ast_path)
                                                return {}

                                                # Extract object type and name from AST if not provided
                                                if object_type == 'unknown' and 'children' in ast and ast['children']:
                                                    extracted_type, extracted_name = self._extract_type_from_ast(ast)
                                                    if extracted_type:
                                                        object_type = extracted_type
                                                        if extracted_name:
                                                            object_name = extracted_name

                                                            # Create base model structure
                                                            model = {
                                                            'type': object_type,
                                                            'name': object_name,
                                                            'timestamp': Path(file_path).stat().st_mtime if Path(file_path).exists() else None,
                                                            'data': {},
                                                            'source_file': file_path
                                                            }

                                                            # Store AST for extraction
                                                            model['ast'] = ast

                                                            return model

                                                            """Process AST data in legacy format.

                                                            ast_path: Path to the AST file
                                                            ast_data: Raw AST data

                                                            Model dictionary
                                                            """
                                                            # Infer object type from filename
                                                            object_type = self._infer_object_type(ast_path.name)
                                                            object_name = ast_path.stem.replace('.ast', '')

                                                            # Create model structure
                                                            model = {
                                                            'type': object_type,
                                                            'name': object_name,
                                                            'timestamp': ast_path.stat().st_mtime if ast_path.exists() else None,
                                                            'data': {},
                                                            'source_file': str(ast_path)
                                                            }

                                                            # Store AST for extraction
                                                            model['ast'] = ast_data

                                                            return model

                                                            """Infer object type from filename.

                                                            filename: Name of the file

                                                            Inferred object type
                                                            """
                                                            name_lower = filename.lower()

                                                            return 'window'
                                                            return 'window'
                                                            elif '.srd' in name_lower or '.dwo' in name_lower or name_lower.startswith('d_'):
                                                                return 'datawindow'
                                                                elif '.sru' in name_lower or name_lower.startswith('u_') or name_lower.startswith('uo_'):
                                                                    return 'userobject'
                                                                    elif '.srf' in name_lower or name_lower.startswith('f_'):
                                                                        return 'function'
                                                                        elif '.srs' in name_lower:
                                                                            return 'structure'
                                                                            elif '.srm' in name_lower or name_lower.startswith('m_'):
                                                                                return 'menu'
                                                                                elif '.sra' in name_lower:
                                                                                    return 'application'
                                                                                    elif '.sql' in name_lower:
                                                                                        return 'query'
                                                                                        else:
                                                                                            return 'unknown'

                                                                                            """Extract object type and name from AST structure.

                                                                                            ast: AST dictionary

                                                                                            Tuple of (object_type, object_name)
                                                                                            """
                                                                                            object_type = None
                                                                                            object_name = None

                                                                                            # Look for type declaration in AST
                                                                                            if 'children' in ast and ast['children']:
                                                                                                # Convert to string for pattern matching
                                                                                                ast_str = str(ast['children'])

                                                                                                # Look for global type definitions
                                                                                                import re
                                                                                                type_match = re.search(
                                                                                                r"global\s+type\s+(\w+)\s+from\s+(\w+)",
                                                                                                ast_str,
                                                                                                re.IGNORECASE
                                                                                                )

                                                                                                object_name = type_match.group(1)
                                                                                                parent_type = type_match.group(2).lower()

                                                                                                # Map parent type to object type
                                                                                                type_mapping = {
                                                                                                'window': 'window',
                                                                                                'w_': 'window',
                                                                                                'userobject': 'userobject',
                                                                                                'u_': 'userobject',
                                                                                                'datawindow': 'datawindow',
                                                                                                'datastore': 'datawindow',
                                                                                                'd_': 'datawindow',
                                                                                                'menu': 'menu',
                                                                                                'm_': 'menu',
                                                                                                'application': 'application',
                                                                                                'function': 'function',
                                                                                                'transaction': 'transaction',
                                                                                                'structure': 'structure',
                                                                                                }

                                                                                                if key in parent_type:
                                                                                                    object_type = value
                                                                                                    break

                                                                                                    object_type = 'userobject'  # Default for custom objects

                                                                                                    # Infer from object name if no type found
                                                                                                    if not object_type and object_name:
                                                                                                        object_type = self._infer_object_type(object_name)

                                                                                                        logger.debug("Error extracting type from AST: %s", e)

                                                                                                        return object_type, object_name

                                                                                                        """Get processing statistics.

                                                                                                        Dictionary with processed and failed counts
                                                                                                        """
                                                                                                        return {
                                                                                                        'processed': self._processed_files,
                                                                                                        'failed': self._failed_files,
                                                                                                        'total': self._processed_files + self._failed_files
                                                                                                        }

                                                                                                        """Reset processing statistics."""
                                                                                                        self._processed_files = 0
                                                                                                        self._failed_files = 0
