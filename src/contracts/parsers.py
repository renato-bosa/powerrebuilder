"""Interfaces for parsing services."""
from typing import Protocol, Optional, Any, Dict, List
from pathlib import Path
from abc import abstractmethod
from lark import Tree, Grammar


class IGrammarManager(Protocol):
    """Interface for grammar management."""
    
    def load_grammar(self, name: str, **kwargs) -> Grammar:
        """Load a grammar by name.
        
        Args:
            name: Grammar name
            **kwargs: Additional grammar options
            
        Returns:
            Loaded grammar
        """
        ...
    
    def get_grammar_path(self, name: str) -> Path:
        """Get path to grammar file.
        
        Args:
            name: Grammar name
            
        Returns:
            Path to grammar file
        """
        ...


class ILibraryManager(Protocol):
    """Interface for library management."""
    
    def resolve_import(self, library_name: str) -> Optional[Path]:
        """Resolve library import to file path.
        
        Args:
            library_name: Name of the library
            
        Returns:
            Path to library file or None if not found
        """
        ...
    
    def add_library_path(self, path: Path) -> None:
        """Add path to search for libraries.
        
        Args:
            path: Directory to search
        """
        ...
    
    def get_library_dependencies(self, library_name: str) -> List[str]:
        """Get dependencies of a library.
        
        Args:
            library_name: Name of the library
            
        Returns:
            List of dependency names
        """
        ...


class ITypeResolver(Protocol):
    """Interface for type resolution."""
    
    def resolve_type(self, type_name: str) -> Optional[Dict[str, Any]]:
        """Resolve a custom type.
        
        Args:
            type_name: Name of the type
            
        Returns:
            Type definition or None if not found
        """
        ...
    
    def register_type(self, type_name: str, type_def: Dict[str, Any]) -> None:
        """Register a custom type.
        
        Args:
            type_name: Name of the type
            type_def: Type definition
        """
        ...
    
    def get_all_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered types.
        
        Returns:
            Dictionary of type definitions
        """
        ...


class IImportResolver(Protocol):
    """Interface for import resolution."""
    
    def resolve_imports(self, source: str) -> str:
        """Resolve implicit imports in source.
        
        Args:
            source: PowerBuilder source code
            
        Returns:
            Source with explicit imports
        """
        ...
    
    def get_implicit_imports(self) -> List[str]:
        """Get list of implicit imports.
        
        Returns:
            List of implicit import statements
        """
        ...


class ITransformer(Protocol):
    """Interface for AST transformation."""
    
    def transform(self, tree: Tree) -> Dict[str, Any]:
        """Transform parse tree to AST.
        
        Args:
            tree: Parse tree
            
        Returns:
            Abstract syntax tree
        """
        ...
    
    def get_position_info(self) -> Dict[str, Any]:
        """Get position tracking information.
        
        Returns:
            Position information from last transform
        """
        ...


class IPreprocessor(Protocol):
    """Interface for source preprocessing."""
    
    def preprocess(self, source: str) -> str:
        """Preprocess source code.
        
        Args:
            source: Raw source code
            
        Returns:
            Preprocessed source code
        """
        ...
    
    def get_includes(self) -> List[str]:
        """Get list of included files.
        
        Returns:
            List of included file paths
        """
        ...


# Keep existing interfaces for compatibility
class IParser(Protocol):
    """Interface for all parsers."""

    @abstractmethod
    def parse(self, source: str, file_path: Optional[Path] = None) -> Any:
        """Parse source code into AST."""
        ...

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if this parser supports the given file."""
        ...


class IParserCoordinator(Protocol):
    """Interface for parse coordinator."""

    @abstractmethod
    def parse(self, input_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Coordinate parsing process."""
        ...

    @abstractmethod
    def parse_file(self, file_path: Path) -> Any:
        """Parse a single file."""
        ...

    @abstractmethod
    def register_parser(self, parser: IParser) -> None:
        """Register a new parser."""
        ...

    @abstractmethod
    def get_parsers(self) -> List[IParser]:
        """Get all registered parsers."""
        ...