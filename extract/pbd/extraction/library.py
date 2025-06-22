"""Provides a high-level API for interacting with PowerBuilder PBD/PBL files."""

import logging
from pathlib import Path
from typing import BinaryIO

import extract.pbd.structures.header as fh  # Import for constants
from extract.pbd.constants import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
from extract.pbd.constants import SOURCE_EXTENSIONS
from extract.pbd.exceptions import HeaderError, PbdError, PfcExcludedError
from extract.pbd.io.file_operations import save_binary_file, save_text_file
from extract.pbd.io.progress import (
    BaseProgressTracker, SilentProgressTracker, TqdmProgressTracker, )
from extract.pbd.io.scanner import (
    EXPECTED_BLOCK_SIZES, detect_block_size_from_dat_spacing, scan_for_signatures, )
from extract.pbd.structures.data_block import (
    get_binary_from_data, )

# Enhanced extraction for 100% accuracy
from extract.pbd.structures.enhanced_data_block import (
    extract_data_from_entry_enhanced, )
from extract.pbd.structures.entry import PbEntryDefinition, read_and_parse_entry_def
from extract.pbd.structures.header import HeaderClass, extract_pbl_header
from extract.pbd.structures.node import NodeClass, extract_nods
from extract.pbd.structures.pbd_object import PbdObject
from extract.pbd.utils.pfc_utils import load_pfc_hashes

logger = logging.getLogger(__name__)


# Define a sort order for object types based on extension
# Lower number means higher priority (extracted earlier)
# This is a heuristic for pseudo-topological sort.
OBJECT_TYPE_SORT_ORDER = {
    # Ancestors / Global things often first
    ".sra": 0, # Application
    ".sru": 1, # User Object (often ancestors or NVOs)
    # Core UI / Logic
    ".srw": 10, # Window
    ".srm": 11, # Menu
    ".srf": 12, # Function
    # Data-related
    ".srd": 20, # DataWindow (object definition)
    ".srj": 21, # Project (less common in PBDs, but for completeness)
    ".srp": 22, # Pipeline
    ".srq": 23, # Query
    # Others / Unspecified
    "DEFAULT": 99, }


class Library:
    """Represents a PowerBuilder Library (PBD/PBL file) and provides
    methods to access its contents.
    """

    def __init__(
        self, pbd_file_path: str | Path, exclude_pfc: bool= False, pfc_hash_file: str | Path | None = None, ) -> None:


        self._initialize_attributes(pbd_file_path, exclude_pfc)
        self._load_pfc_hashes(pfc_hash_file)
        self._validate_file_path()

        try:
            self.file_handle = open(self.pbd_file_path, "rb")
            self._detect_block_size()
            self._parse_header()
            self._extract_nodes_and_entries()
        except PbdError as e:
            logger.exception(
                f"Error initializing Library for {self.pbd_file_path}: {e}"
            )
            self._cleanup_file_handle()
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error initializing Library for {self.pbd_file_path}: {e}", exc_info=True, )
            self._cleanup_file_handle()
            msg = f"Unexpected error during Library initialization for {self.pbd_file_path}: {e}"
            raise PbdError(msg) from e

    def _initialize_attributes(self, pbd_file_path: str | Path, exclude_pfc: bool) -> None:




        """Initialize instance attributes."""
        self.pbd_file_path: Path = Path(pbd_file_path)
        self.file_handle: BinaryIO | None = None
        self.header: HeaderClass | None = None
        self.nodes: list[NodeClass] = []
        self.entries_map: dict[str, PbEntryDefinition] = {}
        self.is_recovered_mode: bool = False
        self.detected_block_size: int | None = None
        self.effective_block_size: int = DEFAULT_BLOCK_SIZE
        self.exclude_pfc = exclude_pfc
        self.pfc_hashes: set[str] = set()

    def _load_pfc_hashes(self, pfc_hash_file: str | Path | None) -> None:




        """Load PFC hashes if PFC exclusion is enabled."""
        if not self.exclude_pfc:
            return

        pfc_hash_file_path = Path(pfc_hash_file) if pfc_hash_file else None
        self.pfc_hashes = load_pfc_hashes(pfc_hash_file_path)

        if self.pfc_hashes:
            logger.info(
                f"PFC exclusion enabled. {len(self.pfc_hashes)} PFC hashes loaded."
            )
        else:
            logger.warning(
                "PFC exclusion was enabled, but no PFC hashes were loaded. All objects will be processed."
            )

    def _validate_file_path(self) -> None:




        """Validate that the PBD file exists and is a file."""
        if not self.pbd_file_path.exists() or not self.pbd_file_path.is_file():
            msg = f"PBD file not found or is not a file: {self.pbd_file_path}"
            raise PbdError(msg)

    def _detect_block_size(self) -> None:




        """Detect the block size from the file."""
        if not self.file_handle:
            return

        try:
            self.file_handle.seek(0)
            self.detected_block_size = detect_block_size_from_dat_spacing(
                self.file_handle
            )

            if (
                self.detected_block_size
                and self.detected_block_size in EXPECTED_BLOCK_SIZES
            ):
                logger.info(
                    f"Using detected block size for {self.pbd_file_path.name}: {self.detected_block_size}"
                )
                self.effective_block_size = self.detected_block_size
                if self.effective_block_size != DEFAULT_BLOCK_SIZE:
                    logger.info(
                        f"Detected block size {self.effective_block_size} for {self.pbd_file_path.name} is being used, differing from default {DEFAULT_BLOCK_SIZE}.", )
            else:
                logger.info(
                    f"Could not reliably auto-detect block size or detected size not in expected values for {self.pbd_file_path.name}. Using default: {DEFAULT_BLOCK_SIZE}."
                )
                self.effective_block_size = DEFAULT_BLOCK_SIZE
            self.file_handle.seek(0)
        except Exception as e_bs_detect:
            logger.warning(
                f"Error during block size detection for {self.pbd_file_path.name}: {e_bs_detect}. Proceeding with default {DEFAULT_BLOCK_SIZE}."
            )
            self.effective_block_size = DEFAULT_BLOCK_SIZE
            self.file_handle.seek(0)

    def _parse_header(self) -> None:




        """Parse the PBL/PBD header with recovery attempts."""
        if not self.file_handle:
            msg = "File handle not initialized"
            raise PbdError(msg)

        try:
            self.header = extract_pbl_header(
                self.file_handle, block_size=self.effective_block_size, file_path_for_error_log=str(self.pbd_file_path), )
            logger.info(
                f"Successfully parsed initial header for {self.pbd_file_path.name} using block size {self.effective_block_size}"
            )
        except HeaderError as he_initial:
            logger.warning(
                f"Initial header parsing failed for {self.pbd_file_path.name} (block size {self.effective_block_size}): {he_initial}. Attempting signature scan."
            )
            self._parse_header_with_recovery(he_initial)

    def _parse_header_with_recovery(self, original_error: HeaderError) -> None:




        """Attempt to parse header using signature scanning."""
        if not self.file_handle:
            raise PbdError("File handle not initialized")

        self.is_recovered_mode = True
        signatures_found = scan_for_signatures(self.file_handle)

        hdr_offsets_to_try = signatures_found.get(
            "UNICODE_HDR", []
        ) + signatures_found.get("ASCII_HDR", [])

        for offset in hdr_offsets_to_try:
            if self._try_parse_header_at_offset(offset):
                return

        logger.exception(
            f"Signature scan did not yield a parsable header for {self.pbd_file_path.name}. Original error: {original_error}"
        )
        msg = f"Could not find a valid header for {self.pbd_file_path.name}, even after scan."
        raise PbdError(msg) from original_error

    def _try_parse_header_at_offset(self, offset: int) -> bool:




        """Try to parse header at a specific offset."""
        if not self.file_handle:
            return False

        logger.info(
            f"Attempting to parse header at scanned offset {offset} for {self.pbd_file_path.name} using block size {self.effective_block_size}"
        )
        try:
            self.file_handle.seek(offset)
            header_candidate_bytes_len = max(
                sum(fh.HEADER_BLOCK_SIZES_UNICODE), sum(fh.HEADER_BLOCK_SIZES_NON_UNICODE), ) + (self.effective_block_size * 2)
            header_candidate_bytes = self.file_handle.read(header_candidate_bytes_len)

            if header_candidate_bytes:
                self.header = extract_pbl_header(
                    header_candidate_bytes, block_size=self.effective_block_size, file_path_for_error_log=f"{self.pbd_file_path.name} at offset {offset}", )
                logger.info(
                    f"Successfully parsed header from scanned offset {offset} for {self.pbd_file_path.name} using block size {self.effective_block_size}"
                )
                return True
        except HeaderError as he_scan:
            logger.warning(
                f"Header parsing at scanned offset {offset} (block size {self.effective_block_size}) failed: {he_scan}"
            )
        return False

    def _extract_nodes_and_entries(self) -> None:




        """Extract nodes and populate entries map."""
        if not self.header:
            msg = f"Failed to parse header for {self.pbd_file_path}"
            raise PbdError(msg)

        if not self.file_handle:
            msg = "File handle not initialized"
            raise PbdError(msg)

        self.file_handle.seek(0)
        self.nodes = extract_nods(
            self.file_handle, self.header.is_unicode, self.header.first_nod_offset, block_size=self.effective_block_size, )

        if not self.nodes and self.header:
            logger.warning(
                f"No NODs extracted for {self.pbd_file_path.name} using header's first_nod_offset ({self.header.first_nod_offset}). "
                f"Attempting brute-force ENT* scan for recovery.", )
            self._perform_brute_force_recovery()

        self._populate_entries_from_nodes()

    def _perform_brute_force_recovery(self) -> None:




        """Perform brute-force ENT* scan for recovery."""
        self.is_recovered_mode = True

        if not self.header or self.header.file_size is None:
            logger.error(
                f"Cannot perform ENT* scan for {self.pbd_file_path.name}: file_size not available in header."
            )
            return

        if not self.file_handle:
            logger.error(
                f"Cannot perform ENT* scan for {self.pbd_file_path.name}: file handle not initialized."
            )
            return

        signatures_found = scan_for_signatures(self.file_handle)
        recovered_count = 0

        # Process ASCII entries
        recovered_count += self._recover_entries(
            signatures_found.get("ASCII_ENT", []), is_unicode=False, entry_type="ASCII"
        )

        # Process Unicode entries
        recovered_count += self._recover_entries(
            signatures_found.get("UNICODE_ENT", []), is_unicode=True, entry_type="Unicode"
        )

        if recovered_count > 0:
            logger.info(
                f"Successfully recovered {recovered_count} entries via brute-force ENT* scan for {self.pbd_file_path.name}."
            )
        else:
            logger.info(
                f"Brute-force ENT* scan did not recover any new entries for {self.pbd_file_path.name}."
            )

    def _recover_entries(self, offsets: list[int], is_unicode: bool, entry_type: str) -> int:




        """Recover entries from given offsets."""
        if not self.file_handle or not self.header:
            return 0

        logger.info(
            f"Found {len(offsets)} potential {entry_type} ENT* signatures for recovery scan."
        )
        recovered_count = 0

        for offset in offsets:
            entry = read_and_parse_entry_def(
                self.file_handle, offset, is_unicode_entry=is_unicode, block_size=self.effective_block_size, file_size=self.header.file_size if self.header.file_size is not None else 0, )

            if entry and entry.objectname not in self.entries_map:
                self.entries_map[entry.objectname] = entry
                recovered_count += 1
                logger.debug(
                    f"Recovered {entry_type} entry via scan: {entry.objectname} at offset {offset}"
                )
            elif entry and entry.objectname in self.entries_map:
                logger.debug(
                    f"Skipping already indexed {entry_type} entry from scan: {entry.objectname} at offset {offset}"
                )

        return recovered_count

    def _populate_entries_from_nodes(self) -> None:




        """Populate entries map from successfully parsed nodes."""
        for node in self.nodes:
            if node and node.entry_defs:
                for entry_def in node.entry_defs:
                    if entry_def and entry_def.objectname:
                        self.entries_map[entry_def.objectname] = entry_def
                        logger.debug("Indexed entry: %s", entry_def.objectname)

    def _cleanup_file_handle(self) -> None:




        """Clean up file handle on error."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def close(self) -> None:




        """Closes the underlying PBD file handle."""
        if self.file_handle:
            logger.debug("Closing file handle for %s", self.pbd_file_path)
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self) -> None:


        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:


        self.close()
        return False  # Do not suppress exceptions

    def __getitem__(self, object_name: str) -> "PbdObject":




        """Retrieves a PBD object by its name. Raises KeyError if not found or PfcExcludedError if excluded."""
        entry_def = self.entries_map.get(object_name)
        if not entry_def:
            msg = (
                f"Object '{object_name}' not found in library {self.pbd_file_path.name}"
            )
            raise KeyError(msg)

        if not self.file_handle or self.file_handle.closed:
            logger.error(
                f"File handle for {self.pbd_file_path.name} is closed. Cannot extract data for '{object_name}'."
            )
            # Attempt to reopen? For now, error out or return None.
            # Reopening here would violate the "one handle" principle for this instance.
            # The Library instance should be recreated if the handle is closed externally.
            msg = f"File handle for {self.pbd_file_path.name} is closed."
            raise PbdError(msg)

        if not self.header:  # Should not happen if __init__ succeeded
            msg = f"Header not available for {self.pbd_file_path.name}. Cannot determine unicode setting or file size for data extraction."
            raise PbdError(msg)

        try:
            # Ensure file_size is available
            if self.header.file_size is None:
                msg = f"File size not available in header for {self.pbd_file_path.name}. Cannot safely extract data."
                raise PbdError(msg)

            # Use enhanced extraction for better accuracy
            data_blocks, is_partial = extract_data_from_entry_enhanced(
                self.file_handle, entry_def, self.header.is_unicode, self.effective_block_size, # Pass effective block size
                self.header.file_size, )
            pbd_obj = PbdObject(
                entry_definition=entry_def, data_blocks=data_blocks, is_partial=is_partial, is_unicode_file_context=self.header.is_unicode, # Pass is_unicode flag
            )

            # PFC Check
            if self.exclude_pfc and self.pfc_hashes:
                content_hash = pbd_obj.get_content_hash()
                if content_hash and content_hash in self.pfc_hashes:
                    logger.info(
                        f"Object '{object_name}' (hash: {content_hash}) matches a PFC hash. Excluding."
                    )
                    msg = f"Object '{object_name}' is excluded as a PFC object."
                    raise PfcExcludedError(msg)

            return pbd_obj
        except PbdError as e:
            logger.exception(
                f"Error extracting data for object '{object_name}' from {self.pbd_file_path.name}: {e}"
            )
            raise  # Re-raise as a PbdError, or a new type like ObjectExtractionError
        except Exception as e:
            logger.error(
                f"Unexpected error extracting data for object '{object_name}' from {self.pbd_file_path.name}: {e}", exc_info=True, )
            msg = f"Unexpected error extracting object '{object_name}': {e}"
            raise PbdError(msg) from e

    def extract_all(
        self, output_dir: str | Path, silent_progress: bool= False
    ) -> None:




        """Extracts all objects from the library to the specified output directory."""
        self._validate_file_handle_for_extraction()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        progress_tracker = self._create_progress_tracker(silent_progress)

        with progress_tracker:
            sorted_entries = self._get_sorted_entries()

            for entry_def in sorted_entries:
                self._extract_single_entry(entry_def, output_dir, progress_tracker)
        logger.info(
            f"Extraction complete for {self.pbd_file_path.name}. Output to: {output_dir}"
        )

    def _validate_file_handle_for_extraction(self) -> None:




        """Validate that the file handle is open and ready for extraction."""
        if not self.file_handle or self.file_handle.closed:
            logger.error(
                f"File handle for {self.pbd_file_path.name} is closed. Cannot extract all objects."
            )
            msg = f"File handle for {self.pbd_file_path.name} is closed."
            raise PbdError(msg)

    def _create_progress_tracker(self, silent_progress: bool) -> BaseProgressTracker:




        """Create appropriate progress tracker based on silent_progress flag."""
        tracker_args = {
            "total": len(self.entries_map), "description": f"Extracting from {self.pbd_file_path.name}", }

        if silent_progress:
            return SilentProgressTracker(**tracker_args)
        else:
            return TqdmProgressTracker(**tracker_args)

    def _get_sorted_entries(self) -> list[PbEntryDefinition]:




        """Get entries sorted by object type and name for deterministic output."""
        return sorted(
            self.entries_map.values(), key=lambda entry_def: (
                OBJECT_TYPE_SORT_ORDER.get(
                    Path(entry_def.objectname).suffix.lower(), OBJECT_TYPE_SORT_ORDER["DEFAULT"], ), entry_def.objectname.lower(), ), )

    def _extract_single_entry(
        self, entry_def: PbEntryDefinition, output_dir: Path, progress_tracker: BaseProgressTracker
    ) -> None:




        """Extract a single entry to the output directory."""
        object_name = entry_def.objectname

        try:
            pbd_obj = self[object_name]
            self._save_object_content(pbd_obj, object_name, output_dir)
        except KeyError:
            logger.exception(
                f"Could not find object '{object_name}' via __getitem__ during extract_all. Skipping."
            )
        except PfcExcludedError:
            logger.info(
                f"Object '{object_name}' was excluded (PFC match). Skipping save."
            )
        except PbdError as e_obj_extract:
            logger.exception(
                f"PBD Error extracting '{object_name}': {e_obj_extract}. Skipping."
            )
        except Exception as e_generic:
            logger.error(
                f"Unexpected error extracting '{object_name}': {e_generic}. Skipping.", exc_info=True, )
         finally:
            progress_tracker.update()

    def _save_object_content(
        self, pbd_obj: PbdObject, object_name: str, output_dir: Path
    ) -> None:




        """Save the content of a PbdObject to disk."""
        is_source = object_name.lower().endswith(tuple(SOURCE_EXTENSIONS))

        if is_source:
            output_file_path = self._save_source_content(pbd_obj, object_name, output_dir)
        else:
            output_file_path = self._save_binary_content(pbd_obj, object_name, output_dir)

        # Extract embedded resources if object was saved
        if pbd_obj and output_file_path:
            pbd_obj.extract_and_save_embedded_resources(output_dir=output_dir)

    def _save_source_content(
        self, pbd_obj: PbdObject, object_name: str, output_dir: Path
    ) -> Path | None:




        """Save source/text content of an object."""
        if pbd_obj.raw_text_content is None:
            logger.warning(
                f"Object {object_name} is source type but has no text content. Skipping save."
            )
            return None

        file_name_base = Path(object_name)
        output_file_path = output_dir / f"{file_name_base}.txt"
        save_text_file(pbd_obj.raw_text_content, output_file_path)
        logger.debug(
            f"Saved text content of {object_name} to {output_file_path}"
        )
        return output_file_path

    def _save_binary_content(
        self, pbd_obj: PbdObject, object_name: str, output_dir: Path
    ) -> Path | None:




        """Save binary content of an object."""
        # Ensure raw_binary_content is populated
        if pbd_obj.raw_binary_content is None:
            pbd_obj.raw_binary_content = get_binary_from_data(pbd_obj.data_blocks)

        if pbd_obj.raw_binary_content is None:
            logger.warning(
                f"Object {object_name} is binary type but has no binary content. Skipping save."
            )
            return None

        output_file_path = output_dir / object_name
        save_binary_file(pbd_obj.raw_binary_content, output_file_path)
        logger.debug(
            f"Saved binary content of {object_name} to {output_file_path}"
        )
        return output_file_path

    def __len__(self) -> int:




        """Returns the number of unique entries in the library."""
        return len(self.entries_map)

    def list_entries(self) -> list[str]:




        """Returns a list of all object names in the library."""
        return list(self.entries_map.keys())