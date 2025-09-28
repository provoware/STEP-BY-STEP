"""Database helper module for managing archive entries via SQLite."""
"""Database helper module for managing archive entries."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from ...core.logging_manager import get_logger
from ...core.resources import ARCHIVE_DB_PATH

ARCHIVE_DB = ARCHIVE_DB_PATH
LEGACY_ARCHIVE_JSON = Path("data/archive.json")
from pathlib import Path
from typing import Dict, List, Optional

from ...core.validators import ensure_unique

ARCHIVE_FILE = Path("data/archive.json")
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

    """Simple record store with duplicate checking."""

    def __init__(self, storage_file: Path = ARCHIVE_FILE) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

    def list_entries(self) -> List[Dict[str, str]]:
        if not self.storage_file.exists():
            return []
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return sorted(
            data.get("entries", []),
            key=lambda entry: entry.get("title", "").casefold(),
        )

    def add_entry(self, title: str, description: str) -> bool:
        entries = self.list_entries()
        titles = [entry.get("title", "") for entry in entries] + [title]
        if not ensure_unique(titles):
            return False
        entries.append({"title": title, "description": description})
        self._write(entries)
        return True

    def search(self, term: str) -> List[Dict[str, str]]:
        term_cf = term.casefold()
        return [
            entry
            for entry in self.list_entries()
            if term_cf in entry.get("title", "").casefold()
            or term_cf in entry.get("description", "").casefold()
        ]

    def filter_by_prefix(self, prefix: str) -> List[Dict[str, str]]:
        prefix_cf = prefix.casefold()
        return [
            entry
            for entry in self.list_entries()
            if entry.get("title", "").casefold().startswith(prefix_cf)
        ]

    def remove(self, title: str) -> bool:
        entries = self.list_entries()
        filtered = [entry for entry in entries if entry.get("title") != title]
        if len(filtered) == len(entries):
            return False
        self._write(filtered)
        return True

    def get_entry(self, title: str) -> Optional[Dict[str, str]]:
        for entry in self.list_entries():
            if entry.get("title") == title:
                return entry
        return None

    def _write(self, entries: List[Dict[str, str]]) -> None:
        payload = {"entries": sorted(entries, key=lambda entry: entry.get("title", "").casefold())}
        self.storage_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def export_entries_to_csv(self, target: Optional[Path] = None) -> Path:
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

            writer = csv.DictWriter(handle, fieldnames=["title", "description"])
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                })
        return target_path

    def export_entries_to_json(self, target: Optional[Path] = None) -> Path:
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

        target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target_path


__all__ = ["DatabaseModule"]
