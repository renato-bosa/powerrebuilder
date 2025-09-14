"""Parallel PowerBuilder P-code decoder with enhanced progress reporting.

This module extends the PCodeDecoderV2 with parallel section processing capabilities
using ThreadPoolExecutor for CPU-bound section decoding and rich progress bars.
"""

import logging
import mmap
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from src.decompile.pcode.decoder import DecodedObject, PCodeDecoderV2, PCodeInstruction
from src.extract.pbd.version_detection import PowerBuilderVersion

logger = logging.getLogger(__name__)


class ParallelPCodeDecoder(PCodeDecoderV2):
    """Enhanced P-code decoder with parallel section processing and rich progress reporting."""

    def __init__(
        self,
        version: PowerBuilderVersion | None = None,
        max_workers: int | None = None,
        use_memory_mapping: bool = True,
        progress_callback=None,
    ) -> None:
        """Initialize the parallel decoder.

        Args:
            version: PowerBuilder version (auto-detected if None)
            max_workers: Maximum number of worker threads (defaults to min(4, CPU count))
            use_memory_mapping: Whether to use memory-mapped files for large files
            progress_callback: Optional callback for progress updates
        """
        super().__init__(version)
        self.max_workers = max_workers or min(4, os.cpu_count() or 2)
        self.use_memory_mapping = use_memory_mapping
        self.progress_callback = progress_callback
        self.console = Console()

        # Adaptive parallelism thresholds
        self.min_section_size = 1024  # Minimum bytes for parallel processing
        self.min_sections_for_parallel = 2  # Minimum sections to use parallelism

        logger.info(
            "ParallelPCodeDecoder initialized with %d workers, memory mapping: %s",
            self.max_workers,
            self.use_memory_mapping,
        )

    def decode_pcode_section(
        self,
        pcode_bytes: bytes,
        object_name: str,
        pcode_info: Any | None = None,
    ) -> DecodedObject:
        """Decode a P-code section with parallel processing when beneficial.

        Args:
            pcode_bytes: Raw P-code bytes
            object_name: Name of the object being decoded
            pcode_info: Optional P-code section information

        Returns:
            Decoded object with instructions
        """
        logger.info(
            "Decoding P-code for '%s' (%d bytes, sections: %s)",
            object_name,
            len(pcode_bytes),
            bool(pcode_info and hasattr(pcode_info, "sections")),
        )

        # Initialize opcode table if not already loaded
        if not self.opcode_table:
            if not self.version:
                self.version = PowerBuilderVersion(10, 5, True)
                logger.info("Using default PowerBuilder version: %s", self.version)

            version_str = str(self.version)
            from src.decompile.pcode.opcodes.definitions import get_opcodes_for_version

            self.opcode_table = get_opcodes_for_version(version_str)
            logger.info(
                "Loaded opcode table for %s (%d opcodes)",
                self.version,
                len(self.opcode_table),
            )

        # Determine if parallel processing is beneficial
        use_parallel = self._should_use_parallel_processing(
            pcode_info, len(pcode_bytes)
        )

        if (
            use_parallel
            and pcode_info
            and hasattr(pcode_info, "sections")
            and pcode_info.sections
        ):
            logger.info(
                "Using parallel processing for %d sections", len(pcode_info.sections)
            )
            instructions = self._decode_sections_parallel(
                pcode_bytes, pcode_info.sections, object_name
            )
        else:
            logger.info("Using sequential processing")
            if pcode_info and hasattr(pcode_info, "sections") and pcode_info.sections:
                instructions = self._decode_sections_sequential(
                    pcode_bytes, pcode_info.sections
                )
            else:
                instructions = self.decode_pcode(pcode_bytes, 0, validate=True)

        # Determine object type from name
        object_type = self._detect_object_type(object_name)
        logger.debug("Detected object type '%s' for '%s'", object_type, object_name)

        # Store metadata from pcode_info
        metadata = {}
        if pcode_info and hasattr(pcode_info, "__dict__"):
            metadata = {
                k: v for k, v in pcode_info.__dict__.items() if not k.startswith("_")
            }

        return DecodedObject(
            name=object_name,
            type=object_type,
            version=self.version,
            instructions=instructions,
            metadata=metadata,
        )

    def _should_use_parallel_processing(
        self, pcode_info: Any, total_bytes: int
    ) -> bool:
        """Determine if parallel processing would be beneficial.

        Args:
            pcode_info: P-code section information
            total_bytes: Total bytes to process

        Returns:
            True if parallel processing should be used
        """
        if not pcode_info or not hasattr(pcode_info, "sections"):
            return False

        sections = pcode_info.sections
        if len(sections) < self.min_sections_for_parallel:
            return False

        # Check if any section is large enough to benefit from parallel processing
        large_sections = sum(
            1 for section in sections if section.length >= self.min_section_size
        )

        # Use parallel processing if we have multiple substantial sections
        # or if the total size is large enough to benefit from parallelism
        should_parallel = large_sections >= 2 or (
            total_bytes > self.min_section_size * 4 and len(sections) >= 2
        )

        logger.debug(
            "Parallel processing decision: %s (sections: %d, large_sections: %d, total_bytes: %d)",
            should_parallel,
            len(sections),
            large_sections,
            total_bytes,
        )

        return should_parallel

    def _decode_sections_parallel(
        self,
        pcode_bytes: bytes,
        sections: list[Any],
        object_name: str,
    ) -> list[PCodeInstruction]:
        """Decode sections in parallel with rich progress reporting.

        Args:
            pcode_bytes: Raw P-code bytes
            sections: List of section information
            object_name: Name of the object being decoded

        Returns:
            List of decoded instructions from all sections
        """
        all_instructions = []

        # Create progress bar for section processing
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]Decoding sections for {object_name}",
                total=len(sections),
            )

            # Prepare section data for parallel processing
            section_jobs = []
            for idx, section in enumerate(sections):
                # Calculate section boundaries
                section_start = 0 if idx == 0 else section.offset - sections[0].offset

                section_end = section_start + section.length
                section_data = pcode_bytes[section_start:section_end]

                section_jobs.append(
                    {
                        "idx": idx + 1,
                        "section": section,
                        "section_data": section_data,
                        "section_start": section_start,
                        "section_end": section_end,
                    }
                )

            # Process sections in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all section jobs
                future_to_section = {
                    executor.submit(
                        self._decode_single_section,
                        job["section_data"],
                        job["section"].offset,
                        job["idx"],
                    ): job
                    for job in section_jobs
                }

                # Collect results as they complete
                section_results = {}
                for future in as_completed(future_to_section):
                    job = future_to_section[future]
                    section_idx = job["idx"]

                    try:
                        section_instructions = future.result()
                        section_results[section_idx] = section_instructions

                        progress.update(
                            task_id,
                            advance=1,
                            description=f"[cyan]Decoded section {section_idx}/{len(sections)} "
                            f"({len(section_instructions)} instructions)",
                        )

                        logger.debug(
                            "Section %d completed: %d instructions",
                            section_idx,
                            len(section_instructions),
                        )

                    except Exception as e:
                        logger.error(
                            "Failed to decode section %d: %s",
                            section_idx,
                            e,
                        )
                        section_results[section_idx] = []
                        progress.update(task_id, advance=1)

            # Combine results in order
            for section_idx in sorted(section_results.keys()):
                instructions = section_results[section_idx]
                all_instructions.extend(instructions)
                logger.info(
                    "Section %d: %d instructions",
                    section_idx,
                    len(instructions),
                )

        logger.info(
            "Parallel decoding complete: %d total instructions from %d sections",
            len(all_instructions),
            len(sections),
        )

        return all_instructions

    def _decode_sections_sequential(
        self,
        pcode_bytes: bytes,
        sections: list[Any],
    ) -> list[PCodeInstruction]:
        """Decode sections sequentially (fallback method).

        Args:
            pcode_bytes: Raw P-code bytes
            sections: List of section information

        Returns:
            List of decoded instructions from all sections
        """
        all_instructions = []

        for idx, section in enumerate(sections):
            logger.info(
                "Processing section %d: offset=0x%04x, length=%d",
                idx + 1,
                section.offset,
                section.length,
            )

            # Calculate section boundaries
            section_start = 0 if idx == 0 else section.offset - sections[0].offset

            section_end = section_start + section.length
            section_data = pcode_bytes[section_start:section_end]

            # Decode this section
            section_instructions = self._decode_single_section(
                section_data, section.offset, idx + 1
            )

            logger.info(
                "Section %d yielded %d instructions",
                idx + 1,
                len(section_instructions),
            )
            all_instructions.extend(section_instructions)

        return all_instructions

    def _decode_single_section(
        self,
        section_data: bytes,
        section_offset: int,
        section_idx: int,
    ) -> list[PCodeInstruction]:
        """Decode a single P-code section.

        This method is thread-safe and can be called in parallel.

        Args:
            section_data: Raw bytes for this section
            section_offset: Base offset for addresses
            section_idx: Section index for logging

        Returns:
            List of decoded instructions for this section
        """
        logger.debug(
            "Decoding section %d: %d bytes at offset 0x%04x",
            section_idx,
            len(section_data),
            section_offset,
        )

        if len(section_data) >= 16:
            logger.debug(
                "Section %d first 16 bytes: %s",
                section_idx,
                section_data[:16].hex(),
            )

        # Use the parent class method for actual decoding
        # This creates a new decoder state for this thread
        return self.decode_pcode(section_data, section_offset, validate=False)

    def decode_large_file_with_mmap(
        self,
        file_path: Path,
        entry_offset: int,
        entry_size: int,
        object_name: str,
    ) -> DecodedObject:
        """Decode a large file using memory mapping for efficiency.

        Args:
            file_path: Path to the PBD file
            entry_offset: Offset to the object's data
            entry_size: Size of the object's data
            object_name: Name of the object

        Returns:
            Decoded object with instructions and metadata
        """
        logger.info(
            "Using memory mapping for large file: %s (size: %d bytes)",
            object_name,
            entry_size,
        )

        with file_path.open("rb") as f:
            # Memory map the file for efficient access
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Extract object data from memory map
                object_data = mm[entry_offset : entry_offset + entry_size]

                # Auto-detect version if not set
                if not self.version:
                    from src.extract.pbd.version_detection import PBVersionDetector

                    detector = PBVersionDetector()
                    # Seek to beginning for version detection
                    mm.seek(0)
                    self.version = detector.detect_from_file(mm)
                    logger.info("Auto-detected PowerBuilder version: %s", self.version)

                # Load version-specific opcode table
                if not self.opcode_table:
                    if self.version is None:
                        raise ValueError("PowerBuilder version detection failed")
                    version_str = f"pb{self.version.major}_{self.version.minor}"
                    from src.decompile.pcode.opcodes.definitions import (
                        get_opcodes_for_version,
                    )

                    self.opcode_table = get_opcodes_for_version(version_str)
                    logger.info("Using opcode table for %s", self.version)

                # Detect object type
                object_type = self._detect_object_type(object_name)

                # Parse object header to find P-code
                pcode_offset, pcode_size = self._find_pcode_in_object(
                    object_data,
                    object_type,
                )

                if pcode_offset and pcode_size:
                    pcode_bytes = object_data[pcode_offset : pcode_offset + pcode_size]
                    instructions = self.decode_pcode(
                        pcode_bytes,
                        entry_offset + pcode_offset,
                    )
                else:
                    instructions = []

                # Create decoded object
                return DecodedObject(
                    name=object_name,
                    type=object_type,
                    version=self.version,
                    instructions=instructions,
                    metadata=self.metadata,
                )

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for the parallel decoder.

        Returns:
            Dictionary containing performance metrics
        """
        return {
            "max_workers": self.max_workers,
            "use_memory_mapping": self.use_memory_mapping,
            "min_section_size": self.min_section_size,
            "min_sections_for_parallel": self.min_sections_for_parallel,
            "opcode_table_size": len(self.opcode_table) if self.opcode_table else 0,
            "version": str(self.version) if self.version else None,
        }
