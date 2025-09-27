"""Database helper module for managing archive entries via SQLite."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from ...core.logging_manager import get_logger

ARCHIVE_DB = Path("data/archive.db")
LEGACY_ARCHIVE_JSON = Path("data/archive.json")
EXPORT_DIR = Path("data/exports")


class DatabaseModule:
    """SQLite-backed record store with duplicate checking (Duplikatprüfung)."""

    def __init__(self, database_file: Path = ARCHIVE_DB, logger: Optional[logging.Logger] = None) -> None:
        self.database_file = database_file
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger or get_logger("modules.database")
        self._initialise_database()

    # ------------------------------------------------------------------
    def list_entries(self) -> List[Dict[str, str]]:
        """Return all entries sorted alphabetically (alphabetisch)."""

        query = (
            "SELECT title, description, created_at FROM archive_entries "
            "ORDER BY LOWER(title)"
        )
        rows = self._fetch_all(query)
        return [self._row_to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    def add_entry(self, title: str, description: str) -> bool:
        """Insert a new entry; return False if the title already exists."""

        statement = "INSERT INTO archive_entries (title, description) VALUES (?, ?)"
        try:
            with self._connect() as connection:
                connection.execute(statement, (title.strip(), description.strip()))
                connection.commit()
        except sqlite3.IntegrityError:
            return False
        return True

    # ------------------------------------------------------------------
    def search(self, term: str) -> List[Dict[str, str]]:
        """Search title and description for a term (Suchwort)."""

        like_term = f"%{term.casefold()}%"
        query = (
            "SELECT title, description, created_at FROM archive_entries "
            "WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ? "
            "ORDER BY LOWER(title)"
        )
        rows = self._fetch_all(query, (like_term, like_term))
        return [self._row_to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    def filter_by_prefix(self, prefix: str) -> List[Dict[str, str]]:
        """Return entries whose title starts with the prefix (Anfang)."""

        like_prefix = f"{prefix.casefold()}%"
        query = (
            "SELECT title, description, created_at FROM archive_entries "
            "WHERE LOWER(title) LIKE ? ORDER BY LOWER(title)"
        )
        rows = self._fetch_all(query, (like_prefix,))
        return [self._row_to_dict(row) for row in rows]

    # ------------------------------------------------------------------
    def remove(self, title: str) -> bool:
        """Delete an entry by title."""

        statement = "DELETE FROM archive_entries WHERE title = ?"
        with self._connect() as connection:
            cursor = connection.execute(statement, (title,))
            connection.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    def get_entry(self, title: str) -> Optional[Dict[str, str]]:
        """Return a single entry by title if it exists."""

        query = (
            "SELECT title, description, created_at FROM archive_entries WHERE title = ? COLLATE NOCASE"
        )
        rows = self._fetch_all(query, (title,), limit=1)
        if rows:
            return self._row_to_dict(rows[0])
        return None

    # ------------------------------------------------------------------
    def export_entries_to_csv(self, target: Optional[Path] = None) -> Path:
        """Export the archive to CSV."""

        entries = self.list_entries()
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        target_path = target or EXPORT_DIR / "archive_export.csv"
        with target_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["title", "description", "created_at"])
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry)
        return target_path

    # ------------------------------------------------------------------
    def export_entries_to_json(self, target: Optional[Path] = None) -> Path:
        """Export the archive to JSON."""

        entries = self.list_entries()
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        target_path = target or EXPORT_DIR / "archive_export.json"
        payload = {"entries": entries}
        target_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return target_path

    # ------------------------------------------------------------------
    def _initialise_database(self) -> None:
        """Create the SQLite file and tables if required."""

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS archive_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE COLLATE NOCASE,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()
        self._migrate_legacy_json()

    # ------------------------------------------------------------------
    def _migrate_legacy_json(self) -> None:
        """Import entries from the previous JSON file if present."""

        if not LEGACY_ARCHIVE_JSON.exists():
            return
        try:
            legacy_payload = json.loads(LEGACY_ARCHIVE_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.logger.warning("Alte Archivdatei konnte nicht gelesen werden: %s", LEGACY_ARCHIVE_JSON)
            return

        entries = legacy_payload.get("entries", [])
        if not entries:
            return

        existing = self._count_entries()
        if existing:
            return

        self.logger.info("Migriere %s Einträge aus data/archive.json in die SQLite-Datenbank", len(entries))
        with self._connect() as connection:
            for entry in entries:
                title = str(entry.get("title", "")).strip()
                description = str(entry.get("description", "")).strip()
                if not title:
                    continue
                try:
                    connection.execute(
                        "INSERT OR IGNORE INTO archive_entries (title, description) VALUES (?, ?)",
                        (title, description),
                    )
                except sqlite3.DatabaseError as exc:
                    self.logger.error("Fehler beim Migrieren des Eintrags '%s': %s", title, exc)
            connection.commit()

    # ------------------------------------------------------------------
    def _count_entries(self) -> int:
        query = "SELECT COUNT(*) AS total FROM archive_entries"
        rows = self._fetch_all(query)
        if rows:
            return int(rows[0][0])
        return 0

    # ------------------------------------------------------------------
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_file)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    # ------------------------------------------------------------------
    def _fetch_all(
        self,
        query: str,
        parameters: Optional[Iterable[object]] = None,
        *,
        limit: Optional[int] = None,
    ) -> List[sqlite3.Row]:
        params_tuple: tuple = tuple(parameters or ())
        sql = query + (" LIMIT ?" if limit is not None else "")
        full_params = params_tuple + ((limit,) if limit is not None else ())
        with self._connect() as connection:
            cursor = connection.execute(sql, full_params)
            rows = cursor.fetchall()
        return rows

    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, str]:
        return {
            "title": str(row["title"]),
            "description": str(row["description"]),
            "created_at": str(row["created_at"]),
        }


__all__ = ["DatabaseModule"]
