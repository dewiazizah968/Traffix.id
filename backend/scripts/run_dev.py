#!/usr/bin/env python3
"""
Development server launcher for Traffix backend.

Usage:
    python scripts/run_dev.py

Reads host, port, and log_level from core/config.py Settings,
which loads values from .env file in the backend root.
"""

import os
import sys

# Ensure backend root is on PYTHONPATH regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from core.config import settings


def main() -> None:
    """Launch the development Uvicorn server."""
    print(f"[Traffix] Launching {settings.app_name} v{settings.app_version}")
    print(f"[Traffix] Environment : {settings.app_env}")
    print(f"[Traffix] Listening on: http://{settings.host}:{settings.port}")
    print(f"[Traffix] Docs at     : http://localhost:{settings.port}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
