"""Interfaces for decompilation services."""
from typing import Protocol, Optional, Any, Dict, List, Tuple
from pathlib import Path
from abc import abstractmethod


class IObjectTypeDetector(Protocol):
    """Interface for object type detection."""
    
    @staticmethod
    def get_object_info(object_name: str) -> tuple[str, bool]:
        """Get object type and whether it's a standard object.
        
        Args:
            object_name: Name of the object
            
        Returns:
            Tuple of (object_type, is_standard_object)
        """
        ...
    
    @staticmethod
    def get_object_type(object_name: str) -> str:
        """Get the type of the object from its name.
        
        Args:
            object_name: Name of the object
            
        Returns:
            Object type string
        """
        ...


class IPCodeDecoder(Protocol):
    """Interface for P-code decoding."""
    
    def decode_pcode_section(
        self, 
        data: bytes, 
        object_name: str, 
        pcode_info: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Decode P-code section.
        
        Args:
            data: P-code binary data
            object_name: Name of the object being decoded
            pcode_info: Optional P-code metadata
            
        Returns:
            Decoded P-code structure
        """
        ...
    
    def get_version(self) -> str:
        """Get decoder version."""
        ...


class IControlFlowAnalyzer(Protocol):
    """Interface for control flow analysis."""
    
    def analyze(self, instructions: List[Any]) -> Dict[str, Any]:
        """Analyze control flow of instructions.
        
        Args:
            instructions: List of decoded instructions
            
        Returns:
            Control flow analysis results
        """
        ...
    
    def build_cfg(self, instructions: List[Any]) -> Any:
        """Build control flow graph.
        
        Args:
            instructions: List of decoded instructions
            
        Returns:
            Control flow graph
        """
        ...


class IExpressionReconstructor(Protocol):
    """Interface for expression reconstruction."""
    
    def reconstruct(self, instructions: List[Any]) -> str:
        """Reconstruct expressions from instructions.
        
        Args:
            instructions: List of decoded instructions
            
        Returns:
            Reconstructed PowerBuilder source code
        """
        ...
    
    def reconstruct_expression(self, expr_instructions: List[Any]) -> str:
        """Reconstruct a single expression.
        
        Args:
            expr_instructions: Instructions for one expression
            
        Returns:
            Reconstructed expression string
        """
        ...


class IOutputFormatter(Protocol):
    """Interface for output formatting."""
    
    def format_source(
        self, 
        object_type: str, 
        object_name: str, 
        decompiled_content: str
    ) -> str:
        """Format decompiled source code.
        
        Args:
            object_type: Type of the object
            object_name: Name of the object
            decompiled_content: Decompiled content
            
        Returns:
            Formatted PowerBuilder source code
        """
        ...


class IOutputValidator(Protocol):
    """Interface for output validation."""
    
    def validate(self, content: str, object_type: str) -> bool:
        """Validate decompiled output.
        
        Args:
            content: Decompiled content
            object_type: Type of the object
            
        Returns:
            True if valid, False otherwise
        """
        ...
    
    def get_validation_errors(self) -> List[str]:
        """Get validation errors from last validation.
        
        Returns:
            List of validation error messages
        """
        ...


class IVersionDetector(Protocol):
    """Interface for PowerBuilder version detection."""
    
    def detect_version(self, data: bytes) -> str:
        """Detect PowerBuilder version from data.
        
        Args:
            data: Binary data to analyze
            
        Returns:
            Version string
        """
        ...


# Keep existing interfaces for compatibility
class IDecompiler(Protocol):
    """Interface for all decompilers."""

    @abstractmethod
    def decompile(self, bytecode: bytes, context: Optional[Dict[str, Any]] = None) -> str:
        """Decompile bytecode to source code."""
        ...

    @abstractmethod
    def supports(self, bytecode: bytes) -> bool:
        """Check if this decompiler supports the given bytecode."""
        ...


class IDecompilerCoordinator(Protocol):
    """Interface for decompile coordinator."""

    @abstractmethod
    def decompile(self, input_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Coordinate decompilation process."""
        ...

    @abstractmethod
    def decompile_file(self, file_path: Path) -> str:
        """Decompile a single file."""
        ...

    @abstractmethod
    def register_decompiler(self, decompiler: IDecompiler) -> None:
        """Register a new decompiler."""
        ...

    @abstractmethod
    def get_decompilers(self) -> List[IDecompiler]:
        """Get all registered decompilers."""
        ...