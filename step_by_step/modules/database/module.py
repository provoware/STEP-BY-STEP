"""Database helper module for managing archive entries."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from ...core.file_utils import atomic_write_json
from ...core.logging_manager import get_logger
from ...core.resources import ARCHIVE_DB_PATH
from ...core.validators import ensure_unique

ARCHIVE_DB = ARCHIVE_DB_PATH
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
    def get_statistics(self, limit: int = 5) -> Dict[str, object]:
        """Return summary information for dashboard insights."""

        stats: Dict[str, object] = {
            "total_entries": 0,
            "latest_entries": [],
            "top_initials": [],
            "last_added": None,
        }

        try:
            total = self._count_entries()
            stats["total_entries"] = total
            if total == 0:
                return stats

            latest_rows = self._fetch_all(
                (
                    "SELECT title, created_at FROM archive_entries "
                    "ORDER BY datetime(created_at) DESC"
                ),
                limit=limit,
            )
            latest_entries = [
                {
                    "title": str(row["title"]),
                    "created_at": str(row["created_at"]),
                }
                for row in latest_rows
            ]
            stats["latest_entries"] = latest_entries
            if latest_entries:
                stats["last_added"] = latest_entries[0]

            initials_rows = self._fetch_all(
                (
                    "SELECT UPPER(SUBSTR(title, 1, 1)) AS initial, COUNT(*) AS total "
                    "FROM archive_entries "
                    "GROUP BY initial ORDER BY total DESC, initial ASC"
                ),
                limit=limit,
            )
            stats["top_initials"] = [
                {
                    "initial": str(row["initial"] or "?"),
                    "count": int(row["total"]),
                }
                for row in initials_rows
            ]
        except sqlite3.DatabaseError as exc:
            self.logger.error("Fehler bei der Statistikabfrage: %s", exc)

        return stats

    # ------------------------------------------------------------------
    def add_entry(self, title: str, description: str) -> bool:
        """Insert a new entry; return False if the title already exists."""

        if not ensure_unique([entry.get("title", "") for entry in self.list_entries()] + [title]):
            return False

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
        """Filter entries by the first letter (Anfangsbuchstabe)."""

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
        if not atomic_write_json(target_path, payload, logger=self.logger):
            self.logger.error("Archiv-Export (JSON) fehlgeschlagen: %s", target_path)
        return target_path

    # ------------------------------------------------------------------
    def _initialise_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                (
                    "CREATE TABLE IF NOT EXISTS archive_entries ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "title TEXT UNIQUE NOT NULL,"
                    "description TEXT NOT NULL,"
                    "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
                    ")"
                )
            )
            connection.commit()

        if LEGACY_ARCHIVE_JSON.exists():
            self._migrate_legacy_json()

    # ------------------------------------------------------------------
    def _migrate_legacy_json(self) -> None:
        try:
            payload = json.loads(LEGACY_ARCHIVE_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.logger.warning("Legacy-Archiv konnte nicht gelesen werden: %s", LEGACY_ARCHIVE_JSON)
            return

        entries = payload.get("entries", [])
        if not entries:
            return

        imported = 0
        for entry in entries:
            title = str(entry.get("title", "")).strip()
            description = str(entry.get("description", "")).strip()
            if not title:
                continue
            if not self.add_entry(title, description):
                continue
            imported += 1

        if imported:
            self.logger.info("%s Einträge aus dem Legacy-Archiv übernommen.", imported)

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
        self, query: str, params: Iterable[object] = (), limit: Optional[int] = None
    ) -> List[sqlite3.Row]:
        with self._connect() as connection:
            cursor = connection.execute(query, tuple(params))
            if limit is not None:
                rows = cursor.fetchmany(limit)
            else:
                rows = cursor.fetchall()
        return list(rows)

    # ------------------------------------------------------------------
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, str]:
        return {
            "title": str(row["title"]),
            "description": str(row["description"]),
            "created_at": str(row["created_at"]),
        }

    # ------------------------------------------------------------------
    def _count_entries(self) -> int:
        with self._connect() as connection:
            cursor = connection.execute("SELECT COUNT(*) FROM archive_entries")
            value = cursor.fetchone()
            return int(value[0]) if value else 0


__all__ = ["DatabaseModule"]

