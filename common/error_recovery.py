"""Error recovery utilities for the pipeline.

This module provides retry mechanisms, error collection, and recovery strategies
for the PowerBuilder conversion pipeline.
"""

import functools
import logging
import time
from datetime import datetime
from typing import TypeVar, Callable, Optional, Dict, List, Tuple, Any
from pathlib import Path
import psutil
import shutil

from .exceptions import SimeFinchError, ExtractError, ParseError, GenerateError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ResourceError(SimeFinchError):
    """Raised when system resources are insufficient."""
    pass


class RetryError(SimeFinchError):
    """Raised when all retry attempts fail."""
    pass


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Factor to multiply delay by for each retry
        exceptions: Tuple of exceptions to catch and retry
        logger: Logger instance for retry messages
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = 1.0
            last_exception = None
            log = logger or logging.getLogger(func.__module__)
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        log.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        log.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise RetryError(f"Failed after {max_attempts} attempts") from last_exception
        
        return wrapper
    return decorator


class FileErrorCollector:
    """Collects and manages errors from file processing."""
    
    def __init__(self):
        self.errors: Dict[str, List[Tuple[str, Exception]]] = {
            'extract': [],
            'parse': [],
            'decompile': [],
            'generate': []
        }
        self.warnings: Dict[str, List[Tuple[str, str]]] = {
            'extract': [],
            'parse': [],
            'decompile': [],
            'generate': []
        }
        
    def add_error(self, stage: str, file_path: str, error: Exception) -> None:
        """Add an error for a specific file and stage."""
        self.errors[stage].append((file_path, error))
        
    def add_warning(self, stage: str, file_path: str, message: str) -> None:
        """Add a warning for a specific file and stage."""
        self.warnings[stage].append((file_path, message))
        
    def has_errors(self, stage: Optional[str] = None) -> bool:
        """Check if there are any errors."""
        if stage:
            return len(self.errors.get(stage, [])) > 0
        return any(len(errors) > 0 for errors in self.errors.values())
        
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors and warnings."""
        return {
            'errors': {
                stage: len(errors) for stage, errors in self.errors.items()
            },
            'warnings': {
                stage: len(warnings) for stage, warnings in self.warnings.items()
            },
            'total_errors': sum(len(errors) for errors in self.errors.values()),
            'total_warnings': sum(len(warnings) for warnings in self.warnings.values())
        }
        
    def log_summary(self) -> None:
        """Log a summary of all errors and warnings."""
        summary = self.get_error_summary()
        
        if summary['total_errors'] > 0:
            logger.error(f"Pipeline completed with {summary['total_errors']} errors:")
            for stage, count in summary['errors'].items():
                if count > 0:
                    logger.error(f"  - {stage}: {count} errors")
                    # Log first few error details
                    for file_path, error in self.errors[stage][:3]:
                        logger.error(f"    • {file_path}: {type(error).__name__}: {error}")
                    if count > 3:
                        logger.error(f"    ... and {count - 3} more")
                        
        if summary['total_warnings'] > 0:
            logger.warning(f"Pipeline completed with {summary['total_warnings']} warnings")


class ResourceChecker:
    """Checks system resources before processing."""
    
    MIN_FREE_DISK_GB = 1.0  # Minimum free disk space in GB
    MIN_FREE_MEMORY_GB = 0.5  # Minimum free memory in GB
    
    @classmethod
    def check_disk_space(cls, path: Path) -> None:
        """Check if there's enough disk space.
        
        Raises:
            ResourceError: If insufficient disk space
        """
        try:
            stat = shutil.disk_usage(path)
            free_gb = stat.free / (1024 ** 3)
            
            if free_gb < cls.MIN_FREE_DISK_GB:
                raise ResourceError(
                    f"Insufficient disk space: {free_gb:.2f}GB free, "
                    f"need at least {cls.MIN_FREE_DISK_GB}GB"
                )
        except ResourceError:
            raise  # Re-raise ResourceError
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            
    @classmethod
    def check_memory(cls) -> None:
        """Check if there's enough memory available.
        
        Raises:
            ResourceError: If insufficient memory
        """
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            
            if available_gb < cls.MIN_FREE_MEMORY_GB:
                raise ResourceError(
                    f"Insufficient memory: {available_gb:.2f}GB available, "
                    f"need at least {cls.MIN_FREE_MEMORY_GB}GB"
                )
        except ResourceError:
            raise  # Re-raise ResourceError
        except Exception as e:
            logger.warning(f"Could not check memory: {e}")
            
    @classmethod
    def check_all(cls, working_dir: Path) -> None:
        """Run all resource checks.
        
        Args:
            working_dir: Directory where processing will occur
            
        Raises:
            ResourceError: If any resource check fails
        """
        cls.check_disk_space(working_dir)
        cls.check_memory()


class PipelineCheckpoint:
    """Manages pipeline checkpointing for recovery."""
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "pipeline_checkpoint.json"
        
    def save(self, stage: str, processed_files: List[str], 
             failed_files: List[str], state: Dict[str, Any]) -> None:
        """Save checkpoint state."""
        import json
        
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'processed_files': processed_files,
            'failed_files': failed_files,
            'state': state
        }
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
                logger.debug(f"Saved checkpoint for stage: {stage}")
        except Exception as e:
            logger.warning(f"Could not save checkpoint: {e}")
            
    def load(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint state."""
        import json
        
        if not self.checkpoint_file.exists():
            return None
            
        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
            return None
            
    def clear(self) -> None:
        """Clear checkpoint."""
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
        except Exception as e:
            logger.warning(f"Could not clear checkpoint: {e}")