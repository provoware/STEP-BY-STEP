"""Graphical user interface (grafische Oberfläche) for STEP-BY-STEP."""

from __future__ import annotations

import datetime as dt
import json
import logging
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

try:
    from ttkbootstrap import Style  # type: ignore
except Exception:  # pragma: no cover - ttkbootstrap optional
    Style = None  # type: ignore

from step_by_step.core.config_manager import UserPreferences
from step_by_step.core.logging_manager import get_logger
from step_by_step.modules.audio.module import AudioPlayer, PlaylistManager

from .info_panels import (
    build_legend_panel,
    build_mockup_panel,
    build_quicklinks_panel,
    build_structure_panel,
)

NOTE_FILE = Path("data/persistent_notes.txt")
STATS_FILE = Path("data/usage_stats.json")

STRUCTURE_SCHEMA: Dict[str, Dict[str, Dict[str, Dict]]] = {
    "STEP-BY-STEP": {
        "start_tool.py": {},
        "requirements.txt": {},
        "data/": {
            "persistent_notes.txt": {},
            "playlists.json": {},
            "todo_items.json": {},
            "usage_stats.json": {},
        },
        "docs/": {"coding_guidelines.md": {}},
        "step_by_step/": {
            "__init__.py": {},
            "core/": {
                "__init__.py": {},
                "config_manager.py": {},
                "startup.py": {},
                "validators.py": {},
            },
            "modules/": {
                "audio/": {"module.py": {}},
                "database/": {"module.py": {}},
                "todo/": {"module.py": {}},
            },
            "ui/": {
                "__init__.py": {},
                "info_panels.py": {},
                "main_window.py": {},
            },
        },
        "todo.txt": {},
        "Fortschritt.txt": {},
        "README.md": {},
    }
}


class MainWindow(tk.Tk):
    """Main application window with accessible layout."""

    def __init__(self, preferences: UserPreferences, logger: Optional[logging.Logger] = None) -> None:
        super().__init__()
        self.preferences = preferences
        self.logger = logger or get_logger("ui.main_window")
        self.playlist_manager = PlaylistManager()
        self.audio_player = AudioPlayer(logger=self.logger, on_error=self._on_audio_error)
        self.audio_player.set_volume(getattr(self.preferences, "audio_volume", 0.8))
        self.playlist_entries: List[Dict[str, str]] = []
        self.color_mode_var = tk.StringVar(
            value=getattr(self.preferences, "color_mode", self.preferences.contrast_theme)
        )
        self.preferences.color_mode = self.color_mode_var.get()
        self.title("STEP-BY-STEP Dashboard")
        self.geometry("1200x800")
        self.minsize(900, 600)
        self.style = self._init_style()
        self._configure_theme()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._notes_cache = ""
        self._create_header()
        self._create_sidebars()
        self._create_main_grid()
        self._load_notes()
        self._load_stats()
        self.after(1000, self._update_clock)
        self._schedule_autosave()
        self.bind_all("<Control-s>", self._handle_ctrl_s)

    # Header -----------------------------------------------------------------
    def _create_header(self) -> None:
        header = ttk.Frame(self, padding=10, style="HighContrast.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)

        self.clock_var = tk.StringVar(value="--:--:--")
        clock_label = ttk.Label(
            header,
            textvariable=self.clock_var,
            font=("Arial", 16, "bold"),
            justify="left",
            style="HighContrast.TLabel",
        )
        clock_label.grid(row=0, column=0, sticky="w")

        self.stats_var = tk.StringVar(value="Bereit für Aktionen")
        stats_label = ttk.Label(
            header,
            textvariable=self.stats_var,
            font=("Arial", 12),
            justify="center",
            style="HighContrast.TLabel",
        )
        stats_label.grid(row=0, column=1, sticky="n")

        self.path_var = tk.StringVar(value=str(Path.cwd()))
        path_label = ttk.Label(
            header,
            textvariable=self.path_var,
            font=("Arial", 10),
            style="HighContrast.TLabel",
        )
        path_label.grid(row=0, column=2, sticky="e")

        ttk.Label(
            header,
            text="Farbschema wählen:",
            style="HighContrast.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.mode_selector = ttk.Combobox(
            header,
            textvariable=self.color_mode_var,
            values=("high_contrast", "light", "dark"),
            state="readonly",
        )
        self.mode_selector.grid(row=1, column=1, sticky="ew", pady=(8, 0))
        self.mode_selector.bind("<<ComboboxSelected>>", self._on_color_mode_change)

        ttk.Label(
            header,
            text=(
                "Hinweis (Screenreader): Mit Tab durch die Bereiche wechseln. "
                "Die Pfeiltasten steuern Listen."
            ),
            wraplength=320,
            style="HighContrast.TLabel",
        ).grid(row=1, column=2, sticky="e", pady=(8, 0))

    # Sidebars ---------------------------------------------------------------
    def _create_sidebars(self) -> None:
        self.sidebar_container = ttk.Frame(self, style="HighContrast.TFrame")
        self.sidebar_container.grid(row=1, column=0, sticky="nsew")
        self.sidebar_container.columnconfigure(1, weight=1)
        self.sidebar_container.rowconfigure(0, weight=1)

        self.left_sidebar = self._build_sidebar(self.sidebar_container, "Links", 0)
        self.right_sidebar = self._build_sidebar(self.sidebar_container, "Rechts", 2)

        toggle_frame = ttk.Frame(self.sidebar_container, style="HighContrast.TFrame")
        toggle_frame.grid(row=0, column=1, sticky="n")
        ttk.Button(
            toggle_frame,
            text="Links ein/aus",
            command=self._toggle_left,
            style="HighContrast.TButton",
        ).grid(
            row=0, column=0, pady=5
        )
        ttk.Button(
            toggle_frame,
            text="Rechts ein/aus",
            command=self._toggle_right,
            style="HighContrast.TButton",
        ).grid(
            row=1, column=0, pady=5
        )

        self.main_container = ttk.Frame(self.sidebar_container, style="HighContrast.TFrame")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.columnconfigure(tuple(range(3)), weight=1)
        self.main_container.rowconfigure(tuple(range(3)), weight=1)

    def _build_sidebar(self, parent: ttk.Frame, title: str, column: int) -> ttk.Frame:
        sidebar = ttk.Frame(parent, width=200, padding=10, style="HighContrast.TFrame")
        sidebar.grid(row=0, column=column, sticky="ns")
        sidebar.grid_propagate(False)
        ttk.Label(
            sidebar,
            text=title,
            font=("Arial", 12, "bold"),
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            sidebar,
            text=(
                "Hier finden Sie Hilfetexte (Erklärungen) und Tipps. "
                "Nutzen Sie die Buttons für schnelle Aktionen."
            ),
            wraplength=180,
            style="HighContrast.TLabel",
        ).pack(anchor="w", pady=5)
        ttk.Label(
            sidebar,
            text="Tastatur: Tab wählt Buttons, Leertaste führt die Aktion aus.",
            wraplength=180,
            style="HighContrast.TLabel",
        ).pack(anchor="w", pady=(0, 5))
        ttk.Button(
            sidebar,
            text="Notizen speichern",
            command=self._save_notes,
            style="HighContrast.TButton",
        ).pack(
            fill="x", pady=5
        )
        ttk.Button(
            sidebar,
            text="Statistik aktualisieren",
            command=self._save_stats,
            style="HighContrast.TButton",
        ).pack(
            fill="x", pady=5
        )
        return sidebar

    def _toggle_left(self) -> None:
        self._toggle_sidebar(self.left_sidebar)

    def _toggle_right(self) -> None:
        self._toggle_sidebar(self.right_sidebar)

    def _toggle_sidebar(self, sidebar: ttk.Frame) -> None:
        if sidebar.winfo_manager():
            sidebar.grid_remove()
        else:
            sidebar.grid()

    # Main grid --------------------------------------------------------------
    def _create_main_grid(self) -> None:
        self.grid_cells: List[ttk.Frame] = []
        for row in range(3):
            for column in range(3):
                cell_index = row * 3 + column
                cell = ttk.LabelFrame(
                    self.main_container,
                    text=f"Bereich {cell_index + 1}",
                    padding=10,
                    labelanchor="n",
                    style="HighContrast.TLabelframe",
                )
                cell.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
                self.main_container.columnconfigure(column, weight=1)
                self.main_container.rowconfigure(row, weight=1)
                self.grid_cells.append(cell)

        titles = {
            0: "Notizblock",
            1: "ToDo Vorschau",
            2: "Playlist",
            3: "Info-Center",
        }
        for index, title in titles.items():
            self.grid_cells[index].configure(text=title)

        self._build_notepad(self.grid_cells[0])
        self._build_todo_preview(self.grid_cells[1])
        self._build_playlist_preview(self.grid_cells[2])
        self._build_info_center(self.grid_cells[3])
        self._refresh_playlist()

    def _build_notepad(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="Notizen",
            font=("Arial", 12, "bold"),
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        self.note_text = tk.Text(
            parent,
            wrap="word",
            height=10,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            insertbackground=self.colors["accent"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            takefocus=True,
        )
        self.note_text.pack(fill="both", expand=True)
        self.note_text.bind("<FocusOut>", lambda _event: self._auto_save())
        ttk.Label(
            parent,
            text="Tipp: Strg+S speichert zusätzlich manuell.",
            style="HighContrast.TLabel",
        ).pack(anchor="w", pady=(4, 0))

    def _build_todo_preview(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="ToDo Vorschau",
            font=("Arial", 12, "bold"),
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        self.todo_list = tk.Listbox(
            parent,
            height=6,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            activestyle="dotbox",
            exportselection=False,
        )
        self.todo_list.pack(fill="both", expand=True)
        for item in self._load_todo_items():
            self.todo_list.insert(tk.END, item)
        ttk.Label(
            parent,
            text="Hinweis: Enter markiert Aufgaben als erledigt (geplant).",
            wraplength=260,
            style="HighContrast.TLabel",
        ).pack(anchor="w", pady=(4, 0))

    def _build_playlist_preview(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="Playlist",
            font=("Arial", 12, "bold"),
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            parent,
            text="Screenreader-Tipp: Mit Pfeiltasten Titel wählen, Enter startet Wiedergabe.",
            wraplength=260,
            style="HighContrast.TLabel",
        ).pack(anchor="w", pady=(2, 4))
        self.playlist_list = tk.Listbox(
            parent,
            height=6,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            activestyle="dotbox",
            exportselection=False,
        )
        self.playlist_list.pack(fill="both", expand=True)
        self.playlist_list.bind("<Double-Button-1>", lambda _event: self._play_selected_track())
        self.playlist_list.bind("<Return>", lambda _event: self._play_selected_track())

        controls = ttk.Frame(parent, style="HighContrast.TFrame")
        controls.pack(fill="x", pady=(6, 0))
        self.play_button = ttk.Button(
            controls,
            text="Abspielen",
            command=self._play_selected_track,
            style="HighContrast.TButton",
        )
        self.play_button.pack(side="left", padx=(0, 8))
        self.stop_button = ttk.Button(
            controls,
            text="Stopp",
            command=self._stop_audio,
            style="HighContrast.TButton",
        )
        self.stop_button.pack(side="left")

        volume_frame = ttk.Frame(parent, style="HighContrast.TFrame")
        volume_frame.pack(fill="x", pady=(6, 0))
        ttk.Label(volume_frame, text="Lautstärke", style="HighContrast.TLabel").pack(side="left")
        self.volume_var = tk.DoubleVar(value=getattr(self.preferences, "audio_volume", 0.8) * 100)
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            command=self._on_volume_change,
        )
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=8)
        self.volume_label = ttk.Label(
            volume_frame,
            text=f"{int(self.volume_var.get())}%",
            style="HighContrast.TLabel",
        )
        self.volume_label.pack(side="left")

        backend_hint = "Audiowiedergabe bereit" if self.audio_player.backend_available else "Audiowiedergabe benötigt Zusatzmodul"
        self.audio_status = ttk.Label(
            parent,
            text=backend_hint,
            style="HighContrast.TLabel",
        )
        self.audio_status.pack(anchor="w", pady=(6, 0))
        if not self.audio_player.backend_available:
            self.play_button.state(["disabled"])

    def _build_info_center(self, parent: ttk.LabelFrame) -> None:
        notebook = ttk.Notebook(parent, style="HighContrast.TNotebook")
        notebook.pack(fill="both", expand=True)

        legend_frame = ttk.Frame(notebook, padding=10, style="HighContrast.TFrame")
        notebook.add(legend_frame, text="Legende")
        build_legend_panel(legend_frame, self.colors)

        mockup_frame = ttk.Frame(notebook, padding=10, style="HighContrast.TFrame")
        notebook.add(mockup_frame, text="Mockup")
        build_mockup_panel(mockup_frame, self.colors)

        structure_frame = ttk.Frame(notebook, padding=10, style="HighContrast.TFrame")
        notebook.add(structure_frame, text="Struktur")
        build_structure_panel(structure_frame, STRUCTURE_SCHEMA, self.colors)

        quicklinks_frame = ttk.Frame(notebook, padding=10, style="HighContrast.TFrame")
        notebook.add(quicklinks_frame, text="Schnelllinks")
        quick_links = [
            ("Aufgaben öffnen", "todo.txt im Standardprogramm anzeigen", lambda: self._open_path(Path("todo.txt"))),
            (
                "Einstellungen öffnen",
                "settings.json zur Anpassung anzeigen",
                lambda: self._open_path(Path("data/settings.json")),
            ),
            (
                "Selbsttest starten",
                "Startet das Tool im Prüfmodus (ohne Fenster)",
                self._run_headless_selftest,
            ),
        ]
        build_quicklinks_panel(quicklinks_frame, quick_links, self.colors)

    def _refresh_playlist(self) -> None:
        self.playlist_entries = self._load_tracks()
        self.playlist_list.delete(0, tk.END)
        for track in self.playlist_entries:
            self.playlist_list.insert(tk.END, track.get("title", "Unbenannt"))

    def _play_selected_track(self) -> None:
        if not self.audio_player.backend_available:
            messagebox.showwarning(
                "Audiowiedergabe",
                "Bitte das Zusatzmodul 'simpleaudio' installieren, um Audio abzuspielen.",
            )
            return
        if not self.playlist_list.curselection():
            messagebox.showinfo("Audiowiedergabe", "Bitte zuerst einen Titel auswählen.")
            return
        index = self.playlist_list.curselection()[0]
        track = self.playlist_entries[index]
        file_path = Path(track.get("path", ""))
        if self.audio_player.play(file_path):
            self.stats_var.set(f"Wiedergabe gestartet: {track.get('title', 'Unbenannt')}")

    def _stop_audio(self) -> None:
        self.audio_player.stop()
        self.stats_var.set("Audiowiedergabe gestoppt")

    def _on_volume_change(self, value: str) -> None:
        try:
            numeric = float(value)
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            return
        volume = max(0.0, min(1.0, numeric / 100))
        self.audio_player.set_volume(volume)
        self.preferences.audio_volume = volume
        self.volume_label.configure(text=f"{int(numeric)}%")

    def _on_audio_error(self, message: str) -> None:
        messagebox.showerror("Audiowiedergabe", message)
        self.stats_var.set("Audiowiedergabe fehlgeschlagen")

    def _handle_ctrl_s(self, _event: tk.Event) -> str:
        self._save_notes()
        return "break"

    # Data helpers -----------------------------------------------------------
    def _update_clock(self) -> None:
        now = dt.datetime.now()
        self.clock_var.set(now.strftime("%d.%m.%Y %H:%M:%S"))
        self.after(1000, self._update_clock)

    def _load_notes(self) -> None:
        NOTE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if NOTE_FILE.exists():
            self.note_text.insert("1.0", NOTE_FILE.read_text(encoding="utf-8"))

    def _save_notes(self) -> None:
        NOTE_FILE.parent.mkdir(parents=True, exist_ok=True)
        NOTE_FILE.write_text(self.note_text.get("1.0", tk.END).strip(), encoding="utf-8")
        self.stats_var.set("Notizen gespeichert")
        self.logger.info("Notizen gespeichert (%s)", NOTE_FILE)

    def _auto_save(self) -> None:
        current = self.note_text.get("1.0", tk.END)
        if current != self._notes_cache:
            self._notes_cache = current
            self._save_notes()
            self.logger.debug("Autospeichern ausgelöst")

    def _load_todo_items(self) -> List[str]:
        data = self._load_json(Path("data/todo_items.json"))
        items = sorted(
            data.get("items", []),
            key=lambda entry: entry.get("due_date", ""),
        )
        formatted: List[str] = []
        for entry in items:
            title = entry.get("title", "")
            due = entry.get("due_date", "")
            done = entry.get("done", False)
            status = "✔" if done else "•"
            formatted.append(f"{status} {title} (bis {due})")
        return formatted

    def _load_tracks(self) -> List[Dict[str, str]]:
        return self.playlist_manager.load_tracks()

    def _load_json(self, file_path: Path) -> Dict[str, List[Dict[str, str]]]:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            return {}
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            messagebox.showwarning(
                "Fehlerhafte Datei",
                "Die gespeicherten Daten waren beschädigt (korrupt). Es wurde eine leere Liste geladen.",
            )
            self.logger.warning("Beschädigte Datei beim Laden repariert: %s", file_path)
            return {}

    def _load_stats(self) -> None:
        data = self._load_json(STATS_FILE)
        counter = data.get("session_count", 0) + 1
        data["session_count"] = counter
        self.stats_var.set(f"Sitzungen: {counter}")
        STATS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.logger.info("Statistik aktualisiert: Sitzungen=%s", counter)

    def _save_stats(self) -> None:
        data = self._load_json(STATS_FILE)
        data["manual_update"] = dt.datetime.now().isoformat()
        STATS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.stats_var.set("Statistik gespeichert")
        self.logger.info("Statistik manuell gespeichert.")

    def _open_path(self, target: Path) -> None:
        try:
            target_path = target.resolve()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.suffix and not target_path.exists():
                target_path.touch()
            webbrowser.open(target_path.as_uri())
            self.stats_var.set(f"Geöffnet: {target_path.name}")
            self.logger.info("Schnelllink geöffnet: %s", target_path)
        except Exception as exc:  # pragma: no cover - user environment dependent
            self.logger.error("Pfad konnte nicht geöffnet werden: %s", target, exc_info=exc)
            messagebox.showerror("Öffnen fehlgeschlagen", f"{target}: {exc}")

    def _run_headless_selftest(self) -> None:
        command = [sys.executable, "start_tool.py", "--headless"]
        try:
            subprocess.Popen(command)
            self.stats_var.set("Selbsttest gestartet (läuft im Hintergrund)")
            self.logger.info("Selbsttest via Schnelllink gestartet: %s", command)
        except Exception as exc:  # pragma: no cover - system dependent
            self.logger.error("Selbsttest konnte nicht gestartet werden", exc_info=exc)
            messagebox.showerror("Selbsttest", f"Start fehlgeschlagen: {exc}")

    # Theme helpers ---------------------------------------------------------
    def _init_style(self):
        if Style is not None:
            return Style("superhero")
        style = ttk.Style(self)
        style.theme_use("clam")
        return style

    def _configure_theme(self) -> None:
        self.colors = self._select_colors()
        self.configure(background=self.colors["background"])

        style = self.style
        style.configure("TFrame", background=self.colors["background"])
        style.configure("TLabel", background=self.colors["background"], foreground=self.colors["on_background"])
        style.configure(
            "Treeview",
            background=self.colors["surface"],
            fieldbackground=self.colors["surface"],
            foreground=self.colors["on_surface"],
        )
        style.configure("TNotebook", background=self.colors["background"], foreground=self.colors["on_background"])
        style.configure("TNotebook.Tab", background=self.colors["surface"], foreground=self.colors["on_surface"])
        style.configure("HighContrast.TFrame", background=self.colors["background"])
        style.configure(
            "HighContrast.TLabel",
            background=self.colors["background"],
            foreground=self.colors["on_background"],
        )
        style.configure(
            "HighContrast.TButton",
            background=self.colors["accent"],
            foreground=self.colors["surface"],
        )
        style.map(
            "HighContrast.TButton",
            background=[("active", self.colors["accent_hover"])],
            foreground=[("active", self.colors["surface"])],
        )
        style.configure(
            "HighContrast.TLabelframe",
            background=self.colors["background"],
            foreground=self.colors["accent"],
        )
        style.configure(
            "HighContrast.TNotebook",
            background=self.colors["background"],
            foreground=self.colors["on_background"],
        )

    def _select_colors(self) -> Dict[str, str]:
        mode = getattr(self.preferences, "color_mode", None) or self.preferences.contrast_theme
        if mode == "high_contrast":
            return {
                "background": "#101820",
                "on_background": "#F2F2F2",
                "surface": "#1F2833",
                "on_surface": "#F2F2F2",
                "accent": "#FEE715",
                "accent_hover": "#FFC600",
            }
        if mode == "dark":
            return {
                "background": "#1E1E2E",
                "on_background": "#E0DEF4",
                "surface": "#2E2E3E",
                "on_surface": "#E0DEF4",
                "accent": "#89B4FA",
                "accent_hover": "#74A0F1",
            }
        return {
            "background": "#f2f2f2",
            "on_background": "#0d0d0d",
            "surface": "#ffffff",
            "on_surface": "#0d0d0d",
            "accent": "#0d6efd",
            "accent_hover": "#0b5ed7",
        }

    def _schedule_autosave(self) -> None:
        interval_minutes = max(1, int(self.preferences.autosave_interval_minutes))
        self.after(interval_minutes * 60 * 1000, self._autosave_tick)
        self.logger.debug("Autosave alle %s Minuten geplant", interval_minutes)

    def _autosave_tick(self) -> None:
        self._auto_save()
        self._schedule_autosave()

    def _on_color_mode_change(self, _event: Optional[tk.Event] = None) -> None:
        mode = self.color_mode_var.get()
        self.preferences.color_mode = mode
        self.preferences.contrast_theme = "high_contrast" if mode == "high_contrast" else mode
        self._configure_theme()
        self._refresh_theme_widgets()
        self.stats_var.set(f"Farbschema aktiviert: {mode}")

    def _refresh_theme_widgets(self) -> None:
        if hasattr(self, "note_text"):
            self.note_text.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                insertbackground=self.colors["accent"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
            )
        if hasattr(self, "todo_list"):
            self.todo_list.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
            )
        if hasattr(self, "playlist_list"):
            self.playlist_list.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
            )
        for child in self.grid_cells[3].winfo_children():
            child.destroy()
        self._build_info_center(self.grid_cells[3])



__all__ = ["MainWindow"]
