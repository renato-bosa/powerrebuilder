"""Utility functions for working with PowerBuilder binary files."""

def calculate_content_hash(content: str | bytes) -> str:
    """Calculates the SHA-1 hash of the given content.
    If content is a string, it's encoded to UTF-8 before hashing.
    """
    import hashlib
    
    sha1 = hashlib.sha1()
    if isinstance(content, str):
        sha1.update(content.encode('utf-8'))
    elif isinstance(content, bytes):
        sha1.update(content)
    else:
        raise TypeError(f"Content must be string or bytes, not {type(content)}")
    
    return sha1.hexdigest()


__all__ = ["calculate_content_hash"]
