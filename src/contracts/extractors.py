"""Interfaces for extraction services."""
from typing import Protocol, Callable, Optional, Any, Dict, List
from pathlib import Path
from abc import abstractmethod


class IPathValidator(Protocol):
    """Interface for path validation service."""
    
    def validate_path(self, path: Path, base_path: Path) -> None:
        """Validate a path is safe and within bounds.
        
        Args:
            path: Path to validate
            base_path: Base directory for boundary checking
            
        Raises:
            ValueError: If path is invalid or outside boundaries
        """
        ...
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe filesystem operations.
        
        Args:
            filename: Raw filename to sanitize
            
        Returns:
            Sanitized filename safe for filesystem
        """
        ...


class IResourceMonitor(Protocol):
    """Interface for resource monitoring service."""
    
    def start_monitoring(self) -> None:
        """Start monitoring system resources."""
        ...
    
    def stop_monitoring(self) -> None:
        """Stop monitoring and clean up."""
        ...
    
    def check_memory_usage(self) -> None:
        """Check current memory usage against limits.
        
        Raises:
            MemoryError: If memory limit exceeded
        """
        ...
    
    def check_file_size(self, size: int, path: str) -> None:
        """Check if file size is within limits.
        
        Args:
            size: File size in bytes
            path: File path for error reporting
            
        Raises:
            ValueError: If file size exceeds limit
        """
        ...
    
    def check_file_count(self) -> None:
        """Check if file count is within limits.
        
        Raises:
            RuntimeError: If file count exceeds limit
        """
        ...


class IProgressTracker(Protocol):
    """Interface for progress tracking."""
    
    def set_total(self, total: int) -> None:
        """Set total number of items to process."""
        ...
    
    def update(self, n: int = 1) -> None:
        """Update progress by n items."""
        ...
    
    def set_description(self, desc: str) -> None:
        """Set progress description."""
        ...
    
    def close(self) -> None:
        """Close and clean up progress tracker."""
        ...


class IPBDReader(Protocol):
    """Interface for PBD/PBL file reading."""
    
    def extract_all(self, output_dir: Path, progress_callback: Optional[Callable] = None) -> int:
        """Extract all entries from PBD/PBL file.
        
        Args:
            output_dir: Directory to extract to
            progress_callback: Optional callback for progress updates
            
        Returns:
            Number of files extracted
        """
        ...
    
    def get_entry_count(self) -> int:
        """Get total number of entries in file."""
        ...
    
    def close(self) -> None:
        """Close file and clean up resources."""
        ...


class IRecoveryEngine(Protocol):
    """Interface for byte-level recovery."""
    
    def recover_objects(self) -> dict[str, Any]:
        """Attempt to recover objects from corrupted data.
        
        Returns:
            Dictionary of recovered objects
        """
        ...
    
    def get_stats(self) -> dict[str, Any]:
        """Get recovery statistics.
        
        Returns:
            Statistics about recovery process
        """
        ...


class IBinaryExtractor(Protocol):
    """Interface for binary data extraction."""
    
    def extract(self, entry: Any, output_path: Path) -> Optional[Path]:
        """Extract binary data from entry.
        
        Args:
            entry: Entry to extract from
            output_path: Output directory
            
        Returns:
            Path to extracted file or None if failed
        """
        ...


class IResourceExtractor(Protocol):
    """Interface for resource extraction."""
    
    def extract(self, entry: Any, output_path: Path) -> Optional[Path]:
        """Extract resources from entry.
        
        Args:
            entry: Entry to extract from
            output_path: Output directory
            
        Returns:
            Path to extracted file or None if failed
        """
        ...


# Keep existing interfaces for compatibility
class IExtractor(Protocol):
    """Interface for all extractors."""

    @abstractmethod
    def extract(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Extract content from input to output."""
        ...

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if this extractor supports the given file."""
        ...


class IExtractorCoordinator(Protocol):
    """Interface for extract coordinator."""

    @abstractmethod
    def extract(self, input_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Coordinate extraction process."""
        ...

    @abstractmethod
    def register_extractor(self, extractor: IExtractor) -> None:
        """Register a new extractor."""
        ...

    @abstractmethod
    def get_extractors(self) -> List[IExtractor]:
        """Get all registered extractors."""
        ...