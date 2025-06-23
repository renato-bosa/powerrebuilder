"""Configuration management for the PowerBuilder model.

This module provides configuration management functionality for the PowerBuilder
model, including settings for parsing, validation, and type checking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ValidationLevel(Enum):
    """Validation strictness levels."""

    STRICT = auto()  # All rules enforced
    STANDARD = auto()  # Default rules
    LENIENT = auto()  # Minimal validation
    NONE = auto()  # No validation


class TypeCheckingMode(Enum):
    """Type checking modes."""

    STATIC = auto()  # Static type checking only
    DYNAMIC = auto()  # Dynamic type checking only
    HYBRID = auto()  # Both static and dynamic
    NONE = auto()  # No type checking


@dataclass
class ParserConfig:
    """Parser configuration settings."""

    max_errors: int = 100
    error_recovery: bool = True
    preserve_comments: bool = True
    preserve_formatting: bool = False
    strict_syntax: bool = False
    allow_extensions: bool = True
    encoding: str = "utf-8"
    line_ending: str = "\n"


@dataclass
class ValidationConfig:
    """Validation configuration settings."""

    level: ValidationLevel = ValidationLevel.STANDARD
    check_naming_conventions: bool = True
    check_unused_variables: bool = True
    check_unreachable_code: bool = True
    check_deprecated_features: bool = True
    check_sql_injection: bool = True
    check_hardcoded_credentials: bool = True
    max_method_lines: int = 200
    max_class_lines: int = 1000
    max_parameters: int = 10
    max_cyclomatic_complexity: int = 15


@dataclass
class TypeCheckingConfig:
    """Type checking configuration settings."""

    mode: TypeCheckingMode = TypeCheckingMode.HYBRID
    infer_types: bool = True
    check_return_types: bool = True
    check_parameter_types: bool = True
    check_assignment_types: bool = True
    allow_implicit_conversions: bool = True
    strict_null_checking: bool = False
    check_array_bounds: bool = True


@dataclass
class OutputConfig:
    """Output configuration settings."""

    format: str = "json"  # json, xml, yaml
    pretty_print: bool = True
    include_source_maps: bool = True
    include_metadata: bool = True
    output_directory: Path = field(default_factory=lambda: Path("output"))
    create_subdirectories: bool = True


@dataclass
class ModelConfig:
    """Main configuration for the PowerBuilder model."""

    parser: ParserConfig = field(default_factory=ParserConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    type_checking: TypeCheckingConfig = field(default_factory=TypeCheckingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Global settings
    debug: bool = False
    verbose: bool = False
    parallel_processing: bool = True
    max_workers: int | None = None  # None means use CPU count
    cache_enabled: bool = True
    cache_directory: Path = field(default_factory=lambda: Path(".cache"))
    
    # PowerBuilder specific settings
    pb_version: str = "2019"
    case_sensitive: bool = False
    allow_forward_references: bool = True
    
    @classmethod
    def from_file(cls, path: str | Path) -> ModelConfig:
        """Load configuration from a JSON file.
        
        Args:
            path: Path to the configuration file
            
        Returns:
            ModelConfig instance
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
            
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> ModelConfig:
        """Create configuration from dictionary."""
        config = cls()
        
        # Parser settings
        if "parser" in data:
            for key, value in data["parser"].items():
                if hasattr(config.parser, key):
                    setattr(config.parser, key, value)
                    
        # Validation settings
        if "validation" in data:
            for key, value in data["validation"].items():
                if key == "level" and isinstance(value, str):
                    config.validation.level = ValidationLevel[value.upper()]
                elif hasattr(config.validation, key):
                    setattr(config.validation, key, value)
                    
        # Type checking settings
        if "type_checking" in data:
            for key, value in data["type_checking"].items():
                if key == "mode" and isinstance(value, str):
                    config.type_checking.mode = TypeCheckingMode[value.upper()]
                elif hasattr(config.type_checking, key):
                    setattr(config.type_checking, key, value)
                    
        # Output settings
        if "output" in data:
            for key, value in data["output"].items():
                if key == "output_directory":
                    config.output.output_directory = Path(value)
                elif hasattr(config.output, key):
                    setattr(config.output, key, value)
                    
        # Global settings
        for key in ["debug", "verbose", "parallel_processing", "max_workers",
                    "cache_enabled", "pb_version", "case_sensitive", 
                    "allow_forward_references"]:
            if key in data:
                if key == "cache_directory":
                    setattr(config, key, Path(data[key]))
                else:
                    setattr(config, key, data[key])
                    
        return config
    
    def to_file(self, path: str | Path) -> None:
        """Save configuration to a JSON file.
        
        Args:
            path: Path to save the configuration file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self._to_dict()
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def _to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "parser": {
                "max_errors": self.parser.max_errors,
                "error_recovery": self.parser.error_recovery,
                "preserve_comments": self.parser.preserve_comments,
                "preserve_formatting": self.parser.preserve_formatting,
                "strict_syntax": self.parser.strict_syntax,
                "allow_extensions": self.parser.allow_extensions,
                "encoding": self.parser.encoding,
                "line_ending": self.parser.line_ending,
            },
            "validation": {
                "level": self.validation.level.name,
                "check_naming_conventions": self.validation.check_naming_conventions,
                "check_unused_variables": self.validation.check_unused_variables,
                "check_unreachable_code": self.validation.check_unreachable_code,
                "check_deprecated_features": self.validation.check_deprecated_features,
                "check_sql_injection": self.validation.check_sql_injection,
                "check_hardcoded_credentials": self.validation.check_hardcoded_credentials,
                "max_method_lines": self.validation.max_method_lines,
                "max_class_lines": self.validation.max_class_lines,
                "max_parameters": self.validation.max_parameters,
                "max_cyclomatic_complexity": self.validation.max_cyclomatic_complexity,
            },
            "type_checking": {
                "mode": self.type_checking.mode.name,
                "infer_types": self.type_checking.infer_types,
                "check_return_types": self.type_checking.check_return_types,
                "check_parameter_types": self.type_checking.check_parameter_types,
                "check_assignment_types": self.type_checking.check_assignment_types,
                "allow_implicit_conversions": self.type_checking.allow_implicit_conversions,
                "strict_null_checking": self.type_checking.strict_null_checking,
                "check_array_bounds": self.type_checking.check_array_bounds,
            },
            "output": {
                "format": self.output.format,
                "pretty_print": self.output.pretty_print,
                "include_source_maps": self.output.include_source_maps,
                "include_metadata": self.output.include_metadata,
                "output_directory": str(self.output.output_directory),
                "create_subdirectories": self.output.create_subdirectories,
            },
            "debug": self.debug,
            "verbose": self.verbose,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "cache_enabled": self.cache_enabled,
            "cache_directory": str(self.cache_directory),
            "pb_version": self.pb_version,
            "case_sensitive": self.case_sensitive,
            "allow_forward_references": self.allow_forward_references,
        }
    
    def validate(self) -> list[str]:
        """Validate configuration settings.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check parser settings
        if self.parser.max_errors < 0:
            errors.append("parser.max_errors must be non-negative")
            
        # Check validation settings
        if self.validation.max_method_lines < 1:
            errors.append("validation.max_method_lines must be positive")
        if self.validation.max_class_lines < 1:
            errors.append("validation.max_class_lines must be positive")
        if self.validation.max_parameters < 1:
            errors.append("validation.max_parameters must be positive")
        if self.validation.max_cyclomatic_complexity < 1:
            errors.append("validation.max_cyclomatic_complexity must be positive")
            
        # Check output settings
        if self.output.format not in ["json", "xml", "yaml"]:
            errors.append(f"output.format '{self.output.format}' is not supported")
            
        # Check global settings
        if self.max_workers is not None and self.max_workers < 1:
            errors.append("max_workers must be positive or None")
            
        return errors


# Default configuration instance
default_config = ModelConfig()