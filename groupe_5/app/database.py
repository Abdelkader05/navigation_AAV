"""Gestion SQLite3 (squelette)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "groupe5.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)
