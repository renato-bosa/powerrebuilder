"""Streaming P-code decoder for improved performance with large files.

This module provides a streaming decoder that processes P-code files in chunks
to reduce memory usage and improve performance for large files.
"""

import logging
import mmap
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from src.decompile.pcode.decoder import DecodedObject, PCodeInstruction
from src.decompile.pcode.opcodes.definitions import get_opcodes_for_version
from src.extract.pbd.version_detection import PowerBuilderVersion

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for streaming decoder."""

    chunk_size: int = 8192  # 8KB chunks
    use_memory_mapping: bool = True
    max_memory_usage_mb: int = 100
    enable_instruction_batching: bool = True
    batch_size: int = 100


class StreamingPCodeDecoder:
    """Streaming P-code decoder for improved performance."""

    def __init__(
        self,
        version: PowerBuilderVersion,
        config: StreamingConfig | None = None,
    ) -> None:
        """Initialize the streaming decoder.

        Args:
            version: PowerBuilder version
            config: Streaming configuration
        """
        self.version = version
        self.config = config or StreamingConfig()

        # Load version-specific opcode table
        version_str = f"pb{version.major}_{version.minor}"
        self.opcode_table = get_opcodes_for_version(version_str)

        logger.debug("Streaming decoder initialized for %s", version)

    def decode_file_streaming(self, file_path: Path) -> Iterator[PCodeInstruction]:
        """Decode a P-code file using streaming approach.

        Args:
            file_path: Path to P-code file

        Yields:
            Decoded P-code instructions
        """
        file_size = file_path.stat().st_size

        if self.config.use_memory_mapping and file_size > 1024 * 1024:  # 1MB
            yield from self._decode_with_memory_mapping(file_path)
        else:
            yield from self._decode_with_chunked_reading(file_path)

    def _decode_with_memory_mapping(
        self, file_path: Path
    ) -> Iterator[PCodeInstruction]:
        """Decode using memory mapping for large files."""
        logger.debug("Using memory mapping for %s", file_path)

        try:
            with file_path.open("rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    yield from self._decode_memory_mapped_data(mm, str(file_path))

        except Exception as e:
            logger.warning("Memory mapping failed for %s: %s", file_path, e)
            # Fallback to regular reading
            yield from self._decode_with_chunked_reading(file_path)

    def _decode_with_chunked_reading(
        self, file_path: Path
    ) -> Iterator[PCodeInstruction]:
        """Decode using chunked reading for smaller files."""
        logger.debug("Using chunked reading for %s", file_path)

        with file_path.open("rb") as f:
            buffer = b""
            offset = 0

            while True:
                chunk = f.read(self.config.chunk_size)
                if not chunk:
                    break

                buffer += chunk

                # Process complete instructions from buffer
                processed_bytes = 0
                for instruction in self._extract_instructions_from_buffer(
                    buffer, offset, str(file_path)
                ):
                    yield instruction
                    processed_bytes = (
                        instruction.offset + len(instruction.raw_bytes) - offset
                    )

                # Keep remaining bytes for next iteration
                if processed_bytes > 0:
                    buffer = buffer[processed_bytes:]
                    offset += processed_bytes

            # Process any remaining buffer
            if buffer:
                for instruction in self._extract_instructions_from_buffer(
                    buffer, offset, str(file_path)
                ):
                    yield instruction

    def _decode_memory_mapped_data(
        self, mm: mmap.mmap, source_name: str
    ) -> Iterator[PCodeInstruction]:
        """Decode instructions from memory-mapped data."""
        offset = 0

        while offset < len(mm):
            try:
                instruction = self._decode_single_instruction(mm, offset, source_name)
                if instruction:
                    yield instruction
                    offset += len(instruction.raw_bytes)
                else:
                    offset += 1  # Skip invalid byte

            except struct.error:
                # End of valid data
                break
            except Exception as e:
                logger.warning("Error decoding at offset %d: %s", offset, e)
                offset += 1

    def _extract_instructions_from_buffer(
        self, buffer: bytes, base_offset: int, source_name: str
    ) -> Iterator[PCodeInstruction]:
        """Extract complete instructions from buffer."""
        offset = 0

        while offset < len(buffer):
            try:
                remaining = buffer[offset:]
                if len(remaining) < 2:  # Need at least 2 bytes for opcode
                    break

                instruction = self._decode_single_instruction(
                    remaining, 0, source_name, base_offset + offset
                )

                if instruction:
                    # Check if we have the complete instruction
                    if len(remaining) >= len(instruction.raw_bytes):
                        yield instruction
                        offset += len(instruction.raw_bytes)
                    else:
                        # Incomplete instruction, wait for more data
                        break
                else:
                    offset += 1

            except struct.error:
                break
            except Exception as e:
                logger.warning("Error decoding at buffer offset %d: %s", offset, e)
                offset += 1

    def _decode_single_instruction(
        self,
        data: bytes | mmap.mmap,
        offset: int,
        source_name: str,
        absolute_offset: int | None = None,
    ) -> PCodeInstruction | None:
        """Decode a single P-code instruction.

        Args:
            data: Data to decode from
            offset: Offset within data
            source_name: Name of source for debugging
            absolute_offset: Absolute offset in file (for buffer decoding)

        Returns:
            Decoded instruction or None if invalid
        """
        if offset + 1 >= len(data):
            return None

        try:
            # Read opcode (first byte or word)
            opcode = data[offset]
            instruction_offset = (
                absolute_offset if absolute_offset is not None else offset
            )

            # Look up opcode in table
            if opcode in self.opcode_table:
                opcode_name, operand_count, description = self.opcode_table[opcode]

                # Calculate instruction size
                instruction_size = 1 + operand_count  # opcode + operands

                if offset + instruction_size > len(data):
                    return None  # Incomplete instruction

                # Extract operands
                operands = []
                raw_bytes = data[offset : offset + instruction_size]

                for i in range(operand_count):
                    operand_offset = offset + 1 + i
                    if operand_offset < len(data):
                        operands.append(data[operand_offset])

                return PCodeInstruction(
                    offset=instruction_offset,
                    opcode=opcode,
                    opcode_name=opcode_name,
                    operands=operands,
                    raw_bytes=bytes(raw_bytes),
                    comment=description,
                )
            # Unknown opcode, treat as single byte
            return PCodeInstruction(
                offset=instruction_offset,
                opcode=opcode,
                opcode_name=f"UNKNOWN_{opcode:02X}",
                operands=[],
                raw_bytes=bytes([opcode]),
                comment="Unknown opcode",
            )

        except Exception as e:
            logger.debug("Failed to decode instruction at offset %d: %s", offset, e)
            return None

    def decode_file_to_object(self, file_path: Path, object_name: str) -> DecodedObject:
        """Decode entire file to DecodedObject using streaming.

        Args:
            file_path: Path to P-code file
            object_name: Name of the object

        Returns:
            Decoded object with all instructions
        """
        instructions = []
        metadata = {"file_size": file_path.stat().st_size, "streaming_used": True}

        # Collect instructions using streaming decoder
        instruction_count = 0
        for instruction in self.decode_file_streaming(file_path):
            instructions.append(instruction)
            instruction_count += 1

            # Batch processing for memory efficiency
            if (
                self.config.enable_instruction_batching
                and instruction_count % self.config.batch_size == 0
            ):
                logger.debug(
                    "Processed %d instructions from %s",
                    instruction_count,
                    file_path.name,
                )

        logger.info(
            "Decoded %d instructions from %s using streaming",
            len(instructions),
            file_path.name,
        )

        return DecodedObject(
            name=object_name,
            type="streaming_decoded",
            version=self.version,
            instructions=instructions,
            metadata=metadata,
        )


def create_streaming_decoder(
    version: PowerBuilderVersion,
    enable_memory_mapping: bool = True,
    chunk_size: int = 8192,
) -> StreamingPCodeDecoder:
    """Create a streaming decoder with optimized configuration.

    Args:
        version: PowerBuilder version
        enable_memory_mapping: Whether to use memory mapping for large files
        chunk_size: Chunk size for reading

    Returns:
        Configured streaming decoder
    """
    config = StreamingConfig(
        chunk_size=chunk_size,
        use_memory_mapping=enable_memory_mapping,
        max_memory_usage_mb=100,
        enable_instruction_batching=True,
        batch_size=100,
    )

    return StreamingPCodeDecoder(version, config)
