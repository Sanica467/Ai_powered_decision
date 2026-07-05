"""Pytest configuration and fixtures."""
import os
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("DEBUG", "true")


@pytest.fixture
def app():
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    from app.database import Base, get_engine
    from app import models  # noqa: F401 - ensure models loaded

    # Create tables in the in-memory SQLite DB
    Base.metadata.create_all(bind=get_engine())

    return TestClient(app)
