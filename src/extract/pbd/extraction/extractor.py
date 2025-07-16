"""Placeholder extractor module for backward compatibility."""

import logging

logger = logging.getLogger(__name__)


class Extractor:
    """Placeholder extractor class."""

    def __init__(self, *args, **kwargs):
        """Initialize placeholder extractor."""
        pass

    def extract(self, *args, **kwargs):
        """Placeholder extract method."""
        logger.warning("Using placeholder extractor - functionality may be limited")
        return None