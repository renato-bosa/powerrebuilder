"""Version detector wrapper implementing IVersionDetector interface."""

from src.extract.pbd.version_detection import PBVersionDetector


class VersionDetector:
    """Wrapper for PBVersionDetector that implements IVersionDetector interface."""

    def detect_version(self, data: bytes) -> str:
        """Detect PowerBuilder version from data.

        Args:
            data: Binary data to analyze

        Returns:
            Version string (e.g., "pb10_5")
        """
        # Try to detect from header
        version = PBVersionDetector.detect_from_header(data[:8])

        if version:
            return str(version)

        # Try opcode pattern detection if header detection fails
        version = PBVersionDetector.detect_from_opcode_patterns(data)

        if version:
            return str(version)

        # Default version
        default_version = PBVersionDetector.get_default_version()
        return str(default_version)
