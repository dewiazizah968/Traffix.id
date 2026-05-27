"""Path resolution helpers for Traffix backend and monorepo assets."""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def backend_root() -> Path:
    """Return the absolute backend package root.

    Returns:
        Path to the `backend/` directory.
    """
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Return the absolute monorepo root (parent of backend).

    Returns:
        Path to the repository root.
    """
    return backend_root().parent


def resolve_asset_path(configured: str) -> Path:
    """Resolve a configured path against backend and repo roots.

    Resolution order:
      1. Absolute path as-is
      2. ``backend/<configured>``
      3. ``repo/<configured>``
      4. ``repo/backend/<configured>`` when configured starts with ``../``

    Args:
        configured: Relative or absolute path from settings.

    Returns:
        First existing path, otherwise backend-relative candidate.
    """
    path = Path(configured)
    if path.is_absolute():
        return path

    candidates = (
        backend_root() / path,
        repo_root() / path,
    )
    if configured.startswith("../"):
        candidates = (
            backend_root() / path,
            (backend_root() / path).resolve(),
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return backend_root() / path
