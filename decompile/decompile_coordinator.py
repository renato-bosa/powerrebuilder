"""Main PowerBuilder decompiler orchestrator.

This module orchestrates the complete decompilation process following the
"best of both worlds" approach, combining accuracy from PbdViewer with
the portability of PowerBuilder-decompile.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.object_type_detector import ObjectTypeDetector
from extract.pbd.constants import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
from extract.pbd.structures.header import extract_pbl_header
from extract.pbd.structures.node import extract_nods
from extract.pbd.utils.version_detector import PBVersionDetector as VersionDetector
from extract.pbd.utils.version_detector import PowerBuilderVersion

from .analysis.control_flow_analyzer import ControlFlowAnalyzer
from .analysis.datawindow_extractor import extract_datawindow_from_pbd
from .analysis.object_parser import ObjectParser
from .core.expression_reconstructor import ExpressionReconstructor
from .core.output_formatter import OutputFormatter
from .core.pcode_decoder import PCodeDecoderV2
from .core.post_processor import DecompiledOutputFilter

logger = logging.getLogger(__name__)


class ExtractedFileDecompiler:
    """Decompiler for extracted P-code files (.fun, .str, .men)."""

    def __init__(
        self, output_dir: Path | None = None, enable_filtering: bool = True
    ) -> None:
        """Initialize the decompiler.

        Args:
            output_dir: Directory to write decompiled files (None for stdout only)
            enable_filtering: Whether to apply post-processing filters
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        self.enable_filtering = enable_filtering
        self.output_filter = DecompiledOutputFilter() if enable_filtering else None

    def decompile_extracted_file(self, file_path: Path) -> bool:
        """Decompile an extracted P-code file.

        Args:
            file_path: Path to the extracted file (.fun, .str, .men)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Decompiling extracted file: {file_path}")

        try:
            # Read the file
            with open(file_path, "rb") as f:
                data = f.read()

            if len(data) == 0:
                logger.warning(f"Empty file: {file_path}")
                return False

            # Get object name from filename
            object_name = file_path.stem
            file_ext = file_path.suffix.lower()
            # Pass full filename with extension for proper type detection
            full_object_name = file_path.name

            # Parse the PowerBuilder object to extract P-code
            pb_object = ObjectParser.parse_object(data, object_name)

            if not pb_object:
                logger.warning(f"Failed to parse object structure in {file_path}")
                return self._generate_stub(
                    file_path, "Failed to parse object structure"
                )

            if pb_object.pcode_offset < 0 or not pb_object.pcode_data:
                logger.warning(f"No P-code found in object {file_path}")
                return self._generate_stub(file_path, "No P-code found in object")

            logger.info(
                f"Found P-code at offset 0x{pb_object.pcode_offset:04x}, length {pb_object.pcode_length} bytes"
            )

            # Detect PowerBuilder version from file structure
            # For now, use a default version (PowerBuilder 10.5 Unicode)
            version = PowerBuilderVersion(10, 5, True)

            # Decode P-code
            decoder = PCodeDecoderV2(version)
            decoded_obj = decoder.decode_pcode_section(
                pb_object.pcode_data,
                full_object_name,  # Use full name with extension for type detection
                None,  # We've already extracted the P-code
            )

            if not decoded_obj.instructions:
                logger.warning(f"No instructions decoded from {file_path}")
                return self._generate_stub(file_path, "No instructions decoded")

            # Step 5: Analyze control flow
            cf_analyzer = ControlFlowAnalyzer()
            control_blocks = cf_analyzer.analyze(decoded_obj.instructions)

            # Step 6: Reconstruct expressions using stack emulation
            emulator = ExpressionReconstructor()
            for block in control_blocks:
                try:
                    emulator.emulate_block(block)
                except Exception as e:
                    logger.warning(
                        f"Expression reconstruction failed for block in {file_path}: {e}"
                    )
                    # Continue with other blocks

            # Step 7: Generate output using advanced formatter
            formatter = OutputFormatter()
            output_lines = formatter.format_object(
                decoded_obj,
                control_blocks,
                str(file_path),
            )

            # Determine output file extension based on input
            output_ext = {
                ".fun": ".sru",  # Functions -> user objects
                ".str": ".srs",  # Structures
                ".men": ".srm",  # Menus
            }.get(file_ext, ".pb")

            # Write output
            if self.output_dir:
                # Preserve directory structure by creating parallel structure
                # Extract structure is typically: output/extracted/pbd_name/pbd_name/file.fun
                # We want: output/decompiled/pbd_name/pbd_name/file.sru
                try:
                    # Find the 'extracted' directory in the path
                    parts = file_path.parts
                    extracted_idx = -1
                    for i, part in enumerate(parts):
                        if part == "extracted":
                            extracted_idx = i
                            break

                    if extracted_idx >= 0:
                        # Get the relative path after 'extracted'
                        relative_parts = parts[extracted_idx + 1 :]
                        relative_path = (
                            Path(*relative_parts) if relative_parts else Path()
                        )
                        output_path = (
                            self.output_dir
                            / relative_path.parent
                            / f"{object_name}{output_ext}"
                        )
                    else:
                        # Fallback: just use the filename
                        output_path = self.output_dir / f"{object_name}{output_ext}"
                except Exception as e:
                    logger.warning(f"Could not preserve directory structure: {e}")
                    output_path = self.output_dir / f"{object_name}{output_ext}"

                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Apply filtering if enabled
                content = "\n".join(output_lines)
                if self.enable_filtering and self.output_filter:
                    content = self.output_filter.filter_output(content)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Wrote decompiled source to {output_path}")
            else:
                pass

            return True

        except Exception as e:
            logger.error(f"Failed to decompile {file_path}: {e}", exc_info=True)
            return False

    def _generate_stub(self, file_path: Path, reason: str) -> bool:
        """Generate a stub file for objects that couldn't be decompiled.

        Args:
            file_path: Path to the original file
            reason: Reason for failure

        Returns:
            True (always succeeds)
        """
        object_name = file_path.stem
        file_ext = file_path.suffix.lower()

        # Generate appropriate stub based on file type
        if file_ext == ".fun":
            stub_content = f"""// Function: {object_name}
// Generated stub - {reason}
// Original file: {file_path}

function {object_name}()
    // TODO: Implementation not available
    // This function's P-code could not be decompiled
end function
"""
        elif file_ext == ".str":
            stub_content = f"""// Structure: {object_name}
// Generated stub - {reason}
// Original file: {file_path}

global type {object_name} from structure
    // TODO: Structure definition not available
end type
"""
        elif file_ext == ".men":
            stub_content = f"""// Menu: {object_name}
// Generated stub - {reason}
// Original file: {file_path}

global type {object_name} from menu
end type
global {object_name} {object_name}

on {object_name}.create
    // TODO: Menu implementation not available
end on

on {object_name}.destroy
    // TODO: Cleanup code not available
end on
"""
        else:
            stub_content = f"""// Object: {object_name}
// Generated stub - {reason}
// Original file: {file_path}
// Type: {file_ext}

// TODO: Implementation not available
"""

        # Determine output extension
        output_ext = {
            ".fun": ".sru",
            ".str": ".srs",
            ".men": ".srm",
        }.get(file_ext, ".pb")

        if self.output_dir:
            # Use same path logic as main decompile method
            try:
                parts = file_path.parts
                extracted_idx = -1
                for i, part in enumerate(parts):
                    if part == "extracted":
                        extracted_idx = i
                        break

                if extracted_idx >= 0:
                    relative_parts = parts[extracted_idx + 1 :]
                    relative_path = Path(*relative_parts) if relative_parts else Path()
                    output_path = (
                        self.output_dir
                        / relative_path.parent
                        / f"{object_name}{output_ext}"
                    )
                else:
                    output_path = self.output_dir / f"{object_name}{output_ext}"
            except Exception as e:
                logger.warning(f"Could not preserve directory structure: {e}")
                output_path = self.output_dir / f"{object_name}{output_ext}"

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(stub_content)
            logger.info(f"Wrote stub file to {output_path}")
        else:
            pass

        return True


class PowerBuilderDecompiler:
    """Main orchestrator for PowerBuilder decompilation."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize the decompiler.

        Args:
            output_dir: Directory to write decompiled files (None for stdout only)
        """
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

    def decompile_pbd(self, pbd_path: Path) -> bool:
        """Decompile a complete PBD file.

        Args:
            pbd_path: Path to the PBD file

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting decompilation of {pbd_path}")

        try:
            with open(pbd_path, "rb") as pbd_file:
                # Step 1: Parse header and detect version
                logger.info("Parsing PBD header...")
                header = extract_pbl_header(
                    pbd_file,
                    block_size=DEFAULT_BLOCK_SIZE,
                    file_path_for_error_log=str(pbd_path),
                )

                # Detect PowerBuilder version
                version = VersionDetector.detect_from_file(pbd_file)
                if version is None:
                    version = VersionDetector.get_default_version(header.is_unicode)
                    logger.warning(
                        f"Could not detect version, using default: {version}"
                    )
                else:
                    logger.info(f"Detected PowerBuilder version: {version}")

                # Step 2: Parse object directory
                logger.info("Parsing object directory...")
                nodes = extract_nods(
                    pbd_file,
                    header.is_unicode,
                    header.first_nod_offset,
                    DEFAULT_BLOCK_SIZE,
                )

                # Count total objects
                total_objects = sum(
                    len(node.entry_defs) if node and hasattr(node, "entry_defs") else 0
                    for node in nodes
                )
                logger.info(f"Found {total_objects} objects in PBD")

                # Step 3: Process each object
                decompiled_count = 0
                for node in nodes:
                    if node and hasattr(node, "entry_defs") and node.entry_defs:
                        for entry in node.entry_defs:
                            if entry:
                                success = self._decompile_object(
                                    pbd_file,
                                    entry,
                                    version,
                                    pbd_path.name,
                                )
                                if success:
                                    decompiled_count += 1

                logger.info(
                    f"Successfully decompiled {decompiled_count}/{total_objects} objects"
                )
                return decompiled_count > 0

        except Exception as e:
            logger.error(f"Failed to decompile {pbd_path}: {e}", exc_info=True)
            return False

    def _decompile_object(
        self, pbd_file, entry, version: PowerBuilderVersion, pbd_name: str
    ) -> bool:
        """Decompile a single object from the PBD.

        Args:
            pbd_file: Open PBD file handle
            entry: Entry definition for the object
            version: PowerBuilder version
            pbd_name: Name of the PBD file

        Returns:
            True if successful, False otherwise
        """
        try:
            object_name = entry.objectname
            logger.debug(f"Decompiling {object_name}")

            # Use object type detector to classify the object
            obj_type_name, contains_pcode = ObjectTypeDetector.get_object_info(
                object_name
            )

            # Check if it's a DataWindow (special handling)
            if ObjectTypeDetector.is_datawindow(object_name):
                logger.debug(
                    f"Skipping DataWindow {object_name} - handled during extraction"
                )
                return False

            # Check if it's a Structure (special handling)
            if ObjectTypeDetector.is_structure(object_name):
                logger.debug(
                    f"Skipping Structure {object_name} - no P-code to decompile"
                )
                return False

            # Skip objects that don't contain P-code
            if not contains_pcode:
                logger.debug(
                    f"Skipping {obj_type_name} {object_name} - no P-code expected"
                )
                return False

            # Step 4: Extract and decode P-code
            decoder = PCodeDecoderV2(version)
            decoded_obj = decoder.decode_pbd_object(
                pbd_file,
                entry.offset,
                entry.objectsize,
                object_name,
            )

            if not decoded_obj.instructions:
                logger.warning(f"No P-code found in {object_name}")
                return False

            # Step 5: Analyze control flow
            cf_analyzer = ControlFlowAnalyzer()
            control_blocks = cf_analyzer.analyze(decoded_obj.instructions)

            # Step 6: Reconstruct expressions using stack emulation
            emulator = ExpressionReconstructor()
            for block in control_blocks:
                emulator.emulate_block(block)

            # Step 7: Generate output
            formatter = OutputFormatter()
            output_lines = formatter.format_object(
                decoded_obj,
                control_blocks,
                pbd_name,
            )

            # Write or print output
            if self.output_dir:
                output_path = self.output_dir / f"{object_name}.pb"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines))
                logger.debug(f"Wrote {output_path}")
            else:
                # Print to stdout
                pass

            return True

        except Exception as e:
            logger.exception(f"Failed to decompile {entry.objectname}: {e}")
            return False

    def _extract_datawindow(self, pbd_file, entry, pbd_name: str) -> bool:
        """Extract DataWindow syntax directly.

        Args:
            pbd_file: Open PBD file handle
            entry: Entry definition for the DataWindow
            pbd_name: Name of the PBD file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Seek to DataWindow data
            pbd_file.seek(entry.offset)
            dw_data = pbd_file.read(entry.objectsize)

            # Use the improved DataWindow extractor
            syntax = extract_datawindow_from_pbd(dw_data, entry.objectname)

            if syntax:
                # Successfully extracted syntax
                output_text = f"""// DataWindow: {entry.objectname}
// From: {pbd_name}
// Type: DataWindow
// Successfully extracted DataWindow syntax

{syntax}
"""

                if self.output_dir:
                    # Save as .sql to indicate it's DataWindow SQL/syntax
                    output_path = self.output_dir / f"{entry.objectname}.sql"
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(output_text)
                    logger.debug(f"Wrote DataWindow syntax to {output_path}")
                else:
                    pass

                return True
            # Could not extract syntax - check if it's a binary DataWindow
            if dw_data.startswith(b"DAT*"):
                # Extract version info
                pdw_version = "Unknown"
                if b"PDW" in dw_data[:50]:
                    pdw_pos = dw_data.find(b"PDW")
                    pdw_version = (
                        dw_data[pdw_pos : pdw_pos + 8]
                        .decode("ascii", errors="ignore")
                        .strip("\x00")
                    )

                output_text = f"""// DataWindow: {entry.objectname}
// Format: Binary/Compiled DataWindow ({pdw_version})
//
// Unable to extract DataWindow syntax from this binary format.
// This could be due to:
// 1. The DataWindow is compiled without embedded source
// 2. The syntax is in an unknown format or location
// 3. The syntax data is compressed or encrypted
//
// Binary format details:
// - Magic: DAT*
// - Size: {entry.objectsize} bytes
// - PowerBuilder Version: {pdw_version}
"""

                if self.output_dir:
                    output_path = self.output_dir / f"{entry.objectname}.txt"
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(output_text)
                    logger.debug(f"Wrote DataWindow metadata to {output_path}")
                else:
                    pass

                return True
            logger.warning(f"Unknown DataWindow format for {entry.objectname}")
            return False

        except Exception as e:
            logger.exception(f"Failed to extract DataWindow {entry.objectname}: {e}")
            return False


def decompile_directory(
    input_dir: str | Path, output_dir: str | Path, progress=None
) -> None:
    """Decompile all extracted P-code files in a directory structure.

    Args:
        input_dir: Directory containing extracted P-code files (.fun, .str, .men)
        output_dir: Directory to write decompiled source files
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Decompiling extracted files from: {input_path} -> {output_path}")

    decompiled_count = 0
    failed_count = 0

    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"Input directory not found: {input_path}")
        return

    # Create a decompiler instance
    decompiler = ExtractedFileDecompiler(output_path)

    # Process only files that contain P-code
    # Note: .str files are structures and don't contain P-code - removing from list
    pcode_extensions = [".fun", ".men", ".mef", ".apf"]
    processed_files = set()

    # First, collect all files to process
    all_pcode_files = []
    for ext in pcode_extensions:
        all_pcode_files.extend(input_path.rglob(f"*{ext}"))

    # Also look for compiled user objects and windows that might not have standard extensions
    for pattern in ["*.udo", "*.win"]:
        all_pcode_files.extend(input_path.rglob(pattern))

    total_files = len(all_pcode_files)

    # Create operation context if progress is provided
    if progress:
        with progress.operation_context(
            "Decompiling functions", total=total_files
        ) as op_task:
            for i, pcode_file in enumerate(all_pcode_files):
                if pcode_file in processed_files:
                    continue
                processed_files.add(pcode_file)

                # Double-check with object type detector
                if not ObjectTypeDetector.should_decompile(str(pcode_file.name)):
                    logger.debug(
                        f"Skipping {pcode_file.name} - not a decompilable file"
                    )
                    continue

                progress.update_operation(i + 1, f"Decompiling {pcode_file.name}")
                logger.info(f"Processing: {pcode_file}")
                try:
                    if decompiler.decompile_extracted_file(pcode_file):
                        decompiled_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.exception(f"Failed to decompile {pcode_file}: {e}")
                    failed_count += 1
    else:
        for pcode_file in all_pcode_files:
            if pcode_file in processed_files:
                continue
            processed_files.add(pcode_file)

            # Double-check with object type detector
            if not ObjectTypeDetector.should_decompile(str(pcode_file.name)):
                logger.debug(f"Skipping {pcode_file.name} - not a decompilable file")
                continue

            logger.info(f"Processing: {pcode_file}")
            try:
                if decompiler.decompile_extracted_file(pcode_file):
                    decompiled_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.exception(f"Failed to decompile {pcode_file}: {e}")
                failed_count += 1

    logger.info(
        f"Decompilation complete. Success: {decompiled_count}, Failed: {failed_count}"
    )


def main() -> None:
    """Command-line interface for the decompiler."""
    parser = argparse.ArgumentParser(
        description="PowerBuilder PBD Decompiler - Best of Both Worlds Edition",
    )
    parser.add_argument(
        "pbd_file",
        type=Path,
        help="Path to the PBD file to decompile",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        help="Directory to write decompiled files (default: stdout)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Check input file
    if not args.pbd_file.exists():
        sys.exit(1)

    if args.pbd_file.suffix.lower() not in [".pbd", ".pbl"]:
        pass

    # Run decompiler
    decompiler = PowerBuilderDecompiler(args.output_dir)
    success = decompiler.decompile_pbd(args.pbd_file)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
