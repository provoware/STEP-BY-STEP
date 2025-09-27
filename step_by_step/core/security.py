"""Data security helpers for STEP-BY-STEP."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .logging_manager import get_logger


DEFAULT_MANIFEST_PATH = Path("data/security_manifest.json")
DEFAULT_BACKUP_DIR = Path("data/backups")

# Files that should be protected by checksum validation.
SENSITIVE_FILES: Iterable[Path] = (
    Path("data/settings.json"),
    Path("data/todo_items.json"),
    Path("data/playlists.json"),
    Path("data/archive.json"),
    Path("data/archive.db"),
    Path("data/release_checklist.json"),
    Path("data/selftest_report.json"),
    Path("data/color_audit.json"),
    Path("data/usage_stats.json"),
    Path("data/persistent_notes.txt"),
    Path("Fortschritt.txt"),
    Path("todo.txt"),
)


@dataclass
class SecuritySummary:
    """Collect the outcome of a manifest validation run."""

    status: str = "unknown"
    verified: int = 0
    issues: List[str] = field(default_factory=list)
    backups: List[str] = field(default_factory=list)
    size_alerts: List[str] = field(default_factory=list)
    pruned_backups: List[str] = field(default_factory=list)
    restore_points: List[Dict[str, object]] = field(default_factory=list)
    restore_issues: List[str] = field(default_factory=list)
    updated_manifest: bool = False
    timestamp: str = dt.datetime.now().isoformat()

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "verified": self.verified,
            "issues": list(self.issues),
            "backups": list(self.backups),
            "size_alerts": list(self.size_alerts),
            "pruned_backups": list(self.pruned_backups),
            "restore_points": [dict(item) for item in self.restore_points],
            "restore_issues": list(self.restore_issues),
            "updated_manifest": self.updated_manifest,
            "timestamp": self.timestamp,
        }


class SecurityManager:
    """Manage checksum manifest validation and backups."""

    def __init__(
        self,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
        backup_dir: Path = DEFAULT_BACKUP_DIR,
    ) -> None:
        self.manifest_path = manifest_path
        self.backup_dir = backup_dir
        self.logger = get_logger("core.security")

    # ------------------------------------------------------------------
    def ensure_manifest(self) -> Dict[str, object]:
        """Ensure that a checksum manifest exists and is well-formed."""

        manifest = self._load_manifest()
        if manifest:
            return manifest
        manifest = self._initial_manifest()
        self._write_manifest(manifest)
        self.logger.info("Sicherheitsmanifest neu angelegt: %s", self.manifest_path)
        return manifest

    # ------------------------------------------------------------------
    def verify_files(self) -> SecuritySummary:
        """Verify protected files against the checksum manifest."""

        manifest = self.ensure_manifest()
        files_section = manifest.setdefault("files", {})
        summary = SecuritySummary(status="ok")

        for path in SENSITIVE_FILES:
            rel_path = str(path)
            entry = files_section.setdefault(rel_path, {})
            checksum = self._hash_file(path)
            size = self._file_size(path)
            summary.verified += 1

            expected = entry.get("sha256")
            if checksum == "missing":
                summary.issues.append(f"{rel_path}: Datei fehlt – bitte prüfen")
                summary.status = "attention"
                summary.updated_manifest = True
                entry["sha256"] = "missing"
                entry["size"] = None
                entry["last_checked"] = summary.timestamp
                continue
            if expected is None:
                entry["sha256"] = checksum
                entry["size"] = size
                summary.updated_manifest = True
                self.logger.info("Manifest ergänzt: %s", rel_path)
            elif checksum != expected:
                backup_file = self._create_backup(path)
                message = (
                    f"Checksum-Abweichung erkannt – Datei gesichert unter {backup_file}"
                )
                summary.issues.append(f"{rel_path}: {message}")
                summary.backups.append(str(backup_file))
                pruned = self._prune_old_backups(path.name)
                if pruned:
                    summary.pruned_backups.extend(str(item) for item in pruned)
                entry["sha256"] = checksum
                entry["size"] = size
                summary.updated_manifest = True
                summary.status = "attention"
                self.logger.warning("%s – neue Prüfsumme gespeichert", message)
            else:
                previous_size = entry.get("size")
                if previous_size is not None and size is not None and previous_size != size:
                    alert = (
                        f"{rel_path}: Dateigröße von {previous_size} auf {size} Byte geändert"
                    )
                    summary.issues.append(alert)
                    summary.size_alerts.append(alert)
                    summary.status = "attention"
                entry["size"] = size

            entry["last_checked"] = summary.timestamp

        if summary.updated_manifest:
            self._write_manifest(manifest)
            self.logger.info("Sicherheitsmanifest aktualisiert.")

        summary.restore_points = self._collect_restore_points(files_section)
        summary.restore_issues.extend(
            entry["message"]
            for entry in summary.restore_points
            if entry.get("status") != "ok" and entry.get("message")
        )

        if summary.issues:
            summary.status = "attention"
        if summary.restore_issues:
            summary.status = "attention"
        elif summary.status != "attention":
            summary.status = "ok"

        return summary

    # ------------------------------------------------------------------
    def _initial_manifest(self) -> Dict[str, object]:
        payload: Dict[str, Dict[str, object]] = {"files": {}}
        timestamp = dt.datetime.now().isoformat()
        for path in SENSITIVE_FILES:
            payload["files"][str(path)] = {
                "sha256": self._hash_file(path),
                "size": self._file_size(path),
                "last_checked": timestamp,
            }
        payload["created_at"] = timestamp
        payload["updated_at"] = timestamp
        return payload

    def _load_manifest(self) -> Dict[str, object]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.logger.error("Sicherheitsmanifest konnte nicht gelesen werden – wird neu erstellt")
            return {}

    def _write_manifest(self, manifest: Dict[str, object]) -> None:
        manifest["updated_at"] = dt.datetime.now().isoformat()
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    def _hash_file(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        if not path.exists():
            self.logger.warning("Datei für Sicherheitsprüfung fehlt: %s", path)
            return "missing"
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _file_size(self, path: Path) -> Optional[int]:
        try:
            return path.stat().st_size
        except FileNotFoundError:
            return None

    def _prune_old_backups(self, original_name: str, keep: int = 5) -> List[Path]:
        if not self.backup_dir.exists():
            return []
        candidates = sorted(
            self.backup_dir.glob(f"{original_name}.*.bak"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        removed: List[Path] = []
        for obsolete in candidates[keep:]:
            try:
                obsolete.unlink()
                removed.append(obsolete)
            except OSError:
                self.logger.warning("Backup konnte nicht gelöscht werden: %s", obsolete)
        return removed

    def _create_backup(self, path: Path) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"{path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        if path.exists():
            shutil.copy2(path, backup_path)
        return backup_path

    def _collect_restore_points(self, files_section: Dict[str, Dict[str, object]]) -> List[Dict[str, object]]:
        """Evaluate whether recent backups can restore protected files."""

        restore_points: List[Dict[str, object]] = []
        for rel_path, entry in files_section.items():
            name = Path(rel_path).name
            latest = self._latest_backup(name)
            checksum = entry.get("sha256")
            if not latest:
                restore_points.append(
                    {
                        "file": rel_path,
                        "status": "missing",
                        "message": "Kein Backup gefunden",
                    }
                )
                continue
            if checksum in (None, "missing"):
                restore_points.append(
                    {
                        "file": rel_path,
                        "status": "unknown",
                        "backup": str(latest),
                        "message": "Manifest enthält keine Prüfsumme",
                    }
                )
                continue
            backup_hash = self._hash_file(latest)
            if backup_hash == checksum:
                restore_points.append(
                    {
                        "file": rel_path,
                        "status": "ok",
                        "backup": str(latest),
                    }
                )
            else:
                message = (
                    f"{rel_path}: Backup stimmt nicht mit der aktuellen Prüfsumme überein"
                    f" ({latest.name})"
                )
                restore_points.append(
                    {
                        "file": rel_path,
                        "status": "mismatch",
                        "backup": str(latest),
                        "message": message,
                    }
                )
        return restore_points

    def _latest_backup(self, original_name: str) -> Optional[Path]:
        if not self.backup_dir.exists():
            return None
        candidates = list(self.backup_dir.glob(f"{original_name}.*.bak"))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item.stat().st_mtime)


__all__ = ["SecurityManager", "SecuritySummary"]

