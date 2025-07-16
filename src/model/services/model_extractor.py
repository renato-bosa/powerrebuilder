"""Model extraction service for extracting models from AST."""
import logging
import re
from typing import Any, Dict, List

from src.contracts.models import IModelExtractor

logger = logging.getLogger(__name__)


class ModelExtractor(IModelExtractor):
    """Extracts model information from AST structures."""
    
    def __init__(self):
        """Initialize the model extractor."""
        self.current_object_name = ""
    
    def extract_window_model(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract window model from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Window model dictionary
        """
        # Try visitor pattern first
        try:
            from src.model.visitors import WindowModelExtractor
            
            visitor = WindowModelExtractor()
            return visitor.extract_model(ast, 'window', self.current_object_name)
        except ImportError:
            # Fallback to regex-based extraction
            return self._extract_window_model_legacy(ast)
        except Exception as e:
            logger.warning("Visitor extraction failed, using legacy method: %s", e)
            return self._extract_window_model_legacy(ast)
    
    def _extract_window_model_legacy(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy regex-based window model extraction."""
        events = []
        methods = []
        controls = []
        variables = []
        
        try:
            if 'children' in ast and ast['children']:
                ast_str = str(ast['children'][0].get('value', ''))
                
                # Extract event handlers
                event_matches = re.findall(
                    r"Tree\(Token\('RULE', 'event_handler'\).*?Token\('IDENTIFIER', '(\w+)'\)", 
                    ast_str
                )
                for event_name in event_matches:
                    events.append({
                        'name': event_name,
                        'type': 'event',
                        'parameters': [],
                        'return_type': 'any'
                    })
                
                # Extract functions
                func_matches = re.findall(
                    r"Tree\(Token\('RULE', 'function_decl'\).*?Token\('TYPE_NAME', '(\w+)'\).*?Token\('IDENTIFIER', '(\w+)'\)", 
                    ast_str
                )
                for return_type, func_name in func_matches:
                    methods.append({
                        'name': func_name,
                        'type': 'function',
                        'return_type': return_type,
                        'parameters': [],
                        'visibility': 'public'
                    })
                
                # Extract controls (simplified)
                control_matches = re.findall(
                    r"type\s+(\w+)\s+from\s+(\w+)", 
                    ast_str, 
                    re.IGNORECASE
                )
                for control_name, control_type in control_matches:
                    if control_name != self.current_object_name:
                        controls.append({
                            'name': control_name,
                            'type': control_type,
                            'properties': {}
                        })
                
                # Extract variables
                var_matches = re.findall(
                    r"(?:instance|global|shared)\s+(\w+)\s+(\w+)", 
                    ast_str, 
                    re.IGNORECASE
                )
                for var_type, var_name in var_matches:
                    variables.append({
                        'name': var_name,
                        'type': var_type,
                        'scope': 'instance'
                    })
                
                # Extract create/destroy handlers
                if "'on_block'" in ast_str:
                    if "'CREATE'" in ast_str:
                        events.append({
                            'name': 'create', 
                            'type': 'system_event',
                            'return_type': 'none'
                        })
                    if "'DESTROY'" in ast_str:
                        events.append({
                            'name': 'destroy', 
                            'type': 'system_event',
                            'return_type': 'none'
                        })
                        
        except Exception as e:
            logger.debug("Error extracting window model: %s", e)
        
        return {
            'type': 'window',
            'name': self.current_object_name,
            'title': '',
            'controls': controls,
            'events': events,
            'methods': methods,
            'variables': variables,
            'properties': {}
        }
    
    def extract_datawindow_model(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract datawindow model from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            DataWindow model dictionary
        """
        # Try visitor pattern first
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            model = visitor.extract_model(ast, 'datawindow', self.current_object_name)
            
            # Add datawindow-specific defaults
            model.setdefault('columns', [])
            model.setdefault('sql', '')
            model.setdefault('presentation_style', 'grid')
            model.setdefault('data_source', 'sql')
            
            return model
            
        except Exception as e:
            logger.warning("Visitor extraction failed, using defaults: %s", e)
            return self._extract_datawindow_model_legacy(ast)
    
    def _extract_datawindow_model_legacy(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy datawindow extraction."""
        columns = []
        sql = ""
        
        try:
            if 'children' in ast:
                ast_str = str(ast)
                
                # Extract SQL
                sql_match = re.search(
                    r"retrieve\s*=\s*[\"']([^\"']+)[\"']", 
                    ast_str, 
                    re.IGNORECASE | re.DOTALL
                )
                if sql_match:
                    sql = sql_match.group(1)
                
                # Extract columns (simplified)
                col_matches = re.findall(
                    r"column\s*=\s*\(.*?name\s*=\s*(\w+).*?type\s*=\s*(\w+)", 
                    ast_str, 
                    re.IGNORECASE | re.DOTALL
                )
                for col_name, col_type in col_matches:
                    columns.append({
                        'name': col_name,
                        'type': col_type,
                        'display_name': col_name
                    })
                    
        except Exception as e:
            logger.debug("Error extracting datawindow model: %s", e)
        
        return {
            'type': 'datawindow',
            'name': self.current_object_name,
            'columns': columns,
            'sql': sql,
            'presentation_style': 'grid',
            'data_source': 'sql' if sql else 'external',
            'properties': {}
        }
    
    def extract_function_model(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract function model from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Function model dictionary
        """
        # Try visitor pattern first
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            model = visitor.extract_model(ast, 'function', self.current_object_name)
            
            # Add function-specific defaults
            model.setdefault('return_type', 'void')
            model.setdefault('parameters', [])
            model.setdefault('body', '')
            model.setdefault('visibility', 'public')
            
            return model
            
        except Exception as e:
            logger.warning("Visitor extraction failed, using defaults: %s", e)
            return self._extract_function_model_legacy(ast)
    
    def _extract_function_model_legacy(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy function extraction."""
        return_type = 'void'
        parameters = []
        body = ''
        visibility = 'public'
        
        try:
            if 'children' in ast:
                ast_str = str(ast)
                
                # Extract return type
                ret_match = re.search(
                    r"function\s+(\w+)\s+(\w+)", 
                    ast_str, 
                    re.IGNORECASE
                )
                if ret_match:
                    return_type = ret_match.group(1)
                
                # Extract visibility
                if re.search(r"\bprivate\b", ast_str, re.IGNORECASE):
                    visibility = 'private'
                elif re.search(r"\bprotected\b", ast_str, re.IGNORECASE):
                    visibility = 'protected'
                
                # Extract parameters (simplified)
                param_match = re.search(
                    r"\(([^)]*)\)", 
                    ast_str
                )
                if param_match and param_match.group(1).strip():
                    param_str = param_match.group(1)
                    # Simple parameter parsing
                    params = param_str.split(',')
                    for param in params:
                        parts = param.strip().split()
                        if len(parts) >= 2:
                            parameters.append({
                                'name': parts[-1],
                                'type': ' '.join(parts[:-1]),
                                'pass_by': 'value'
                            })
                            
        except Exception as e:
            logger.debug("Error extracting function model: %s", e)
        
        return {
            'type': 'function',
            'name': self.current_object_name,
            'return_type': return_type,
            'parameters': parameters,
            'body': body,
            'visibility': visibility
        }
    
    def extract_generic_model(self, ast: Dict[str, Any], object_type: str) -> Dict[str, Any]:
        """Extract generic model from AST.
        
        Args:
            ast: Abstract syntax tree
            object_type: Type of object
            
        Returns:
            Generic model dictionary
        """
        # Try visitor pattern first
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            model = visitor.extract_model(ast, object_type, self.current_object_name)
            
            # If visitor didn't extract much, include raw AST
            if not model.get('events') and not model.get('methods') and not model.get('variables'):
                model['raw_ast'] = ast
            
            return model
            
        except Exception as e:
            logger.warning("Visitor extraction failed, returning generic model: %s", e)
            return {
                'type': object_type,
                'name': self.current_object_name,
                'events': [],
                'methods': [],
                'variables': [],
                'properties': {},
                'raw_ast': ast
            }
    
    def set_current_object(self, object_name: str) -> None:
        """Set the current object being processed.
        
        Args:
            object_name: Name of the current object
        """
        self.current_object_name = object_name