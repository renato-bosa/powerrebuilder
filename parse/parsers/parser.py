"""Unified PowerBuilder parser module.

This module provides a unified parser that can handle all PowerBuilder file types
by delegating to specialized parsers as needed.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

from .base_parser import PowerBuilderBaseParser
from .specialized.sql_parser import SQLParser
from .specialized.transaction_parser import TransactionParser
from .specialized.type_parser import TypeParser
from .enhanced_parser import EnhancedPowerBuilderParser
from .specialized.pseudocode_parser import PowerBuilderPseudocodeParser

logger = logging.getLogger(__name__)


class UnifiedPowerBuilderParser:
    """Unified parser for all PowerBuilder file types.
    
    This parser automatically selects the appropriate specialized parser
    based on file extension or content type.
    """
    
    # Map of file extensions to specialized parsers
    EXTENSION_PARSERS: Dict[str, Type[PowerBuilderBaseParser]] = {
        # SQL files
        "sql": SQLParser,
        "srq": SQLParser,
        
        # Transaction files  
        "trn": TransactionParser,
        
        # Type definition files
        "srd": TypeParser,
        "typ": TypeParser,
        
        # Standard PowerBuilder source files
        "sra": EnhancedPowerBuilderParser,
        "srw": EnhancedPowerBuilderParser,
        "sru": EnhancedPowerBuilderParser,
        "srf": EnhancedPowerBuilderParser,
        "srm": EnhancedPowerBuilderParser,
        "srs": EnhancedPowerBuilderParser,
    }
    
    # Content type detection patterns
    CONTENT_PATTERNS = {
        "SELECT": SQLParser,
        "INSERT": SQLParser,
        "UPDATE": SQLParser,
        "DELETE": SQLParser,
        "BEGIN TRANSACTION": TransactionParser,
        "COMMIT": TransactionParser,
        "ROLLBACK": TransactionParser,
        "type ": TypeParser,
        "global type": TypeParser,
    }
    
    def __init__(self, base_path: Path | None = None, enable_error_recovery: bool = True):
        """Initialize unified parser.
        
        Args:
            base_path: Base path for resolving includes
            enable_error_recovery: Whether to enable error recovery
        """
        self.base_path = base_path or Path.cwd()
        self.enable_error_recovery = enable_error_recovery
        self._parser_cache: Dict[Type[PowerBuilderBaseParser], PowerBuilderBaseParser] = {}
        
    def parse(self, source: str | Path, parser_type: str | None = None) -> Tree | Dict[str, Any]:
        """Parse PowerBuilder source code.
        
        Args:
            source: Source code string or file path
            parser_type: Optional parser type override ('sql', 'transaction', 'type', 'enhanced')
            
        Returns:
            Parse tree or dictionary representation
            
        Raises:
            ValueError: If appropriate parser cannot be determined
            UnexpectedInput: If parsing fails
        """
        # Determine source content and path
        if isinstance(source, Path):
            source_path = source
            with open(source, 'r', encoding='utf-8') as f:
                source_text = f.read()
        else:
            source_path = None
            source_text = source
            
        # Determine which parser to use
        if parser_type:
            parser_class = self._get_parser_by_type(parser_type)
        elif source_path:
            parser_class = self._get_parser_by_extension(source_path.suffix.lstrip('.'))
        else:
            parser_class = self._get_parser_by_content(source_text)
            
        if not parser_class:
            raise ValueError("Could not determine appropriate parser for source")
            
        # Get or create parser instance
        parser = self._get_parser_instance(parser_class)
        
        # Parse the source
        try:
            return parser.parse(source)
        except UnexpectedInput as e:
            logger.error(f"Parse error: {e}")
            raise
            
    def _get_parser_by_type(self, parser_type: str) -> Type[PowerBuilderBaseParser] | None:
        """Get parser class by type name."""
        type_map = {
            'sql': SQLParser,
            'transaction': TransactionParser,
            'type': TypeParser,
            'enhanced': EnhancedPowerBuilderParser,
            'pseudocode': PowerBuilderPseudocodeParser,
        }
        return type_map.get(parser_type.lower())
        
    def _get_parser_by_extension(self, extension: str) -> Type[PowerBuilderBaseParser] | None:
        """Get parser class by file extension."""
        return self.EXTENSION_PARSERS.get(extension.lower())
        
    def _get_parser_by_content(self, content: str) -> Type[PowerBuilderBaseParser]:
        """Detect parser type by content analysis."""
        # Check for specific patterns
        content_upper = content.upper()
        for pattern, parser_class in self.CONTENT_PATTERNS.items():
            if pattern in content_upper:
                return parser_class
                
        # Default to enhanced parser
        return EnhancedPowerBuilderParser
        
    def _get_parser_instance(self, parser_class: Type[PowerBuilderBaseParser]) -> PowerBuilderBaseParser:
        """Get or create parser instance."""
        if parser_class not in self._parser_cache:
            # Create appropriate instance based on parser type
            if parser_class == SQLParser:
                self._parser_cache[parser_class] = SQLParser()
            elif parser_class == TransactionParser:
                self._parser_cache[parser_class] = TransactionParser(self.base_path)
            elif parser_class == TypeParser:
                self._parser_cache[parser_class] = TypeParser(self.base_path)
            elif parser_class == EnhancedPowerBuilderParser:
                self._parser_cache[parser_class] = EnhancedPowerBuilderParser(
                    self.base_path, 
                    self.enable_error_recovery
                )
            elif parser_class == PowerBuilderPseudocodeParser:
                self._parser_cache[parser_class] = PowerBuilderPseudocodeParser()
            else:
                self._parser_cache[parser_class] = parser_class(self.base_path)
                
        return self._parser_cache[parser_class]
        
    def parse_file(self, file_path: Path) -> Tree | Dict[str, Any]:
        """Parse a PowerBuilder file.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Parse tree or dictionary representation
        """
        return self.parse(file_path)
        
    def parse_string(self, source: str, parser_type: str | None = None) -> Tree | Dict[str, Any]:
        """Parse a PowerBuilder source string.
        
        Args:
            source: Source code string
            parser_type: Optional parser type override
            
        Returns:
            Parse tree or dictionary representation
        """
        return self.parse(source, parser_type)


# Convenience function for backward compatibility
def parse_powerbuilder(source: str | Path, **kwargs) -> Tree | Dict[str, Any]:
    """Parse PowerBuilder source using unified parser.
    
    Args:
        source: Source code or file path
        **kwargs: Additional arguments passed to UnifiedPowerBuilderParser
        
    Returns:
        Parse tree or dictionary representation
    """
    parser = UnifiedPowerBuilderParser(**kwargs)
    return parser.parse(source)