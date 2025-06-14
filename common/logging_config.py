"""Logging configuration for the PowerBuilder pipeline."""

import logging
import os
from typing import Optional


def configure_pipeline_logging(
    verbose: bool = False,
    log_file: Optional[str] = None,
    max_message_length: int = 200,
) -> None:
    """Configure logging for pipeline execution.
    
    Args:
        verbose: If True, enable detailed logging. If False, reduce verbosity.
        log_file: Optional path to log file. If provided, logs will be written to file.
        max_message_length: Maximum length of log messages before truncation.
    """
    # Base configuration
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if log_file:
        # File logging with full details
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, mode='w'),
                logging.StreamHandler()  # Also log to console
            ]
        )
    else:
        # Console only logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format=log_format
        )
    
    # Configure specific loggers to reduce verbosity
    if not verbose:
        # Extraction phase - reduce DAT block messages
        logging.getLogger('extract.pbd.structures.data_block').setLevel(logging.WARNING)
        logging.getLogger('extract.pbd.extraction').setLevel(logging.WARNING)
        logging.getLogger('extract.pbd.io').setLevel(logging.WARNING)
        
        # Decompilation phase - reduce P-code messages  
        logging.getLogger('decompile.analysis').setLevel(logging.WARNING)
        logging.getLogger('decompile.core.pcode_decoder').setLevel(logging.WARNING)
        logging.getLogger('decompile.core.expression_reconstructor').setLevel(logging.WARNING)
        
        # Keep coordinator level messages
        logging.getLogger('extract.extract_coordinator').setLevel(logging.INFO)
        logging.getLogger('decompile.decompile_coordinator').setLevel(logging.INFO)
        logging.getLogger('parse.parse_coordinator').setLevel(logging.INFO)
        logging.getLogger('model.model_coordinator').setLevel(logging.INFO)
        logging.getLogger('generate.generate_coordinator').setLevel(logging.INFO)
    
    # Add custom filter to truncate long messages
    class MessageTruncateFilter(logging.Filter):
        def filter(self, record):
            if len(record.getMessage()) > max_message_length:
                record.msg = record.getMessage()[:max_message_length] + "... [truncated]"
                record.args = ()  # Clear args to prevent re-formatting
            return True
    
    # Apply truncation filter to root logger
    if not verbose:
        root_logger = logging.getLogger()
        truncate_filter = MessageTruncateFilter()
        for handler in root_logger.handlers:
            handler.addFilter(truncate_filter)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_extraction_progress_mode() -> None:
    """Set logging mode for extraction progress display."""
    # Silence most extraction logs except progress
    for logger_name in [
        'extract.pbd.structures.data_block',
        'extract.pbd.extraction.extractor', 
        'extract.pbd.io.file_operations',
        'extract.pbd.analysis.symbol_table',
        'extract.pbd.analysis.cross_reference',
    ]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Keep only coordinator INFO level
    logging.getLogger('extract.extract_coordinator').setLevel(logging.INFO)


def set_decompilation_progress_mode() -> None:
    """Set logging mode for decompilation progress display."""
    # Silence most decompilation logs except progress
    for logger_name in [
        'decompile.analysis.pcode_detector',
        'decompile.analysis.pcode_detector_enhanced',
        'decompile.core.pcode_decoder',
        'decompile.core.expression_reconstructor',
        'decompile.core.output_formatter',
    ]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Keep only coordinator INFO level
    logging.getLogger('decompile.decompile_coordinator').setLevel(logging.INFO)