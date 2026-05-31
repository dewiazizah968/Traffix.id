"""Shared pytest fixtures for Traffix API tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from core.config import settings
from ml.registry import registry
from sim.tick_engine import tick_engine


@pytest.fixture(scope="session")
def api_client() -> Iterator[TestClient]:
    """Create a TestClient with heavyweight startup integrations disabled."""
    old_ml_auto_load = settings.ml_auto_load
    old_simulation_auto_start = settings.simulation_auto_start
    old_prediction_auto_refresh = settings.prediction_auto_refresh

    settings.ml_auto_load = False
    settings.simulation_auto_start = False
    settings.prediction_auto_refresh = False
    registry.clear()

    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client

    settings.ml_auto_load = old_ml_auto_load
    settings.simulation_auto_start = old_simulation_auto_start
    settings.prediction_auto_refresh = old_prediction_auto_refresh


@pytest.fixture(autouse=True)
def ensure_tick_stopped() -> Iterator[None]:
    """Keep tests from leaking background simulation tasks."""
    yield
    if tick_engine.is_running():
        # TestClient owns the event loop during lifespan; route tests should not
        # leave the loop running when auto-start is disabled.
        tick_engine._running = False
