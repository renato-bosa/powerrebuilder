"""PBD extraction exceptions.

This module re-exports PBD-specific exceptions from common.exceptions
for backward compatibility. All exceptions are now consolidated in the common module.

DEPRECATED: Import directly from common.exceptions instead.
"""

# Re-export PBD-specific exceptions from common module
from common.exceptions import (
    DataExtractionError,
    DatError,
    EntryError,
    HeaderError,
    NodeError,
    PbdError,
    PfcExcludedError,
)

# Aliases for backward compatibility
PBDError = PbdError
PBDHeaderError = HeaderError
PBDNodeError = NodeError
PBDEntryError = EntryError
PBDDataError = DatError

__all__ = [
    "DatError",
    "DataExtractionError",
    "EntryError",
    "HeaderError",
    "NodeError",
    "PBDDataError",
    "PBDEntryError",
    # Aliases
    "PBDError",
    "PBDHeaderError",
    "PBDNodeError",
    "PbdError",
    "PfcExcludedError",
]
