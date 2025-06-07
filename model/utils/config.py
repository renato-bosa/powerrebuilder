"""Configuration handling for PowerBuilder tools.

This module provides configuration loading and validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomli

import logging

from .errors import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Tool configuration."""

    # Input/Output
    input_dir: Path
    output_dir: Path

    # Processing options
    unicode: bool = False
    verbose: bool = False

    # Frontend options
    frontend_framework: str = "react"
    ui_style: str = "tailwind"
    include_docker: bool = False

    # Logging options
    log_file: Path | None = None
    json_logs: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        """Create config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Convert path strings to Path objects
            if "input_dir" in data:
                data["input_dir"] = Path(data["input_dir"])
            if "output_dir" in data:
                data["output_dir"] = Path(data["output_dir"])
            if "log_file" in data:
                data["log_file"] = Path(data["log_file"])

            return cls(**data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e


def load_config(config_file: Path) -> Config:
    """Load configuration from TOML file.

    Args:
        config_file: Path to TOML configuration file

    Returns:
        Config instance

    Raises:
        ConfigurationError: If configuration file cannot be loaded or is invalid
    """
    try:
        with open(config_file, "rb") as f:
            data = tomli.load(f)
        return Config.from_dict(data)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load config from {config_file}: {e}",
        ) from e


def validate_config(config: Config) -> None:
    """Validate configuration.

    Args:
        config: Configuration to validate

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Check input directory
    if not config.input_dir.exists():
        raise ConfigurationError(f"Input directory does not exist: {config.input_dir}")

    # Check output directory parent exists
    if not config.output_dir.parent.exists():
        raise ConfigurationError(
            f"Parent of output directory does not exist: {config.output_dir.parent}",
        )

    # Check frontend framework
    if config.frontend_framework not in {"react", "astro"}:
        raise ConfigurationError(
            f"Invalid frontend framework: {config.frontend_framework}",
        )

    # Check UI style
    if config.ui_style not in {"tailwind", "daisyui", "apple"}:
        raise ConfigurationError(
            f"Invalid UI style: {config.ui_style}",
        )

    # Check log file parent directory exists
    if config.log_file and not config.log_file.parent.exists():
        raise ConfigurationError(
            f"Parent of log file does not exist: {config.log_file.parent}",
        )
