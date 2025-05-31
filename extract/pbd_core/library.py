"""Provides a high-level API for interacting with PowerBuilder PBD/PBL files."""
import logging
from pathlib import Path
from typing import BinaryIO

import extract.pbd_core.header as fh  # Import for constants
from extract.pbd_core.dat import (
    extract_data_from_entry,
    get_binary_from_data,
)
from extract.pbd_core.entry import PbEntryDefinition, read_and_parse_entry_def
from extract.pbd_core.exceptions import HeaderError, PbdError, PfcExcludedError
from extract.pbd_core.header import HeaderClass, extract_pbl_header
from extract.pbd_core.node import NodeClass, extract_nods
from extract.pbd_core.pbd_object import PbdObject
from extract.pbd_core.pfc_utils import load_pfc_hashes
from extract.pbd_io.file_operations import (  # For extract_all later
    save_binary_file,
    save_text_file,
)
from extract.pbd_io.progress import (  # Import specific classes
    BaseProgressTracker,
    SilentProgressTracker,
    TqdmProgressTracker,
)
from extract.pbd_io.scanner import (
    detect_block_size_from_dat_spacing,
    scan_for_signatures,
    EXPECTED_BLOCK_SIZES,
)
from extract.pbd_io.utils import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
from extract.pbd_io.utils import (  # Import default block size and expected block sizes
    SOURCE_EXTENSIONS,
)

logger = logging.getLogger(__name__)

# Define a sort order for object types based on extension
# Lower number means higher priority (extracted earlier)
# This is a heuristic for pseudo-topological sort.
OBJECT_TYPE_SORT_ORDER = {
    # Ancestors / Global things often first
    ".sra": 0,  # Application
    ".sru": 1,  # User Object (often ancestors or NVOs)
    # Core UI / Logic
    ".srw": 10,  # Window
    ".srm": 11,  # Menu
    ".srf": 12,  # Function
    # Data-related
    ".srd": 20,  # DataWindow (object definition)
    ".srj": 21,  # Project (less common in PBDs, but for completeness)
    ".srp": 22,  # Pipeline
    ".srq": 23,  # Query
    # Others / Unspecified
    "DEFAULT": 99,
}


class Library:
    """Represents a PowerBuilder Library (PBD/PBL file) and provides
    methods to access its contents.
    """
    def __init__(self,
                 pbd_file_path: str | Path,
                 exclude_pfc: bool = False,
                 pfc_hash_file: str | Path | None = None,
        ) -> None:
        self.pbd_file_path: Path = Path(pbd_file_path)
        self.file_handle: BinaryIO | None = None
        self.header: HeaderClass | None = None
        self.nodes: list[NodeClass] = []
        self.entries_map: dict[str, PbEntryDefinition] = {}  # Keyed by object name
        self.is_recovered_mode: bool = False
        self.detected_block_size: int | None = None
        self.effective_block_size: int = DEFAULT_BLOCK_SIZE  # Initialize with default
        self.exclude_pfc = exclude_pfc
        self.pfc_hashes: set[str] = set()

        if self.exclude_pfc:
            pfc_hash_file_path = Path(pfc_hash_file) if pfc_hash_file else None
            self.pfc_hashes = load_pfc_hashes(pfc_hash_file_path)
            if self.pfc_hashes:
                logger.info(f"PFC exclusion enabled. {len(self.pfc_hashes)} PFC hashes loaded.")
            else:
                logger.warning("PFC exclusion was enabled, but no PFC hashes were loaded. All objects will be processed.")

        if not self.pbd_file_path.exists() or not self.pbd_file_path.is_file():
            raise PbdError(f"PBD file not found or is not a file: {self.pbd_file_path}")

        try:
            self.file_handle = open(self.pbd_file_path, 'rb')

            try:
                self.file_handle.seek(0)
                self.detected_block_size = detect_block_size_from_dat_spacing(self.file_handle)
                if self.detected_block_size and self.detected_block_size in EXPECTED_BLOCK_SIZES:
                    logger.info(f"Using detected block size for {self.pbd_file_path.name}: {self.detected_block_size}")
                    self.effective_block_size = self.detected_block_size
                    if self.effective_block_size != DEFAULT_BLOCK_SIZE:
                        logger.info(  # Changed from warning to info as we are now using it.
                            f"Detected block size {self.effective_block_size} for {self.pbd_file_path.name} is being used, differing from default {DEFAULT_BLOCK_SIZE}.",
                        )
                else:
                    logger.info(f"Could not reliably auto-detect block size or detected size not in expected values for {self.pbd_file_path.name}. Using default: {DEFAULT_BLOCK_SIZE}.")
                    self.effective_block_size = DEFAULT_BLOCK_SIZE  # Explicitly set to default
                self.file_handle.seek(0)
            except Exception as e_bs_detect:
                logger.warning(f"Error during block size detection for {self.pbd_file_path.name}: {e_bs_detect}. Proceeding with default {DEFAULT_BLOCK_SIZE}.")
                self.effective_block_size = DEFAULT_BLOCK_SIZE  # Ensure default on error
                self.file_handle.seek(0)

            try:
                self.header = extract_pbl_header(
                    self.file_handle,
                    block_size=self.effective_block_size,  # Pass effective block size
                    file_path_for_error_log=str(self.pbd_file_path),
                )
                logger.info(f"Successfully parsed initial header for {self.pbd_file_path.name} using block size {self.effective_block_size}")
            except HeaderError as he_initial:
                logger.warning(f"Initial header parsing failed for {self.pbd_file_path.name} (block size {self.effective_block_size}): {he_initial}. Attempting signature scan.")
                self.is_recovered_mode = True
                signatures_found = scan_for_signatures(self.file_handle)

                hdr_offsets_to_try = signatures_found.get("UNICODE_HDR", []) + signatures_found.get("ASCII_HDR", [])
                found_valid_header_from_scan = False
                for offset in hdr_offsets_to_try:
                    logger.info(f"Attempting to parse header at scanned offset {offset} for {self.pbd_file_path.name} using block size {self.effective_block_size}")
                    try:
                        self.file_handle.seek(offset)
                        header_candidate_bytes_len = max(sum(fh.HEADER_BLOCK_SIZES_UNICODE), sum(fh.HEADER_BLOCK_SIZES_NON_UNICODE)) + (self.effective_block_size * 2)
                        header_candidate_bytes = self.file_handle.read(header_candidate_bytes_len)

                        if header_candidate_bytes:
                            self.header = extract_pbl_header(
                                header_candidate_bytes,
                                block_size=self.effective_block_size,  # Pass effective block size
                                file_path_for_error_log=f"{self.pbd_file_path.name} at offset {offset}",
                            )
                            logger.info(f"Successfully parsed header from scanned offset {offset} for {self.pbd_file_path.name} using block size {self.effective_block_size}")
                            found_valid_header_from_scan = True
                            break
                    except HeaderError as he_scan:
                        logger.warning(f"Header parsing at scanned offset {offset} (block size {self.effective_block_size}) failed: {he_scan}")
                        continue

                if not found_valid_header_from_scan:
                    logger.error(f"Signature scan did not yield a parsable header for {self.pbd_file_path.name}. Original error: {he_initial}")
                    raise PbdError(f"Could not find a valid header for {self.pbd_file_path.name}, even after scan.") from he_initial

            if self.header:
                self.file_handle.seek(0)
                self.nodes = extract_nods(
                    self.file_handle,
                    self.header.is_unicode,
                    self.header.first_nod_offset,
                    block_size=self.effective_block_size,
                )
                if not self.nodes and self.header:  # If header exists but no NODs found
                    logger.warning(
                        f"No NODs extracted for {self.pbd_file_path.name} using header's first_nod_offset ({self.header.first_nod_offset}). "
                        f"Attempting brute-force ENT* scan for recovery.",
                    )
                    self.is_recovered_mode = True  # Mark as recovered due to ENT scan

                    # Ensure file_size is available for brute-force scan boundary checks
                    if self.header.file_size is None:
                        logger.error(f"Cannot perform ENT* scan for {self.pbd_file_path.name}: file_size not available in header.")
                    else:
                        signatures_found_for_ent_scan = scan_for_signatures(self.file_handle)
                        recovered_entries_count = 0

                        # Process ASCII ENT* entries
                        ascii_ent_offsets = signatures_found_for_ent_scan.get("ASCII_ENT", [])
                        logger.info(f"Found {len(ascii_ent_offsets)} potential ASCII ENT* signatures for recovery scan.")
                        for ent_offset in ascii_ent_offsets:
                            entry = read_and_parse_entry_def(
                                self.file_handle,
                                ent_offset,
                                is_unicode_entry=False,
                                block_size=self.effective_block_size,
                                file_size=self.header.file_size,
                            )
                            if entry and entry.objectname not in self.entries_map:  # Avoid duplicates if any NODs were found
                                self.entries_map[entry.objectname] = entry
                                recovered_entries_count += 1
                                logger.debug(f"Recovered ASCII entry via scan: {entry.objectname} at offset {ent_offset}")
                            elif entry and entry.objectname in self.entries_map:
                                logger.debug(f"Skipping already indexed ASCII entry from scan: {entry.objectname} at offset {ent_offset}")

                        # Process Unicode ENT* entries
                        unicode_ent_offsets = signatures_found_for_ent_scan.get("UNICODE_ENT", [])
                        logger.info(f"Found {len(unicode_ent_offsets)} potential Unicode ENT* signatures for recovery scan.")
                        for ent_offset in unicode_ent_offsets:
                            entry = read_and_parse_entry_def(
                                self.file_handle,
                                ent_offset,
                                is_unicode_entry=True,
                                block_size=self.effective_block_size,
                                file_size=self.header.file_size,
                            )
                            if entry and entry.objectname not in self.entries_map:
                                self.entries_map[entry.objectname] = entry
                                recovered_entries_count += 1
                                logger.debug(f"Recovered Unicode entry via scan: {entry.objectname} at offset {ent_offset}")
                            elif entry and entry.objectname in self.entries_map:
                                logger.debug(f"Skipping already indexed Unicode entry from scan: {entry.objectname} at offset {ent_offset}")

                        if recovered_entries_count > 0:
                            logger.info(f"Successfully recovered {recovered_entries_count} entries via brute-force ENT* scan for {self.pbd_file_path.name}.")
                        else:
                            logger.info(f"Brute-force ENT* scan did not recover any new entries for {self.pbd_file_path.name}.")

                # Original logic to populate entries_map from successfully parsed NODs
                # This should run regardless, and the brute-force scan adds to it if NODs failed.
                # If NODs were partially successful, brute-force might find more or dups (handled by `not in self.entries_map`).
                for node in self.nodes:
                    if node and node.entry_defs:
                        for entry_def in node.entry_defs:
                            if entry_def and entry_def.objectname:
                                # Normalize object name for consistent keying (e.g., lowercasing)
                                # For now, using as-is, but consider normalization.
                                self.entries_map[entry_def.objectname] = entry_def
                                logger.debug(f"Indexed entry: {entry_def.objectname}")
            else:
                raise PbdError(f"Failed to parse header for {self.pbd_file_path}")

        except PbdError as e:
            logger.error(f"Error initializing Library for {self.pbd_file_path}: {e}")
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
            raise  # Re-raise the PbdError
        except Exception as e:
            logger.error(f"Unexpected error initializing Library for {self.pbd_file_path}: {e}", exc_info=True)
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
            raise PbdError(f"Unexpected error during Library initialization for {self.pbd_file_path}: {e}") from e

        # Note: File handle remains open for subsequent operations like __getitem__ or extract_all.
        # A close() method or context manager protocol will be needed.

    def close(self) -> None:
        """Closes the underlying PBD file handle."""
        if self.file_handle:
            logger.debug(f"Closing file handle for {self.pbd_file_path}")
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Do not suppress exceptions

    def __getitem__(self, object_name: str) -> "PbdObject":
        """Retrieves a PBD object by its name. Raises KeyError if not found or PfcExcludedError if excluded."""
        entry_def = self.entries_map.get(object_name)
        if not entry_def:
            raise KeyError(f"Object '{object_name}' not found in library {self.pbd_file_path.name}")

        if not self.file_handle or self.file_handle.closed:
            logger.error(f"File handle for {self.pbd_file_path.name} is closed. Cannot extract data for '{object_name}'.")
            # Attempt to reopen? For now, error out or return None.
            # Reopening here would violate the "one handle" principle for this instance.
            # The Library instance should be recreated if the handle is closed externally.
            raise PbdError(f"File handle for {self.pbd_file_path.name} is closed.")

        if not self.header:  # Should not happen if __init__ succeeded
            raise PbdError(f"Header not available for {self.pbd_file_path.name}. Cannot determine unicode setting or file size for data extraction.")

        try:
            # Ensure file_size is available
            if self.header.file_size is None:
                raise PbdError(f"File size not available in header for {self.pbd_file_path.name}. Cannot safely extract data.")

            data_blocks, is_partial = extract_data_from_entry(
                self.file_handle,
                entry_def,
                self.header.is_unicode,
                self.effective_block_size,  # Pass effective block size
                self.header.file_size,
            )
            pbd_obj = PbdObject(
                entry_definition=entry_def,
                data_blocks=data_blocks,
                is_partial=is_partial,
                is_unicode_file_context=self.header.is_unicode,  # Pass is_unicode flag
            )

            # PFC Check
            if self.exclude_pfc and self.pfc_hashes:
                content_hash = pbd_obj.get_content_hash()
                if content_hash and content_hash in self.pfc_hashes:
                    logger.info(f"Object '{object_name}' (hash: {content_hash}) matches a PFC hash. Excluding.")
                    raise PfcExcludedError(f"Object '{object_name}' is excluded as a PFC object.")

            return pbd_obj
        except PbdError as e:
            logger.error(f"Error extracting data for object '{object_name}' from {self.pbd_file_path.name}: {e}")
            raise  # Re-raise as a PbdError, or a new type like ObjectExtractionError
        except Exception as e:
            logger.error(f"Unexpected error extracting data for object '{object_name}' from {self.pbd_file_path.name}: {e}", exc_info=True)
            raise PbdError(f"Unexpected error extracting object '{object_name}': {e}") from e

    def extract_all(self, output_dir: str | Path, silent_progress: bool = False) -> None:
        """Extracts all objects from the library to the specified output directory."""
        if not self.file_handle or self.file_handle.closed:
            logger.error(f"File handle for {self.pbd_file_path.name} is closed. Cannot extract all objects.")
            raise PbdError(f"File handle for {self.pbd_file_path.name} is closed.")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        progress_tracker: BaseProgressTracker
        if silent_progress:
            progress_tracker = SilentProgressTracker(total=len(self.entries_map), description=f"Extracting from {self.pbd_file_path.name}")
        else:
            progress_tracker = TqdmProgressTracker(total=len(self.entries_map), description=f"Extracting from {self.pbd_file_path.name}")

        with progress_tracker:
            # Get entries and sort them for deterministic output
            # Sorting by object type extension (heuristic) and then by name
            sorted_entries = sorted(
                self.entries_map.values(),
                key=lambda entry_def: (
                    OBJECT_TYPE_SORT_ORDER.get(Path(entry_def.objectname).suffix.lower(), OBJECT_TYPE_SORT_ORDER["DEFAULT"]),
                    entry_def.objectname.lower(),
                ),
            )

            for entry_def in sorted_entries:
                object_name = entry_def.objectname  # Get object_name from the sorted entry_def
                try:
                    # Use __getitem__ to get the PbdObject, which handles data extraction and PFC check
                    pbd_obj = self[object_name]
                    # If __getitem__ returned without error, it's not a PFC object (if exclude_pfc is on)
                    # or PFC exclusion is off.

                    # Determine file extension and content type
                    _, _extension = Path(object_name).suffix.lower(), ""
                    is_source = object_name.lower().endswith(tuple(SOURCE_EXTENSIONS))

                    file_name_base = Path(object_name)
                    output_file_path: Path | None = None

                    if is_source:
                        # Save text content (source code, p-code, or combined)
                        if pbd_obj.raw_text_content is not None:
                            # For .pbl files, it might be useful to save the raw_pcode to a separate file.
                            # For now, primary save is raw_text_content to .ext.txt for clarity.
                            output_file_path = output_dir / f"{file_name_base}.txt"
                            save_text_file(pbd_obj.raw_text_content, output_file_path)
                            logger.debug(f"Saved text content of {object_name} to {output_file_path}")

                            # Optionally save p-code if distinct and desired (e.g. for .pbl export)
                            # if pbd_obj.raw_pcode and pbd_obj.raw_pcode != pbd_obj.raw_text_content:
                            #     pcode_file_path = output_dir / f"{file_name_base}.pcode.txt"
                            #     save_pcode_file(pbd_obj.raw_pcode, pcode_file_path)
                            #     logger.debug(f"Saved p-code of {object_name} to {pcode_file_path}")
                        else:
                            logger.warning(f"Object {object_name} is source type but has no text content. Skipping save.")
                    else:  # Binary/resource file
                        # Ensure raw_binary_content is populated if not already
                        if pbd_obj.raw_binary_content is None:
                            pbd_obj.raw_binary_content = get_binary_from_data(pbd_obj.data_blocks)

                        if pbd_obj.raw_binary_content is not None:
                            output_file_path = output_dir / object_name  # Save with original name/ext
                            save_binary_file(pbd_obj.raw_binary_content, output_file_path)
                            logger.debug(f"Saved binary content of {object_name} to {output_file_path}")
                        else:
                            logger.warning(f"Object {object_name} is binary type but has no binary content. Skipping save.")

                    # After saving primary content, attempt to extract embedded resources
                    if pbd_obj and output_file_path:  # Ensure obj exists and was saved
                        pbd_obj.extract_and_save_embedded_resources(output_dir=output_dir)

                except KeyError:  # From self[object_name] if somehow entry is in map but not gettable
                    logger.error(f"Could not find object '{object_name}' via __getitem__ during extract_all. Skipping.")
                except PfcExcludedError:  # Catch PFC exclusion
                    logger.info(f"Object '{object_name}' was excluded (PFC match). Skipping save.")
                except PbdError as e_obj_extract:
                    logger.error(f"PBD Error extracting '{object_name}': {e_obj_extract}. Skipping.")
                except Exception as e_generic:
                    logger.error(f"Unexpected error extracting '{object_name}': {e_generic}. Skipping.", exc_info=True)
                finally:
                    progress_tracker.update()
        logger.info(f"Extraction complete for {self.pbd_file_path.name}. Output to: {output_dir}")

    def __len__(self) -> int:
        """Returns the number of unique entries in the library."""
        return len(self.entries_map)

    def list_entries(self) -> list[str]:
        """Returns a list of all object names in the library."""
        return list(self.entries_map.keys())
