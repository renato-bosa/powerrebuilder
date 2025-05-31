class DataExtractionError(Exception):
    pass


class PbdError(Exception):
    """Base class for all PBD parsing errors."""
    pass


class HeaderError(PbdError):
    """Error related to PBL/PBD header parsing."""
    pass


class NodeError(PbdError):
    """Error related to NOD block parsing."""
    pass


class EntryError(PbdError):
    """Error related to PbEntryDefinition parsing."""
    pass


class DatError(PbdError):
    """Error related to DAT block parsing."""
    pass


class PfcExcludedError(PbdError):
    """Indicates that an object was skipped because it matched a PFC hash."""
    pass
