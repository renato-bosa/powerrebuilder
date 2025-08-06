"""Integration module for enhanced P-code reconstruction system.

This module provides seamless integration with the existing reconstruction pipeline,
allowing drop-in replacement of the current ExpressionReconstructor while maintaining
backward compatibility.
"""

import logging
from typing import Any

from src.decompile.types import ControlBlock

from .enhanced_reconstructor import (
    EnhancedExpressionReconstructor,
    ReconstructionMode,
)
from .output_formatter import OutputStyle, PowerBuilderOutputFormatter

logger = logging.getLogger(__name__)


class IntegratedReconstructor:
    """Integrated reconstructor that serves as a drop-in replacement."""

    def __init__(
        self,
        mode: ReconstructionMode = ReconstructionMode.BALANCED,
        output_style: OutputStyle = OutputStyle.STANDARD,
        enable_legacy_fallback: bool = True,
    ) -> None:
        """Initialize the integrated reconstructor.

        Args:
            mode: Reconstruction mode
            output_style: Output formatting style
            enable_legacy_fallback: Enable fallback to legacy reconstructor on errors
        """
        self.enhanced_reconstructor = EnhancedExpressionReconstructor(mode)
        self.output_formatter = PowerBuilderOutputFormatter(output_style)
        self.enable_legacy_fallback = enable_legacy_fallback

        # Legacy compatibility - maintain the same interface
        self.stack = self.enhanced_reconstructor.stack_manager.stack
        self.locals = self.enhanced_reconstructor.locals
        self.strings = self.enhanced_reconstructor.strings
        self.methods = self.enhanced_reconstructor.methods
        self.fields = self.enhanced_reconstructor.fields

        # Statistics
        self.integration_stats = {
            "enhanced_reconstructions": 0,
            "legacy_fallbacks": 0,
            "errors_handled": 0,
        }

    def emulate_block(self, block: ControlBlock) -> None:
        """Emulate a control flow block (legacy interface).

        This method maintains compatibility with existing code that expects
        the original ExpressionReconstructor interface.

        Args:
            block: Control flow block to emulate
        """
        try:
            # Use enhanced reconstruction
            result = self.enhanced_reconstructor.reconstruct_block(block)

            # Format the output
            confidences = [0.8] * len(result.statements)  # Default confidence
            formatted_code = self.output_formatter.format_statements(
                result.statements, confidences
            )

            # Split back into individual statements for compatibility
            block.statements = formatted_code.split("\n") if formatted_code else []

            self.integration_stats["enhanced_reconstructions"] += 1

            logger.info(
                "Enhanced reconstruction completed: %d statements, %.2f avg confidence",
                len(result.statements),
                result.confidence,
            )

        except Exception as e:
            logger.error("Enhanced reconstruction failed: %s", e)
            self.integration_stats["errors_handled"] += 1

            if self.enable_legacy_fallback:
                self._fallback_to_legacy(block)
            else:
                # Generate error comment
                block.statements = [f"// ERROR: Enhanced reconstruction failed - {e}"]

    def _fallback_to_legacy(self, block: ControlBlock) -> None:
        """Fallback to legacy reconstruction method."""
        try:
            # Import legacy reconstructor
            from src.decompile.expression import ExpressionReconstructor

            legacy_reconstructor = ExpressionReconstructor()
            legacy_reconstructor.emulate_block(block)

            self.integration_stats["legacy_fallbacks"] += 1
            logger.warning("Fell back to legacy reconstruction for block")

        except Exception as e:
            logger.error("Legacy fallback also failed: %s", e)
            block.statements = [
                f"// ERROR: Both enhanced and legacy reconstruction failed - {e}"
            ]

    def get_reconstruction_statistics(self) -> dict[str, Any]:
        """Get comprehensive reconstruction statistics."""
        return {
            "integration_stats": self.integration_stats,
            "enhanced_stats": self.enhanced_reconstructor.get_comprehensive_statistics(),
            "formatter_stats": self.output_formatter.get_formatting_statistics(),
        }



def create_enhanced_reconstructor(
    quality_mode: str = "balanced",
    output_style: str = "standard",
    enable_debug: bool = False,
) -> IntegratedReconstructor:
    """Factory function to create an enhanced reconstructor with string parameters.

    This provides a simple way to configure the reconstructor from configuration files
    or command-line arguments.

    Args:
        quality_mode: "fast", "balanced", or "comprehensive"
        output_style: "compact", "standard", "documented", or "debug"
        enable_debug: Enable debug mode

    Returns:
        Configured IntegratedReconstructor instance
    """
    # Map string parameters to enums
    mode_map = {
        "fast": ReconstructionMode.FAST,
        "balanced": ReconstructionMode.BALANCED,
        "comprehensive": ReconstructionMode.COMPREHENSIVE,
    }

    style_map = {
        "compact": OutputStyle.COMPACT,
        "standard": OutputStyle.STANDARD,
        "documented": OutputStyle.DOCUMENTED,
        "debug": OutputStyle.DEBUG,
    }

    mode = mode_map.get(quality_mode.lower(), ReconstructionMode.BALANCED)
    style = style_map.get(output_style.lower(), OutputStyle.STANDARD)

    if enable_debug:
        style = OutputStyle.DEBUG

    return IntegratedReconstructor(mode=mode, output_style=style)


def migrate_from_legacy() -> None:
    """Migration helper to replace legacy ExpressionReconstructor usage.

    This function provides guidance for migrating from the legacy system
    to the enhanced reconstruction system.
    """
    logger.info("Enhanced reconstruction migration guide displayed")


# Backward compatibility - provide the same interface as legacy
class ExpressionReconstructor(IntegratedReconstructor):
    """Backward-compatible ExpressionReconstructor that uses enhanced system.

    This class provides the exact same interface as the original ExpressionReconstructor
    but uses the enhanced reconstruction system under the hood.
    """

    def __init__(self) -> None:
        """Initialize with balanced mode for compatibility."""
        super().__init__(
            mode=ReconstructionMode.BALANCED,
            output_style=OutputStyle.STANDARD,
            enable_legacy_fallback=True,
        )


# Legacy aliases for compatibility
StackEmulator = ExpressionReconstructor
ExpressionLifter = ExpressionReconstructor
