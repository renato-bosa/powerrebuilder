"""Utilities for PFC (PowerBuilder Foundation Class) filtering."""

import hashlib
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_PFC_HASH_FILE = Path(__file__).parent / "pfc_hashes.yaml"


def load_pfc_hashes(pfc_hash_file_path: Path | None = None) -> set[str]:
    """Loads a set of PFC object SHA-1 hashes from a YAML file.
    The YAML file is expected to have a top-level key 'pfc_object_sha1_hashes'
    which contains a list of hash strings.

    Args:
        pfc_hash_file_path: Path to the YAML file. If None, uses default.

    Returns:
        A set of SHA-1 hash strings. Returns an empty set if file not found or error.
    """
    if pfc_hash_file_path is None:
        pfc_hash_file_path = DEFAULT_PFC_HASH_FILE

    if not pfc_hash_file_path.exists():
        logger.warning(f"PFC hash file not found: {pfc_hash_file_path}. No PFC objects will be excluded by default.")
        return set()

    try:
        with open(pfc_hash_file_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and "pfc_object_sha1_hashes" in data and isinstance(data["pfc_object_sha1_hashes"], list):
                hashes = {str(h) for h in data["pfc_object_sha1_hashes"]}
                logger.info(f"Loaded {len(hashes)} PFC object hashes from {pfc_hash_file_path}.")
                return hashes
            logger.warning(f"PFC hash file {pfc_hash_file_path} is not in the expected format. Expected a list under 'pfc_object_sha1_hashes'.")
            return set()
    except yaml.YAMLError as e:
        logger.error(f"Error parsing PFC hash file {pfc_hash_file_path}: {e}")
        return set()
    except OSError as e:
        logger.error(f"Error reading PFC hash file {pfc_hash_file_path}: {e}")
        return set()


def calculate_content_hash(content: str | bytes) -> str:
    """Calculates the SHA-1 hash of the given content.
    If content is a string, it's encoded to UTF-8 before hashing.
    """
    sha1 = hashlib.sha1()
    if isinstance(content, str):
        sha1.update(content.encode('utf-8'))
    elif isinstance(content, bytes):
        sha1.update(content)
    else:
        # Should not happen with type hinting, but as a safeguard
        raise TypeError("Content for hashing must be str or bytes.")
    return sha1.hexdigest()
