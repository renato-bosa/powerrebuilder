"""Defines the PbdObject class, representing a single extracted object from a PBD library."""


import base64
import logging
import re
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from src.extract.pbd.constants import BLOCK_SIZE
from src.extract.pbd.io.resource_utils import extract_embedded_images
from src.extract.utils.binary import calculate_content_hash

from .data_block import DataClass, get_binary_from_data, get_text_from_data
from .entry import PbEntryDefinition

logger = logging.getLogger(__name__)

# Regex to find DataWindow syntax:
# Looks for Syntax=(0)"uncompressed_syntax" or Syntax=(1)"base64_zlib_compressed_syntax"
# It captures the compression flag (0 or 1) and the syntax content within quotes.
# This regex assumes the syntax string doesn't contain escaped quotes for simplicity.
# Group 1: compression_flag (0 or 1)
# Group 2: syntax_content (string within quotes)
DW_SYNTAX_REGEX = re.compile(
    r"Syntax\s*=\s*\(([01])\)\s*\"((?:\\\"|[^\"])*)\"", re.IGNORECASE,
)
# Simpler version if PB always uses `Syntax=`
# DW_SYNTAX_REGEX = re.compile(r"Syntax=\((\d)\)\"(.*?)\"", re.IGNORECASE)


@dataclass(slots=True)
class PbdObject:
    """Represents a single object (entry) extracted from a PowerBuilder PBD file."""

    entry_definition: PbEntryDefinition
    is_unicode_file_context: bool = field(repr=False)
    data_blocks: list[DataClass] = field(repr=False)  # Avoid excessively long repr
    is_partial: bool = False  # Added to indicate potentially incomplete data
    raw_text_content: str | None = field(init=False, default=None)
    raw_binary_content: bytes | None = field(init=False, default=None)
    raw_pcode: str | None = field(init=False, default=None)
    # The raw_pcode attribute mentioned in the user story will be derived from raw_text_content

    def _try_inflate_datawindow_syntax(self, text_content: str) -> str:




        """Attempts to find and decompress zlib-compressed DataWindow syntax within text_content.
        Looks for patterns like Syntax=(1)"base64_encoded_zlib_data".
        """
        # Only attempt for objects that typically contain DataWindow syntax
        if not self.name.lower().endswith((".srd", ".srw", ".sru")):
            return text_content

        match = DW_SYNTAX_REGEX.search(text_content)
        if not match:
            # Check for a simpler pattern: `release ... Syntax: ... EndSyntax` where content might be binary
            # This is harder as raw binary zlib data is not easily distinguishable from other binary data
            # without more specific markers or context.
            # For now, we only support the Syntax=(1)"base64_data" pattern.
            return text_content

        compression_flag = match.group(1)
        syntax_data_b64 = match.group(2)

        if compression_flag == "1":
            logger.debug(
                f"Found compressed DataWindow syntax (Syntax=(1)) in {self.name}. Attempting to inflate.",
            )
            try:
                # PowerBuilder often uses a slightly non-standard Base64 string that might include
                # characters like `~` or other symbols if the encoding process was custom.
                # Standard base64 should mostly work. If issues, might need custom decode.
                # Also, need to ensure the string is properly formed for base64 decoding (padding, etc.)
                # For now, assume it's standard base64 encoded string of bytes.

                # The syntax_data_b64 might have escaped quotes like \", convert them back.
                syntax_data_b64_cleaned = syntax_data_b64.replace('\\"', '"')

                # Ensure it's bytes for b64decode if it was captured from a string context
                # The regex captures from a string, so we need to encode it to bytes that represent the original b64 string
                compressed_data = base64.b64decode(
                    syntax_data_b64_cleaned.encode("ascii"),
                )  # PB usually uses ASCII for b64

                # Decompress. wbits = 15 (default) for zlib header.
                # If it's raw deflate stream, wbits = -15.
                # PowerBuilder likely uses standard zlib format.
                decompressed_syntax_bytes = zlib.decompress(compressed_data)

                # The decompressed syntax is usually text. Determine encoding.
                # If the overall PBD is Unicode, decompressed syntax is likely UTF-16LE or similar.
                # If not, it's likely ANSI (e.g., latin1, cp1252).
                # Let's assume it follows the file's unicode context for now.
                encoding = (
                    "utf-16-le" if self.is_unicode_file_context else "latin1"
                )  # Or cp1252 often used by PB
                try:
                    decompressed_syntax_str = decompressed_syntax_bytes.decode(encoding)
                except UnicodeDecodeError:
                    logger.warning(
                        f"Failed to decode inflated DataWindow syntax for {self.name} with {encoding}. Trying 'cp1252'.",
                    )
                    try:
                        decompressed_syntax_str = decompressed_syntax_bytes.decode(
                            "cp1252",
                        )
                    except UnicodeDecodeError:
                        logger.exception(
                            f"Failed to decode inflated DataWindow syntax for {self.name} with cp1252 as well. Storing as bytes repr.",
                        )
                        decompressed_syntax_str = f"<DECOMPRESSION_DECODE_ERROR: {decompressed_syntax_bytes!r}>"

                logger.info("Successfully inflated DataWindow syntax for %s.", self.name)

                # Replace the original Syntax=(1)"base64_data" with Syntax=(0)"inflated_data"
                # Need to escape quotes in the decompressed_syntax_str for embedding back into the string literal
                escaped_decompressed_syntax = decompressed_syntax_str.replace(
                    '"', '\\"',
                )

                # Reconstruct the full text content with the decompressed syntax
                # This ensures that the overall structure of the object source is maintained.
                # The new syntax string might be very long.
                new_syntax_block = f'Syntax=(0)"{escaped_decompressed_syntax}"'
                return text_content.replace(match.group(0), new_syntax_block, 1)

            except base64.binascii.Error as b64e:
                logger.exception(
                    f"Base64 decoding failed for DataWindow syntax in {self.name}: {b64e}. Content: '{syntax_data_b64[:100]}...'",
                )
            except zlib.error as ze:
                logger.exception(
                    f"Zlib decompression failed for DataWindow syntax in {self.name}: {ze}",
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during DataWindow syntax inflation for {self.name}: {e}", exc_info=True, )
            # If any error, return original content
            return text_content
        # Syntax=(0) means it's already uncompressed (or should be text)
        logger.debug(
            f"DataWindow syntax in {self.name} is marked as uncompressed (Syntax=(0)).",
        )
        return text_content

    def __post_init__(self) -> None:


        # Process data_blocks to populate raw_text_content and raw_pcode
        full_text = get_text_from_data(self.data_blocks, self.is_unicode_file_context)

        # Validate total declared length against extracted text length
        declared_length = self.entry_definition.length
        if full_text is not None:
            actual_chars = len(full_text)
            expected_min_bytes = 0
            expected_max_bytes = 0

            if self.is_unicode_file_context:
                # For UTF-16LE, each char is 2 bytes. Null terminator is 2 bytes.
                expected_min_bytes = actual_chars * 2
                expected_max_bytes = actual_chars * 2 + 2
            else:
                # For ANSI (e.g., latin1, cp1252), each char is 1 byte. Null terminator is 1 byte.
                # The full_text might have been decoded from bytes that included a null terminator, # which `decode` utility likely strips. So, declared_length could be len(full_text_bytes) or len(full_text_bytes) + 1
                # Re-encoding `full_text` to get its byte length without null terminator is tricky
                # if the original encoding had multi-byte chars for some symbols.
                # However, `get_text_from_data` uses 'latin1' or 'utf-16-le'.
                # For 'latin1', chars mostly map 1:1 to bytes.
                expected_min_bytes = actual_chars
                expected_max_bytes = actual_chars + 1

            # Allow a small tolerance for block padding or minor discrepancies if entry is partial
            # This tolerance is somewhat arbitrary and may need adjustment.
            # The primary goal is to catch large deviations.
            length_tolerance = 0
            if self.is_partial:
                length_tolerance = BLOCK_SIZE  # Allow up to one block size if marked partial (BLOCK_SIZE not defined here, use a fixed value or pass it)
                # Placeholder for BLOCK_SIZE. Ideally, this would come from context.
                # Using a common value like 512 or 1024 if relevant, or a smaller fixed number like 16 bytes.
                # For now, using a small fixed tolerance for partial data.
                length_tolerance = 16

            if not (
                expected_min_bytes
                <= declared_length
                <= expected_max_bytes + length_tolerance
            ):
                # If it's an SRD, the declared_length might be for the *original* compressed data, # not the inflated text. So, this warning might be a false positive for inflated SRDs.
                # We can skip this check if inflation occurred.
                is_srd_or_similar = self.name.lower().endswith((".srd", ".srw", ".sru"))
                syntax_match_for_inflation_check = (
                    DW_SYNTAX_REGEX.search(full_text) if full_text else None
                )
                # Check if it *was* compressed (Syntax=(1)) and successfully replaced (Syntax=(0) now)
                # A bit heuristic: if it's an SRD-like object and now has Syntax=(0), it might have been inflated.
                was_likely_inflated = (
                    is_srd_or_similar
                    and syntax_match_for_inflation_check
                    and syntax_match_for_inflation_check.group(1) == "0"
                )

                if not was_likely_inflated:
                    logger.warning(
                        f"Object '{self.name}': Declared length ({declared_length} bytes) vs. extracted text length "
                        f"({actual_chars} chars) discrepancy. "
                        f"Context: Unicode={self.is_unicode_file_context}, Partial={self.is_partial}. "
                        f"Expected byte range for {actual_chars} chars: [{expected_min_bytes} - {expected_max_bytes}]. "
                        f"Tolerance applied if partial: {length_tolerance if self.is_partial else 0} bytes.", )
        elif (
            declared_length > 0
        ):  # full_text is None but declared_length suggests content
            logger.warning(
                f"Object '{self.name}': Declared length is {declared_length} bytes, but extracted text is None. "
                f"Context: Unicode={self.is_unicode_file_context}, Partial={self.is_partial}.", )

        # Attempt to inflate DataWindow syntax if present
        if full_text:  # Ensure full_text is not None
            full_text = self._try_inflate_datawindow_syntax(full_text)

        self.raw_text_content = full_text

        # Basic p-code extraction logic (can be made more sophisticated)
        if (
            self.raw_text_content
            and self.entry_definition.commentlen > 0
            and len(self.raw_text_content) >= self.entry_definition.commentlen
        ):
            # Ensure commentlen does not exceed actual content length to avoid slicing errors
            comment_len_safe = min(
                self.entry_definition.commentlen, len(self.raw_text_content),
            )
            self.raw_pcode = self.raw_text_content[comment_len_safe:]
        elif self.raw_text_content:  # Check if raw_text_content is not None
            self.raw_pcode = self.raw_text_content
        else:
            self.raw_pcode = ""  # Default to empty string if raw_text_content is None

        # raw_binary_content is a separate concern, usually for resource files.
        # For now, it's not populated by this generic __post_init__ from text-oriented DAT blocks.
        # self.raw_binary_content = get_binary_from_data(self.data_blocks) # if applicable

    @property
    def name(self) -> str:

        return self.entry_definition.objectname

    @property
    def version(self) -> str:

        return self.entry_definition.version

    @property
    def timestamp(self) -> any:  
        # datetime.datetime
        return self.entry_definition.moddatetime

    @property
    def comment(self) -> str | None:

        if self.raw_text_content and self.entry_definition.commentlen > 0:
            return self.raw_text_content[: self.entry_definition.commentlen]
        return None

    # raw_pcode is now an attribute set in __post_init__

    # If true binary content needs to be distinctly handled from text: # def get_binary_content(self) -> bytes | None: #     if not self.raw_binary_content and self.data_blocks: # Lazy load if needed
    #         self.raw_binary_content = get_binary_from_data(self.data_blocks)
    #     return self.raw_binary_content

    def extract_and_save_embedded_resources(
        self, output_dir: Path, resource_subdir_name: str = "resources", ) -> list[Path]:




        """Attempts to find and save embedded resources (like images) from this PBD object.
        Currently targets .srm (menu) objects by heuristic.

        Args:
            output_dir: The base directory where the object's primary content is saved.
                        Resources will be saved in a subdirectory of this.
            resource_subdir_name: The name of the subdirectory for resources.

        Returns:
            A list of paths to the saved resource files.
        """
        saved_resources: list[Path] = []
        # Heuristic: only attempt for .srm files for now
        if not self.name.lower().endswith(".srm"):
            return saved_resources

        # Ensure raw_binary_content is populated
        if self.raw_binary_content is None:
            # This assumes data_blocks could contain binary data for .srm files
            # If .srm DAT blocks are always text, this might need adjustment
            # or ensure raw_binary_content is populated if entry is non-text type.
            # For now, let's explicitly try to get binary data.
            # A better approach might be to determine this when PbdObject is created.
            self.raw_binary_content = get_binary_from_data(self.data_blocks)

        if not self.raw_binary_content:
            logger.debug(
                f"No raw binary content available to extract resources from {self.name}",
            )
            return saved_resources

        resource_path = output_dir / resource_subdir_name
        try:
            resource_path.mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured resource directory exists: %s", resource_path)

            extracted = extract_embedded_images(
                data_bytes=self.raw_binary_content, base_filename=self.name, output_resource_dir=resource_path, )
            saved_resources.extend(extracted)
            if extracted:
                logger.info(
                    f"Found and saved {len(extracted)} resource(s) for {self.name} in {resource_path}",
                )

        except Exception as e:
            logger.error(
                f"Error creating resource directory or extracting resources for {self.name}: {e}", exc_info=True, )

        return saved_resources

    def get_content_hash(self) -> str | None:




        """Calculates and returns the SHA-1 hash of the object's primary content.
        Prefers raw_text_content (UTF-8 encoded) if available, otherwise uses raw_binary_content.
        Returns None if no content is available.
        """
        content_to_hash: str | bytes | None = None
        if self.raw_text_content is not None:
            content_to_hash = self.raw_text_content
        elif self.raw_binary_content is not None:
            # If raw_binary_content was populated, use it directly
            content_to_hash = self.raw_binary_content
        elif (
            self.data_blocks
        ):  # Fallback: try to get binary data if not already populated
            # This is a bit redundant if raw_binary_content is supposed to be the source
            # But ensures we try if it wasn't explicitly set for some reason for a binary obj
            logger.debug(
                f"get_content_hash: raw_text/binary not set for {self.name}, trying get_binary_from_data.",
            )
            temp_binary_content = get_binary_from_data(self.data_blocks)
            if temp_binary_content:
                content_to_hash = temp_binary_content

        if content_to_hash is None:
            logger.warning(
                f"No content available to calculate hash for object: {self.name}",
            )
            return None

        return calculate_content_hash(content_to_hash)
