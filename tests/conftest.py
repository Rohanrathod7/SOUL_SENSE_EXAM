import sqlite3
import pytest
import tempfile
import os

@pytest.fixture
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    def _get_conn():
        return sqlite3.connect(path)

    monkeypatch.setattr("app.db.get_connection", _get_conn)

    yield path

    os.remove(path)
