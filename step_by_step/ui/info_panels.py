"""Reusable info panels for the STEP-BY-STEP dashboard."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Iterable, Optional, Sequence, Tuple

LegendEntry = Tuple[str, str]
QuickLink = Tuple[str, str, Callable[[], None]]


def build_legend_panel(parent: ttk.LabelFrame, colors: Optional[Dict[str, str]] = None) -> None:
    """Create a legend that explains core tool areas in simple language."""
    description = ttk.Label(
        parent,
        text="Legende (Erklärung der Bereiche)",
        font=("Arial", 12, "bold"),
    )
    description.pack(anchor="w")

    legend_items: Iterable[LegendEntry] = (
        ("Dashboard", "Zentrale Übersicht mit Uhrzeit, Status und Speicherort."),
        (
            "Notizen",
            "Freies Textfeld zum Mitschreiben. Speichert automatisch beim Verlassen.",
        ),
        (
            "ToDo",
            "Liste offener Aufgaben. Zeigt Vorschau aus der Aufgabenverwaltung.",
        ),
        (
            "Playlist",
            "Anzeige gespeicherter Titel. Dient als Ausgangspunkt für den Audioplayer.",
        ),
        (
            "Legende & Mockup",
            "Hilfsbereich mit Erklärung, Entwurfsskizze (Mockup) und Strukturplan.",
        ),
    )

    for title, explanation in legend_items:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{title}:", font=("Arial", 10, "bold")).pack(side="left")
        ttk.Label(
            row,
            text=explanation,
            wraplength=240,
            justify="left",
        ).pack(side="left", padx=(5, 0))


def build_mockup_panel(parent: ttk.LabelFrame, colors: Optional[Dict[str, str]] = None) -> None:
    """Create a simple text-based mockup that illustrates the grid layout."""
    ttk.Label(parent, text="Mockup (Entwurf)", font=("Arial", 12, "bold")).pack(anchor="w")
    mockup_text = tk.Text(parent, height=8, width=40, wrap="word", relief="groove")
    if colors:
        mockup_text.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            insertbackground=colors.get("accent", "black"),
        )
    mockup_text.pack(fill="both", expand=True, pady=(5, 0))
    mockup_text.insert(
        "1.0",
        """
+-------------------+-------------------+-------------------+
|  Notizen          |  ToDo Vorschau    |  Playlist         |
+-------------------+-------------------+-------------------+
|  Legende & Hilfe  |  Frei für Module  |  Frei für Module  |
+-------------------+-------------------+-------------------+
|  Strukturplan     |  Frei für Module  |  Frei für Module  |
+-------------------+-------------------+-------------------+
        """.strip()
    )
    mockup_text.configure(state="disabled")


def build_structure_panel(
    parent: ttk.LabelFrame, schema: Dict[str, Dict], colors: Optional[Dict[str, str]] = None
) -> None:
    """Render a folder structure tree view from a nested dictionary schema."""
    ttk.Label(parent, text="Ordner- und Dateistruktur", font=("Arial", 12, "bold")).pack(
        anchor="w"
    )
    tree = ttk.Treeview(parent, show="tree", height=10)
    if colors:
        tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    tree.pack(fill="both", expand=True, pady=(5, 0))

    def insert_nodes(parent_id: str, node_schema: Dict[str, Dict]) -> None:
        for name, children in sorted(node_schema.items()):
            node_id = tree.insert(parent_id, "end", text=name)
            if isinstance(children, dict) and children:
                insert_nodes(node_id, children)

    insert_nodes("", schema)


def build_quicklinks_panel(
    parent: ttk.LabelFrame,
    links: Sequence[QuickLink],
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Render accessible quick actions for common tool workflows."""

    ttk.Label(parent, text="Schnelllinks", font=("Arial", 12, "bold")).pack(anchor="w")
    ttk.Label(
        parent,
        text=(
            "Tipp: Wählen Sie einen Button, um eine häufige Aktion zu starten. "
            "Alle Links besitzen eine Kurzbeschreibung."
        ),
        wraplength=260,
        justify="left",
    ).pack(anchor="w", pady=(2, 8))

    for label, description, command in links:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)
        button = ttk.Button(frame, text=label, command=command)
        if colors:
            button.configure(style="HighContrast.TButton")
        button.pack(side="left")
        ttk.Label(
            frame,
            text=description,
            wraplength=200,
            justify="left",
        ).pack(side="left", padx=(8, 0))


__all__ = [
    "build_legend_panel",
    "build_mockup_panel",
    "build_structure_panel",
    "build_quicklinks_panel",
]
