import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_cached_opcodes: dict[int, dict[str, Any]] | None = None
_unknown_opcode_logger_configured = False
UNKNOWN_OPCODE_LOGGER_NAME = "unknown_opcodes"
UNKNOWN_OPCODE_LOG_FILE = "unknown_opcodes.log"

# Determine the path to opcodes.yaml relative to this file
# This assumes opcodes.py and opcodes.yaml are in the same directory
DEFAULT_OPCODES_YAML_PATH = Path(__file__).parent / "opcodes.yaml"


def load_opcodes(opcodes_yaml_path: Path = DEFAULT_OPCODES_YAML_PATH) -> dict[int, dict[str, Any]]:
    """Loads PowerBuilder opcode definitions from a YAML file.

    The YAML file is expected to have a top-level dictionary where keys are
    integer opcode byte values (or hex strings like "0x0A" that can be converted to int),
    and values are dictionaries containing opcode properties (mnemonic, operands, etc.).

    Args:
        opcodes_yaml_path: Path to the opcodes.yaml file.

    Returns:
        A dictionary mapping opcode byte values (int) to their definitions.
        Returns an empty dictionary if the file is not found or cannot be parsed.
    """
    global _cached_opcodes
    if _cached_opcodes is not None:
        # Potentially add a check here if opcodes_yaml_path differs from the one used for caching
        # For now, if cached, return it directly.
        return _cached_opcodes

    raw_opcodes: dict[Any, Any] = {}
    parsed_opcodes: dict[int, dict[str, Any]] = {}

    if not opcodes_yaml_path.exists():
        logger.warning(f"Opcode definition file not found: {opcodes_yaml_path}. No opcodes will be loaded.")
        _cached_opcodes = {}
        return _cached_opcodes

    try:
        with open(opcodes_yaml_path, encoding='utf-8') as f:
            raw_opcodes = yaml.safe_load(f)
        if not raw_opcodes:  # Handles empty YAML file
            logger.info(f"Opcode definition file {opcodes_yaml_path} is empty. Loaded 0 opcodes.")
            _cached_opcodes = {}
            return _cached_opcodes

    except yaml.YAMLError as e:
        logger.error(f"Error parsing opcode definition file {opcodes_yaml_path}: {e}")
        _cached_opcodes = {}
        return _cached_opcodes
    except OSError as e:
        logger.error(f"Error reading opcode definition file {opcodes_yaml_path}: {e}")
        _cached_opcodes = {}
        return _cached_opcodes

    # Process raw_opcodes to ensure keys are integers
    for key, value in raw_opcodes.items():
        opcode_val: int | None = None
        if isinstance(key, int):
            opcode_val = key
        elif isinstance(key, str):
            try:
                opcode_val = int(key, 0)  # int(key, 0) handles "0x" prefix, or dec if no prefix
            except ValueError:
                logger.warning(f"Invalid opcode key '{key}' in {opcodes_yaml_path}. Must be integer or hex string. Skipping.")
                continue
        else:
            logger.warning(f"Invalid type for opcode key '{key}' (type: {type(key)}) in {opcodes_yaml_path}. Skipping.")
            continue

        if not isinstance(value, dict):
            logger.warning(f"Opcode definition for key '{key}' (value: {opcode_val}) in {opcodes_yaml_path} is not a dictionary. Skipping.")
            continue

        parsed_opcodes[opcode_val] = value

    _cached_opcodes = parsed_opcodes
    logger.info(f"Successfully loaded {len(_cached_opcodes)} opcodes from {opcodes_yaml_path}.")
    return _cached_opcodes


def get_opcode_info(opcode_value: int, opcodes_yaml_path: Path = DEFAULT_OPCODES_YAML_PATH) -> dict[str, Any] | None:
    """Retrieves the definition for a specific opcode value.
    Loads opcodes from YAML if not already cached.

    Args:
        opcode_value: The byte value of the opcode.
        opcodes_yaml_path: Path to the opcodes.yaml file (if loading is needed).

    Returns:
        The opcode definition dictionary, or None if not found.
    """
    opcodes = load_opcodes(opcodes_yaml_path)
    return opcodes.get(opcode_value)


def _setup_unknown_opcode_logger() -> None:
    """Sets up the logger for unknown opcodes if not already configured."""
    global _unknown_opcode_logger_configured
    if _unknown_opcode_logger_configured:
        return

    ulogger = logging.getLogger(UNKNOWN_OPCODE_LOGGER_NAME)
    # Prevent propagation to root logger to avoid duplicate console output
    # if root logger also has a handler that logs to console.
    ulogger.propagate = False
    ulogger.setLevel(logging.INFO)  # Or desired level for this specific log

    # Check if a handler for this file is already added to avoid duplicates
    # across multiple calls or in different parts of an application,
    # though with _unknown_opcode_logger_configured flag, this might be redundant here.
    if not any(isinstance(h, logging.FileHandler) and Path(h.baseFilename).name == UNKNOWN_OPCODE_LOG_FILE for h in ulogger.handlers):
        try:
            fh = logging.FileHandler(UNKNOWN_OPCODE_LOG_FILE, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - Opcode: 0x%(opcode_value)02X - Pos: %(stream_pos)s - Obj: %(source_obj)s - Context: %(context_hex)s - Note: %(message)s')
            fh.setFormatter(formatter)
            ulogger.addHandler(fh)
            _unknown_opcode_logger_configured = True
            logger.debug(f"Unknown opcode logger '{UNKNOWN_OPCODE_LOGGER_NAME}' configured to write to {UNKNOWN_OPCODE_LOG_FILE}")
        except Exception as e:
            logger.error(f"Failed to configure file handler for unknown opcode logger: {e}", exc_info=True)
            # Potentially fall back to logging to main logger if file setup fails
    else:
        _unknown_opcode_logger_configured = True  # Already configured by another handler presumably


def log_unknown_opcode(
    opcode_value: int,
    context_bytes_around: bytes | None = None,  # e.g., 3 bytes before, opcode, 3 bytes after
    num_context_bytes_each_side: int = 3,
    stream_position: int | None = None,
    source_object_name: str | None = "UnknownObject",
    note: str = "Opcode not found in definition table.",
) -> None:
    """Logs an unknown opcode and its surrounding context to a dedicated log file.

    Args:
        opcode_value: The byte value of the unknown opcode.
        context_bytes_around: Bytes surrounding the opcode. Ideally, this includes
                              `num_context_bytes_each_side`, then the opcode byte(s),
                              then `num_context_bytes_each_side` again.
                              If None, context will be logged as N/A.
        num_context_bytes_each_side: How many context bytes are expected on each side of the opcode itself within context_bytes_around.
        stream_position: The absolute position/offset of the opcode in the p-code stream.
        source_object_name: The name of the PBD object (e.g., window, function) where this occurred.
        note: An additional note for the log entry.
    """
    _setup_unknown_opcode_logger()
    ulogger = logging.getLogger(UNKNOWN_OPCODE_LOGGER_NAME)

    context_hex = "N/A"
    if context_bytes_around:
        context_hex = context_bytes_around.hex(' ')

    # Ensure stream_pos and source_obj have a string representation for the formatter
    pos_str = str(stream_position) if stream_position is not None else "N/A"
    obj_str = str(source_object_name) if source_object_name else "N/A"

    # Log using a dictionary for the extra fields that the formatter expects
    log_record_extra = {
        "opcode_value": opcode_value,
        "stream_pos": pos_str,
        "source_obj": obj_str,
        "context_hex": context_hex,
    }
    ulogger.info(note, extra=log_record_extra)


# Placeholder types for symbolic execution context (to be refined)
class SymbolicStack:
    """Placeholder for a symbolic execution stack."""
    def __init__(self) -> None:
        self.depth = 0

    def push(self, items=1) -> None:
        self.depth += items

    def pop(self, items=1) -> None:
        self.depth = max(0, self.depth - items)


class CFGNode:
    """Placeholder for a Control Flow Graph node."""
    def __init__(self, address: int) -> None:
        self.address = address
        self.successors: list[CFGNode] = []


@dataclass
class FallbackResult:
    """Result of a symbolic execution fallback attempt."""
    treated_as_nop: bool = True
    potential_jump_target: int | None = None
    stack_change: int = 0  # Net change to stack depth


def attempt_symbolic_fallback(
    opcode_value: int,
    operand_bytes: bytes | None = None,
    # current_stack: Optional[SymbolicStack] = None, # To be used later
    # current_cfg_node: Optional[CFGNode] = None,    # To be used later
    source_object_name: str | None = "UnknownObject",
) -> FallbackResult:
    """Placeholder for attempting symbolic execution fallback for an unknown opcode.
    Currently, it logs and assumes the opcode is a NOP for CFG purposes.

    Args:
        opcode_value: The byte value of the unknown opcode.
        operand_bytes: Any bytes read as potential operands for this opcode.
        source_object_name: Name of the source PBD object.

    Returns:
        A FallbackResult indicating how to treat the opcode.
    """
    operands_hex = operand_bytes.hex(' ') if operand_bytes else "N/A"
    logger.info(
        f"Symbolic fallback for UNKNOWN Opcode 0x{opcode_value:02X} in '{source_object_name}'. "
        f"Operands (hex): {operands_hex}. Treating as NOP for now.",
    )
    # In the future, this function would analyze operand_bytes to infer behavior:
    # - Check for potential jump offsets (e.g., small relative offsets).
    # - Guess stack effects based on common patterns.
    # - Modify current_stack or current_cfg_node based on inferences.
    return FallbackResult(treated_as_nop=True, stack_change=0)


if __name__ == '__main__':
    # Example usage and test
    logging.basicConfig(level=logging.DEBUG)

    # Create a dummy opcodes.yaml for testing this script directly
    dummy_yaml_content = """
0x01:
  mnemonic: "NOP"
  description: "No operation"
"TestKey": # Invalid key example
  mnemonic: "INVALID_KEY_TYPE"
0x10:
  mnemonic: "PUSH_CONST"
  operands: ["int16"]
"0x2A": # Hex key example
  mnemonic: "CALL_FUNC"
  description: "Call function by ID"
not_a_dict_key: "some string" # Invalid value type
    """
    dummy_path = Path("./dummy_opcodes_test.yaml")
    with open(dummy_path, 'w', encoding="utf-8") as f_dummy:
        f_dummy.write(dummy_yaml_content)

    logger.info("--- Testing with dummy_opcodes_test.yaml ---")
    loaded_dummy_opcodes = load_opcodes(dummy_path)
    logger.info(f"Loaded opcodes: {loaded_dummy_opcodes}")

    nop_info = get_opcode_info(0x01, dummy_path)
    logger.info(f"Info for 0x01 (NOP): {nop_info}")
    assert nop_info
    assert nop_info['mnemonic'] == "NOP"

    push_info = get_opcode_info(0x10, dummy_path)
    logger.info(f"Info for 0x10 (PUSH_CONST): {push_info}")
    assert push_info
    assert push_info['mnemonic'] == "PUSH_CONST"

    call_info = get_opcode_info(0x2A, dummy_path)
    logger.info(f"Info for 0x2A (CALL_FUNC): {call_info}")
    assert call_info
    assert call_info['mnemonic'] == "CALL_FUNC"

    missing_info = get_opcode_info(0xFF, dummy_path)
    logger.info(f"Info for 0xFF (MISSING): {missing_info}")
    assert missing_info is None

    # Test logging unknown opcodes
    logger.info("--- Testing unknown opcode logging ---")
    # Simulate some context bytes: 3 before, 0xFE (unknown), 3 after
    # Opcode itself would be part of this stream typically
    example_context = b'\x01\x02\x03\xFE\x0A\x0B\x0C'
    log_unknown_opcode(0xFE, context_bytes_around=example_context, stream_position=1234, source_object_name="w_test.ue_event", note="First encounter")
    log_unknown_opcode(0xFD, stream_position=1250, source_object_name="f_my_func")  # No context
    log_unknown_opcode(0xFC, context_bytes_around=b'\xAA\xBB\xFC\xDD\xEE', num_context_bytes_each_side=2, stream_position=1280, source_object_name="w_another.cb_1.clicked")
    logger.info(f"Unknown opcodes should be logged to ./{UNKNOWN_OPCODE_LOG_FILE}")

    logger.info("--- Testing symbolic fallback placeholder ---")
    fallback_nop = attempt_symbolic_fallback(0xF0, source_object_name="test_obj_1")
    assert fallback_nop.treated_as_nop
    fallback_with_ops = attempt_symbolic_fallback(0xF1, operand_bytes=b'\x12\x34', source_object_name="test_obj_2")
    assert fallback_with_ops.treated_as_nop

    # Test with default path (likely empty or non-existent during this test run)
    logger.info("--- Testing with default opcodes.yaml (may be empty/missing) ---")
    _cached_opcodes = None  # Clear cache for this test
    default_opcodes = load_opcodes()
    logger.info(f"Loaded default opcodes: {default_opcodes}")

    # Clean up dummy file
    dummy_path.unlink()
    logger.info("--- Test finished ---")
