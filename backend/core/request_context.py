"""Request context utilities for Traffix backend."""

import uuid


def generate_request_id() -> str:
    """Generate short request ID.

    Returns:
        Formatted request ID string.
    """
    return f"req_{uuid.uuid4().hex[:8]}"
