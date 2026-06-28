"""Shared pytest fixtures.

Each test runs against a fresh, isolated SQLite database in a temp dir, so tests
never touch the real users.db and don't leak state into each other.
"""
import sys
from pathlib import Path

import pytest

# app.py lives in backend/ (the parent of this tests/ dir); put it on the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as flask_app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A Flask test client backed by a throwaway database."""
    db_path = tmp_path / "test.db"
    # get_db() reads the module-level DATABASE at call time, so pointing it at a
    # temp file (and re-running init_db) isolates every test.
    monkeypatch.setattr(flask_app, "DATABASE", str(db_path))
    flask_app.init_db()
    flask_app.app.config.update(TESTING=True)
    with flask_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def auth_client(client):
    """A client already registered and logged in as 'alice'."""
    client.post("/register", json={"username": "alice", "password": "secret"})
    client.post("/login", json={"username": "alice", "password": "secret"})
    return client
