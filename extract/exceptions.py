"""Custom exceptions for PBD processing."""


class PbdError(Exception):
    """Base class for exceptions in PBD processing."""
    pass


class PbdFileError(PbdError):
    """Exception related to PBD file access or structure."""
    pass


class PbdHeaderError(PbdFileError):
    """Exception for errors encountered while parsing PBD header."""
    pass


class PbdNodeError(PbdFileError):
    """Exception for errors related to PBD NOD (Node B-Tree) blocks."""
    pass


class PbdEntryError(PbdFileError):
    """Exception for errors related to PBD ENT (Entry) definitions."""
    pass


class PbdDataError(PbdFileError):
    """Exception for errors related to PBD DAT (Data) blocks."""
    pass


class PbdObjectError(PbdError):
    """Exception for errors related to a specific PbdObject."""
    pass


class PbdResourceError(PbdObjectError):
    """Exception for errors related to resource extraction from PbdObject."""
    pass


class PbdPfcError(PbdError):
    """Exception for errors related to PFC (PowerBuilder Foundation Classes) handling."""
    pass
