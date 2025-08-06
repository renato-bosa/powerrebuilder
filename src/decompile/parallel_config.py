"""Configuration management for enhanced parallel decompilation.

This module provides configuration classes and utilities for managing
the complex settings required by the enhanced parallel processing system.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, Optional

import psutil


@dataclass
class TimeoutConfig:
    """Configuration for dynamic timeout calculation."""
    
    # Base timeout factors
    base_timeout_seconds: float = 30.0
    timeout_per_mb: float = 60.0  # seconds per MB
    max_timeout_seconds: float = 1800.0  # 30 minutes
    min_timeout_seconds: float = 30.0  # 30 seconds
    
    # File type multipliers
    type_multipliers: Dict[str, float] = field(default_factory=lambda: {
        '.fun': 1.0,    # Functions - baseline
        '.men': 0.3,    # Menus - simpler
        '.win': 2.0,    # Windows - more complex
        '.app': 1.5,    # Applications
        '.udo': 2.5,    # User objects - most complex
    })
    
    # Complexity adjustment factors
    complexity_multiplier: float = 1.5
    pcode_density_threshold: float = 0.7
    pcode_density_multiplier: float = 1.3
    nested_depth_threshold: int = 5
    nested_depth_multiplier: float = 1.2
    instruction_count_factor: float = 0.001  # per instruction


@dataclass 
class MemoryConfig:
    """Configuration for memory management and monitoring."""
    
    # System memory thresholds (percentages)
    max_system_memory_percent: float = 80.0
    throttle_threshold_percent: float = 75.0
    force_gc_threshold_percent: float = 85.0
    oom_prevention_percent: float = 95.0
    
    # Per-worker memory limits
    worker_memory_limit_mb: float = 512.0
    worker_memory_warning_mb: float = 400.0
    
    # Memory monitoring settings  
    memory_check_interval_seconds: float = 2.0
    memory_history_size: int = 100
    enable_swap_monitoring: bool = True
    
    @classmethod
    def auto_configure(cls) -> 'MemoryConfig':
        """Auto-configure based on system capabilities."""
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        
        config = cls()
        
        # Adjust limits based on available memory
        if total_gb < 4:
            # Low memory system
            config.max_system_memory_percent = 70.0
            config.worker_memory_limit_mb = 256.0
            config.throttle_threshold_percent = 65.0
        elif total_gb > 16:
            # High memory system - can be more aggressive
            config.max_system_memory_percent = 85.0
            config.worker_memory_limit_mb = 1024.0
            config.throttle_threshold_percent = 80.0
        
        return config


@dataclass
class ProgressConfig:
    """Configuration for progress tracking and reporting."""
    
    # Heartbeat settings
    heartbeat_interval_seconds: float = 5.0
    heartbeat_timeout_multiplier: float = 3.0  # 3x interval = timeout
    
    # Checkpoint settings
    checkpoint_interval_seconds: float = 30.0
    checkpoint_retention_days: int = 7
    enable_checkpoint_compression: bool = True
    
    # Progress reporting
    progress_update_interval_seconds: float = 1.0
    enable_eta_calculation: bool = True
    eta_smoothing_window: int = 10
    
    # Performance tracking
    track_detailed_metrics: bool = True
    metrics_history_size: int = 1000


@dataclass
class ParallelismConfig:
    """Configuration for parallel processing behavior."""
    
    # Worker management
    max_workers: Optional[int] = None  # Auto-detect if None
    min_workers: int = 1
    worker_startup_timeout_seconds: float = 30.0
    worker_shutdown_timeout_seconds: float = 10.0
    
    # Task scheduling
    enable_work_stealing: bool = True
    work_stealing_threshold: int = 2  # Minimum tasks before stealing
    rebalance_interval_seconds: float = 10.0
    
    # Process vs thread selection
    prefer_processes: bool = True
    thread_threshold_file_size_mb: float = 0.5  # Use threads for smaller files
    process_memory_overhead_mb: float = 50.0
    
    # Adaptive behavior
    enable_adaptive_scheduling: bool = True
    adaptation_window_size: int = 50  # Files to analyze for adaptation
    performance_threshold_improvement: float = 0.1  # 10% improvement needed
    
    @classmethod
    def auto_configure(cls) -> 'ParallelismConfig':
        """Auto-configure based on system capabilities."""
        cpu_count = os.cpu_count() or 4
        memory = psutil.virtual_memory()
        
        config = cls()
        
        # Determine optimal worker count
        config.max_workers = min(cpu_count, 16)  # Cap at 16
        
        # Adjust based on memory availability
        available_gb = memory.available / (1024**3)
        max_by_memory = max(1, int(available_gb / 0.5))  # 500MB per worker
        config.max_workers = min(config.max_workers, max_by_memory)
        
        # Use threads for low-memory systems
        if available_gb < 4:
            config.prefer_processes = False
            config.max_workers = min(config.max_workers, cpu_count * 2)
        
        return config


@dataclass
class DecompilationConfig:
    """Main configuration class combining all sub-configurations."""
    
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig) 
    progress: ProgressConfig = field(default_factory=ProgressConfig)
    parallelism: ParallelismConfig = field(default_factory=ParallelismConfig)
    
    # Global settings
    enable_caching: bool = True
    cache_directory: Optional[Path] = None
    log_level: str = "INFO"
    debug_mode: bool = False
    
    # Output settings
    output_format: str = "pb"  # pb, txt, md
    preserve_directory_structure: bool = True
    generate_statistics: bool = True
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        config_dict = asdict(self)
        
        # Convert Path objects to strings
        if config_dict.get('cache_directory'):
            config_dict['cache_directory'] = str(config_dict['cache_directory'])
        
        with config_path.open('w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'DecompilationConfig':
        """Load configuration from JSON file."""
        with config_path.open('r') as f:
            config_dict = json.load(f)
        
        # Convert string paths back to Path objects
        if config_dict.get('cache_directory'):
            config_dict['cache_directory'] = Path(config_dict['cache_directory'])
        
        # Recreate nested dataclass objects
        if 'timeout' in config_dict:
            config_dict['timeout'] = TimeoutConfig(**config_dict['timeout'])
        if 'memory' in config_dict:
            config_dict['memory'] = MemoryConfig(**config_dict['memory'])
        if 'progress' in config_dict:
            config_dict['progress'] = ProgressConfig(**config_dict['progress'])
        if 'parallelism' in config_dict:
            config_dict['parallelism'] = ParallelismConfig(**config_dict['parallelism'])
        
        return cls(**config_dict)
    
    @classmethod
    def auto_configure(cls) -> 'DecompilationConfig':
        """Create auto-configured instance based on system capabilities."""
        return cls(
            memory=MemoryConfig.auto_configure(),
            parallelism=ParallelismConfig.auto_configure(),
            cache_directory=Path.home() / '.powerrebuilder' / 'cache'
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate timeout settings
        if self.timeout.min_timeout_seconds >= self.timeout.max_timeout_seconds:
            issues.append("Minimum timeout must be less than maximum timeout")
        
        if self.timeout.timeout_per_mb <= 0:
            issues.append("Timeout per MB must be positive")
        
        # Validate memory settings
        if self.memory.worker_memory_limit_mb <= 0:
            issues.append("Worker memory limit must be positive")
        
        if self.memory.throttle_threshold_percent >= self.memory.max_system_memory_percent:
            issues.append("Throttle threshold must be less than max memory percent")
        
        # Validate parallelism settings
        if self.parallelism.max_workers is not None and self.parallelism.max_workers < 1:
            issues.append("Max workers must be at least 1")
        
        if self.parallelism.min_workers < 1:
            issues.append("Min workers must be at least 1")
        
        # Validate output format
        if self.output_format not in ['pb', 'txt', 'md']:
            issues.append(f"Invalid output format: {self.output_format}")
        
        return issues
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information for diagnostics."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_count': os.cpu_count(),
            'cpu_freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 'unknown',
            'memory_total_gb': memory.total / (1024**3),
            'memory_available_gb': memory.available / (1024**3),
            'memory_percent_used': memory.percent,
            'disk_free_gb': disk.free / (1024**3),
            'disk_percent_used': (disk.used / disk.total) * 100,
            'platform': psutil.uname()._asdict(),
        }


class ConfigManager:
    """Configuration manager with environment variable support."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize config manager."""
        self.config_file = config_file or Path.cwd() / 'powerrebuilder_config.json'
        self._config: Optional[DecompilationConfig] = None
    
    def get_config(self) -> DecompilationConfig:
        """Get configuration, loading from file or auto-configuring."""
        if self._config is None:
            if self.config_file.exists():
                try:
                    self._config = DecompilationConfig.load_from_file(self.config_file)
                    self._apply_environment_overrides()
                except Exception as e:
                    print(f"Failed to load config from {self.config_file}: {e}")
                    print("Using auto-configuration")
                    self._config = DecompilationConfig.auto_configure()
            else:
                self._config = DecompilationConfig.auto_configure()
                self._apply_environment_overrides()
        
        return self._config
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        if not self._config:
            return
        
        # Timeout overrides
        if os.getenv('POWERREBUILDER_MAX_TIMEOUT'):
            try:
                self._config.timeout.max_timeout_seconds = float(os.getenv('POWERREBUILDER_MAX_TIMEOUT'))
            except ValueError:
                pass
        
        # Memory overrides
        if os.getenv('POWERREBUILDER_WORKER_MEMORY_LIMIT'):
            try:
                self._config.memory.worker_memory_limit_mb = float(os.getenv('POWERREBUILDER_WORKER_MEMORY_LIMIT'))
            except ValueError:
                pass
        
        # Parallelism overrides
        if os.getenv('POWERREBUILDER_MAX_WORKERS'):
            try:
                self._config.parallelism.max_workers = int(os.getenv('POWERREBUILDER_MAX_WORKERS'))
            except ValueError:
                pass
        
        # Debug mode
        if os.getenv('POWERREBUILDER_DEBUG', '').lower() in ['true', '1', 'yes']:
            self._config.debug_mode = True
            self._config.log_level = 'DEBUG'
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if self._config:
            self._config.save_to_file(self.config_file)
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to auto-configured defaults."""
        self._config = DecompilationConfig.auto_configure()
        self._apply_environment_overrides()
    
    def validate_config(self) -> list[str]:
        """Validate current configuration."""
        config = self.get_config()
        return config.validate()


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[Path] = None) -> ConfigManager:
    """Get global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def get_config() -> DecompilationConfig:
    """Get current configuration."""
    return get_config_manager().get_config()


# Example configuration presets
def create_development_config() -> DecompilationConfig:
    """Create configuration optimized for development/testing."""
    config = DecompilationConfig.auto_configure()
    
    # Reduce timeouts for faster feedback
    config.timeout.max_timeout_seconds = 300.0  # 5 minutes
    config.timeout.base_timeout_seconds = 15.0
    
    # Enable debug features
    config.debug_mode = True
    config.log_level = "DEBUG"
    config.progress.track_detailed_metrics = True
    
    # Conservative parallelism
    config.parallelism.max_workers = min(4, os.cpu_count() or 4)
    
    return config


def create_production_config() -> DecompilationConfig:
    """Create configuration optimized for production processing."""
    config = DecompilationConfig.auto_configure()
    
    # Aggressive timeouts for throughput
    config.timeout.max_timeout_seconds = 3600.0  # 1 hour
    config.timeout.timeout_per_mb = 30.0  # 30s per MB
    
    # Maximum performance
    config.parallelism.max_workers = None  # Use all available
    config.parallelism.enable_adaptive_scheduling = True
    
    # Production logging
    config.log_level = "INFO"
    config.debug_mode = False
    
    return config


def create_memory_constrained_config() -> DecompilationConfig:
    """Create configuration for memory-constrained environments."""
    config = DecompilationConfig.auto_configure()
    
    # Conservative memory usage
    config.memory.max_system_memory_percent = 60.0
    config.memory.worker_memory_limit_mb = 256.0
    config.memory.throttle_threshold_percent = 50.0
    
    # Use threads instead of processes
    config.parallelism.prefer_processes = False
    config.parallelism.max_workers = min(4, os.cpu_count() or 4)
    
    # Disable caching to save memory
    config.enable_caching = False
    
    return config