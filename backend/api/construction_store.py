import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime


class ConstructionStore:
    def __init__(self, path):
        self.path = path
        with self.connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS construction_sources (
                    name TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS construction_visibility (
                    notice_id TEXT PRIMARY KEY,
                    hidden INTEGER NOT NULL CHECK (hidden IN (0, 1)),
                    changed_at TEXT NOT NULL,
                    changed_by TEXT NOT NULL
                )
            """)

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def read_sources(self):
        with self.connection() as connection:
            return {
                name: json.loads(payload)
                for name, payload in connection.execute(
                    "SELECT name, payload FROM construction_sources"
                )
            }

    def save_sources(self, sources):
        with self.connection() as connection:
            connection.executemany("""
                INSERT INTO construction_sources (name, payload) VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET payload = excluded.payload
            """, [
                (name, json.dumps(data, ensure_ascii=False))
                for name, data in sources.items()
            ])

    def hidden_ids(self):
        with self.connection() as connection:
            return {row[0] for row in connection.execute(
                "SELECT notice_id FROM construction_visibility WHERE hidden = 1"
            )}

    def set_hidden(self, notice_id, hidden, previous_hidden, account):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT hidden FROM construction_visibility WHERE notice_id = ?", (notice_id,)
            ).fetchone()
            if bool(current[0] if current else False) != previous_hidden:
                return False
            connection.execute("""
                INSERT INTO construction_visibility
                    (notice_id, hidden, changed_at, changed_by) VALUES (?, ?, ?, ?)
                ON CONFLICT(notice_id) DO UPDATE SET
                    hidden = excluded.hidden,
                    changed_at = excluded.changed_at,
                    changed_by = excluded.changed_by
            """, (notice_id, hidden, datetime.now(UTC).isoformat(timespec="seconds"), account))
            return True
