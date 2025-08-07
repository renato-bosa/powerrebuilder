#!/usr/bin/env python3
"""Demo of standardized error handling patterns.

This demonstrates the unified error handling system including:
- Error context management
- Recovery strategies
- Error collection and aggregation
- User-friendly error reporting
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.common.errors import (
    ErrorCollector,
    ErrorContext,
    ErrorManager,
    ErrorSeverity,
    error_handler,
    get_error_manager,
    with_retry,
)
from src.core.exceptions import (
    ExtractError,
    ParseError,
    TransactionError,
    ValidationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_error_context():
    """Demonstrate error context management."""
    logger.info("=== Error Context Management Demo ===")

    # Example 1: Basic error context
    try:
        with error_handler("parse", "parsing source file", file_path=Path("test.sru")):
            # Simulate parsing error
            raise ParseError(
                "Unexpected token 'THEN'", filename="test.sru", line=42, column=15
            )
    except ParseError as e:
        logger.error("Caught parse error: %s", e)

    # Example 2: Error with additional context
    try:
        with error_handler(
            "extract",
            "extracting object",
            file_path=Path("app.pbl"),
            object_name="w_main",
            object_type="window",
        ):
            # Simulate extraction error
            raise ExtractError("Corrupted object header")
    except ExtractError as e:
        logger.error("Caught extraction error: %s", e)

    # Example 3: Nested contexts
    try:
        with error_handler("generate", "generating code"):
            logger.info("Processing application...")

            with error_handler(
                "generate", "processing window", file_path=Path("w_main.srw")
            ):
                # Simulate nested error
                raise ValidationError("Invalid control property: negative width")
    except ValidationError as e:
        logger.error("Caught validation error: %s", e)


def demo_error_collection():
    """Demonstrate error collection and aggregation."""
    logger.info("\n=== Error Collection Demo ===")

    # Create error collector for parsing stage
    collector = ErrorCollector(stage="parse", max_errors=50)

    # Simulate parsing multiple files
    files = [
        ("file1.sru", [(10, "Missing semicolon"), (25, "Undefined variable")]),
        ("file2.sru", [(5, "Invalid syntax"), (30, "Type mismatch")]),
        ("file3.sru", [(15, "Unexpected EOF")]),
    ]

    for filename, errors in files:
        for line, message in errors:
            try:
                # Simulate error in context
                with error_handler(
                    "parse",
                    f"parsing {filename}",
                    file_path=Path(filename),
                    collector=collector,
                ) as ctx:
                    ctx.line_number = line
                    raise ParseError(message, filename=filename, line=line)
            except ParseError:
                pass  # Collected, not raised

    # Add some warnings
    collector.add_warning(
        "Deprecated function usage", ErrorContext(stage="parse", operation="analysis")
    )
    collector.add_warning(
        "Unused variable 'temp'",
        ErrorContext(
            stage="parse",
            operation="analysis",
            file_path=Path("file1.sru"),
            line_number=50,
        ),
    )

    # Show summary
    summary = collector.get_summary()
    logger.info("Error summary: %s", summary)

    # Format errors for display
    logger.info("\nFormatted errors:")

    # Check if we should fail
    if collector.has_errors():
        logger.warning("Found %d errors", collector.get_error_count())
        # collector.raise_if_errors()  # Would raise exception


def demo_retry_logic():
    """Demonstrate retry logic for transient errors."""
    logger.info("\n=== Retry Logic Demo ===")

    # Simulate flaky operation
    attempt_count = 0

    def flaky_operation() -> str:
        nonlocal attempt_count
        attempt_count += 1
        logger.info("Attempt %d: Trying to connect...", attempt_count)

        if attempt_count < 3:
            raise ConnectionError("Connection refused")

        return "Connection successful!"

    # Use retry wrapper
    try:
        result = with_retry(
            flaky_operation,
            max_retries=3,
            delay=0.5,
            backoff=2.0,
            exceptions=(ConnectionError,),
        )
        logger.info("Result: %s", result)
    except ConnectionError as e:
        logger.error("Failed after all retries: %s", e)


def demo_recovery_strategies():
    """Demonstrate error recovery strategies."""
    logger.info("\n=== Recovery Strategies Demo ===")

    get_error_manager()

    # Example 1: Encoding error with fallback
    try:
        with error_handler("extract", "reading file"):
            # Simulate encoding error
            b"\x80\x81\x82".decode("utf-8")
    except UnicodeDecodeError:
        logger.info("Handled encoding error with fallback")

    # Example 2: File not found with custom handling
    class CustomFileHandler:
        def handle_missing_file(self, filename: str) -> str:
            logger.info("File %s not found, using default content", filename)
            return "# Default content\n"

    handler = CustomFileHandler()

    try:
        with error_handler("parse", "loading configuration"):
            # Try to read non-existent file
            Path("missing_config.ini").read_text()
    except FileNotFoundError:
        # Use custom recovery
        handler.handle_missing_file("missing_config.ini")
        logger.info("Recovered with default content")


def demo_error_aggregation():
    """Demonstrate error aggregation across pipeline stages."""
    logger.info("\n=== Error Aggregation Demo ===")

    error_manager = ErrorManager()

    # Simulate pipeline stages with errors
    stages = ["extract", "parse", "model", "generate"]

    for stage in stages:
        collector = error_manager.get_collector(stage)

        # Add some errors and warnings
        for i in range(3):
            if i == 0:
                collector.add_error(
                    ValueError(f"Invalid value in {stage}"),
                    ErrorContext(stage=stage, operation=f"process_item_{i}"),
                )
            else:
                collector.add_warning(
                    f"Potential issue in item {i}",
                    ErrorContext(stage=stage, operation=f"process_item_{i}"),
                )

    # Get comprehensive report
    report = error_manager.get_error_report()
    logger.info("Pipeline error report:")
    logger.info("  Total errors: %d", report["total_errors"])
    logger.info("  Total warnings: %d", report["total_warnings"])
    logger.info("  Affected stages: %s", list(report["stages"].keys()))

    # Format report for display


def demo_exception_chains():
    """Demonstrate exception chain formatting."""
    logger.info("\n=== Exception Chain Formatting Demo ===")

    # Create chained exceptions
    try:
        try:
            try:
                # Original error
                raise ValueError("Invalid configuration value: -1")
            except ValueError as e:
                # Wrap in domain error
                raise ValidationError("Configuration validation failed") from e
        except ValidationError as e:
            # Wrap in transaction error
            raise TransactionError(
                "Failed to initialize transaction", sql_state="HY000"
            ) from e
    except TransactionError:
        # Format the exception chain
        logger.error("Exception chain:")


def demo_stage_specific_handling():
    """Demonstrate stage-specific error handling patterns."""
    logger.info("\n=== Stage-Specific Error Handling Demo ===")

    # Extract stage pattern
    def extract_with_recovery(pbl_path: Path) -> list[str]:
        """Extract with multiple recovery attempts."""
        collector = ErrorCollector(stage="extract")
        extracted = []

        # Try standard extraction
        try:
            with error_handler(
                "extract",
                "standard extraction",
                file_path=pbl_path,
                collector=collector,
            ):
                # Simulate extraction
                if pbl_path.name == "corrupted.pbl":
                    raise ExtractError("Invalid PBL header")
                extracted.append("object1")
        except ExtractError:
            # Try recovery mode
            logger.info("Standard extraction failed, trying recovery mode")
            try:
                with error_handler(
                    "extract",
                    "recovery extraction",
                    file_path=pbl_path,
                    collector=collector,
                ):
                    # Simulate recovery
                    extracted.append("object1_recovered")
            # Test: catch all exceptions to verify error handling
            except Exception as e:
                collector.add_error(e, severity=ErrorSeverity.WARNING)

        # Show what we extracted
        logger.info("Extracted %d objects from %s", len(extracted), pbl_path)
        if collector.has_errors():
            logger.warning(
                "Extraction completed with %d errors", collector.get_error_count()
            )

        return extracted

    # Test extraction
    extract_with_recovery(Path("normal.pbl"))
    extract_with_recovery(Path("corrupted.pbl"))

    # Parse stage pattern with error limits
    def parse_with_error_limit(source_files: list[Path], max_errors: int = 10):
        """Parse with error limit."""
        collector = ErrorCollector(stage="parse", max_errors=max_errors)
        parsed = []

        for source_file in source_files:
            try:
                with error_handler(
                    "parse",
                    f"parsing {source_file.name}",
                    file_path=source_file,
                    collector=collector,
                ):
                    # Simulate parsing with some errors
                    if "error" in source_file.name:
                        raise ParseError(
                            f"Syntax error in {source_file.name}",
                            filename=str(source_file),
                            line=10,
                        )
                    parsed.append(f"AST for {source_file.name}")
            except ParseError:
                pass  # Continue parsing other files

        logger.info("Parsed %d/%d files successfully", len(parsed), len(source_files))

        # Decide whether to continue
        if collector.has_critical_errors():
            logger.error("Critical errors found, cannot continue")
            collector.raise_if_errors()
        elif collector.get_error_count() > max_errors:
            logger.error("Too many errors (%d), stopping", collector.get_error_count())
            collector.raise_if_errors()

        return parsed

    # Test parsing
    test_files = [
        Path("file1.sru"),
        Path("file_with_error.sru"),
        Path("file2.sru"),
        Path("another_error.sru"),
    ]

    try:
        parse_with_error_limit(test_files, max_errors=5)
    except Exception as e:
        logger.error("Parsing failed: %s", e)


def demo_custom_error_handlers():
    """Demonstrate custom error handler registration."""
    logger.info("\n=== Custom Error Handlers Demo ===")

    from src.common.errors import BaseErrorHandler

    class BusinessRuleHandler(BaseErrorHandler):
        """Handle business rule violations."""

        def can_handle(self, error: Exception) -> bool:
            return (
                isinstance(error, ValidationError)
                and "business rule" in str(error).lower()
            )

        def handle(self, error: Exception, context: ErrorContext) -> Any:
            logger.info("Business rule violation in %s: %s", context.operation, error)

            # Record for audit
            self.record_error(error, context, severity=ErrorSeverity.WARNING)

            # Return default value based on context
            if "price" in context.operation:
                return 0.0  # Default price
            if "quantity" in context.operation:
                return 1  # Default quantity

            return None

    # Register custom handler
    error_manager = ErrorManager()
    error_manager.register_handler(BusinessRuleHandler())

    # Test custom handler
    try:
        with error_manager.error_context("validation", "validating price"):
            raise ValidationError("Business rule: price cannot be negative")
    except ValidationError:
        logger.info("Business rule violation was handled")


def main():
    """Run all error handling demos."""
    logger.info("PowerRebuilder Error Handling Demo")
    logger.info("=" * 50)

    # Demo 1: Error context management
    demo_error_context()

    # Demo 2: Error collection
    demo_error_collection()

    # Demo 3: Retry logic
    demo_retry_logic()

    # Demo 4: Recovery strategies
    demo_recovery_strategies()

    # Demo 5: Error aggregation
    demo_error_aggregation()

    # Demo 6: Exception chains
    demo_exception_chains()

    # Demo 7: Stage-specific handling
    demo_stage_specific_handling()

    # Demo 8: Custom handlers
    demo_custom_error_handlers()

    logger.info("\n" + "=" * 50)
    logger.info("Demo completed!")
    logger.info("\nKey Benefits of Standardized Error Handling:")
    logger.info("✓ Consistent error context across all stages")
    logger.info("✓ Automatic retry for transient errors")
    logger.info("✓ Graceful fallback strategies")
    logger.info("✓ Error aggregation without failing fast")
    logger.info("✓ User-friendly error reporting")
    logger.info("✓ Easy integration with logging and monitoring")


if __name__ == "__main__":
    main()
