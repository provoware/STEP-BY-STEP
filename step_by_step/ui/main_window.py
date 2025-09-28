"""Graphical user interface (grafische Oberfläche) for STEP-BY-STEP."""

from __future__ import annotations

import datetime as dt
import json
import logging
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

from step_by_step.core import LogReader
from step_by_step.core.config_manager import UserPreferences
from step_by_step.core.file_utils import atomic_write_json, atomic_write_text
from step_by_step.core.logging_manager import get_logger
from step_by_step.core.themes import THEME_ORDER, get_theme_colors
from step_by_step.modules.audio.module import AudioFormatInspector, AudioPlayer, PlaylistManager
from step_by_step.modules.database.module import DatabaseModule
from step_by_step.modules.release.module import ReleaseChecklist
from step_by_step.modules.todo.module import TodoModule, TodoItem

from .info_panels import (
    build_legend_panel,
    build_font_tips_panel,
    build_contrast_panel,
    build_database_insights_panel,
    build_color_audit_panel,
    build_mockup_panel,
    build_release_panel,
    build_quicklinks_panel,
    build_structure_panel,
    build_palette_panel,
    build_security_panel,
    build_diagnostics_panel,
)
from .widgets import ScrollableFrame

NOTE_FILE = Path("data/persistent_notes.txt")
STATS_FILE = Path("data/usage_stats.json")
SELFTEST_FILE = Path("data/selftest_report.json")
DIAGNOSTICS_FILE = Path("data/diagnostics_report.json")

STRUCTURE_SCHEMA: Dict[str, Dict[str, Dict[str, Dict]]] = {
    "STEP-BY-STEP": {
        "start_tool.py": {},
        "requirements.txt": {},
        "data/": {
            "persistent_notes.txt": {},
            "playlists.json": {},
            "todo_items.json": {},
            "usage_stats.json": {},
            "selftest_report.json": {},
            "diagnostics_report.json": {},
            "release_checklist.json": {},
            "security_manifest.json": {},
            "color_audit.json": {},
            "archive.db": {},
            "converted_audio/": {},
            "backups/": {},
            "exports/": {
                "archive_export.csv": {},
                "archive_export.json": {},
            },
        },
        "docs/": {
            "coding_guidelines.md": {},
            "release_checklist.md": {},
        },
        "step_by_step/": {
            "__init__.py": {},
            "core/": {
                "__init__.py": {},
                "config_manager.py": {},
                "color_audit.py": {},
                "startup.py": {},
                "validators.py": {},
                "log_reader.py": {},
                "themes.py": {},
            },
            "modules/": {
                "audio/": {"module.py": {}},
                "database/": {"module.py": {}},
                "release/": {"module.py": {}},
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
        self.audio_inspector = AudioFormatInspector(logger=self.logger)
        self.audio_player = AudioPlayer(logger=self.logger, on_error=self._on_audio_error)
        self.audio_player.set_volume(getattr(self.preferences, "audio_volume", 0.8))
        self.playlist_entries: List[Dict[str, str]] = []
        self.todo_module = TodoModule()
        self.todo_entries: List[TodoItem] = []
        self.database_module = DatabaseModule()
        self.database_insights_data: Dict[str, object] = self.database_module.get_statistics()
        self.release_checklist = ReleaseChecklist()
        self.release_items = [item.to_dict() for item in self.release_checklist.load_items()]
        progress = self.release_checklist.progress()
        if progress.get("total"):
            self.release_progress_text = (
                f"Fortschritt: {progress['done']} von {progress['total']} Aufgaben erledigt"
            )
        else:
            self.release_progress_text = "Noch keine Checkliste gespeichert."
        self.log_reader = LogReader(Path("logs/startup.log"))
        self.session_count: int = 0
        default_mode = getattr(self.preferences, "color_mode", None) or self.preferences.contrast_theme
        if default_mode not in THEME_ORDER:
            default_mode = THEME_ORDER[0]
        self.available_color_modes = THEME_ORDER
        self.color_mode_var = tk.StringVar(value=default_mode)
        self.font_scale_var = tk.DoubleVar(
            value=float(getattr(self.preferences, "font_scale", self.preferences.font_scale))
        )
        self.font_scale_display_var = tk.StringVar(value="100 %")
        self.selftest_var = tk.StringVar(value="Selbsttest: noch keine Daten")
        self.log_search_var = tk.StringVar(value="")
        self.log_status_var = tk.StringVar(
            value="Letzte Meldungen anzeigen mit 'Neu laden'."
        )
        self.security_var = tk.StringVar(value="Datensicherheit: lädt...")
        self.security_summary_data: Dict[str, object] = {}
        self.color_audit_var = tk.StringVar(value="Farbaudit: lädt...")
        self.color_audit_data: Dict[str, object] = {}
        self.diagnostics_var = tk.StringVar(value="Diagnose: lädt...")
        self.diagnostics_data: Dict[str, object] = self._load_json(DIAGNOSTICS_FILE)
        self.preferences.color_mode = self.color_mode_var.get()
        self.preferences.contrast_theme = (
            "high_contrast" if self.color_mode_var.get() == "high_contrast" else self.color_mode_var.get()
        )
        self.title("STEP-BY-STEP Dashboard")
        self.geometry("1200x800")
        self.minsize(900, 600)
        self.style = self._init_style()
        self._configure_theme()
        self._configure_fonts()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._notes_cache = ""
        self._create_header()
        self._create_sidebars()
        self._create_main_grid()
        self._load_notes()
        self._load_stats()
        self._load_selftest_summary()
        self._apply_security_summary(self.security_summary_data or None)
        self._apply_color_audit(self.color_audit_data or None)
        if hasattr(self, "grid_cells") and len(self.grid_cells) > 3:
            for child in self.grid_cells[3].winfo_children():
                child.destroy()
            self._build_info_center(self.grid_cells[3])
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
        self.clock_label = ttk.Label(
            header,
            textvariable=self.clock_var,
            font=self.fonts["title"],
            justify="left",
            style="HighContrast.TLabel",
        )
        self.clock_label.grid(row=0, column=0, sticky="w")

        self.stats_overview = "Bereit für Aktionen"
        self.stats_var = tk.StringVar(value=self.stats_overview)
        self.stats_label = ttk.Label(
            header,
            textvariable=self.stats_var,
            font=self.fonts["body"],
            justify="center",
            style="HighContrast.TLabel",
        )
        self.stats_label.grid(row=0, column=1, sticky="n")

        self.path_var = tk.StringVar(value=str(Path.cwd()))
        self.path_label = ttk.Label(
            header,
            textvariable=self.path_var,
            font=self.fonts["small"],
            style="HighContrast.TLabel",
        )
        self.path_label.grid(row=0, column=2, sticky="e")

        self.selftest_label = ttk.Label(
            header,
            textvariable=self.selftest_var,
            font=self.fonts["body"],
            style="HighContrast.TLabel",
        )
        self.selftest_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.color_mode_label = ttk.Label(
            header,
            text="Farbschema wählen:",
            style="HighContrast.TLabel",
            font=self.fonts["body"],
        )
        self.color_mode_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.mode_selector = ttk.Combobox(
            header,
            textvariable=self.color_mode_var,
            values=self.available_color_modes,
            state="readonly",
            font=self.fonts["body"],
        )
        self.mode_selector.grid(row=2, column=1, sticky="ew", pady=(8, 0))
        self.mode_selector.bind("<<ComboboxSelected>>", self._on_color_mode_change)
        self._bind_focus_highlight(
            self.mode_selector,
            "Farbschema-Selector aktiv. Mit Pfeiltasten wechseln, Enter bestätigt.",
        )

        self.screenreader_hint_label = ttk.Label(
            header,
            text=(
                "Hinweis (Screenreader): Mit Tab durch die Bereiche wechseln. "
                "Die Pfeiltasten steuern Listen."
            ),
            wraplength=320,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        )
        self.screenreader_hint_label.grid(row=2, column=2, sticky="e", pady=(8, 0))

        self.security_label = ttk.Label(
            header,
            font=self.fonts["body"],
            style="HighContrast.TLabel",
            textvariable=self.security_var,
        )
        self.security_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.color_audit_label = ttk.Label(
            header,
            textvariable=self.color_audit_var,
            font=self.fonts["body"],
            style="HighContrast.TLabel",
        )
        self.color_audit_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 0))

        self.diagnostics_label = ttk.Label(
            header,
            textvariable=self.diagnostics_var,
            font=self.fonts["body"],
            style="HighContrast.TLabel",
        )
        self.diagnostics_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 0))

        self.font_scale_label = ttk.Label(
            header,
            text="Schriftgröße (Zoom):",
            style="HighContrast.TLabel",
            font=self.fonts["body"],
        )
        self.font_scale_label.grid(row=6, column=0, sticky="w", pady=(8, 0))

        self.font_scale_slider = ttk.Scale(
            header,
            from_=0.8,
            to=1.6,
            orient="horizontal",
            variable=self.font_scale_var,
            command=self._on_font_scale_slider,
            style="HighContrast.Horizontal.TScale",
        )
        self.font_scale_slider.grid(row=6, column=1, sticky="ew", padx=(0, 10), pady=(8, 0))
        self.font_scale_slider.configure(takefocus=True)
        self._bind_focus_highlight(
            self.font_scale_slider,
            "Schriftgrößenregler aktiv. Links verkleinert, rechts vergrößert den Text.",
        )

        self.font_scale_value_label = ttk.Label(
            header,
            textvariable=self.font_scale_display_var,
            style="HighContrast.TLabel",
            font=self.fonts["body"],
        )
        self.font_scale_value_label.grid(row=6, column=2, sticky="e", pady=(8, 0))

        self.font_scale_reset_button = ttk.Button(
            header,
            text="Standardgröße",
            command=self._reset_font_scale,
            style="HighContrast.TButton",
        )
        self.font_scale_reset_button.grid(row=7, column=2, sticky="e", pady=(4, 0))
        self._bind_focus_highlight(
            self.font_scale_reset_button,
            "Standardgröße wiederherstellen. Enter setzt 100 % Schriftgröße.",
        )

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
        left_toggle = ttk.Button(
            toggle_frame,
            text="Links ein/aus",
            command=self._toggle_left,
            style="HighContrast.TButton",
        )
        left_toggle.grid(row=0, column=0, pady=5)
        self._bind_focus_highlight(
            left_toggle,
            "Linke Seitenleiste umschalten. Enter klappt Hilfebereich links ein oder aus.",
        )
        right_toggle = ttk.Button(
            toggle_frame,
            text="Rechts ein/aus",
            command=self._toggle_right,
            style="HighContrast.TButton",
        )
        right_toggle.grid(row=1, column=0, pady=5)
        self._bind_focus_highlight(
            right_toggle,
            "Rechte Seitenleiste umschalten. Enter blendet zusätzliche Tipps ein oder aus.",
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
            font=self.fonts["heading"],
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
            font=self.fonts["body"],
        ).pack(anchor="w", pady=5)
        ttk.Label(
            sidebar,
            text="Tastatur: Tab wählt Buttons, Leertaste führt die Aktion aus.",
            wraplength=180,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        ).pack(anchor="w", pady=(0, 5))
        save_button = ttk.Button(
            sidebar,
            text="Notizen speichern",
            command=self._save_notes,
            style="HighContrast.TButton",
        )
        save_button.pack(fill="x", pady=5)
        self._bind_focus_highlight(
            save_button,
            "Knopf Notizen speichern aktiv. Enter speichert sofort alle Notizen.",
        )
        stats_button = ttk.Button(
            sidebar,
            text="Statistik aktualisieren",
            command=self._save_stats,
            style="HighContrast.TButton",
        )
        stats_button.pack(fill="x", pady=5)
        self._bind_focus_highlight(
            stats_button,
            "Knopf Statistik aktualisieren aktiv. Enter schreibt aktuelle Werte weg.",
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
            4: "Startprotokoll",
        }
        for index, title in titles.items():
            self.grid_cells[index].configure(text=title)

        self._build_notepad(self.grid_cells[0])
        self._build_todo_preview(self.grid_cells[1])
        self._build_playlist_preview(self.grid_cells[2])
        self._build_info_center(self.grid_cells[3])
        self._build_log_viewer(self.grid_cells[4])
        self._refresh_playlist()

    def _build_notepad(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="Notizen",
            font=self.fonts["heading"],
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        text_container = ttk.Frame(parent, style="HighContrast.TFrame")
        text_container.pack(fill="both", expand=True)
        self.note_text = tk.Text(
            text_container,
            wrap="word",
            height=10,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            insertbackground=self.colors["accent"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            takefocus=True,
            font=self.fonts["body"],
            highlightthickness=2,
            highlightcolor=self.colors["accent"],
            highlightbackground=self.colors["background"],
        )
        self.note_text.pack(side="left", fill="both", expand=True)
        note_scroll = ttk.Scrollbar(text_container, command=self.note_text.yview)
        note_scroll.pack(side="right", fill="y")
        self.note_text.configure(yscrollcommand=note_scroll.set)
        self.note_text.bind("<FocusOut>", lambda _event: self._auto_save())
        self._bind_focus_highlight(
            self.note_text,
            "Notizblock fokussiert. Tippen Sie direkt, speichern erfolgt automatisch.",
        )
        ttk.Label(
            parent,
            text="Tipp: Strg+S speichert zusätzlich manuell.",
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        ).pack(anchor="w", pady=(4, 0))

    def _build_todo_preview(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="ToDo Vorschau",
            font=self.fonts["heading"],
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        self.todo_summary_var = tk.StringVar(value="Keine Aufgaben geladen")
        ttk.Label(
            parent,
            textvariable=self.todo_summary_var,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        ).pack(anchor="w", pady=(0, 4))
        todo_frame = ttk.Frame(parent, style="HighContrast.TFrame")
        todo_frame.pack(fill="both", expand=True)
        self.todo_list = tk.Listbox(
            todo_frame,
            height=6,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            activestyle="dotbox",
            exportselection=False,
            font=self.fonts["body"],
            highlightthickness=2,
            highlightcolor=self.colors["accent"],
            highlightbackground=self.colors["background"],
        )
        self.todo_list.pack(side="left", fill="both", expand=True)
        todo_scroll = ttk.Scrollbar(todo_frame, command=self.todo_list.yview)
        todo_scroll.pack(side="right", fill="y")
        self.todo_list.configure(yscrollcommand=todo_scroll.set)
        self.todo_list.bind("<<ListboxSelect>>", self._on_todo_selected)
        self.todo_list.bind("<Return>", self._toggle_selected_todo)
        self.todo_list.bind("<space>", self._toggle_selected_todo)
        self.todo_list.bind("<Double-Button-1>", self._toggle_selected_todo)
        self._bind_focus_highlight(
            self.todo_list,
            "ToDo-Liste aktiv. Mit Pfeiltasten navigieren, Enter oder Leertaste schalten den Status um.",
        )
        controls = ttk.Frame(parent, style="HighContrast.TFrame")
        controls.pack(fill="x", pady=(6, 0))
        self.todo_toggle_button = ttk.Button(
            controls,
            text="Status wechseln",
            command=self._toggle_selected_todo,
            style="HighContrast.TButton",
        )
        self.todo_toggle_button.pack(side="left")
        self._bind_focus_highlight(
            self.todo_toggle_button,
            "Button: markiert die ausgewählte Aufgabe als erledigt oder offen.",
        )
        ttk.Button(
            controls,
            text="todo.txt öffnen",
            command=lambda: self._open_path(Path("todo.txt")),
            style="HighContrast.TButton",
        ).pack(side="left", padx=(8, 0))
        self.todo_status_var = tk.StringVar(
            value="Mit Enter, Leertaste oder Doppelklick den Status anpassen."
        )
        ttk.Label(
            parent,
            textvariable=self.todo_status_var,
            wraplength=260,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        ).pack(anchor="w", pady=(4, 0))
        self._refresh_todo_list()

    def _build_playlist_preview(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="Playlist",
            font=self.fonts["heading"],
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            parent,
            text="Screenreader-Tipp: Mit Pfeiltasten Titel wählen, Enter startet Wiedergabe.",
            wraplength=260,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        ).pack(anchor="w", pady=(2, 4))
        playlist_frame = ttk.Frame(parent, style="HighContrast.TFrame")
        playlist_frame.pack(fill="both", expand=True)
        self.playlist_list = tk.Listbox(
            playlist_frame,
            height=6,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            activestyle="dotbox",
            exportselection=False,
            font=self.fonts["body"],
            highlightthickness=2,
            highlightcolor=self.colors["accent"],
            highlightbackground=self.colors["background"],
        )
        self.playlist_list.pack(side="left", fill="both", expand=True)
        playlist_scroll = ttk.Scrollbar(playlist_frame, command=self.playlist_list.yview)
        playlist_scroll.pack(side="right", fill="y")
        self.playlist_list.configure(yscrollcommand=playlist_scroll.set)
        self._bind_focus_highlight(
            self.playlist_list,
            "Playlist aktiv. Pfeiltasten wählen Titel, Enter spielt den Titel.",
        )
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
        ttk.Label(
            volume_frame,
            text="Lautstärke",
            style="HighContrast.TLabel",
            font=self.fonts["body"],
        ).pack(side="left")
        self.volume_var = tk.DoubleVar(value=getattr(self.preferences, "audio_volume", 0.8) * 100)
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            command=self._on_volume_change,
            style="HighContrast.Horizontal.TScale",
        )
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=8)
        self.volume_slider.configure(takefocus=True)
        self._bind_focus_highlight(
            self.volume_slider,
            "Lautstärkeregler aktiv. Links leiser, rechts lauter.",
        )
        self.volume_label = ttk.Label(
            volume_frame,
            text=f"{int(self.volume_var.get())}%",
            style="HighContrast.TLabel",
            font=self.fonts["body"],
        )
        self.volume_label.pack(side="left")

        format_frame = ttk.Frame(parent, style="HighContrast.TFrame")
        format_frame.pack(fill="x", pady=(6, 0))
        inspect_button = ttk.Button(
            format_frame,
            text="Format prüfen",
            command=self._inspect_selected_track,
            style="HighContrast.TButton",
        )
        inspect_button.pack(side="left")
        self._bind_focus_highlight(
            inspect_button,
            "Button Format prüfen. Zeigt Kanäle, Bitbreite und Laufzeit an.",
        )
        convert_button = ttk.Button(
            format_frame,
            text="Als WAV normalisieren",
            command=self._normalise_selected_track,
            style="HighContrast.TButton",
        )
        convert_button.pack(side="left", padx=(8, 0))
        self._bind_focus_highlight(
            convert_button,
            "Button normalisieren. Erstellt bei Bedarf eine 16-Bit-WAV-Kopie im Ordner data/converted_audio.",
        )

        backend_hint = "Audiowiedergabe bereit" if self.audio_player.backend_available else "Audiowiedergabe benötigt Zusatzmodul"
        self.audio_status = ttk.Label(
            parent,
            text=f"{backend_hint} – Formatprüfung für WAV verfügbar",
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        )
        self.audio_status.pack(anchor="w", pady=(6, 0))
        if not self.audio_player.backend_available:
            self.play_button.state(["disabled"])

    def _build_info_center(self, parent: ttk.LabelFrame) -> None:
        notebook = ttk.Notebook(parent, style="HighContrast.TNotebook")
        notebook.pack(fill="both", expand=True)

        self._refresh_release_data()
        self._refresh_database_insights()

        def add_tab(title: str) -> ttk.Frame:
            scroll = ScrollableFrame(notebook, style="HighContrast.TFrame")
            scroll.canvas.configure(background=self.colors["background"])
            scroll.body.configure(style="HighContrast.TFrame")
            notebook.add(scroll, text=title)
            frame = ttk.Frame(scroll.body, padding=10, style="HighContrast.TFrame")
            frame.pack(fill="both", expand=True)
            return frame

        legend_frame = add_tab("Legende")
        build_legend_panel(legend_frame, self.colors)

        mockup_frame = add_tab("Mockup")
        build_mockup_panel(mockup_frame, self.colors)

        structure_frame = add_tab("Struktur")
        build_structure_panel(structure_frame, STRUCTURE_SCHEMA, self.colors)

        database_frame = add_tab("Daten")
        build_database_insights_panel(database_frame, self.database_insights_data, self.colors)

        quicklinks_frame = add_tab("Schnelllinks")
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
            (
                "Archiv als CSV",
                "Exportiert das Datenbank-Archiv nach data/exports/archive_export.csv",
                self._export_archive_csv,
            ),
            (
                "Archiv als JSON",
                "Exportiert das Datenbank-Archiv nach data/exports/archive_export.json",
                self._export_archive_json,
            ),
            (
                "Sicherheitsmanifest",
                "Prüfprotokoll der Checksummen öffnen",
                lambda: self._open_path(Path("data/security_manifest.json")),
            ),
            (
                "Backup-Ordner",
                "Versionierte Sicherungen ansehen",
                lambda: self._open_path(Path("data/backups")),
            ),
            (
                "Farbaudit",
                "Auswertung der Farbkontraste ansehen",
                lambda: self._open_path(Path("data/color_audit.json")),
            ),
            (
                "Diagnosebericht",
                "Systemdiagnose als JSON (Datenformat) öffnen",
                lambda: self._open_path(Path("data/diagnostics_report.json")),
            ),
        ]
        build_quicklinks_panel(quicklinks_frame, quick_links, self.colors)

        font_tips_frame = add_tab("Schrift")
        build_font_tips_panel(font_tips_frame, self.colors, float(self.font_scale_var.get()))

        contrast_frame = add_tab("Kontrast")
        build_contrast_panel(contrast_frame, self.colors)

        palette_frame = add_tab("Palette")
        build_palette_panel(palette_frame, self.colors)

        audit_frame = add_tab("Farbaudit")
        build_color_audit_panel(audit_frame, self.color_audit_data or None, self.colors)

        release_frame = add_tab("Release")
        build_release_panel(release_frame, self.release_items, self.release_progress_text, self.colors)

        security_frame = add_tab("Sicherheit")
        build_security_panel(security_frame, self.security_summary_data or None, self.colors)

        diagnostics_frame = add_tab("Diagnose")
        build_diagnostics_panel(diagnostics_frame, self.diagnostics_data or None, self.colors)

    def _build_log_viewer(self, parent: ttk.LabelFrame) -> None:
        ttk.Label(
            parent,
            text="Startprotokoll durchsuchen",
            font=self.fonts["heading"],
            style="HighContrast.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            parent,
            text=(
                "Begriff eingeben und auf 'Suchen' klicken. Ohne Begriff zeigt 'Neu laden' "
                "die letzten Meldungen aus logs/startup.log."
            ),
            wraplength=320,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
        ).pack(anchor="w", pady=(2, 6))

        search_frame = ttk.Frame(parent, style="HighContrast.TFrame")
        search_frame.pack(fill="x", pady=(0, 6))
        search_entry = ttk.Entry(search_frame, textvariable=self.log_search_var)
        search_entry.pack(side="left", fill="x", expand=True)
        self._bind_focus_highlight(
            search_entry,
            "Suchfeld aktiv. Begriff eingeben und Enter drückt die Suche.",
        )
        search_entry.bind("<Return>", lambda _event: self._search_logs())
        search_button = ttk.Button(
            search_frame,
            text="Suchen",
            command=self._search_logs,
            style="HighContrast.TButton",
        )
        search_button.pack(side="left", padx=(6, 0))
        self._bind_focus_highlight(
            search_button,
            "Button Startprotokoll durchsuchen. Enter startet die Suche.",
        )
        reload_button = ttk.Button(
            search_frame,
            text="Neu laden",
            command=self._reload_logs,
            style="HighContrast.TButton",
        )
        reload_button.pack(side="left", padx=(6, 0))
        self._bind_focus_highlight(
            reload_button,
            "Button neu laden. Zeigt die letzten Logzeilen ohne Filter.",
        )

        log_frame = ttk.Frame(parent, style="HighContrast.TFrame")
        log_frame.pack(fill="both", expand=True)
        self.log_listbox = tk.Listbox(
            log_frame,
            height=10,
            background=self.colors["surface"],
            foreground=self.colors["on_surface"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["surface"],
            font=self.fonts["body"],
            highlightthickness=2,
            highlightcolor=self.colors["accent"],
            highlightbackground=self.colors["background"],
        )
        self.log_listbox.pack(side="left", fill="both", expand=True)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_listbox.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_listbox.configure(yscrollcommand=log_scroll.set)
        self._bind_focus_highlight(
            self.log_listbox,
            "Logliste aktiv. Pfeiltasten bewegen den Fokus, Enter kopiert die Zeile in die Zwischenablage.",
        )
        self.log_listbox.bind(
            "<Return>",
            lambda _event: self._copy_log_selection(),
        )

        ttk.Button(
            parent,
            text="Logdatei öffnen",
            command=lambda: self._open_path(Path("logs/startup.log")),
            style="HighContrast.TButton",
        ).pack(anchor="w", pady=(6, 0))

        ttk.Label(
            parent,
            textvariable=self.log_status_var,
            style="HighContrast.TLabel",
            font=self.fonts["small"],
            wraplength=320,
        ).pack(anchor="w", pady=(4, 0))

        self._reload_logs()

    def _refresh_todo_list(self) -> None:
        items = self._load_todo_items()
        self.todo_entries = items
        if hasattr(self, "todo_list"):
            self.todo_list.delete(0, tk.END)
            done_count = 0
            for index, item in enumerate(items):
                if item.done:
                    done_count += 1
                self.todo_list.insert(tk.END, self._format_todo_item(item))
                if item.done:
                    self.todo_list.itemconfig(index, foreground=self.colors.get("accent_hover", self.colors["accent"]))
            if not items:
                self.todo_list.insert(tk.END, "Keine Aufgaben vorhanden")
        open_count = len([item for item in items if not item.done])
        done_count = len(items) - open_count
        if hasattr(self, "todo_summary_var"):
            if items:
                self.todo_summary_var.set(f"Offen: {open_count} | Erledigt: {done_count}")
            else:
                self.todo_summary_var.set("Noch keine Aufgaben gespeichert")
        if hasattr(self, "todo_status_var") and not items:
            self.todo_status_var.set("Im Menü 'todo.txt öffnen' neue Aufgaben ergänzen.")
        self._update_stats_overview(force=False)

    def _format_todo_item(self, item: TodoItem) -> str:
        status = "✔" if item.done else "⏳"
        due_text = item.due_date.strftime("%d.%m.%Y")
        return f"{status} {item.title} (bis {due_text})"

    def _update_stats_overview(self, force: bool = True) -> None:
        open_tasks = len([item for item in getattr(self, "todo_entries", []) if not item.done])
        summary = f"Sitzungen: {self.session_count}"
        summary += f" | Offene Aufgaben: {open_tasks}" if open_tasks else " | Alle Aufgaben erledigt"
        self.stats_overview = summary
        if force:
            self.stats_var.set(summary)

    def _refresh_playlist(self) -> None:
        self.playlist_entries = self._load_tracks()
        self.playlist_list.delete(0, tk.END)
        for track in self.playlist_entries:
            self.playlist_list.insert(tk.END, track.get("title", "Unbenannt"))

    def _toggle_selected_todo(self, _event: Optional[tk.Event] = None) -> str:
        if not getattr(self, "todo_entries", None):
            messagebox.showinfo("Aufgaben", "Keine Aufgaben vorhanden.")
            return "break"
        selection = self.todo_list.curselection()
        if not selection:
            messagebox.showinfo("Aufgaben", "Bitte zuerst eine Aufgabe auswählen.")
            return "break"
        index = selection[0]
        if index >= len(self.todo_entries):
            return "break"
        item = self.todo_entries[index]
        toggled = self.todo_module.toggle_item(item.title, item.due_date)
        if toggled:
            new_state = not item.done
            message = f"'{item.title}' ist jetzt {'erledigt' if new_state else 'offen'}."
            self.todo_status_var.set(message)
            self.stats_var.set(message)
            self.logger.info(
                "Aufgabe umgeschaltet: %s | erledigt=%s | fällig=%s",
                item.title,
                new_state,
                item.due_date.isoformat(),
            )
            # Toggle in memory copy for immediate feedback
            item.done = new_state
            self._refresh_todo_list()
            self.after(3500, self._update_stats_overview)
        else:
            messagebox.showwarning(
                "Aufgaben",
                "Der Aufgabenstatus konnte nicht geändert werden. Bitte todo_items.json prüfen.",
            )
            self.logger.warning("Aufgabe konnte nicht umgeschaltet werden: %s", item.title)
        return "break" if _event is not None else None

    def _on_todo_selected(self, _event: Optional[tk.Event] = None) -> None:
        selection = self.todo_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.todo_entries):
            return
        item = self.todo_entries[index]
        status_text = "erledigt" if item.done else "offen"
        self.todo_status_var.set(
            f"Ausgewählt: {item.title} – Status {status_text}, fällig am {item.due_date.strftime('%d.%m.%Y')}"
        )

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

    def _inspect_selected_track(self) -> None:
        if not self.playlist_list.curselection():
            messagebox.showinfo("Audiowiedergabe", "Bitte zuerst einen Titel auswählen.")
            return
        index = self.playlist_list.curselection()[0]
        track = self.playlist_entries[index]
        file_path = Path(track.get("path", ""))
        info = self.audio_inspector.inspect(file_path)
        if info is None:
            messagebox.showwarning("Audiowiedergabe", "Das Format konnte nicht geprüft werden.")
            return
        message = (
            f"Kanäle: {info.channels}, Samplebreite: {info.sample_width * 8}-Bit, "
            f"Abtastrate: {info.frame_rate} Hz, Dauer: {info.duration_seconds:.1f} s"
        )
        self.audio_status.configure(text=message)
        self.stats_var.set(f"Format geprüft: {track.get('title', 'Unbenannt')}")

    def _normalise_selected_track(self) -> None:
        if not self.playlist_list.curselection():
            messagebox.showinfo("Audiowiedergabe", "Bitte zuerst einen Titel auswählen.")
            return
        index = self.playlist_list.curselection()[0]
        track = self.playlist_entries[index]
        file_path = Path(track.get("path", ""))
        target = self.audio_inspector.normalise(file_path)
        if target is None:
            messagebox.showwarning(
                "Audiowiedergabe",
                "Das Format konnte nicht konvertiert werden. Bitte WAV-Dateien verwenden.",
            )
            return
        if target == file_path:
            messagebox.showinfo(
                "Audiowiedergabe",
                "Die Datei erfüllt bereits den Standard (16-Bit, maximal 2 Kanäle).",
            )
            self.audio_status.configure(text="Datei ist bereits kompatibel (16-Bit WAV)")
        else:
            messagebox.showinfo(
                "Audiowiedergabe",
                (
                    "Die normalisierte WAV-Datei wurde gespeichert unter:\n"
                    f"{target}"
                ),
            )
            self.audio_status.configure(
                text=f"Normalisierte Kopie gespeichert: {target.name}"
            )
        self.stats_var.set(f"Format normalisiert: {track.get('title', 'Unbenannt')}")

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

    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        if not timestamp:
            return "–"
        try:
            parsed = dt.datetime.fromisoformat(timestamp)
            return parsed.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            return str(timestamp)

    def _load_notes(self) -> None:
        NOTE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if NOTE_FILE.exists():
            self.note_text.insert("1.0", NOTE_FILE.read_text(encoding="utf-8"))

    def _save_notes(self) -> None:
        NOTE_FILE.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(NOTE_FILE, self.note_text.get("1.0", tk.END).strip(), logger=self.logger)
        self.stats_var.set("Notizen gespeichert")
        self.logger.info("Notizen gespeichert (%s)", NOTE_FILE)

    def _auto_save(self) -> None:
        current = self.note_text.get("1.0", tk.END)
        if current != self._notes_cache:
            self._notes_cache = current
            self._save_notes()
            self.logger.debug("Autospeichern ausgelöst")

    def _load_todo_items(self) -> List[TodoItem]:
        items = sorted(
            self.todo_module.load_items(),
            key=lambda entry: (entry.due_date, entry.title.lower()),
        )
        return items

    def _load_tracks(self) -> List[Dict[str, str]]:
        return self.playlist_manager.load_tracks()

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
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
        self.session_count = counter
        self._update_stats_overview()
        atomic_write_json(STATS_FILE, data, logger=self.logger)
        self.logger.info("Statistik aktualisiert: Sitzungen=%s", counter)

    def _save_stats(self) -> None:
        data = self._load_json(STATS_FILE)
        data["manual_update"] = dt.datetime.now().isoformat()
        atomic_write_json(STATS_FILE, data, logger=self.logger)
        self.stats_var.set("Statistik gespeichert")
        self.logger.info("Statistik manuell gespeichert.")

    def _load_selftest_summary(self) -> None:
        if not SELFTEST_FILE.exists():
            self.selftest_var.set("Selbsttest: noch keine Daten gespeichert")
            self.selftest_label.configure(foreground=self.colors.get("warning", self.colors["accent"]))
            self._apply_security_summary(None)
            self._apply_color_audit(None)
            return
        data = self._load_json(SELFTEST_FILE)
        if not data:
            self.selftest_var.set("Selbsttest: Daten konnten nicht gelesen werden")
            self.selftest_label.configure(foreground=self.colors.get("danger", self.colors["accent"]))
            self._apply_security_summary(None)
            self._apply_color_audit(None)
            return
        tests = [entry for entry in data.get("self_tests", []) if isinstance(entry, dict)]
        total = len(tests)
        passed = len([entry for entry in tests if entry.get("passed")])
        last_run = self._format_timestamp(data.get("last_run"))
        if total:
            message = f"Selbsttest: {passed}/{total} bestanden am {last_run}"
            color_key = "success" if passed == total else "danger"
        else:
            message = f"Selbsttest: keine Ergebnisse gespeichert (Stand {last_run})"
            color_key = "warning"
        self.selftest_var.set(message)
        self.selftest_label.configure(foreground=self.colors.get(color_key, self.colors["on_surface"]))
        self._apply_security_summary(data.get("security_summary"))
        self._apply_color_audit(data.get("color_audit"))
        diagnostics_snapshot = data.get("diagnostics")
        if isinstance(diagnostics_snapshot, dict) and diagnostics_snapshot:
            new_data = diagnostics_snapshot
        else:
            new_data = self.diagnostics_data or {}
        previous = getattr(self, "diagnostics_data", {})
        self._apply_diagnostics_summary(new_data)
        if new_data and new_data != previous and hasattr(self, "grid_cells") and len(self.grid_cells) > 3:
            for child in self.grid_cells[3].winfo_children():
                child.destroy()
            self._build_info_center(self.grid_cells[3])

    def _apply_security_summary(self, summary: Optional[Dict[str, object]]) -> None:
        if not hasattr(self, "security_label"):
            return
        if not isinstance(summary, dict) or not summary:
            self.security_summary_data = {}
            self.security_var.set("Datensicherheit: keine Prüfwerte vorhanden")
            self.security_label.configure(
                foreground=self.colors.get("warning", self.colors["accent"])
            )
            return

        self.security_summary_data = dict(summary)
        status = str(summary.get("status", "unknown"))
        verified = int(summary.get("verified", 0))
        issues = summary.get("issues", []) or []
        backups = summary.get("backups", []) or []
        pruned = summary.get("pruned_backups", []) or []
        timestamp = summary.get("timestamp", "")
        restore_points = summary.get("restore_points", []) or []
        restore_issues = summary.get("restore_issues", []) or []
        restore_ok = len([item for item in restore_points if item.get("status") == "ok"])

        if status == "ok":
            extra_cleanup = f" – {len(pruned)} alte Backups aufgeräumt" if pruned else ""
            extra_restore = (
                f" – {restore_ok} Wiederherstellungspunkte getestet" if restore_points else ""
            )
            message = (
                f"Datensicherheit: {verified} Dateien geprüft – ohne Auffälligkeiten"
                f"{extra_cleanup}{extra_restore} ({timestamp})"
            )
            color_key = "success"
        else:
            message = (
                f"Datensicherheit: {len(issues)} Hinweise, {len(backups)} Sicherungen, "
                f"{len(pruned)} Aufräumaktionen, {len(restore_issues)} Restore-Hinweise "
                f"({timestamp})"
            )
            color_key = "danger"
        self.security_var.set(message)
        self.security_label.configure(foreground=self.colors.get(color_key, self.colors["accent"]))

    def _apply_color_audit(self, audit: Optional[Dict[str, object]]) -> None:
        if not hasattr(self, "color_audit_label"):
            return
        if not isinstance(audit, dict) or not audit:
            self.color_audit_data = {}
            self.color_audit_var.set("Farbaudit: keine Auswertung gespeichert")
            self.color_audit_label.configure(
                foreground=self.colors.get("warning", self.colors["accent"])
            )
            return

        self.color_audit_data = dict(audit)
        status = str(audit.get("overall_status", "unknown"))
        themes = audit.get("themes", []) or []
        issues = audit.get("issues", []) or []
        worst_ratio = float(audit.get("worst_ratio", 0.0))
        timestamp = self._format_timestamp(audit.get("generated_at"))
        recommendations = audit.get("recommendations", []) or []

        if status != "ok":
            fallback_mode = "accessible"
            active_mode = getattr(self.preferences, "color_mode", fallback_mode)
            if active_mode != fallback_mode:
                self.preferences.color_mode = fallback_mode
                self.preferences.contrast_theme = fallback_mode
                self._configure_theme()
                self._refresh_theme_widgets(from_audit=True)
                self.stats_var.set(
                    "Farbschema automatisch auf barrierefreie Variante gestellt (Farbaudit)."
                )

        if status == "ok":
            message = (
                f"Farbaudit: {len(themes)} Schemata geprüft – Mindestkontraste erfüllt"
                f" ({timestamp})"
            )
            color_key = "success"
        else:
            message = (
                f"Farbaudit: {len(issues)} Hinweise, {len(recommendations)} Tipps, "
                f"niedrigster Kontrast {worst_ratio:.2f}:1 ({timestamp})"
            )
            color_key = "danger"

        self.color_audit_var.set(message)
        self.color_audit_label.configure(
            foreground=self.colors.get(color_key, self.colors["accent"])
        )

    def _apply_diagnostics_summary(self, diagnostics: Optional[Dict[str, object]]) -> None:
        if not hasattr(self, "diagnostics_label"):
            return
        if not isinstance(diagnostics, dict) or not diagnostics:
            self.diagnostics_data = {}
            self.diagnostics_var.set("Diagnose: keine Daten gespeichert")
            self.diagnostics_label.configure(
                foreground=self.colors.get("warning", self.colors["accent"])
            )
            return

        self.diagnostics_data = dict(diagnostics)
        summary = diagnostics.get("summary", {}) or {}
        issues = summary.get("issues", []) or []
        generated = self._format_timestamp(diagnostics.get("generated_at"))
        status = str(summary.get("status", "unknown"))
        html_path = diagnostics.get("html_report_path")
        if status == "ok" and not issues:
            message = f"Diagnose: System geprüft – keine Auffälligkeiten ({generated})"
            color_key = "success"
        else:
            message = f"Diagnose: {len(issues)} Hinweis(e) – Bericht {generated}"
            color_key = "danger" if issues else "warning"
        if html_path:
            message = f"{message} – HTML-Ansicht gespeichert"
        self.diagnostics_var.set(message)
        self.diagnostics_label.configure(
            foreground=self.colors.get(color_key, self.colors["accent"])
        )

    def _refresh_release_data(self) -> None:
        items = self.release_checklist.load_items()
        self.release_items = [item.to_dict() for item in items]
        progress = self.release_checklist.progress()
        if progress.get("total"):
            self.release_progress_text = (
                f"Fortschritt: {progress['done']} von {progress['total']} Aufgaben erledigt"
            )
        else:
            self.release_progress_text = "Noch keine Checkliste gespeichert."

    def _refresh_database_insights(self) -> None:
        try:
            self.database_insights_data = self.database_module.get_statistics()
        except Exception as exc:  # pragma: no cover - defensive catch
            self.logger.error("Datenbank-Auswertung fehlgeschlagen", exc_info=exc)
            self.database_insights_data = {}

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

    def _export_archive_csv(self) -> None:
        target = self.database_module.export_entries_to_csv()
        self.stats_var.set(f"Archiv als CSV gespeichert: {target.name}")
        self.logger.info("Archivexport CSV erzeugt: %s", target)

    def _export_archive_json(self) -> None:
        target = self.database_module.export_entries_to_json()
        self.stats_var.set(f"Archiv als JSON gespeichert: {target.name}")
        self.logger.info("Archivexport JSON erzeugt: %s", target)

    def _reload_logs(self) -> None:
        entries = self.log_reader.read_tail(limit=80)
        self._render_log_results(entries, term="")

    def _search_logs(self) -> None:
        term = self.log_search_var.get().strip()
        entries = self.log_reader.search(term, limit=80)
        self._render_log_results(entries, term=term)

    def _render_log_results(self, entries, term: str) -> None:
        if not hasattr(self, "log_listbox"):
            return
        self.log_listbox.delete(0, tk.END)
        for entry in entries:
            display = f"{entry.line_number:>5}: {entry.content}"
            self.log_listbox.insert(tk.END, display)
        count = len(entries)
        if term:
            if count:
                self.log_status_var.set(f"{count} Treffer für '{term}'")
            else:
                self.log_status_var.set(f"Keine Treffer für '{term}' gefunden.")
        else:
            self.log_status_var.set(f"Letzte {count} Zeilen aus logs/startup.log")

    def _copy_log_selection(self) -> str:
        selection = self.log_listbox.curselection()
        if not selection:
            return "break"
        text = self.log_listbox.get(selection[0])
        self.clipboard_clear()
        self.clipboard_append(text)
        self.stats_var.set("Logzeile kopiert (Zwischenablage)")
        return "break"

    # Theme helpers ---------------------------------------------------------
    def _init_style(self):
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
        style.configure(
            "HighContrast.Horizontal.TScale",
            background=self.colors["background"],
            troughcolor=self.colors["surface"],
        )
        style.map(
            "HighContrast.Horizontal.TScale",
            background=[("active", self.colors["accent_hover"])],
        )

    def _select_colors(self) -> Dict[str, str]:
        mode = getattr(self.preferences, "color_mode", None) or self.preferences.contrast_theme
        if mode not in THEME_ORDER:
            mode = THEME_ORDER[0]
        return get_theme_colors(mode)

    def _configure_fonts(self) -> None:
        scale = float(self.font_scale_var.get()) if hasattr(self, "font_scale_var") else 1.0
        clamped = max(0.8, min(1.6, scale))
        if abs(clamped - scale) > 1e-6 and hasattr(self, "font_scale_var"):
            self.font_scale_var.set(clamped)
        if not hasattr(self, "fonts"):
            self.fonts = {
                "title": tkfont.Font(family="Arial", weight="bold"),
                "heading": tkfont.Font(family="Arial", weight="bold"),
                "body": tkfont.Font(family="Arial"),
                "small": tkfont.Font(family="Arial"),
            }
            self._font_bases = {"title": 16, "heading": 14, "body": 12, "small": 10}
        for name, font in self.fonts.items():
            base_size = self._font_bases[name]
            font.configure(size=max(8, int(round(base_size * clamped))))
        style = self.style
        style.configure("HighContrast.TLabel", font=self.fonts["body"])
        style.configure("HighContrast.TButton", font=self.fonts["body"])
        style.configure("HighContrast.TLabelframe", font=self.fonts["heading"])
        style.configure("HighContrast.TNotebook.Tab", font=self.fonts["body"])
        style.configure("TLabel", font=self.fonts["body"])
        style.configure("TButton", font=self.fonts["body"])
        style.configure("Treeview.Heading", font=self.fonts["heading"])
        style.configure("Treeview", rowheight=max(20, int(round(24 * clamped))))
        default_font = tkfont.nametofont("TkDefaultFont")
        text_font = tkfont.nametofont("TkTextFont")
        heading_font = tkfont.nametofont("TkHeadingFont")
        menu_font = tkfont.nametofont("TkMenuFont")
        fixed_font = tkfont.nametofont("TkFixedFont")
        system_fonts = {
            default_font: 12,
            text_font: 12,
            heading_font: 14,
            menu_font: 11,
            fixed_font: 11,
        }
        for font_obj, base_size in system_fonts.items():
            font_obj.configure(family="Arial", size=max(8, int(round(base_size * clamped))))
        heading_font.configure(weight="bold")
        self.preferences.font_scale = clamped
        self._update_font_scale_display()

    def _on_font_scale_slider(self, _value: str) -> None:
        self._apply_font_scale(float(self.font_scale_var.get()))

    def _reset_font_scale(self) -> None:
        self._apply_font_scale(1.0)

    def _apply_font_scale(self, scale: float) -> None:
        clamped = max(0.8, min(1.6, float(scale)))
        if abs(self.font_scale_var.get() - clamped) > 1e-6:
            self.font_scale_var.set(clamped)
        self._configure_fonts()
        self._refresh_fonts_on_widgets()
        self._refresh_theme_widgets()
        self.stats_var.set(f"Schriftgröße gesetzt auf {int(round(clamped * 100))} %")

    def _refresh_fonts_on_widgets(self) -> None:
        if hasattr(self, "clock_label"):
            self.clock_label.configure(font=self.fonts["title"])
        if hasattr(self, "stats_label"):
            self.stats_label.configure(font=self.fonts["body"])
        if hasattr(self, "path_label"):
            self.path_label.configure(font=self.fonts["small"])
        if hasattr(self, "color_mode_label"):
            self.color_mode_label.configure(font=self.fonts["body"])
        if hasattr(self, "mode_selector"):
            self.mode_selector.configure(font=self.fonts["body"])
        if hasattr(self, "color_audit_label"):
            self.color_audit_label.configure(font=self.fonts["body"])
        if hasattr(self, "diagnostics_label"):
            self.diagnostics_label.configure(font=self.fonts["body"])
        if hasattr(self, "screenreader_hint_label"):
            self.screenreader_hint_label.configure(font=self.fonts["small"])
        if hasattr(self, "font_scale_label"):
            self.font_scale_label.configure(font=self.fonts["body"])
        if hasattr(self, "font_scale_value_label"):
            self.font_scale_value_label.configure(font=self.fonts["body"])
        if hasattr(self, "note_text"):
            self.note_text.configure(font=self.fonts["body"])
        if hasattr(self, "todo_list"):
            self.todo_list.configure(font=self.fonts["body"])
        if hasattr(self, "playlist_list"):
            self.playlist_list.configure(font=self.fonts["body"])
        if hasattr(self, "volume_label"):
            self.volume_label.configure(font=self.fonts["body"])
        if hasattr(self, "audio_status"):
            self.audio_status.configure(font=self.fonts["small"])
        if hasattr(self, "log_listbox"):
            self.log_listbox.configure(font=self.fonts["body"])

    def _update_font_scale_display(self) -> None:
        if hasattr(self, "font_scale_display_var"):
            percent = int(round(float(self.font_scale_var.get()) * 100))
            self.font_scale_display_var.set(f"{percent} %")

    def _bind_focus_highlight(self, widget: tk.Widget, message: str) -> None:
        widget.bind("<FocusIn>", lambda _event, text=message: self._announce_focus(text))

    def _announce_focus(self, message: str) -> None:
        self.stats_var.set(message)
        self.logger.info("Focus: %s", message)

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
        self.after(2500, self._update_stats_overview)

    def _refresh_theme_widgets(self, *, from_audit: bool = False) -> None:
        if hasattr(self, "note_text"):
            self.note_text.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                insertbackground=self.colors["accent"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
                highlightbackground=self.colors["background"],
                highlightcolor=self.colors["accent"],
            )
        if hasattr(self, "todo_list"):
            self.todo_list.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
                highlightbackground=self.colors["background"],
                highlightcolor=self.colors["accent"],
            )
        if hasattr(self, "playlist_list"):
            self.playlist_list.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
                highlightbackground=self.colors["background"],
                highlightcolor=self.colors["accent"],
            )
        if hasattr(self, "log_listbox"):
            self.log_listbox.configure(
                background=self.colors["surface"],
                foreground=self.colors["on_surface"],
                selectbackground=self.colors["accent"],
                selectforeground=self.colors["surface"],
                highlightbackground=self.colors["background"],
                highlightcolor=self.colors["accent"],
            )
        for child in self.grid_cells[3].winfo_children():
            child.destroy()
        self._build_info_center(self.grid_cells[3])
        if hasattr(self, "log_listbox"):
            for child in self.grid_cells[4].winfo_children():
                child.destroy()
            self._build_log_viewer(self.grid_cells[4])
        if hasattr(self, "todo_entries"):
            self._refresh_todo_list()
        self._load_selftest_summary()
        self._apply_security_summary(self.security_summary_data or None)
        if not from_audit:
            self._apply_color_audit(self.color_audit_data or None)



__all__ = ["MainWindow"]
